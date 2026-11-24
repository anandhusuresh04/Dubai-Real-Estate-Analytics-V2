"""Explicit evidence context with no inferred sample sizes, years, or causality."""
from html import escape


def evidence_panel(st, *, cohort: str | None = None, period: str | None = None,
                   method: str | None = None, coverage: str | None = None,
                   claim_id: str | None = None, restriction: str | None = None,
                   expanded: bool = False) -> None:
    with st.expander('Evidence & interpretation', expanded=expanded):
        fields = [('Population',cohort),('Period',period),('Method',method),
                  ('Matched coverage',coverage),('Claim ID',claim_id)]
        for label,val in fields:
            st.markdown(f'**{label}:** {escape(str(val)) if val is not None else "Not supplied"}')
        st.markdown('**Research restriction:** ' +
                    escape(str(restriction or 'Observational registered-sales data; no causal or investment-return inference.')))
