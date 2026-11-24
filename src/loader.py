"""Lossless ingestion of the frozen Dubai DLD Parquet transaction snapshot.

The loader does not clean, infer missing values, parse dates, or coerce columns.
The validation layer owns the semantic checks; transformations belong elsewhere.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SOURCE = Path("data/raw/dld_sales_transactions.parquet")
PARQUET_MAGIC = b"PAR1"


class DataLoadError(RuntimeError):
    """A source could not be read without violating the ingestion contract."""


@dataclass(frozen=True)
class SourceInfo:
    path: str
    size_bytes: int
    sha256: str
    row_count: int
    column_count: int
    columns: tuple[str, ...]
    pandas_dtypes: dict[str, str]
    parquet_schema: str | None = None
    parquet_row_groups: int | None = None


def resolve_source_path(source: str | Path = DEFAULT_SOURCE, *, root: Path | None = None) -> Path:
    """Resolve project-relative paths against project root, never the shell cwd."""
    candidate = Path(source).expanduser()
    if not candidate.is_absolute():
        candidate = (PROJECT_ROOT if root is None else Path(root)) / candidate
    return candidate.resolve()


def _file_sha256(path: Path, chunk_bytes: int = 4 * 1024 * 1024) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        while block := stream.read(chunk_bytes):
            digest.update(block)
    return digest.hexdigest()


def _check_parquet_container(path: Path) -> None:
    """Reject missing, empty, truncated or wrongly named inputs early."""
    if path.suffix.lower() != ".parquet":
        raise DataLoadError(f"Only the project's Parquet source is supported: {path}")
    if not path.exists():
        raise FileNotFoundError(f"Dubai transactions Parquet not found: {path}")
    if not path.is_file():
        raise DataLoadError(f"Parquet path is not a regular file: {path}")
    size = path.stat().st_size
    if size < 12:
        raise DataLoadError(f"Parquet file is empty or truncated ({size} bytes): {path}")
    with path.open("rb") as stream:
        header = stream.read(4)
        stream.seek(-4, 2)
        footer = stream.read(4)
    if header != PARQUET_MAGIC or footer != PARQUET_MAGIC:
        raise DataLoadError(f"Missing Parquet PAR1 header/footer (corrupt or wrong format): {path}")


def _arrow_schema_metadata(path: Path) -> tuple[str | None, int | None]:
    """Return physical schema/row groups; pyarrow is a declared project dependency."""
    try:
        import pyarrow.parquet as pq
    except ImportError:
        return None, None
    file = pq.ParquetFile(str(path))
    return str(file.schema_arrow), file.metadata.num_row_groups


def load_raw_data(
    file_path: str | Path = DEFAULT_SOURCE,
    *,
    root: Path | None = None,
    expected_sha256: str | None = None,
    with_source_info: bool = False,
) -> pd.DataFrame | tuple[pd.DataFrame, SourceInfo]:
    """Load *all* rows and columns of the project source without transformations.

    Args:
        file_path: Absolute path or project-root-relative Parquet file.
        root: Override root for tests/alternative cloned project locations.
        expected_sha256: Optional snapshot pin; mismatch fails before reading.
        with_source_info: Return a reproducibility manifest beside the frame.

    Raises:
        FileNotFoundError: Source does not exist.
        DataLoadError: Unsupported, corrupt, unreadable, mismatched or empty source.

    No implicit sorting, deduplication, row filtering, type casting, date parsing
    or null filling is performed. Use `load_and_validate` for a checked dataset.
    """
    path = resolve_source_path(file_path, root=root)
    try:
        _check_parquet_container(path)
        actual_sha = _file_sha256(path) if (expected_sha256 or with_source_info) else None
        if expected_sha256 and actual_sha.lower() != expected_sha256.lower():
            raise DataLoadError(
                f"Source snapshot checksum mismatch for {path}: expected "
                f"{expected_sha256.lower()}, got {actual_sha}. This is a different dataset snapshot."
            )
        frame = pd.read_parquet(path, engine="pyarrow")
        if not isinstance(frame, pd.DataFrame):
            raise DataLoadError(f"Parquet reader did not return a DataFrame: {path}")
        if frame.empty:
            raise DataLoadError(f"Dataset has zero rows or columns: {path}")
        if not frame.columns.is_unique:
            raise DataLoadError(f"Duplicate column names in input schema: {path}")
        if not with_source_info:
            return frame
        physical_schema, groups = _arrow_schema_metadata(path)
        info = SourceInfo(
            path=str(path), size_bytes=path.stat().st_size,
            sha256=actual_sha or _file_sha256(path),
            row_count=len(frame), column_count=len(frame.columns),
            columns=tuple(map(str, frame.columns)),
            pandas_dtypes={str(col): str(dtype) for col, dtype in frame.dtypes.items()},
            parquet_schema=physical_schema, parquet_row_groups=groups,
        )
        return frame, info
    except (FileNotFoundError, DataLoadError):
        raise
    except (OSError, ValueError, TypeError, ImportError, RuntimeError) as exc:
        raise DataLoadError(f"Unable to load unmodified Parquet source {path}: {exc}") from exc
    except Exception as exc:
        # pyarrow raises its own Arrow*Error subclasses, not all of which derive
        # from the exception types above. Preserve the original as __cause__.
        raise DataLoadError(f"Parquet decoding failed for {path}: {exc}") from exc


def load_and_validate(
    file_path: str | Path = DEFAULT_SOURCE,
    *,
    root: Path | None = None,
    expected_sha256: str | None = None,
    strict: bool = True,
) -> tuple[pd.DataFrame, SourceInfo, Any]:
    """Load source, attach provenance, and check the 20-column DLD contract.

    When strict=True, dataset-level errors raise DataValidationError; warnings
    remain in the report and do not cause destructive filtering.
    """
    from src.validation import validate_transactions

    frame, source_info = load_raw_data(
        file_path, root=root, expected_sha256=expected_sha256, with_source_info=True
    )
    report = validate_transactions(frame, source_info=source_info, strict=strict)
    return frame, source_info, report
