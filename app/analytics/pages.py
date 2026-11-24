"""Six evidence-first analytical workspaces. No calculations of research estimates."""
from __future__ import annotations
from html import escape
from app.config import get_settings
from app.content import GUIDES
from app.navigation import PAGES
from app.runtime import check_release
from app.components.header import page_header
from app.components.footer import page_footer
from .catalog import PAGE_EXHIBITS,BY_ID
from .render import render_exhibit,render_exhibit_grid,render_annual_kpis,render_decision_summary

PAGE_SECTIONS={
 'intelligence_brief':(
  ('The registered market','Annual transaction and nominal-value evidence for the frozen historical period.',('annual_count','annual_value')),
  ('Composition behind the headline','Registration categories and raw residential price evidence use different defined populations.',('registration_mix','raw_price')),
  ('What the evidence permits','RQ-level conclusions and restrictions, not an unqualified market forecast.',('decisions',)),
 ),
 'market_dynamics':(
  ('Market activity','Annual and quarterly counts from the source-defined population.',('annual_count','quarterly','annual_value')),
  ('Registration composition','Ready and Off-Plan categories and property-type counts are observed registrations, not available inventory.',('registration_mix','property_mix','contributions')),
  ('Geographic breadth','Concentration measures are only meaningful within the stated geography universe.',('concentration',)),
 ),
 'price_reality':(
  ('Observed transaction pricing','Descriptive observed price levels, interpreted within the strict residential cohort.',('raw_price',)),
  ('Comparable-design evidence','Matched price changes require individually published claims and fixed design windows.',('matched_index','index_endpoint','index_coverage')),
  ('Price composition and nominal budgets','Recorded size composition, nominal transactions and the upper tail remain separate estimands.',('size_mix','budget','tail')),
 ),
 'community_intelligence':(
  ('Recorded community histories','Search and compare only source-observed community identifiers. Descriptive trends are not matched growth.',('community_activity','community_prices')),
  ('Validated comparable change','Community growth is withheld unless eligible and individually authorized.',('community_eligibility','community_growth')),
  ('Comparability, dispersion and stability','Community dispersion, regimes and stability use the research-defined samples.',('community_dispersion','community_regimes','stability')),
 ),
 'market_structure':(
  ('Registration composition versus matched gaps','Unadjusted registration shares are not price premia. Matched comparisons are noncausal and permission-gated.',('raw_reg_gap','matched_gap','matched_gap_summary','gap_uncertainty')),
  ('Recorded size and price','Precomputed size bins and registered Unit/Villa associations; no raw transaction-level re-estimation.',('size_price','size_elasticity')),
  ('Support limits','Bedroom association is restricted to approved contrasts; parking is a feasibility problem, never an estimable premium.',('bedrooms','bedroom_estimate','parking')),
 ),
 'research_reliability':(
  ('Source integrity and population selection','The frozen input and audited cohort-selection evidence.',('source','selection')),
  ('Missingness and sensitivity','Quality policy and temporal checks; separate evidence from the inferential target.',('temporal_quality','quality','sensitivity')),
  ('Scientific decisions and permissions','Search the decisions and the individually withheld/published claim ledger.',('decisions','claim_registry')),
 ),
}

PAGE_DESCRIPTIONS={
 'intelligence_brief':'Understand the scale and composition of registered activity before interpreting any price comparison.',
 'market_dynamics':'Explore the history of recorded sales, nominal consideration and registration composition at authorized time grains.',
 'price_reality':'Compare observed and matched views only when population, common support and frozen design permit.',
 'community_intelligence':'Explore communities without implying unvalidated rankings or investment performance.',
 'market_structure':'Separate registration mix from matched contemporaneous comparisons and recorded property characteristics.',
 'research_reliability':'Inspect what was validated, what remains qualified, and which individual interpretations are withheld.',
}


def render_research_page(st,spec):
    root=get_settings().project_root
    state=check_release(root)
    i=next(i for i,p in enumerate(PAGES,1) if p.key==spec.key)
    page_header(st,spec.title,spec.subtitle,
         breadcrumb='DUBAI REAL ESTATE / RESEARCH INTELLIGENCE',page_number=i)
    if not state.authorized:
        st.markdown('<div class="v3-unavailable" role="alert"><strong>🔒 Research publication restricted</strong>'
                    'No analytical data will be displayed until release verification succeeds.</div>',unsafe_allow_html=True)
        st.markdown(escape(state.explanation))
        with st.expander('Why is this view restricted?'):
            st.write('Notebook 06 release integrity and claim-level permissions must pass before any approved metric is served.')
        page_footer(st)
        return
    st.markdown('<div class="v2-strip" role="status"><div class="v2-strip-label">'
         '<span class="v2-dot"></span> VALIDATED RESEARCH FOUNDATION</div>'
         '<div class="v2-strip-sub">Approved with qualifications · No causal attribution · Exact-grain source evidence</div></div>',
         unsafe_allow_html=True)
    guide=GUIDES[spec.key]
    st.markdown('<div class="v3-page-intro"><div><span class="v3-eyebrow">HISTORICAL RESEARCH · 2010–2025</span>'
        f'<h3>{escape(PAGE_DESCRIPTIONS[spec.key])}</h3></div>'
        '<div class="v3-scope">FROZEN SNAPSHOT <span>·</span> NOMINAL AED <span>·</span> REGISTERED SALES</div></div>',
        unsafe_allow_html=True)
    if spec.key in ('intelligence_brief','market_dynamics'):
        render_annual_kpis(st,root)
    if spec.key=='intelligence_brief':
        render_decision_summary(st,root)
    for j,(title,description,ids) in enumerate(PAGE_SECTIONS[spec.key],1):
        st.markdown(f'<div class="v3-section"><span class="v3-index">{j:02d} / RESEARCH VIEW</span>'
               f'<h2>{escape(title)}</h2><p>{escape(description)}</p></div>',unsafe_allow_html=True)
        render_exhibit_grid(st,root,ids)
    if spec.key=='intelligence_brief' and hasattr(st,'page_link'):
        st.markdown('<div class="v3-section"><span class="v3-index">EXPLORE FURTHER</span>'
                    '<h2>Continue the research</h2><p>Navigate to a focused analytical workspace.</p></div>',unsafe_allow_html=True)
        cols=st.columns(4)
        for col,key in zip(cols,('market_dynamics','price_reality','community_intelligence','research_reliability')):
            target=next(p for p in PAGES if p.key==key)
            with col:st.page_link('app/pages/'+target.filename,label=target.title,icon=target.icon,use_container_width=True)
    with st.expander('Evidence contract and scientific interpretation',expanded=(spec.key=='research_reliability')):
        st.markdown(f'**Research questions:** {escape(", ".join(guide.question_ids))}')
        st.markdown(f'**Selection rule:** {escape(guide.selection_rule)}')
        st.markdown(f'**Interpretation boundary:** {escape(guide.non_inference)}')
        st.caption('The dashboard only subsets approved precomputed exports; chart views cannot recompute matched prices, medians, model coefficients or research eligibility.')
    if spec.key=='research_reliability':
        st.info('RQ06: predictive signal remains INCONCLUSIVE. No forecasting or investment-return models are published. Claims withheld in the Notebook 06 subclaim registry are not rehabilitated by RQ-level approval.')
    page_footer(st)
