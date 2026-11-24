import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest
from src.visualization import (plot_coverage, plot_observed_series, plot_conditional_intervals,
                               plot_budget_curve, save_figure)


def test_coverage_marks_undefined_without_zero(tmp_path):
    data=pd.DataFrame({'community':['A','B'],'matched':[2,0],'parent':[4,0]})
    fig,ax=plot_coverage(data,category='community',numerator='matched',denominator='parent',title='coverage')
    assert len(ax.patches)==1
    assert any(t.get_text()=='N/A' for t in ax.texts)
    assert save_figure(fig,tmp_path/'nested/test.png').exists()
    plt.close(fig)
    with pytest.raises(ValueError):plot_coverage(data.assign(matched=[8,0]),category='community',numerator='matched',denominator='parent',title='bad')


def test_observed_years_not_connected_across_gaps():
    data=pd.DataFrame({'year':[2021,2023,2024], 'value':[1.,2.,np.nan]})
    fig,ax=plot_observed_series(data,x='year',y='value',title='period',ylabel='value',connect_consecutive=True)
    assert len(ax.lines)==0
    plt.close(fig)
    fig,ax=plot_observed_series(data,x='year',y='value',title='period',ylabel='value')
    assert len(ax.lines)==0
    plt.close(fig)


def test_intervals_do_not_impute_missing():
    d=pd.DataFrame({'area':['A','B'],'estimate':[10.,np.nan],'lo':[5.,np.nan],'hi':[20.,np.nan]})
    fig,ax=plot_conditional_intervals(d,label='area',estimate='estimate',low='lo',high='hi',title='conditional')
    assert any('not estimable' in t.get_text() for t in ax.texts)
    plt.close(fig)
    with pytest.raises(ValueError):plot_conditional_intervals(d.assign(lo=[11,np.nan]),label='area',estimate='estimate',low='lo',high='hi',title='bad')


def test_budget_monotonic_and_save_contract(tmp_path):
    d=pd.DataFrame({'community':['A','A'],'budget_aed':[1000000,2000000],'share_pct':[35.,60.]})
    fig,ax=plot_budget_curve(d)
    assert len(ax.lines)==1
    with pytest.raises(ValueError):save_figure(fig,tmp_path/'plot.txt')
    plt.close(fig)
    with pytest.raises(ValueError):plot_budget_curve(d.assign(share_pct=[70.,40.]))
