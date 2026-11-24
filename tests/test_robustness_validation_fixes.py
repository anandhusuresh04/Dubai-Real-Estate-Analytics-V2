"""Independent regression tests for Notebook 06 finalization controls.
No empirical outcome is fabricated; these use small adversarial oracles.
"""
from __future__ import annotations
import ast
import re
import importlib.util
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
import nbformat


def _helpers():
    candidates=[Path(__file__).resolve().parents[1]/'notebooks'/'06_Robustness_Validation.ipynb',
                Path(__file__).resolve().parent/'06_Robustness_Validation_Corrected.ipynb']
    source=next((p for p in candidates if p.is_file()),None)
    assert source is not None,'The corrected notebook is mandatory'
    nb=nbformat.read(source,as_version=4)
    tree=ast.parse(nb.cells[3].source)
    names={'normalize_rqs','map_claim_rq','verify_frame_values','relevant_blockers','release_gate'}
    functions=[node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name in names]
    assert len(functions)==len(names),names-{f.name for f in functions}
    env={'np':np,'pd':pd,'re':re,'RQ_IDS':[f'RQ{i:02d}' for i in range(1,16)]}
    exec(compile(ast.Module(body=functions,type_ignores=[]),str(source),'exec'),env)
    return env


H=_helpers()


@pytest.mark.parametrize('raw,expected',[('RQ01','RQ01'),('RQ04','RQ04'),('RQ09','RQ09'),
                                          ('RQ10','RQ10'),('RQ11','RQ11'),('RQ15','RQ15')])
def test_mapping_explicit_research_questions(raw,expected):
    rq,error=H['map_claim_rq']({'research_question':raw,'claim_id':'MKT01'})
    assert (rq,error)==(expected,'')


def test_conflicting_rq_fields_not_guessed():
    assert H['map_claim_rq']({'research_question':'RQ04','rq':'RQ05'})[1]=='CONFLICTING_STRUCTURED_RQ'


def test_unmapped_claim_is_not_silently_promoted():
    assert H['map_claim_rq']({'claim_id':'MKT01'})==(None,'RQ_NOT_EXPLICITLY_IDENTIFIED')


def test_readback_uses_values_not_only_shape():
    a=pd.DataFrame({'id':[1,2], 'value':[10.0,12.5], 'category':['Ready',None]})
    b=a.copy()
    assert H['verify_frame_values'](a,b)[0]
    b.loc[1,'value']=13.5
    assert not H['verify_frame_values'](a,b)[0]


def test_readback_handles_storage_dtype_and_roundoff():
    a=pd.DataFrame({'count':pd.Series([1,None],dtype='Int64'), 'score':[1.0,1e-12]})
    b=pd.DataFrame({'count':[1.,np.nan], 'score':[1.0,1e-12+1e-15]})
    assert H['verify_frame_values'](a,b)[0]


def test_readback_null_mask_mismatch_blocks():
    a=pd.DataFrame({'category':['NA',None]})
    b=pd.DataFrame({'category':[None,'NA']})
    ok,reason=H['verify_frame_values'](a,b)
    assert not ok and 'NULL_MASK' in reason


def test_export_issue_is_not_scientific_blocker():
    issues=[{'section':'EXPORT','code':'PARQUET','severity':'BLOCKED','affected_rqs':'ALL'},
            {'section':'TESTS','code':'FAILED','severity':'BLOCKED','affected_rqs':'RELEASE'}]
    assert not H['relevant_blockers']('RQ01',issues)
    assert not H['relevant_blockers']('RQ15',issues)


def test_source_failure_blocks_all_scientific_claims():
    issues=[{'section':'SOURCE','code':'SOURCE_HASH_MISMATCH','severity':'BLOCKED','affected_rqs':'ALL'}]
    for n in range(1,16):
        assert H['relevant_blockers'](f'RQ{n:02d}',issues)


def test_targeted_failure_only_blocks_dependents():
    issues=[{'section':'RQ11','code':'MATCHING_ERROR','severity':'BLOCKED','affected_rqs':'RQ11'}]
    assert H['relevant_blockers']('RQ11',issues)
    assert not H['relevant_blockers']('RQ01',issues)


def test_release_gate_fails_for_bad_export_but_preserves_science():
    manifest=pd.DataFrame([{'status':'BLOCKED'}])
    figures=pd.DataFrame([{'exists':True}])
    assert not H['release_gate']([],manifest,figures,True,True,True)
    manifest.loc[0,'status']='VERIFIED'
    assert H['release_gate']([],manifest,figures,True,True,True)
    assert not H['release_gate']([],manifest,figures,False,True,True)


def test_release_gate_fails_on_unresolved_blocker():
    manifest=pd.DataFrame([{'status':'VERIFIED'}])
    assert not H['release_gate']([{'severity':'BLOCKED'}],manifest,pd.DataFrame(),True,True,True)


def _export_function(tmp_path):
    """Load exactly the notebook's export function, not a duplicated test implementation."""
    nb=nbformat.read(Path(__file__).resolve().parents[1]/'notebooks'/'06_Robustness_Validation.ipynb',as_version=4)
    tree=ast.parse(nb.cells[73].source)
    func=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='write_verified_table')
    import hashlib
    env={**H,'pd':pd,'np':np,'TABLE_DIR':tmp_path/'tables','AGG_DIR':tmp_path/'aggregates',
         'MANDATORY_NONEMPTY':{'06_independent_cohort_membership'},
         'RUN_ID':'06-PYTEST-ISOLATED',
         'digest':lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()}
    env['TABLE_DIR'].mkdir();env['AGG_DIR'].mkdir()
    exec(compile(ast.Module(body=[func],type_ignores=[]),'<notebook_export>','exec'),env)
    return env['write_verified_table']


def test_missing_mandatory_export_is_blocked(tmp_path):
    writer=_export_function(tmp_path)
    result=writer('06_independent_cohort_membership',pd.DataFrame())
    assert result['status']=='BLOCKED'


def test_optional_missing_export_is_explicitly_withheld(tmp_path):
    writer=_export_function(tmp_path)
    result=writer('06_optional_diagnostic',pd.DataFrame())
    assert result['status']=='WITHHELD_EMPTY'


def test_actual_parquet_and_csv_readback(tmp_path):
    pytest.importorskip('pyarrow')
    writer=_export_function(tmp_path)
    values=pd.DataFrame({'n':pd.Series([1,2],dtype='Int64'),
                         'gap':[0.000000000001,12.5], 'kind':['NA','Ready']})
    result=writer('06_independent_cohort_membership',values)
    assert result['status']=='VERIFIED',result
    assert result['parquet_sha256'] and result['csv_sha256']


def test_corrupted_parquet_readback_rejected(tmp_path,monkeypatch):
    pytest.importorskip('pyarrow')
    writer=_export_function(tmp_path)
    original=pd.read_parquet
    def corrupted(*a,**kw):
        z=original(*a,**kw)
        z.loc[0,'amount']=99999
        return z
    monkeypatch.setattr(pd,'read_parquet',corrupted)
    result=writer('06_independent_cohort_membership',pd.DataFrame({'amount':[10.,20.]}))
    assert result['status']=='BLOCKED'
    assert 'NUMERIC_VALUES' in result['error']
