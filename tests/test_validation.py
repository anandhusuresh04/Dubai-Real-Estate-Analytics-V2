import json
import numpy as np
import pandas as pd
import pytest
from src.validation import (DataValidationError, SQFT_PER_SQM,
                            validate_transactions)


def finding(report, code):
    return next((x for x in report.findings if x.code == code), None)


def test_happy_path_keeps_raw_frame_unchanged(valid_frame):
    frozen = valid_frame.copy(deep=True)
    report = validate_transactions(valid_frame, strict=True)
    assert report.passed
    assert report.row_count == 3
    pd.testing.assert_frame_equal(valid_frame, frozen)
    assert report.monthly_completeness['transactions'].sum() == 3
    assert report.yearly_completeness['transactions'].sum() == 3
    assert report.monthly_completeness.loc[report.monthly_completeness.period=='2026-03', 'provisional_2026'].iloc[0]


def test_missing_essential_column_errors(valid_frame):
    frame = valid_frame.drop(columns='price_aed')
    with pytest.raises(DataValidationError, match='price_aed'):
        validate_transactions(frame, strict=True)
    report = validate_transactions(frame)
    assert finding(report, 'missing_columns').count == 1


def test_extra_column_retained_and_warning(valid_frame):
    valid_frame['new_source_column'] = [1, 2, 3]
    report = validate_transactions(valid_frame, strict=True)
    assert finding(report, 'extra_columns').count == 1
    assert 'new_source_column' in valid_frame


def test_empty_dataframe_errors():
    report = validate_transactions(pd.DataFrame())
    assert not report.passed
    with pytest.raises(DataValidationError):
        validate_transactions(pd.DataFrame(), strict=True)


def test_duplicate_id_detected_as_critical(valid_frame):
    valid_frame.loc[2, 'transaction_id'] = 1002
    report = validate_transactions(valid_frame)
    assert finding(report, 'transaction_id_duplicate').count == 2
    with pytest.raises(DataValidationError, match='transaction_id_duplicate'):
        validate_transactions(valid_frame, strict=True)


def test_null_id_detected_as_critical(valid_frame):
    valid_frame['transaction_id'] = valid_frame.transaction_id.astype('Int64')
    valid_frame.loc[1, 'transaction_id'] = pd.NA
    with pytest.raises(DataValidationError, match='transaction_id_null'):
        validate_transactions(valid_frame, strict=True)


def test_missing_date_does_not_dilute_time_based_denominator(valid_frame):
    valid_frame.loc[2, 'instance_date'] = pd.NaT
    report = validate_transactions(valid_frame)
    assert finding(report, 'instance_date_missing').count == 1
    assert report.monthly_completeness.transactions.sum() == 2


def test_unparseable_date_warns_without_mutating(valid_frame):
    valid_frame['instance_date'] = valid_frame['instance_date'].dt.strftime('%Y-%m-%d')
    valid_frame.loc[1, 'instance_date'] = 'not-a-date'
    report = validate_transactions(valid_frame)
    assert finding(report, 'instance_date_unparseable').count == 1
    assert valid_frame.loc[1,'instance_date'] == 'not-a-date'


def test_wrong_column_type_is_error(valid_frame):
    valid_frame['price_aed'] = valid_frame.price_aed.astype(str)
    with pytest.raises(DataValidationError, match='price_aed_dtype'):
        validate_transactions(valid_frame, strict=True)


def test_wrong_boolean_type_is_error_not_silently_cast(valid_frame):
    valid_frame['has_parking'] = ['False', 'True', None]
    report = validate_transactions(valid_frame)
    assert finding(report, 'has_parking_dtype')
    assert finding(report, 'has_parking_invalid').count == 2
    assert valid_frame.has_parking.iloc[0] == 'False'


def test_missing_boolean_remains_unknown(valid_frame):
    report = validate_transactions(valid_frame, strict=True)
    assert report.passed
    assert pd.isna(valid_frame.has_parking.iloc[2])
    assert finding(report, 'has_parking_missing_2026').count == 1


def test_invalid_rooms_and_zero_negative_numeric_values_are_reported(valid_frame):
    valid_frame.loc[0, 'rooms_bucket'] = 7
    valid_frame.loc[0, 'area_sqm'] = 0.0
    valid_frame.loc[1, 'price_aed'] = -1.0
    report = validate_transactions(valid_frame)
    assert finding(report, 'rooms_bucket_outside_domain').count == 1
    assert finding(report, 'area_sqm_zero').count == 1
    assert finding(report, 'price_aed_negative').count == 1
    assert valid_frame.loc[0,'area_sqm'] == 0.0


