"""Additional adversarial tests for the final V2 research audit.
These are not empirical Dubai-data tests; they target gating and serialization contracts.
"""
import ast
import re
from pathlib import Path
import nbformat
import numpy as np
import pandas as pd
import pytest

NB = Path(__file__).resolve().parents[1] / 'notebooks' / '06_Robustness_Validation.ipynb'

def helpers():
    nb=nbformat.read(NB,as_version=4)
    body=ast.parse(nb.cells[3].source)
    names={'normalize_rqs','map_claim_rq','verify_frame_values','relevant_blockers','release_gate'}
    funcs=[x for x in body.body if isinstance(x,ast.FunctionDef) and x.name in names]
    env={'np':np,'pd':pd,'re':re,'RQ_IDS':[f'RQ{i:02d}' for i in range(1,16)]}
    exec(compile(ast.Module(body=funcs,type_ignores=[]),'<helpers>','exec'),env)
    return env
H=helpers()

@pytest.mark.parametrize('value,expected',[
 ('RQ01 matched change','RQ01'),('RQ04','RQ04'),('RQ05 registered growth','RQ05'),
 ('RQ09 community regimes','RQ09'),('RQ10','RQ10'),('RQ15','RQ15')])
def test_executed_notebook_research_question_labels(value,expected):
    assert H['map_claim_rq']({'research_question':value})==(expected,'')

def test_declared_cross_cutting_community_metadata_not_arbitrarily_assigned():
    assert H['map_claim_rq']({'claim_id':'COM01','research_question':'Evidence reliability'}) == (None,'CROSS_CUTTING_SOURCE_FINDING')

def test_unknown_cross_cutting_identifier_is_not_auto_accepted():
    assert H['map_claim_rq']({'claim_id':'COMXX','research_question':'Evidence reliability'})[1].startswith('INVALID_STRUCTURED_RQ')

def test_composite_rq_finding_requires_manual_disambiguation():
    assert H['map_claim_rq']({'research_question':'RQ01 and RQ02'})[1]=='AMBIGUOUS_STRUCTURED_RQ'

def test_unknown_rq_not_falsely_parsed():
    assert H['map_claim_rq']({'research_question':'RQ16'})[0] is None

def test_empty_release_export_not_approved():
    assert not H['release_gate']([],pd.DataFrame(),pd.DataFrame(),True,True,True)

def test_targeted_statistical_blocker_preserves_other_research():
    faults=[{'severity':'BLOCKED','section':'RQ11','code':'BAD_CLUSTER','affected_rqs':'RQ11'}]
    assert H['relevant_blockers']('RQ11',faults)
    assert not H['relevant_blockers']('RQ04',faults)

def test_project_level_export_failure_does_not_modify_scientific_status():
    faults=[{'severity':'BLOCKED','section':'EXPORT','code':'CSV_READBACK_FAILED','affected_rqs':'RELEASE'}]
    assert H['relevant_blockers']('RQ11',faults)==[]
    assert not H['release_gate'](faults,pd.DataFrame([{'status':'VERIFIED'}]),pd.DataFrame(),True,True,True)

def test_null_mask_and_literal_na_are_distinct():
    a=pd.DataFrame({'a':['NA',None,'None','nan'],'n':pd.Series([1,None,3,4],dtype='Int64')})
    b=a.copy()
    assert H['verify_frame_values'](a,b)[0]
    b.loc[0,'a']=None
    assert not H['verify_frame_values'](a,b)[0]

def test_value_difference_rejected_even_same_schema_and_count():
    a=pd.DataFrame({'price':[10.,20.],'metric':['x','y']})
    b=pd.DataFrame({'price':[10.,200.],'metric':['x','y']})
    ok,why=H['verify_frame_values'](a,b)
    assert not ok and 'NUMERIC_VALUES' in why

def test_notebook_02_known_saved_findings_variable_is_declared():
    nb=nbformat.read(NB,as_version=4)
    assert "'02':['02_price_research_decisions']" in nb.cells[67].source
    assert "'02':['price_research_decisions']" in nb.cells[67].source

def test_claim_specific_subclaims_cannot_auto_publish():
    nb=nbformat.read(NB,as_version=4)
    assert 'published=False' in nb.cells[69].source
    assert 'claim_specific_replication_complete=False' in nb.cells[69].source

def test_rq15_covers_all_five_flagships_with_actual_sensitivity_methods():
    nb=nbformat.read(NB,as_version=4)
    source=nb.cells[59].source
    assert "flagships={'RQ01','RQ04','RQ05','RQ07','RQ11'}" in source
    assert 'Leave-one-community-out matched gap' in source
    assert 'Common-support threshold' in source
    assert 'Geographic concentration by cohort' in source

def test_source_notebook_exports_not_implicitly_created():
    nb=nbformat.read(NB,as_version=4)
    assert 'SAVED_NOTEBOOK_OUTPUT_LEVEL_D' in nb.cells[67].source
    assert "'MISSING_EVIDENCE'" in nb.cells[69].source
