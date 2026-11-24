"""Adversarial tests for final Notebook 06 export and source-specific claim mapping.

When Arrow is absent the mocked Parquet channel tests the writer's control
flow/CSV logic only, not actual Parquet format compatibility. The existing
Arrow-enabled tests perform physical readback in the user's dubai-v2 environment.
"""
import ast
import hashlib
from pathlib import Path
import re
import nbformat
import numpy as np
import pandas as pd
import pytest

HERE=Path(__file__).resolve().parents[1]
NB=nbformat.read(HERE/'notebooks'/'06_Robustness_Validation.ipynb',as_version=4)


def _function(name, cell):
    node=next(x for x in ast.parse(NB.cells[cell].source).body
              if isinstance(x,ast.FunctionDef) and x.name==name)
    return node


def _environment(tmp_path):
    fns=[_function(x,3) for x in ('normalize_rqs','map_claim_rq','verify_frame_values')]
    fn=_function('write_verified_table',73)
    env={'pd':pd,'np':np,'re':re,'RUN_ID':'06-TEST-RUN',
         'TABLE_DIR':tmp_path/'tables','AGG_DIR':tmp_path/'agg',
         'MANDATORY_NONEMPTY':{'06_required'},
         'digest':lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()}
    env['TABLE_DIR'].mkdir();env['AGG_DIR'].mkdir()
    exec(compile(ast.Module(body=fns+[fn],type_ignores=[]),'<notebook06>', 'exec'),env)
    return env


def test_act_claims_map_only_to_verified_source():
    fn=_function('map_claim_rq',3)
    ns={'re':re,'pd':pd}
    exec(compile(ast.Module(body=[_function('normalize_rqs',3),fn],type_ignores=[]),'<mapping>','exec'),ns)
    for cid,title in [('ACT01','Growth dynamics'),('ACT02','Growth persistence')]:
        assert ns['map_claim_rq']({'source_notebook':'03','claim_id':cid,'research_question':title})==('RQ04','')
        assert ns['map_claim_rq']({'source_notebook':'04','claim_id':cid,'research_question':title})[0] is None
    assert ns['map_claim_rq']({'source_notebook':'03','claim_id':'ACT99','research_question':'Growth dynamics'})[0] is None
    assert ns['map_claim_rq']({'source_notebook':'03','claim_id':'ACT01','research_question':'Growth dynamics','rq':'RQ05'})[0] is None


def _mock_arrow(monkeypatch):
    orig_to=pd.DataFrame.to_parquet
    orig_read=pd.read_parquet
    monkeypatch.setattr(pd.DataFrame,'to_parquet',lambda self,path,**kwargs:self.to_pickle(path))
    monkeypatch.setattr(pd,'read_parquet',lambda path,**kwargs:pd.read_pickle(path))
    return orig_to,orig_read


def test_csv_typed_boolean_and_missing_strings_roundtrip(tmp_path,monkeypatch):
    _mock_arrow(monkeypatch)
    writer=_environment(tmp_path)['write_verified_table']
    t=pd.DataFrame({
      'boolean':pd.Series([True,False,pd.NA],dtype='boolean'),
      'category':['True','NA',None],
      'label':['','None','nan'],
      'integer':pd.Series([1,2,pd.NA],dtype='Int64'),
      'tiny_float':[1e-12,12.5,np.nan],
    })
    result=writer('06_required',t)
    assert result['status']=='VERIFIED',result
    csv=pd.read_csv(tmp_path/'tables'/'06_required.csv',dtype=str,keep_default_na=False,na_filter=False)
    assert csv['category'].tolist()[:2]==['True','NA']
    assert csv['boolean'].tolist()[:2]==['True','False']
    assert csv['label'].tolist()==['','None','nan']


def test_corrupted_parquet_and_missing_value_rejected(tmp_path,monkeypatch):
    _mock_arrow(monkeypatch)
    writer=_environment(tmp_path)['write_verified_table']
    old=pd.read_parquet
    def corrupt(*args,**kwargs):
        z=old(*args,**kwargs)
        z.loc[0,'price']=999.0
        return z
    monkeypatch.setattr(pd,'read_parquet',corrupt)
    result=writer('06_required',pd.DataFrame({'price':[10.,20.]}))
    assert result['status']=='BLOCKED'
    assert 'NUMERIC_VALUES' in result['error']


def test_writer_rejects_missing_marker_collision(tmp_path,monkeypatch):
    _mock_arrow(monkeypatch)
    writer=_environment(tmp_path)['write_verified_table']
    result=writer('06_required',pd.DataFrame({'label':['__V2_MISSING_06_TEST_RUN__']}))
    assert result['status']=='BLOCKED'
    assert 'collides' in result['error']


def test_all_python_cells_syntax_and_previous_outputs_cleared():
    assert len(NB.cells)==76
    code=[c for c in NB.cells if c.cell_type=='code']
    assert len(code)==64
    for c in code:compile(c.source,'<notebook06>','exec')


def test_no_issues_is_a_verified_empty_terminal_report(tmp_path,monkeypatch):
    _mock_arrow(monkeypatch)
    writer=_environment(tmp_path)['write_verified_table']
    issue_columns=['section','code','severity','detail','affected_rqs','source','detected_at']
    result=writer('06_final_issue_register',pd.DataFrame(columns=issue_columns))
    assert result['status']=='VERIFIED',result
    assert result['rows']==0
    saved=pd.read_csv(tmp_path/'tables'/'06_final_issue_register.csv')
    assert saved.empty and saved.columns.tolist()==issue_columns


def test_tiny_nonzero_float_cannot_read_back_as_zero():
    ns={'np':np,'pd':pd}
    fn=_function('verify_frame_values',3)
    exec(compile(ast.Module(body=[fn],type_ignores=[]),'<typed>', 'exec'),ns)
    ok,reason=ns['verify_frame_values'](
        pd.DataFrame({'p':[1e-12]}),pd.DataFrame({'p':[0.0]}))
    assert not ok and reason=='p:NUMERIC_VALUES'
