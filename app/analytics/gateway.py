"""Single fail-closed Phase 3 reader on top of Phase 1 contracts.

Upstream artifacts need a separately generated, explicit local integrity attestation;
a filename or a matching data type is not publication permission. The attestation
binds fixed bytes to the approved research source and final Notebook 06 release.
"""
from __future__ import annotations
import json
from pathlib import Path
from functools import lru_cache
import pandas as pd
from app_core.artifact_registry import SOURCE_SHA256, get_artifact, resolve_artifact
from app_core.claim_permissions import Permissions, PermissionDenied
from app_core.data_access import read_artifact, sha256_file
from app_core.integrity import validate_06_release_pair, verify_06_manifest_entry
from app_core.approved_data import SOURCE_PAGE_BY_RQ, load_approved_metric
from app_core.metric_contracts import METRICS
from .catalog import Exhibit, CLAIM_EXHIBIT_BINDINGS

ATTESTATION = Path('reports/tables/dashboard_upstream_attestation.json')

class EvidenceUnavailable(RuntimeError):
    """Expected research evidence is missing, untrusted or unsuited to this exhibit."""


def attested_hash(root: Path, key: str) -> str:
    path = Path(root) / ATTESTATION
    if not path.is_file():
        raise EvidenceUnavailable('Upstream integrity attestation not installed. Run the Phase 3 local verification script.')
    obj = json.loads(path.read_text(encoding='utf-8'))
    if obj.get('source_sha256') != SOURCE_SHA256 or obj.get('release_status') != 'APPROVED_WITH_QUALIFICATIONS':
        raise EvidenceUnavailable('Integrity attestation does not bind the frozen approved research source.')
    if obj.get('attestation_version') != 1:
        raise EvidenceUnavailable('Unsupported integrity attestation version.')
    record = obj.get('artifacts',{}).get(key)
    if not isinstance(record,dict) or not record.get('verified'):
        raise EvidenceUnavailable(f'No trusted upstream attestation for {key}.')
    if record.get('relative_path') != get_artifact(key).relative_path.as_posix():
        raise EvidenceUnavailable('Attested file location differs from the approved registry.')
    hash_value = record.get('sha256')
    if not isinstance(hash_value,str) or len(hash_value)!=64:
        raise EvidenceUnavailable('Missing upstream integrity digest.')
    return hash_value


def published_claims(perms: Permissions, rq: str) -> tuple[str,...]:
    """Never count a qualified RQ as publishing every component claim."""
    result=[]
    for _,row in perms.claim_table.iterrows():
        if str(row.get('rq_id'))!=rq: continue
        claim=str(row.get('upstream_claim_id',''))
        if not claim: continue
        try: perms.authorize_claim(claim)
        except PermissionDenied: continue
        result.append(claim)
    return tuple(sorted(set(result)))


def _validated_release(root: Path) -> Permissions:
    validate_06_release_pair(root)
    perms = Permissions.load(root)
    if not perms.approved: raise EvidenceUnavailable('Research publication is not approved.')
    return perms


