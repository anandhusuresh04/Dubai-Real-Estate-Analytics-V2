"""Fail-closed release, RQ, and individual-claim publication authorization."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import pandas as pd
import numpy as np
from .data_access import read_artifact

class PermissionDenied(RuntimeError): pass

APPROVED_RELEASE = 'APPROVED_WITH_QUALIFICATIONS'
RQ_STATES = frozenset({'SUPPORTED','QUALIFIED'})


def _bool(value: object) -> bool:
    """Do not use Python bool('False') == True for CSV values."""
    if isinstance(value, (bool, np.bool_)):return bool(value)
    if isinstance(value, str) and value.strip().lower() in ('true','false'):
        return value.strip().lower()=='true'
    if pd.isna(value):return False
    raise PermissionDenied(f'Invalid Boolean permission: {value!r}')

@dataclass(frozen=True)
class Permissions:
    release_status: str
    approved: bool
    rq_table: pd.DataFrame
    dashboard_table: pd.DataFrame
    claim_table: pd.DataFrame

    @classmethod
    def load(cls, root: Path) -> 'Permissions':
        run=read_artifact(root,'06_reproducibility_acceptance')
        rqs=read_artifact(root,'06_final_research_decisions')
        page=read_artifact(root,'06_dashboard_readiness')
        claims=read_artifact(root,'06_subclaim_evidence_register')
        if len(run)!=1:raise PermissionDenied('Ambiguous final release record')
        release=str(run.iloc[0]['release_status'])
        approved=release==APPROVED_RELEASE and _bool(run.iloc[0]['ready_for_qualified_publication'])
        rqids={f'RQ{i:02}' for i in range(1,16)}
        if set(rqs['rq_id'].astype(str))!=rqids or rqs['rq_id'].duplicated().any():
            raise PermissionDenied('RQ registry does not uniquely cover all 15 questions')
        if not set(page['rq'].astype(str)).issubset(rqids):
            raise PermissionDenied('Unknown RQ in dashboard permissions')
        if page[['page','rq']].duplicated().any():
            raise PermissionDenied('Duplicate page/RQ permissions')
        if not approved and page['publishable'].map(_bool).any():
            raise PermissionDenied('Contradiction: publishable RQ with blocked release')
        return cls(release,approved,rqs,page,claims)

    def authorize_metric(self, *, page: str, rq: str, artifact_verified: bool,
                         evidence_label: str = 'observed') -> None:
        if not self.approved:raise PermissionDenied(f'Release not approved: {self.release_status}')
        matched=self.dashboard_table.loc[(self.dashboard_table['page']==page) & (self.dashboard_table['rq']==rq)]
        if len(matched)!=1 or not _bool(matched.iloc[0]['publishable']):
            raise PermissionDenied(f'RQ not approved for {page}: {rq}')
        r=self.rq_table.loc[self.rq_table.rq_id==rq]
        if len(r)!=1 or str(r.iloc[0]['final_status']) not in RQ_STATES:
            raise PermissionDenied(f'Unapproved scientific status for {rq}')
        if not artifact_verified:
            raise PermissionDenied('Artifact has not passed physical readback/hash/schema checks')
        if evidence_label not in ('observed','qualified_association','methodology'):
            raise PermissionDenied('Interpretation category not supported')

    def authorize_claim(self, claim_id: str) -> pd.Series:
        if not self.approved:raise PermissionDenied('Release not approved')
        match=self.claim_table.loc[self.claim_table['upstream_claim_id'].astype(str)==str(claim_id)]
        if len(match)!=1:raise PermissionDenied(f'Unknown or duplicate claim ID: {claim_id}')
        row=match.iloc[0]
        if not _bool(row['published']):raise PermissionDenied(f'Claim withheld: {claim_id}')
        if 'release_approved' in row.index and not _bool(row['release_approved']):
            raise PermissionDenied(f'Claim release not approved: {claim_id}')
        if str(row['rq_id']) not in set(self.rq_table.rq_id.astype(str)):
            raise PermissionDenied('Claim RQ mapping invalid')
        return row
