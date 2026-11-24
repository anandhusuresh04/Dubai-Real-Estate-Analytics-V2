"""Real-data integration test. Run locally with DLD Parquet in data/raw/.

Skipped when this source or pyarrow isn't available (for example in a CI build
without the private/raw dataset). Observed counts are snapshot benchmarks, NOT
permanent cleaning rules. A different checksum means a new snapshot.
"""
from pathlib import Path
import pytest
from src.loader import load_and_validate

SOURCE = Path(__file__).resolve().parents[1] / 'data/raw/dld_sales_transactions.parquet'
SHA256 = '8294c3dd83dde2e16e64eaf1ef155a1ad14ec16b6b39384561777afb8425417e'


def test_frozen_source_profile_matches_audit():
    pytest.importorskip('pyarrow')
    if not SOURCE.is_file():
        pytest.skip('Raw Parquet file not included in the test workspace')
    df, info, report = load_and_validate(SOURCE, expected_sha256=SHA256, strict=True)
    assert len(df) == 1_382_848
    assert info.column_count == 20
    assert df.transaction_id.nunique(dropna=True) == len(df)
    assert int((df.quality_flags == 0).sum()) == 1_354_155
    assert int(df.building_name.isna().sum()) == 408_903
    assert int(df.has_parking.isna().sum()) == 43_942
    assert int(df.procedure_name_en.isna().sum()) == 26_971
    assert report.passed
    assert report.monthly_completeness.transactions.sum() == len(df)
