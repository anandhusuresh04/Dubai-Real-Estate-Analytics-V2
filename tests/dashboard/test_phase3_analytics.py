"""Phase 3 scientific safety, source-contract and chart/permission regression tests."""
import json
from pathlib import Path
import pandas as pd
import pytest
from app.analytics.catalog import EXHIBITS,BY_ID,PAGE_EXHIBITS,Exhibit
from app.analytics.gateway import (EvidenceUnavailable,select_columns,exact_period,
                                   published_claims,load_exhibit,attested_hash)
from app.analytics.charts import validated_chart_frame,make_figure,exact_value
from app.analytics.pages import PAGE_SECTIONS
from app_core.claim_permissions import Permissions,PermissionDenied
from app_core.artifact_registry import get_artifact,SOURCE_SHA256


def test_six_analytical_pages_and_unique_exhibits():
    assert len(PAGE_SECTIONS)==6
    assert set(PAGE_EXHIBITS)==set(PAGE_SECTIONS)
    assert len(BY_ID)==len(EXHIBITS)
    for page,sections in PAGE_SECTIONS.items():
        assert len(sections)>=3
        assert set(x for _,_,ids in sections for x in ids)==set(PAGE_EXHIBITS[page])


def test_every_exhibit_references_allowlisted_artifact_and_valid_rq():
    assert len(EXHIBITS)>=30
    for exhibit in EXHIBITS:
        assert exhibit.rq in get_artifact(exhibit.artifact).rq
        assert exhibit.kind in {'line','bar','scatter','table'}
        assert exhibit.dimension and exhibit.value
        assert not set(exhibit.filters)-set(exhibit.dimension+exhibit.segment+('year','universe_id','design','design_id'))


def test_no_arbitrary_numeric_column_fallback():
    e=BY_ID['annual_count']
    with pytest.raises(EvidenceUnavailable):select_columns(pd.DataFrame({'year':[2025],'other_number':[999]}),e)


def test_missing_permission_artifact_fails_closed(tmp_path):
    with pytest.raises(EvidenceUnavailable):load_exhibit(tmp_path,BY_ID['annual_count'])


def test_upstream_attestation_requires_real_frozen_source_digest(tmp_path):
    path=tmp_path/'reports/tables/dashboard_upstream_attestation.json'
    path.parent.mkdir(parents=True)
    key='market_yearly'
    path.write_text(json.dumps({'attestation_version':1,'source_sha256':'0'*64,
          'release_status':'APPROVED_WITH_QUALIFICATIONS','artifacts':{key:{'verified':True,
           'relative_path':get_artifact(key).relative_path.as_posix(),'sha256':'a'*64}}}))
    with pytest.raises(EvidenceUnavailable):attested_hash(tmp_path,key)


def test_attestation_does_not_accept_an_unlisted_or_unverified_record(tmp_path):
    path=tmp_path/'reports/tables/dashboard_upstream_attestation.json'
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({'attestation_version':1,'source_sha256':SOURCE_SHA256,
          'release_status':'APPROVED_WITH_QUALIFICATIONS','artifacts':{}}))
    with pytest.raises(EvidenceUnavailable):attested_hash(tmp_path,'market_yearly')


def test_restricted_field_selection_never_selects_wrong_numeric_column():
    e=BY_ID['annual_value']
    df=pd.DataFrame({'year':[2024,2025],'n_transactions':[1,2],
       'recorded_gross_value_aed':[10,20]})
    x,y,z=select_columns(df,e)
    assert (x,y,z)==('year','recorded_gross_value_aed',None)


def test_duplicate_grain_blocks_unapproved_reaggregation():
    e=BY_ID['annual_count']
    df=pd.DataFrame({'year':[2025,2025],'n_transactions':[10,20]})
    with pytest.raises(EvidenceUnavailable,match='multiple observations'):
        validated_chart_frame(df,e)


def test_historical_year_filter_excludes_provisional_and_prior():
    df=pd.DataFrame({'year':[2009,2010,2025,2026],'n_transactions':[1,2,3,4]})
    out=exact_period(df)
    assert out.year.tolist()==[2010,2025]


def test_exact_value_does_not_sum_or_average_rows():
    df=pd.DataFrame({'value':[10,20]})
    assert exact_value(df,'value')==10
    assert exact_value(df,'value',row=1)==20


def test_claim_permissions_are_not_inherited_from_rq():
    claims=pd.DataFrame({'upstream_claim_id':['A','B'],'rq_id':['RQ01','RQ01'],
         'published':[False,True],'release_approved':[False,True]})
    p=Permissions('APPROVED_WITH_QUALIFICATIONS',True,
        pd.DataFrame({'rq_id':['RQ01'],'final_status':['QUALIFIED']}),
        pd.DataFrame({'page':['Price Reality'],'rq':['RQ01'],'publishable':[True]}),claims)
    assert published_claims(p,'RQ01')==('B',)
    with pytest.raises(PermissionDenied):p.authorize_claim('A')


