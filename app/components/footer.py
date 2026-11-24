"""Consistent portfolio-source footer."""

def page_footer(st) -> None:
    st.markdown('<div class="v2-footer">'
                'Dubai Real Estate Analytics V2 · Registered transactions, historical 2010–2025 · '
                'Nominal AED · Research findings are observational and subject to cohort, selection, and uncertainty restrictions. '
                'The dashboard does not provide investment recommendations or property-specific valuations.'
                '</div>',unsafe_allow_html=True)
