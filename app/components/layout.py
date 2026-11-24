"""Research-grade six-page presentation shell; no estimation and no data-driven claims."""
from html import escape
from app.config import get_settings
from app.content import GUIDES, MODULE_DESCRIPTIONS
from app.navigation import PAGES
from app.runtime import check_release
from app.components.header import page_header
from app.components.status import status_badge
from app.components.evidence import evidence_panel
from app.components.empty_state import empty_state
from app.components.footer import page_footer


def _module_card(position: int, title: str, description: str) -> str:
    return (
        '<article class="v2-module" aria-label="Planned analytical module">'
        '<div class="v2-module-top">'
        f'<span class="v2-module-no">{position:02d} / MODULE</span>'
        '<span class="v2-module-state">PLANNED · PHASE 3</span></div>'
        f'<div class="v2-module-title">{escape(title)}</div>'
        f'<div class="v2-module-desc">{escape(description)}</div>'
        '</article>'
    )


def _context_card(question: str, guide) -> str:
    return (
        '<section class="v2-panel v2-panel--ink" aria-label="Research question">'
        '<div class="v2-panel-kicker">Research question</div>'
        f'<p class="v2-lead">{escape(question)}</p>'
        f'<p class="v2-body">{escape(guide.purpose)}</p>'
        '<div class="v2-rule"></div>'
        '<div class="v2-side-label">Interpretation boundary</div>'
        f'<p class="v2-body">{escape(guide.non_inference)}</p>'
        '</section>'
    )


def render_shell(st, spec) -> None:
    settings = get_settings()
    release = check_release(settings.project_root)
    guide = GUIDES[spec.key]
    index = next(i for i, item in enumerate(PAGES, 1) if item.key == spec.key)

    page_header(st, spec.title, spec.subtitle,
                breadcrumb='DUBAI REAL ESTATE  /  RESEARCH INTELLIGENCE', page_number=index)
    if release.authorized:
        st.markdown(
            '<div class="v2-strip" role="status">'
            '<div class="v2-strip-label"><span class="v2-dot"></span>'
            'Validated research foundation</div>'
            '<div class="v2-strip-sub">Release approved with qualifications · '
            'Metric-specific and claim-specific permissions remain mandatory.</div>'
            '</div>', unsafe_allow_html=True)
    else:
        st.markdown(
            '<div class="v2-strip" role="alert">'
            '<div class="v2-strip-label"><span class="v2-dot v2-dot--blocked"></span>'
            'Publication access restricted</div>'
            '<div class="v2-strip-sub">Research release unavailable · Empirical findings withheld.</div>'
            '</div>', unsafe_allow_html=True)
        empty_state(st, 'release_blocked', detail=release.explanation)

    st.markdown('<div class="v2-section-head"><div class="v2-section-title">Research workspace</div>'
                '<div class="v2-section-meta">FROZEN 2010–2025 &nbsp; / &nbsp; REGISTERED SALES &nbsp; / &nbsp; NOMINAL AED</div>'
                '</div>', unsafe_allow_html=True)
    module_descriptions = MODULE_DESCRIPTIONS[spec.key]
    # Existing static research guide describes each module's intent, never its observed result.
    module_markup = ''.join(_module_card(i, section,
        module_descriptions[i-1] if i-1 < len(module_descriptions) else 'Approved analytical content will be introduced after scientific checks.')
        for i, section in enumerate(spec.sections, 1))
    st.markdown(
        '<div class="v2-overview"><section aria-label="Planned dashboard modules">'
        '<div class="v2-section-head"><div class="v2-panel-kicker">01 &nbsp; / &nbsp; ANALYTICAL MODULES</div>'
        '<div class="v2-section-meta">Structure ready · No published figures in Phase 2</div></div>'
        f'<div class="v2-modules">{module_markup}</div>'
        '</section>' + _context_card(spec.question, guide) + '</div>', unsafe_allow_html=True)

    st.markdown('<div style="height:1.2rem" aria-hidden="true"></div>', unsafe_allow_html=True)
    overview, evidence = st.tabs(['Evidence & methods', 'Publication safeguards'])
    with overview:
        st.markdown('<div class="v2-section-head"><div class="v2-section-title">Methodological guardrails</div>'
                    '<div class="v2-section-meta">Reference context · not an empirical estimate</div></div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="v2-evidence-layout">'
            '<div class="v2-evidence-item"><div class="v2-evidence-name">Primary audience</div>'
            f'<div class="v2-evidence-text">{escape(guide.audience)}</div></div>'
            '<div class="v2-evidence-item"><div class="v2-evidence-name">Research coverage</div>'
            f'<div class="v2-evidence-text">{escape(", ".join(guide.question_ids))}</div></div>'
            '<div class="v2-evidence-item"><div class="v2-evidence-name">Approved selection principle</div>'
            f'<div class="v2-evidence-text">{escape(guide.selection_rule)}</div></div>'
            '<div class="v2-evidence-item"><div class="v2-evidence-name">Interpretation boundary</div>'
            f'<div class="v2-evidence-text">{escape(guide.non_inference)}</div></div>'
            '</div>', unsafe_allow_html=True)
    with evidence:
        st.markdown('<div class="v2-section-title">Release and claim safeguards</div>',unsafe_allow_html=True)
        if release.authorized:
            status_badge(st, 'QUALIFIED', note='Release-level qualification; individual claims gated')
            st.markdown('<p class="v2-body">Approved with qualifications does not grant permission '
                        'to publish every claim or recalculate estimates at a new filter grain.</p>',unsafe_allow_html=True)
        else:
            status_badge(st, 'BLOCKED', note='No research content authorized')
            empty_state(st, 'release_blocked', detail=release.explanation)
        evidence_panel(st,restriction=guide.non_inference)
    st.markdown('<div class="v2-callout"><strong>Evidence-first publication.</strong> '
                'This phase contains no market estimates. Phase 3 visualizations will require verified source artifacts, '
                'exact-grain metric contracts and individual claim permissions before publication.</div>',
                unsafe_allow_html=True)
    page_footer(st)