def load_exhibit(root: Path, exhibit: Exhibit, *, filters: dict[str,object]|None=None,
                 claim_id: str|None=None) -> pd.DataFrame:
    """Return full precomputed source rows after release, RQ, hash, and claim checks.

    No grouping or aggregation occurs. The chart renderer also requires an exact
    supported x/y field, and never computes a new median, index or model.
    """
    root=Path(root)
    filters=filters or {}
    invalid=set(filters)-set(exhibit.filters)
    if invalid:raise EvidenceUnavailable(f'Unsupported filter(s) for this exhibit: {sorted(invalid)}')
    if any(value is None for value in filters.values()):
        raise EvidenceUnavailable('Null is not an approved selection.')
    try:
        perms=_validated_release(root)
        page=SOURCE_PAGE_BY_RQ.get(exhibit.rq)
        if page is None: raise EvidenceUnavailable('Research question is not approved for publication.')
        spec=get_artifact(exhibit.artifact)
        if exhibit.claim_sensitive:
            choices=published_claims(perms,exhibit.rq)
            if not choices:
                raise EvidenceUnavailable(f'No individually published claim is available for {exhibit.rq}.')
            if not claim_id:
                raise EvidenceUnavailable('Select an individually published claim before opening this comparison.')
            if claim_id not in choices or claim_id not in CLAIM_EXHIBIT_BINDINGS.get(exhibit.id,()):
                raise EvidenceUnavailable('Selected claim is not individually published and explicitly bound to this exhibit.')
            row=perms.authorize_claim(claim_id)
            if str(row['rq_id'])!=exhibit.rq:
                raise EvidenceUnavailable('Claim and chart research question do not match.')
        if spec.owner=='06':
            verify_06_manifest_entry(root,spec.key)
            df=read_artifact(root,spec.key)
        else:
            hash_value=attested_hash(root,spec.key)
            # Use existing Phase 1 metric gateway wherever there is an exact
            # matching metric contract. Otherwise use its same scientific checks.
            matching=[m for m in METRICS.values() if m.artifact==spec.key and m.rq==exhibit.rq]
            if matching and set(filters).issubset(set(matching[0].filter_fields)):
                df=load_approved_metric(root,matching[0].name,filters,
                       trusted_upstream_sha256=hash_value,claim_id=claim_id)
                filters={}
            else:
                df=read_artifact(root,spec.key,expected_hash=hash_value)
        perms.authorize_metric(page=page,rq=exhibit.rq,artifact_verified=True)
        for col,value in filters.items():
            if col not in df.columns:raise EvidenceUnavailable(f'Approved artifact has no {col!r} selection dimension.')
            df=df.loc[df[col].notna() & df[col].astype(str).eq(str(value))]
        # Per-estimate support is independent of the enclosing RQ decision.
        if exhibit.id=='community_growth':
            if not {'matched_price_eligible','decision'}.issubset(df.columns):
                raise EvidenceUnavailable('Community eligibility columns unavailable.')
            eligible=df['matched_price_eligible'].astype(str).str.lower().eq('true')
            df=df.loc[eligible & df['decision'].astype(str).eq('QUALIFIED')]
        elif exhibit.id=='bedroom_estimate':
            if not {'term','decision','association_pct'}.issubset(df.columns):
                raise EvidenceUnavailable('Bedroom coefficient support columns unavailable.')
            # A size-control coefficient is not a bedroom contrast.
            df=df.loc[df['decision'].astype(str).eq('QUALIFIED')]
            support=read_artifact(root,'05_bedroom_contrast_support',
                         expected_hash=attested_hash(root,'05_bedroom_contrast_support'))
            required={'term','decision','area_overlap_supported'}
            if not required.issubset(support.columns):
                raise EvidenceUnavailable('Independent bedroom support gates unavailable.')
            allowed=support.loc[support['decision'].astype(str).eq('QUALIFIED') &
                support['area_overlap_supported'].astype(str).str.lower().eq('true'),'term']
            df=df.loc[df['term'].astype(str).isin(allowed.astype(str))]
        elif exhibit.id=='matched_index' and 'supported' in df.columns:
            df=df.loc[df['supported'].astype(str).str.lower().eq('true')]
        if df.empty: raise EvidenceUnavailable('No individually supported, approved precomputed rows for this selection.')
        return df.copy()
    except EvidenceUnavailable:raise
    except (Exception) as exc:
        # The exception is surfaced only to a local diagnostics pane, not to the
        # public visitor, which sees a short evidence-unavailable explanation.
        raise EvidenceUnavailable(f'Integrity or publication gate rejected {exhibit.artifact}: {type(exc).__name__}') from exc


def select_columns(frame: pd.DataFrame, exhibit: Exhibit) -> tuple[str,str,str|None]:
    """Reject unknown table shapes rather than choosing the first numeric column."""
    cols=set(frame.columns)
    x=next((c for c in exhibit.dimension if c in cols),None)
    y=next((c for c in exhibit.value if c in cols),None)
    z=next((c for c in exhibit.segment if c in cols),None)
    if exhibit.kind!='table' and (x is None or y is None):
        raise EvidenceUnavailable(f'{exhibit.artifact}: chart columns not verified for this schema.')
    if exhibit.kind=='table' and (x is None or y is None):
        raise EvidenceUnavailable(f'{exhibit.artifact}: required table columns not available.')
    if x==y:raise EvidenceUnavailable('Dimension and measure cannot refer to the same column.')
    return x,y,z


def exact_period(frame:pd.DataFrame, column:str='year',*, start:int=2010,end:int=2025)->pd.DataFrame:
    """Subset historical rows; never introduce 2026 provisional data."""
    if column not in frame.columns:return frame
    years=pd.to_numeric(frame[column],errors='coerce')
    return frame.loc[years.between(start,end,inclusive='both')].copy()
