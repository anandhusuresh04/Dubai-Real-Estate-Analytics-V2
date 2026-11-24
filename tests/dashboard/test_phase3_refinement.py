"""Phase 3 refinement: exact research schema, labeling and publication safeguards."""
from dataclasses import replace
import pandas as pd
import pytest
from app.analytics.catalog import BY_ID, CLAIM_EXHIBIT_BINDINGS
from app.analytics.gateway import select_columns, EvidenceUnavailable
from app.analytics.charts import validated_chart_frame, make_figure
from app.analytics.render import _filters, _readable_id


class MiniUI:
    def __init__(self):self.selections=[]
    def selectbox(self,label,options,**kwargs):
        picked=options[kwargs.get('index',0)]
        self.selections.append((label,picked))
        return picked
    def multiselect(self,label,options,**kwargs):
        self.selections.append((label,list(kwargs.get('default',[]))))
        return list(kwargs.get('default',[]))
    def select_slider(self,label,**kwargs):return kwargs['value']
    def text_input(self,*args,**kwargs):return ''


def test_size_model_exact_notebook05_schema():
    model=BY_ID['size_elasticity']
    assert model.artifact=='05_size_price_linear_models'
    assert model.value==('beta',)
    assert model.facets==('outcome',)
    df=pd.DataFrame({'property_type_label':['Unit','Unit','Villa','Villa'],
        'outcome':['log_price','log_psm','log_price','log_psm'],
        'beta':[.7,-.3,.8,-.2],'se_cluster':[.02,.02,.05,.05]})
    x,y,z=select_columns(df,model)
    assert (x,y,z)==('property_type_label','beta',None)
    ui=MiniUI(); filtered=_filters(ui,df,model)
    assert filtered.outcome.tolist()==['log_price','log_price']
    assert filtered.beta.tolist()==[.7,.8]
    assert ('Fixed outcome','log_price') in ui.selections


def test_room_known_prefers_known_categories_without_aggregation():
    spec=BY_ID['size_mix']
    rows=pd.DataFrame({'year':[2025]*4,'property_type_label':['Unit']*4,
        'reg_type_label':['Off-Plan']*4,'room_known':[True,False,True,False],
        'size_coarse':['Unit:02','Unit:02','Unit:05','Unit:05'],'n':[100,2,50,1]})
    ui=MiniUI(); out=_filters(ui,rows,spec)
    assert len(out)==2
    assert out.n.tolist()==[100,50]
    assert ('Fixed room known','True') in ui.selections


def test_dispersion_endpoints_are_not_connected():
    pytest.importorskip('plotly.express')
    e=BY_ID['community_dispersion']
    df=pd.DataFrame({'year':[2021,2025], 'log_p90_p10':[1.08,.96]})
    fig=make_figure(df,e)
    assert 'lines' not in fig.data[0].mode
    assert list(fig.data[0].y)==[1.08,.96]


def test_quarter_labels_are_not_all_rotated():
    pytest.importorskip('plotly.express')
    df=pd.DataFrame({'year_quarter':[f'{y}Q{q}' for y in range(2010,2026) for q in range(1,5)],
                     'n_transactions':list(range(64))})
    fig=make_figure(df,BY_ID['quarterly'])
    assert len(fig.layout.xaxis.tickvals)<len(df)
    assert fig.layout.xaxis.tickangle==0
    assert list(fig.data[0].y)==list(range(64))


def test_no_claim_permission_repair_or_release():
    assert CLAIM_EXHIBIT_BINDINGS=={}
    assert all(BY_ID[x].claim_sensitive for x in (
        'matched_index','index_endpoint','index_coverage','community_growth',
        'matched_gap','matched_gap_summary','gap_uncertainty','bedroom_estimate'))


def test_source_category_labels_are_presentation_only():
    assert _readable_id(230.0)=='230'
    assert _readable_id('230.0')=='230'
    assert _readable_id('230.5')=='230.5'
    assert _readable_id('Abu Hail')=='Abu Hail'


def test_invalid_duplicate_source_grain_still_blocked():
    e=BY_ID['annual_count']
    with pytest.raises(EvidenceUnavailable):
        validated_chart_frame(pd.DataFrame({'year':[2025,2025],
            'n_transactions':[1,2]}),e)


def test_model_duplicate_rows_are_withheld_even_if_columns_match():
    model=BY_ID['size_elasticity']
    frame=pd.DataFrame({'property_type_label':['Unit','Unit'],
        'outcome':['log_price','log_price'],'beta':[.5,.9]})
    with pytest.raises(EvidenceUnavailable,match='duplicate coefficient'):
        validated_chart_frame(frame,model)


