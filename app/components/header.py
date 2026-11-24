"""Compact premium hero, with escaped labels and no empirical results."""
from html import escape


def page_header(st, title: str, subtitle: str, *, breadcrumb: str = 'RESEARCH INTELLIGENCE', page_number: int | None = None) -> None:
    index = f'<span class="v2-hero-index">BRIEF {page_number:02d} / 06</span>' if page_number is not None else ''
    st.markdown(
        '<section class="v2-hero" aria-label="Page introduction">'
        f'<div class="v2-hero-top"><span class="v2-eyebrow">{escape(breadcrumb)}</span>{index}</div>'
        f'<h1 class="v2-heading">{escape(title)}</h1>'
        f'<p class="v2-subtitle">{escape(subtitle)}</p>'
        '</section>', unsafe_allow_html=True)


def scope_badges(st, *labels: str) -> None:
    """Optional compact context chips for other components; not an authorization grant."""
    st.markdown('<div class="v2-scope-row">' + ''.join(
        f'<span class="v2-chip">{escape(label)}</span>' for label in labels
    ) + '</div>', unsafe_allow_html=True)
