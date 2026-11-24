import pytest
import pandas as pd

@pytest.fixture
def source_frame():
    return pd.DataFrame({
        'transaction_id': [101,102,103,104,105,106],
        'instance_date': ['2025-01-15','2026-07-02','2025-03-01','2024-01-02','2025-02-20','2025-01-02'],
        'reg_type_label': ['Ready','Ready','Off-Plan','Ready','Ready','Off-Plan'],
        'area_id': [10., 10., 11., 11., 12., None],
        'area_name_en': ['A','A','B','B','C',None],
        'project_name': [None]*6, 'master_project_name':[None]*6,
        'building_name': [None]*6,
        'property_type_label': ['Unit','Unit','Villa','Land','Unit','Unit'],
        'property_sub_type': [None]*6,
        'usage_label': ['Residential','Residential','Residential','Residential','Residential','Residential'],
        'rooms_bucket': [1.,2.,5.,None,None,0.],
        'has_parking': [True,None,False,False,False,False],
        'area_sqm': [100.,80.,200.,100.,0.,50.],
        'price_aed': [1_000_000.,1_000_000.,2_000_000.,100_000.,100_000.,500_000.],
        'price_psf': [929.03,1161.29,929.03,92.903,0.,929.03],
        'procedure_id': [1.]*6, 'procedure_name_en':['Sale']*6,
        'is_pre_registration': [False]*6,
        'quality_flags':[0,0,4,0,2,0],
    })
import pandas as pd
import pytest


@pytest.fixture
def valid_frame():
    # Synthetic rows mirror the *field inventory and semantics* of the audited
    # DLD source. These are not copied transaction records.
    return pd.DataFrame({
        'transaction_id': [1001, 1002, 1003],
        'instance_date': pd.to_datetime(['2025-01-15', '2025-02-15', '2026-03-03']),
        'reg_type_label': ['Ready', 'Off-Plan', 'Ready'],
        'area_id': [10, 10, 11],
        'area_name_en': ['Area A', 'Area A', 'Area B'],
        'project_name': ['Project A', 'Project A', 'Project B'],
        'master_project_name': ['Master A', 'Master A', 'Master B'],
        'building_name': ['Tower A', 'Tower A', None],
        'property_type_label': ['Unit', 'Unit', 'Villa'],
        'property_sub_type': ['Flat', 'Flat', 'Villa'],
        'usage_label': ['Residential'] * 3,
        'rooms_bucket': pd.Series([0, 5, pd.NA], dtype='Int64'),
        'has_parking': pd.Series([False, True, pd.NA], dtype='boolean'),
        'area_sqm': [50., 100., 150.],
        'price_aed': [500000., 1500000., 3000000.],
        'price_psf': [500000/50/10.76391041671, 1500000/100/10.76391041671, 3000000/150/10.76391041671],
        'procedure_id': pd.Series([1, 2, pd.NA], dtype='Int64'),
        'procedure_name_en': ['Sell', 'Sell - Pre registration', None],
        'is_pre_registration': pd.Series([False, True, pd.NA], dtype='boolean'),
        'quality_flags': [0, 0, 0],
    })
