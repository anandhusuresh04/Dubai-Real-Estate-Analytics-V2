"""One entry point for artifact-bound, approved metric retrieval.

Consumers cannot manually assert artifact_verified=True. Release and physical
artifact integrity are checked before returning data. Phase 1 only: no UI.
"""
from __future__ import annotations
from pathlib import Path
from .artifact_registry import get_artifact
from .claim_permissions import Permissions, PermissionDenied
from .data_access import read_artifact, sha256_file, ArtifactError
from .integrity import verify_06_manifest_entry, validate_06_release_pair
from .metric_contracts import METRICS, validate_filter, UnsupportedInteraction

# Notebook 06 approved five research source pages. The sixth-page executive
# landing view reuses those approved *source-page* permissions without inventing
# a new scientific claim or changing an estimand.
SOURCE_PAGE_BY_RQ={
    'RQ01':'Price Reality','RQ02':'Price Reality','RQ03':'Price Reality',
    'RQ04':'Market Overview','RQ05':'Market Overview','RQ06':None,
    'RQ07':'Community Intelligence','RQ08':'Community Intelligence',
    'RQ09':'Community Intelligence','RQ10':'Market Structure',
    'RQ11':'Market Structure','RQ12':'Market Structure',
    'RQ13':'Community Intelligence','RQ14':'Price Reality',
    'RQ15':'Data Reliability',
}


def load_approved_metric(root: Path, metric_name: str, filters: dict[str, object],
                         *, trusted_upstream_sha256: str | None = None,
                         claim_id: str | None = None):
    """Return only a verified, approved, exact-grain metric table slice.

    `trusted_upstream_sha256` must come from an independently verified upstream
    manifest, not a digest computed opportunistically on the requested file.
    Without it, upstream metrics are withheld rather than assumed approved.
    """
    root=Path(root)
    metric=validate_filter(metric_name,filters)
    spec=get_artifact(metric.artifact)
    perms=Permissions.load(root)
    validate_06_release_pair(root)
    source_page=SOURCE_PAGE_BY_RQ.get(metric.rq)
    if source_page is None:raise PermissionDenied('Metric not eligible for dashboard publication')
    if spec.owner=='06':
        verify_06_manifest_entry(root,spec.key)
        expected=None
    else:
        if not trusted_upstream_sha256:
            raise PermissionDenied('No independently trusted upstream artifact hash supplied')
        expected=trusted_upstream_sha256
    data=read_artifact(root,spec.key,expected_hash=expected)
    validate_filter(metric_name,filters,available_columns=tuple(data.columns))
    perms.authorize_metric(page=source_page,rq=metric.rq,artifact_verified=True)
    if claim_id:
        allowed=perms.authorize_claim(claim_id)
        if str(allowed['rq_id'])!=metric.rq:
            raise PermissionDenied('Claim does not belong to metric RQ')
    for col,val in filters.items():
        # Use stable string matching for user selectors; never coerce missing
        # categories into a real selected category.
        data=data.loc[data[col].notna() & data[col].astype(str).eq(str(val))]
    if data.empty:
        raise UnsupportedInteraction('No precomputed approved data for selected filters')
    return data.copy()
