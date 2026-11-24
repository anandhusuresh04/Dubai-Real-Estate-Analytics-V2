import pandas as pd
import numpy as np
import pytest
from pandas.testing import assert_frame_equal
from src.cleaning import clean_transactions
from src.features import engineer_features


def test_features_exact_and_source_preserved(source_frame):
    clean=clean_transactions(source_frame)
    old=clean.copy(deep=True)
    f=engineer_features(clean)
    assert_frame_equal(clean, old)
    assert_frame_equal(f[clean.columns],clean)
    assert f.loc[0,'price_per_sqm']==10000
    assert np.isclose(f.loc[0,'price_per_sqft_calculated'], 10000/10.76391041671)
    assert f.loc[0,'price_psf']==929.03
    assert pd.isna(f.loc[4,'price_per_sqm'])


def test_year_month_quarter_from_date(source_frame):
    f=engineer_features(clean_transactions(source_frame))
    assert (f.loc[0,'year'],f.loc[0,'month'],f.loc[0,'quarter'],f.loc[0,'year_quarter'])==(2025,1,1,'2025-Q1')
    assert f.loc[1,'year_quarter']=='2026-Q3'


def test_parking_and_bedroom_semantics(source_frame):
    f=engineer_features(clean_transactions(source_frame))
    assert f.loc[0,'parking_status']=='Yes'
    assert pd.isna(f.loc[1,'parking_status'])
    assert f.loc[2,'parking_status']=='No'
    assert f.loc[2,'bedroom_label']=='5+BR'
    assert pd.isna(f.loc[4,'bedroom_label'])
    assert f.loc[5,'bedroom_label']=='Studio'


def test_registration_binary_with_no_inference(source_frame):
    source_frame.loc[1,'reg_type_label']=None
    f=engineer_features(clean_transactions(source_frame))
    assert pd.isna(f.loc[1,'is_offplan'])
    assert not f.loc[1,'registration_known']
    assert f.loc[0,'is_offplan']==False
    assert f.loc[2,'is_offplan']==True


def test_invalid_dates_preserve_null_features(source_frame):
    source_frame.loc[0,'instance_date']='bad'
    f=engineer_features(clean_transactions(source_frame))
    assert pd.isna(f.loc[0,'year'])
    assert pd.isna(f.loc[0,'year_quarter'])


def test_invalid_num_does_not_create_spurious_price(source_frame):
    source_frame.loc[0,'price_aed']=np.inf
    f=engineer_features(clean_transactions(source_frame))
    assert pd.isna(f.loc[0,'price_per_sqm'])


def test_missing_cleaning_prerequisites_fail(source_frame):
    with pytest.raises(ValueError,match='Feature prerequisites missing'):
        engineer_features(source_frame)


def test_duplicate_feature_creation_fails(source_frame):
    f=engineer_features(clean_transactions(source_frame))
    with pytest.raises(ValueError,match='Refusing to overwrite'):
        engineer_features(f)