def test_invalid_model_outcome_is_withheld():
    model=BY_ID['size_elasticity']
    frame=pd.DataFrame({'property_type_label':['Unit'],
        'outcome':['causal_effect'],'beta':[.5]})
    with pytest.raises(EvidenceUnavailable,match='Unrecognized model outcome'):
        validated_chart_frame(frame,model)


def test_displayed_model_beta_is_not_transformed_or_averaged():
    model=BY_ID['size_elasticity']
    frame=pd.DataFrame({'property_type_label':['Unit','Villa'],
        'outcome':['log_price','log_price'],'beta':[.65,.81]})
    out,x,y,_=validated_chart_frame(frame,model)
    assert (x,y)==('property_type_label','beta')
    assert out.beta.tolist()==[.65,.81]


def test_repeated_unreleased_exhibits_get_one_safe_summary(monkeypatch):
    from app.analytics import render
    class RestrictedUI:
        def __init__(self):self.messages=[]
        def columns(self,n,**kwargs):return [self]*n
        def container(self,**kwargs):return self
        def markdown(self,v,**kwargs):self.messages.append(v)
        def caption(self,v):self.messages.append(v)
        def info(self,v):self.messages.append(v)
        def __enter__(self):return self
        def __exit__(self,*args):return False
    ui=RestrictedUI(); shown=[]
    monkeypatch.setattr(render,'render_exhibit',lambda st,root,k:shown.append(k))
    render.render_exhibit_grid(ui,object(),('raw_reg_gap','matched_gap',
                                          'matched_gap_summary','gap_uncertainty'))
    assert shown==['raw_reg_gap']
    text=' '.join(ui.messages)
    assert all(BY_ID[k].title in text for k in ('matched_gap',
                                               'matched_gap_summary','gap_uncertainty'))
    assert 'cannot publish estimates' in text


def test_source_defined_physical_area_bins_have_exact_boundaries():
    from app.analytics.charts import size_band_label
    assert size_band_label('Unit:00')=='0–45 m²'
    assert size_band_label('Unit:02')=='65–90 m²'
    assert size_band_label('Unit:06')=='>250 m²'
    assert size_band_label('Villa:00')=='0–150 m²'
    assert size_band_label('Villa:07')=='>1100 m²'
    assert size_band_label('unknown')=='unknown'


def test_size_plot_uses_source_area_bin_names_without_changing_values():
    pytest.importorskip('plotly.express')
    from app.analytics.charts import make_figure
    df=pd.DataFrame({'size_coarse':['Unit:00','Unit:02','Unit:06'],
                     'n':[4,6,7]})
    fig=make_figure(df,BY_ID['size_mix'])
    assert list(fig.data[0].y)==[4,6,7]
    assert '65–90 m²' in list(fig.layout.xaxis.ticktext)


def test_qualified_model_coefficients_still_require_individual_claim():
    assert BY_ID['size_elasticity'].claim_sensitive
    assert CLAIM_EXHIBIT_BINDINGS.get('size_elasticity') is None


def test_residential_default_does_not_pool_usage_populations():
    spec=BY_ID['property_mix']
    frame=pd.DataFrame({'year':[2025,2025],'usage_group':['Commercial','Residential'],
        'property_group':['Unit','Unit'],'n_transactions':[10,99]})
    ui=MiniUI();out=_filters(ui,frame,spec)
    assert out.n_transactions.tolist()==[99]
    assert ('Fixed usage group','Residential') in ui.selections


def test_full_scientific_restriction_is_readable_in_detail_panel():
    from app.analytics.render import _render_verified_table
    from types import SimpleNamespace
    class TableUI:
        column_config=SimpleNamespace(TextColumn=lambda *a,**kw:None)
        def __init__(self):self.messages=[];self.table=None
        def dataframe(self,frame,**kwargs):self.table=frame.copy()
        def expander(self,*args,**kwargs):return self
        def selectbox(self,label,values,**kwargs):return values[0]
        def markdown(self,v,**kwargs):self.messages.append(v)
        def write(self,v,**kwargs):self.messages.append(str(v))
        def __enter__(self):return self
        def __exit__(self,*args):return False
    st=TableUI()
    restriction='Verified methodological restriction: ' + 'interpretation caveat ' * 35
    rows=pd.DataFrame({'rq_id':['RQ11'],'final_status':['QUALIFIED'],
                       'restriction':[restriction]})
    _render_verified_table(st,rows,BY_ID['decisions'])
    assert 'restriction' in st.table
    assert restriction in st.messages


