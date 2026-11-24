"""Read-only Phase 1 scientific authorization. Never calculate research metrics."""
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class ReleaseView:
    authorized: bool
    status: str
    explanation: str
    rq_count: int = 0
    claim_count: int = 0


def check_release(root: Path) -> ReleaseView:
    """Fail closed on any release, integrity, permission, or missing-file problem.

    This check is deliberately small and performed per selected page rerun.
    It never modifies upstream artifacts, and never substitutes synthetic evidence.
    """
    try:
        from app_core.claim_permissions import Permissions
        from app_core.integrity import validate_06_release_pair
        validate_06_release_pair(Path(root))
        perms = Permissions.load(Path(root))
        if not perms.approved:
            return ReleaseView(False, perms.release_status, 'The scientific publication gate is not approved.')
        return ReleaseView(True, perms.release_status,
            'Approved with qualifications. Claim-level permissions and restrictions remain mandatory.',
            len(perms.rq_table), len(perms.claim_table))
    except (Exception) as exc:
        # The application shell remains accessible; no research result is authorized.
        # Avoid disclosing local paths or sensitive exception details to public viewers.
        return ReleaseView(False, 'UNAVAILABLE',
                           'Validated release files or their integrity checks are unavailable. '
                           'Research figures are withheld until the evidence is restored.')


def require_claim(root: Path, claim_id: str):
    """Explicit Phase 1 authorization API for later analytical phases.

    Raises PermissionDenied for missing or withheld claims. No UI override.
    """
    from app_core.claim_permissions import Permissions
    from app_core.integrity import validate_06_release_pair
    validate_06_release_pair(Path(root))
    return Permissions.load(Path(root)).authorize_claim(claim_id)
