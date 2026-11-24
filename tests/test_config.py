from pathlib import Path
import pytest
from src.config import (MATCHING_DESIGNS, COARSE_AREA_BANDS_SQM, FINE_AREA_BANDS_SQM,
                        research_paths, validate_year_window, SNAPSHOT_SHA256)


def test_paths_have_no_side_effects(tmp_path):
    p = research_paths(tmp_path / 'new_project')
    assert p.raw_source == (tmp_path/'new_project/data/raw/dld_sales_transactions.parquet').resolve()
    assert p.figures == (tmp_path/'new_project/reports/figures').resolve()
    assert not (tmp_path/'new_project').exists()


def test_matching_specs_exact():
    assert list(MATCHING_DESIGNS) == ['A_broad','B_bedrooms','C_size_only','D_size_bedrooms','E_fine_bedrooms']
    assert MATCHING_DESIGNS['C_size_only'][-1] == 'size_coarse'
    assert MATCHING_DESIGNS['E_fine_bedrooms'][-2:] == ('size_fine','rooms_bucket')
    assert COARSE_AREA_BANDS_SQM['Unit'][1] == 45
    assert FINE_AREA_BANDS_SQM['Villa'][-2] == 1500
    assert len(SNAPSHOT_SHA256) == 64


def test_year_window():
    assert validate_year_window(2021,2025) == (2021,2025)
    with pytest.raises(ValueError): validate_year_window(2025,2026)
    assert validate_year_window(2025,2026,allow_provisional=True) == (2025,2026)
    with pytest.raises(ValueError): validate_year_window(2025,2024)
    with pytest.raises(TypeError): validate_year_window(True,2025)
