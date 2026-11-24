"""Focused Notebook 05 tests: read its pure estimator without loading the private dataset.

Place beside the existing project tests. The notebook's logic is tested rather than
reimplementing its estimator in the test suite. No source modules are modified.
"""
from pathlib import Path
import ast
import numpy as np
import pandas as pd
import pytest
import nbformat


def _get_estimator():
    root=Path(__file__).resolve().parents[1]
    candidates=[root/'notebooks'/'05_Market_Structure.ipynb',root/'05_Market_Structure.ipynb']
    file=next((p for p in candidates if p.exists()),None)
    if file is None:pytest.skip('Notebook 05 has not yet been installed')
    notebook=nbformat.read(file,as_version=4)
    for cell in notebook.cells:
        if cell.cell_type!='code' or 'def contemporaneous_gap(' not in cell.source:continue
        source=ast.parse(cell.source)
        node=next(n for n in source.body if isinstance(n,ast.FunctionDef) and n.name=='contemporaneous_gap')
        module=ast.Module(body=[node],type_ignores=[])
        scope={'pd':pd,'np':np}
        exec(compile(ast.fix_missing_locations(module),str(file),'exec'),scope)
        return scope['contemporaneous_gap']
    pytest.fail('Notebook estimator missing')


@pytest.fixture
def gap():return _get_estimator()


def _frame(nr=40,no=60,delta=.2):
    return pd.DataFrame({
        'transaction_id':np.arange(nr+no)+1,
        'reg_type_label':['Ready']*nr+['Off-Plan']*no,
        'community':['A']*(nr+no),
        'log_psm':[10.]*nr+[10.+delta]*no,
    })


@pytest.mark.parametrize('mode',['pooled','ready','offplan','equal'])
def test_known_log_gap(gap,mode):
    est,detail=gap(_frame(),['community'],30,mode)
    assert np.isclose(est['log_gap'],.2)
    assert np.isclose(est['gap_pct'],100*np.expm1(.2))
    assert np.isclose(detail.weight.sum(),1)
    assert (detail.ready_n>=30).all() and (detail.offplan_n>=30).all()


def test_sparse_two_sided_support_is_not_estimable(gap):
    est,detail=gap(_frame(nr=30,no=29),['community'],30)
    assert est is None and detail.empty


def test_one_sided_group_is_not_estimable(gap):
    x=_frame();x=x[x.reg_type_label.eq('Ready')]
    est,detail=gap(x,['community'],30)
    assert est is None and detail.empty


def test_duplicate_transaction_ids_blocked(gap):
    x=_frame();x.loc[1,'transaction_id']=x.loc[0,'transaction_id']
    with pytest.raises(ValueError,match='Duplicate'):
        gap(x,['community'],30)


def test_different_reference_weights_change_estimated_target(gap):
    a=_frame(nr=100,no=40,delta=.1)
    b=_frame(nr=40,no=100,delta=.4);b['community']='B';b.transaction_id+=1000
    x=pd.concat([a,b],ignore_index=True)
    ready,_=gap(x,['community'],30,'ready')
    offplan,_=gap(x,['community'],30,'offplan')
    assert not np.isclose(ready['log_gap'],offplan['log_gap'])
    assert ready['log_gap'] < offplan['log_gap']


def test_invalid_weight_mode_raises(gap):
    with pytest.raises(ValueError,match='weight_mode'):
        gap(_frame(),['community'],30,'invalid')
