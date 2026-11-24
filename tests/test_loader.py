from pathlib import Path
from hashlib import sha256
from unittest.mock import patch
import pandas as pd
import pytest

from src.loader import (DataLoadError, load_raw_data, load_and_validate,
                        resolve_source_path)


def fake_parquet(path: Path, contents: bytes = b'PAR1' + b'\x00' * 8 + b'PAR1') -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(contents)
    return path


def test_project_relative_resolution_is_independent_of_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert resolve_source_path('data/raw/x.parquet', root=tmp_path) == (tmp_path/'data/raw/x.parquet').resolve()


def test_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError, match='not found'):
        load_raw_data('data/raw/absent.parquet', root=tmp_path)


@pytest.mark.parametrize('name,contents', [
    ('empty.parquet', b''), ('truncated.parquet', b'PAR1'),
    ('wrong.parquet', b'PAR1' + b'x'*8 + b'BAD!'),
])
def test_invalid_parquet_container(tmp_path, name, contents):
    path = tmp_path/name
    path.write_bytes(contents)
    with pytest.raises(DataLoadError):
        load_raw_data(path)


def test_unsupported_extension(tmp_path):
    path = tmp_path/'sales.csv'
    path.write_text('a,b\n1,2')
    with pytest.raises(DataLoadError, match='Only'):
        load_raw_data(path)


def test_checksum_rejection_before_read(tmp_path):
    path = fake_parquet(tmp_path/'sales.parquet')
    with patch('src.loader.pd.read_parquet') as read:
        with pytest.raises(DataLoadError, match='checksum mismatch'):
            load_raw_data(path, expected_sha256='0'*64)
        read.assert_not_called()


def test_read_errors_wrapped_and_original_available(tmp_path):
    path = fake_parquet(tmp_path/'sales.parquet')
    with patch('src.loader.pd.read_parquet', side_effect=ValueError('corrupt footer')):
        with pytest.raises(DataLoadError, match='corrupt footer') as exc:
            load_raw_data(path)
        assert isinstance(exc.value.__cause__, ValueError)


def test_empty_frame_rejected(tmp_path):
    path = fake_parquet(tmp_path/'sales.parquet')
    with patch('src.loader.pd.read_parquet', return_value=pd.DataFrame({'x': []})):
        with pytest.raises(DataLoadError, match='zero rows'):
            load_raw_data(path)


def test_loader_preserves_rows_columns_dtypes_and_nulls(tmp_path):
    path = fake_parquet(tmp_path/'data/raw/source.parquet')
    source = pd.DataFrame({'price_aed': [10.25, 20.5],
                           'has_parking': pd.Series([False, pd.NA], dtype='boolean'),
                           'instance_date': pd.to_datetime(['2025-01-01','2025-01-02'])})
    snapshot = source.copy(deep=True)
    with patch('src.loader.pd.read_parquet', return_value=source):
        with patch('src.loader._arrow_schema_metadata', return_value=('arrow-schema', 2)):
            got, info = load_raw_data('data/raw/source.parquet', root=tmp_path, with_source_info=True)
    pd.testing.assert_frame_equal(got, snapshot)
    assert info.sha256 == sha256(path.read_bytes()).hexdigest()
    assert info.row_count == 2 and info.parquet_row_groups == 2
    assert info.pandas_dtypes['has_parking'] == 'boolean'


def test_full_load_validation_integration(tmp_path, valid_frame):
    path = fake_parquet(tmp_path/'raw.parquet')
    with patch('src.loader.pd.read_parquet', return_value=valid_frame):
        with patch('src.loader._arrow_schema_metadata', return_value=(None, None)):
            frame, source, report = load_and_validate(path, strict=True)
    assert report.passed
    assert frame is valid_frame
    assert report.source_sha256 == source.sha256