def test_all_six_page_sections_keep_original_research_scope():
    from app.analytics.pages import PAGE_SECTIONS
    from app.analytics.catalog import PAGE_EXHIBITS
    assert len(PAGE_SECTIONS)==6
    for page,sections in PAGE_SECTIONS.items():
        flattened=tuple(x for _,_,ids in sections for x in ids)
        assert set(flattened)==set(PAGE_EXHIBITS[page])
        assert len(flattened)==len(set(flattened))


def test_narrow_viewport_style_has_actual_breakpoints():
    from app.theme.phase3 import CSS
    assert 'max-width:900px' in CSS
    assert 'max-width:720px' in CSS
    assert 'stMetric' in CSS


def test_verified_community_names_change_legends_not_source_values():
    pytest.importorskip('plotly.express')
    from app.analytics.charts import make_figure
    df=pd.DataFrame({'year':[2024,2025,2024,2025],
        'area_key':[230.0,230.0,232.0,232.0],
        'p0_transactions':[2,3,7,8]})
    fig=make_figure(df,BY_ID['community_activity'],area_names={'230':'Abu Hail','232':'Mirdif'})
    names={trace.name:list(trace.y) for trace in fig.data}
    assert names=={'Abu Hail (230)':[2,3],'Mirdif (232)':[7,8]}


def test_exhibit_audit_distinguishes_fixed_schema_from_withheld_publication(monkeypatch,tmp_path):
    from scripts import check_phase3_dashboard as auditmod
    from app.analytics.gateway import EvidenceUnavailable
    from app.analytics.catalog import BY_ID
    monkeypatch.setattr(auditmod,'EXHIBITS',(BY_ID['size_elasticity'],))
    monkeypatch.setattr(auditmod,'validate_06_release_pair',lambda root:None)
    monkeypatch.setattr(auditmod.Permissions,'load',lambda root:object())
    monkeypatch.setattr(auditmod,'published_claims',lambda perms,rq:())
    def denied(root,spec,claim_id=None):
        raise EvidenceUnavailable('No individually published claim is available for RQ10.')
    monkeypatch.setattr(auditmod,'load_exhibit',denied)
    monkeypatch.setattr(auditmod,'attested_hash',lambda root,key:'a'*64)
    monkeypatch.setattr(auditmod,'read_artifact',lambda *a,**kw:pd.DataFrame({
        'property_type_label':['Unit','Villa'],'outcome':['log_price','log_price'],
        'beta':[.7,.8]}))
    rows=auditmod.audit(tmp_path)
    assert rows[0]['classification']=='CLAIM_WITHHELD'
    assert rows[0]['technical_schema']=='READY_WITHHELD'
    assert rows[0]['status']=='WITHHELD_OR_UNAVAILABLE'


def test_parking_support_card_reports_exact_cells_not_estimate():
    from app.analytics.render import _render_parking_feasibility
    class UI:
        def __init__(self):self.metrics=[];self.warnings=[]
        def columns(self,n,**kwargs):return [self]*n
        def metric(self,label,value):self.metrics.append((label,value))
        def warning(self,value):self.warnings.append(value)
        def __enter__(self):return self
        def __exit__(self,*a):return False
    ui=UI()
    src=pd.DataFrame({'parent_n':[236872],'overlap_communities':[9]})
    _render_parking_feasibility(ui,src,BY_ID['parking'])
    assert ui.metrics==[('Source parent observations','236,872'),
                        ('Communities with overlap','9')]
    assert 'NOT ESTIMABLE' in ui.warnings[0]
    assert 'premium' in ui.warnings[0]


def test_budget_lines_have_readable_thresholds_and_original_values():
    pytest.importorskip('plotly.express')
    from app.analytics.charts import make_figure
    rows=pd.DataFrame({'year':[2024,2025,2024,2025],
        'budget_aed':[1000000,1000000,1500000,1500000],
        'within_budget_pct':[44.3,40.1,62.2,58.4]})
    fig=make_figure(rows,BY_ID['budget'])
    traces={t.name:list(t.y) for t in fig.data}
    assert traces=={'AED 1M':[44.3,40.1],'AED 1.5M':[62.2,58.4]}


def test_tail_lines_have_human_labels_without_changing_precomputed_shares():
    pytest.importorskip('plotly.express')
    from app.analytics.charts import make_figure
    rows=pd.DataFrame({'year':[2024,2025], 'tail_fraction':[.01,.1],
        'tail_value_share_pct':[9.1,33.0]})
    fig=make_figure(rows,BY_ID['tail'])
    traces={t.name:list(t.y) for t in fig.data}
    assert traces=={'Top 1%':[9.1],'Top 10%':[33.0]}
