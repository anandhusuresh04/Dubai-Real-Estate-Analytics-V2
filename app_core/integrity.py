"""Physical hash verification against the *saved* Notebook 06 export manifest.

This is distinct from the publication permission and from schema readability.
"""
from __future__ import annotations
from pathlib import Path
import pandas as pd
from .artifact_registry import get_artifact
from .data_access import ArtifactError, read_artifact, sha256_file


def verify_06_manifest_entry(root: Path, artifact_key: str) -> None:
    spec=get_artifact(artifact_key)
    if spec.owner!='06':
        raise ArtifactError('Notebook 06 manifest cannot certify upstream artifacts')
    if artifact_key=='06_export_manifest':
        # Self-reference prohibited. Readability may be tested; integrity must
        # be established from an independently supplied trusted manifest hash.
        raise ArtifactError('Manifest cannot certify its own hash')
    manifest=read_artifact(root,'06_export_manifest',required_columns=('name','status','csv_sha256','parquet_sha256'))
    rows=manifest.loc[manifest.name.astype(str)==artifact_key]
    if len(rows)!=1 or str(rows.iloc[0].status)!='VERIFIED':
        raise ArtifactError(f'Missing/invalid manifest entry: {artifact_key}')
    digest_col='parquet_sha256' if spec.fmt=='parquet' else 'csv_sha256'
    claimed=str(rows.iloc[0][digest_col])
    if len(claimed)!=64 or any(ch not in '0123456789abcdef' for ch in claimed.lower()):
        raise ArtifactError('Missing valid 64-character SHA-256')
    from .artifact_registry import resolve_artifact
    filename=resolve_artifact(root, artifact_key)
    if not filename.is_file() or sha256_file(filename)!=claimed:
        raise ArtifactError(f'File differs from verified final manifest: {artifact_key}')


def validate_06_release_pair(root: Path) -> None:
    """Reject contradictory final release, manifest, or claim permissions."""
    from .claim_permissions import Permissions
    perms=Permissions.load(root)
    for key in ('06_dashboard_readiness','06_reproducibility_acceptance',
                '06_final_research_decisions','06_subclaim_evidence_register',
                '06_finalization_checks'):
        verify_06_manifest_entry(root,key)
    checks=read_artifact(root,'06_finalization_checks')
    if not checks.passed.map(lambda v: str(v).lower()=='true').all():
        raise ArtifactError('A mandatory finalization check failed')
    issues_path=root/'reports/tables/06_final_issue_register.csv'
    # The issue table is permitted to have zero rows; no_data failure in the
    # generic data reader is intentionally bypassed for this terminal ledger.
    if not issues_path.is_file():
        raise ArtifactError('Missing final issue register')
    issues=pd.read_csv(issues_path,dtype='string',keep_default_na=False)
    if 'severity' not in issues:
        raise ArtifactError('Issue ledger has no severity column')
    if issues['severity'].eq('BLOCKED').any():
        raise ArtifactError('Unresolved critical issue in final ledger')
    if not perms.approved:
        raise ArtifactError('Release blocked by Notebook 06')
