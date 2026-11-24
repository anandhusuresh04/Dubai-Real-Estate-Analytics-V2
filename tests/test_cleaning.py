import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal
from src.cleaning import clean_transactions, cohort_audit
from src.validation import DataValidationError


def test_no_raw_data_change(source_frame):
    old=source_frame.copy(deep=True)
    result=clean_transactions(source_frame)
    assert_frame_equal(source_frame, old)
    assert_frame_equal(result[source_frame.columns], old)
    assert len(result)==6 and result.index.equals(source_frame.index)


def test_expected_cohorts(source_frame):
    c=clean_transactions(source_frame)
    assert c['eligible_market_activity'].tolist()==[True]*6
    assert c['eligible_residential_core'].tolist()==[True,True,True,False,False,True]
    assert c['eligible_residential_strict'].tolist()==[True,True,False,False,False,True]
    assert c['eligible_known_segment'].tolist()==[True,True,False,False,False,False]
    assert c['eligible_amenity_known'].tolist()==[True,False,False,False,False,True]
    assert c['eligible_2026_provisional'].tolist()==[False,True,False,False,False,False]


def test_funnel_reconciles(source_frame):
    a=cohort_audit(clean_transactions(source_frame))
    assert (a.input_n==a.retained_n+a.excluded_n).all()
    assert a.set_index('cohort_id').loc['P1_STRICT','retained_n']==3
    assert a.set_index('cohort_id').loc['P3_AMENITY_KNOWN','retained_n']==2


def test_duplicate_transaction_is_never_counted(source_frame):
    source_frame.loc[1,'transaction_id']=101
    with pytest.raises(DataValidationError): clean_transactions(source_frame)
    c=clean_transactions(source_frame, strict=False)
    assert not c.loc[0,'eligible_market_activity']
    assert not c.loc[1,'eligible_market_activity']


def test_invalid_date_and_nonpositive_price_excluded_from_p0(source_frame):
    source_frame.loc[0,'instance_date']='invalid'
    source_frame.loc[1,'price_aed']=-1
    c=clean_transactions(source_frame)
    assert not c.loc[0,'eligible_market_activity']
    assert not c.loc[1,'eligible_market_activity']
    assert pd.isna(c.loc[0,'transaction_date'])


def test_zero_total_price_is_activity_eligible_but_not_pricing(source_frame):
    source_frame.loc[0,'price_aed']=0
    c=clean_transactions(source_frame)
    assert c.loc[0,'eligible_market_activity']
    assert not c.loc[0,'eligible_residential_core']


def test_source_nulls_and_unknown_parking_preserved(source_frame):
    c=clean_transactions(source_frame)
    assert pd.isna(c.loc[1,'has_parking'])
    assert not c.loc[1,'eligible_amenity_known']
    assert pd.isna(c.loc[5,'area_id'])


def test_outlier_flag_kept_but_not_strict(source_frame):
    c=clean_transactions(source_frame)
    assert c.loc[2,'eligible_residential_core']
    assert not c.loc[2,'eligible_residential_strict']


def test_missing_schema_and_empty_fail(source_frame):
    with pytest.raises(DataValidationError): clean_transactions(source_frame.drop(columns='price_aed'))
    with pytest.raises(DataValidationError): clean_transactions(source_frame.iloc[:0])


def test_repeated_cleaning_rejected(source_frame):
    with pytest.raises(DataValidationError, match='Derived columns already exist'):
        clean_transactions(clean_transactions(source_frame))


def test_nondefault_index_retained(source_frame):
    source_frame.index=[18,3,9,6,1,0]
    c=clean_transactions(source_frame)
    assert c.index.tolist()==[18,3,9,6,1,0]


def test_nonfinite_area_excluded_without_deletion(source_frame):
    source_frame.loc[0,'area_sqm']=np.inf
    c=clean_transactions(source_frame)
    assert len(c)==6 and not c.loc[0,'eligible_residential_core']