def test_no_claims_means_no_sensitive_chart_even_if_release_approved(monkeypatch,tmp_path):
    p=Permissions('APPROVED_WITH_QUALIFICATIONS',True,
        pd.DataFrame({'rq_id':['RQ01'],'final_status':['QUALIFIED']}),
        pd.DataFrame({'page':['Price Reality'],'rq':['RQ01'],'publishable':[True]}),
        pd.DataFrame({'upstream_claim_id':['X'],'rq_id':['RQ01'],'published':[False]}))
    monkeypatch.setattr('app.analytics.gateway._validated_release',lambda root:p)
    with pytest.raises(EvidenceUnavailable,match='individually published'):
        load_exhibit(tmp_path,BY_ID['matched_index'])


def test_plotly_has_real_source_y_values_not_mocked(monkeypatch):
    px=pytest.importorskip('plotly.express')
    df=pd.DataFrame({'year':[2024,2025],'n_transactions':[5,7]})
    fig=make_figure(df,BY_ID['annual_count'])
    assert list(fig.data[0].y)==[5,7]
    assert 'template' in fig.layout


def test_invalid_size_chart_grain_blocked():
    e=BY_ID['size_price']
    df=pd.DataFrame({'median_area':[50,50],'median_price':[600000,900000],
         'property_type_label':['Unit','Unit']})
    with pytest.raises(EvidenceUnavailable):validated_chart_frame(df,e)


def test_all_pages_preserve_caveats():
    from app.analytics.pages import PAGE_DESCRIPTIONS
    assert len(PAGE_DESCRIPTIONS)==6
    assert 'investment' not in PAGE_DESCRIPTIONS['intelligence_brief'].lower()
    assert BY_ID['parking'].kind=='table'
    assert BY_ID['matched_gap'].claim_sensitive
    assert BY_ID['community_growth'].claim_sensitive
    assert not BY_ID['bedrooms'].claim_sensitive  # diagnostic support only, never adjusted estimates

class LightweightStreamlit:
    """Render contract checks; this does not substitute for real browser testing."""
    def __init__(self):self.messages=[]
    def markdown(self,text,**kw):self.messages.append(str(text))
    def caption(self,text):self.messages.append(str(text))
    def write(self,text):self.messages.append(str(text))
    def info(self,text):self.messages.append(str(text))
    def expander(self,*args,**kwargs):return self
    def columns(self,n,**kwargs):return [self]*n
    def __enter__(self):return self
    def __exit__(self,*args):return False


def test_six_page_restricted_render_never_calls_data_loader(monkeypatch):
    from app.analytics import pages
    from app.runtime import ReleaseView
    from app.navigation import PAGES
    monkeypatch.setattr(pages,'check_release',lambda root:ReleaseView(False,'UNAVAILABLE','Blocked release'))
    monkeypatch.setattr(pages,'render_exhibit_grid',lambda *args:pytest.fail('Must fail closed'))
    st=LightweightStreamlit()
    for page in PAGES:pages.render_research_page(st,page)
    assert '🔒' in ''.join(st.messages)
    assert all(p.title in ''.join(st.messages) for p in PAGES)


def test_six_approved_page_layouts_call_only_declared_exhibits(monkeypatch):
    from app.analytics import pages
    from app.runtime import ReleaseView
    from app.navigation import PAGES
    monkeypatch.setattr(pages,'check_release',lambda root:ReleaseView(True,'APPROVED_WITH_QUALIFICATIONS','Approved',15,36))
    displayed=[]
    monkeypatch.setattr(pages,'render_exhibit_grid',lambda st,root,ids:displayed.extend(ids))
    monkeypatch.setattr(pages,'render_annual_kpis',lambda st,root:None)
    monkeypatch.setattr(pages,'render_decision_summary',lambda st,root:None)
    st=LightweightStreamlit()
    for page in PAGES:pages.render_research_page(st,page)
    assert set(displayed)==set(x for ids in PAGE_EXHIBITS.values() for x in ids)
    assert 'INCONCLUSIVE' in ''.join(st.messages)


def test_metric_switching_is_explicit_and_only_reuses_source_fields():
    from app.analytics.catalog import MEASURE_OPTIONS
    assert set(MEASURE_OPTIONS).issubset(set(BY_ID))
    for key,options in MEASURE_OPTIONS.items():
        assert len({x[0] for x in options})==len(options)
        assert all(len(x)==3 and all(x) for x in options)
        assert not BY_ID[key].claim_sensitive