def test_unexpected_categories_warning(valid_frame):
    valid_frame.loc[0, 'reg_type_label'] = 'Unknown Category'
    report = validate_transactions(valid_frame)
    assert finding(report, 'reg_type_label_unknown').count == 1


def test_flags_are_decoded_bitwise_and_not_removed(valid_frame):
    valid_frame['quality_flags'] = [0, 5, 16]
    report = validate_transactions(valid_frame, strict=True)
    assert report.quality_flags['bit_counts']['1'] == 1
    assert report.quality_flags['bit_counts']['4'] == 1
    assert report.quality_flags['bit_counts']['16'] == 1
    assert finding(report, 'publisher_quality_flags_nonzero').count == 2
    assert len(valid_frame) == 3


def test_unknown_flag_bit_warning(valid_frame):
    valid_frame.loc[0,'quality_flags'] = 32
    report = validate_transactions(valid_frame)
    assert finding(report, 'quality_flags_unknown_bits').count == 1


def test_invalid_flag_is_critical(valid_frame):
    valid_frame['quality_flags'] = [0.0, -1.0, 0.0]
    with pytest.raises(DataValidationError, match='quality_flags_invalid'):
        validate_transactions(valid_frame, strict=True)


def test_ambiguous_geography_detected(valid_frame):
    valid_frame.loc[1, 'area_name_en'] = 'Different Name'
    report = validate_transactions(valid_frame)
    assert finding(report, 'area_id_mapping_ambiguous').count == 2
    assert not report.area_mapping.empty


def test_inconsistent_procedure_mapping_detected(valid_frame):
    valid_frame.loc[1, 'procedure_id'] = 1
    report = validate_transactions(valid_frame)
    assert finding(report, 'procedure_id_mapping_ambiguous').count == 2


def test_price_psf_tolerance_and_exceptions(valid_frame):
    valid_frame.loc[0,'price_psf'] = 100.0
    report = validate_transactions(valid_frame)
    assert finding(report, 'price_psf_discrepancy').count == 1
    assert len(report.psf_exceptions) == 1
    assert report.psf_exceptions.iloc[0].transaction_id == 1001


def test_price_psf_exact_computed_without_false_warning(valid_frame):
    valid_frame['price_psf'] = valid_frame.price_aed / (valid_frame.area_sqm * SQFT_PER_SQM)
    report = validate_transactions(valid_frame)
    assert finding(report, 'price_psf_discrepancy') is None


def test_2026_procedure_warning(valid_frame):
    report = validate_transactions(valid_frame)
    assert finding(report, 'procedure_completeness').count == 1
    assert finding(report, 'procedure_name_en_missing_2026').count == 1


def test_report_export_files(tmp_path, valid_frame):
    report = validate_transactions(valid_frame)
    report.export(tmp_path)
    summary = json.loads((tmp_path/'validation_summary.json').read_text())
    assert summary['rows'] == 3
    assert (tmp_path/'data_quality_monthly.csv').exists()
    assert (tmp_path/'column_profile.csv').exists()
    assert (tmp_path/'quality_flags.json').exists()


def test_blank_string_is_not_conflated_with_null(valid_frame):
    valid_frame.loc[0, 'building_name'] = ''
    report = validate_transactions(valid_frame)
    assert report.column_profile[7]['missing_n'] == 1
    assert valid_frame.loc[0,'building_name'] == ''


def test_nullable_object_booleans_from_parquet_are_valid(valid_frame):
    # pyarrow/pandas can materialize nullable bool columns as object dtype.
    valid_frame['has_parking'] = pd.Series([False, True, None], dtype='object')
    valid_frame['is_pre_registration'] = pd.Series([False, True, None], dtype='object')
    report = validate_transactions(valid_frame, strict=True)
    assert report.passed
    assert finding(report, 'has_parking_dtype') is None
    assert finding(report, 'is_pre_registration_dtype') is None


def test_nullable_numeric_and_psf_zero(valid_frame):
    valid_frame['area_sqm'] = pd.Series([50, pd.NA, 150], dtype='Float64')
    valid_frame.loc[0, 'price_psf'] = 0
    report = validate_transactions(valid_frame, strict=True)
    assert report.passed
    assert finding(report, 'price_psf_nonpositive').count == 1


def test_null_quality_flag_fails(valid_frame):
    valid_frame['quality_flags'] = pd.Series([0, 0, pd.NA], dtype='Int64')
    with pytest.raises(DataValidationError, match='quality_flags_invalid'):
        validate_transactions(valid_frame, strict=True)
