"""Real snapshot smoke test; runs locally with installed pyarrow and source file."""
import pytest
from src.loader import load_raw_data, PROJECT_ROOT
from src.cleaning import clean_transactions, cohort_audit
from src.features import engineer_features


def test_raw_snapshot_cohorts_and_features():
    source = PROJECT_ROOT / 'data/raw/dld_sales_transactions.parquet'
    if not source.exists():
        pytest.skip('Local raw DLD Parquet snapshot is not mounted')
    pytest.importorskip('pyarrow')
    raw = load_raw_data()
    cleaned = clean_transactions(raw, strict=True)
    features = engineer_features(cleaned)
    assert len(raw) == len(cleaned) == len(features) == 1_382_848
    assert raw['transaction_id'].equals(features['transaction_id'])
    audit = cohort_audit(cleaned)
    assert (audit.input_n == audit.retained_n + audit.excluded_n).all()
    assert cleaned['eligible_residential_strict'].sum() <= cleaned['eligible_residential_core'].sum()
    assert cleaned['eligible_residential_core'].sum() <= cleaned['eligible_market_activity'].sum()
    assert features['price_per_sqm'].notna().sum() <= len(raw)
    assert not cleaned.loc[cleaned['quality_flags'].ne(0), 'eligible_residential_strict'].any()
