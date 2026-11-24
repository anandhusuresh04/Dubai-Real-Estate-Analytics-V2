"""Deliberate unavailable-content states (not fake analytics)."""
from html import escape

REASONS = {
    'phase3':('Analytical content in preparation','This section is reserved for Phase 3. No research result is displayed in this Phase 2 skeleton.'),
    'missing_artifact':('Required research data unavailable','The validated source file could not be verified. No substitute estimates are displayed.'),
    'unsupported_filter':('Unsupported selection','This filter combination changes the approved estimate or has no verified output.'),
    'withheld':('Result withheld','The claim is not individually authorized for publication.'),
    'not_estimable':('Not estimable','The research did not meet its prespecified identification or support requirement.'),
    'release_blocked':('Research release unavailable','Scientific publication checks have not been verified for this environment.'),
}

def empty_state(st, reason: str = 'phase3', *, title: str | None = None, detail: str | None = None):
    if reason not in REASONS:
        raise ValueError(f'Unknown empty-state type: {reason}')
    default_title, default_detail = REASONS[reason]
    st.markdown('<div class="v2-placeholder" role="status">'
                f'<div class="v2-placeholder-name">{escape(title or default_title)}</div>'
                f'<div class="v2-placeholder-desc">{escape(detail or default_detail)}</div>'
                '</div>',unsafe_allow_html=True)
