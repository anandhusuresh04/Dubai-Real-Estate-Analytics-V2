import numpy as np
import pandas as pd
import pytest
from src.statistics import (ratio_coverage, check_count_value_identity, fixed_weighted_log_change,
                            complete_calendar_activity, matched_group_median_change,
                            conditional_matched_bootstrap)


def sample():
    rows=[]
    for group,base,end in [('A',100.,150.),('B',300.,330.)]:
        for yr,val in [(2021,base),(2025,end)]:
            for i in range(6):
                rows.append(dict(group=group, year=yr, price_per_sqm=val+(i-2.5)*2))
    return pd.DataFrame(rows)


def test_coverage_definitions():
    assert ratio_coverage(2,4)==50
    assert np.isnan(ratio_coverage(0,0))
    for a,b in [(1,0),(-1,4),(5,4),(np.nan,4)]:
        with pytest.raises(ValueError): ratio_coverage(a,b)


def test_value_identity_and_log_math():
    assert check_count_value_identity([2,3],[7,4],[14,12])
    assert not check_count_value_identity([2],[7],[15])
    assert np.isclose(fixed_weighted_log_change([100,200],[110,210],[.25,.75]),.25*np.log(1.1)+.75*np.log(1.05))
    with pytest.raises(ValueError): fixed_weighted_log_change([100],[110],[0.5])
    with pytest.raises(ValueError): fixed_weighted_log_change([0],[110],[1.0])


def test_calendar_year_gaps_and_zero_baseline():
    frame=pd.DataFrame({'area_key':['A','A'],'year':[2021,2023],'transactions':[10,30]})
    out=complete_calendar_activity(frame,start_year=2021,end_year=2023,areas=['A','B'])
    a=out.query("area_key=='A'")
    assert a.transactions.tolist()==[10,0,30]
    assert a.yoy_pct.isna().iloc[0]
    assert a.yoy_pct.iloc[1]==-100
    assert np.isnan(a.yoy_pct.iloc[2])
    assert out.query("area_key=='B'").transactions.eq(0).all()
    with pytest.raises(ValueError): complete_calendar_activity(frame,start_year=2022,end_year=2023)


def test_matched_group_weights_and_conditional_bootstrap():
    frame=sample()
    old=frame.copy(deep=True)
    result,detail=matched_group_median_change(frame,group_cols=['group'],base_year=2021,end_year=2025,min_group_n=5)
    assert result.matched_groups==2
    assert result.matched_base_n==12
    assert result.matched_end_n==12
    assert result.coverage_base_pct==100
    assert np.isclose(result.effective_groups,2)
    assert np.isclose(result.change_pct,100*np.expm1(.5*np.log(1.5)+.5*np.log(1.1)))
    assert np.isclose(detail.base_weight.sum(),1)
    ci=conditional_matched_bootstrap(frame,detail,group_cols=['group'],base_year=2021,end_year=2025,replicates=100,seed=12)
    assert ci.ci_low_pct.iloc[0] <= ci.ci_high_pct.iloc[0]
    pd.testing.assert_frame_equal(ci,conditional_matched_bootstrap(frame,detail,group_cols=['group'],base_year=2021,end_year=2025,replicates=100,seed=12))
    pd.testing.assert_frame_equal(frame,old)


def test_empty_support_and_coverage_denominators():
    frame=sample()
    result,detail=matched_group_median_change(frame,group_cols=['group'],base_year=2021,end_year=2025,min_group_n=20)
    assert result is None and detail.empty
    result,_=matched_group_median_change(frame,group_cols=['group'],base_year=2021,end_year=2025,min_group_n=5,parent_base_n=24,parent_end_n=30)
    assert result.coverage_base_pct==50 and result.coverage_end_pct==40
    with pytest.raises(ValueError): matched_group_median_change(frame,group_cols=['group'],base_year=2021,end_year=2025,min_group_n=5,parent_base_n=1)


def test_invalid_prices_and_year_requirements():
    frame=sample()
    frame.loc[0,'price_per_sqm']=0
    with pytest.raises(ValueError): matched_group_median_change(frame,group_cols=['group'],base_year=2021,end_year=2025,min_group_n=3)
    with pytest.raises(ValueError): matched_group_median_change(sample(),group_cols=['group'],base_year=2021,end_year=2021)
