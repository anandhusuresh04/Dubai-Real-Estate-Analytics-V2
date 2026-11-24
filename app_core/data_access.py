"""Validated read-only research artifact access (no research recomputation)."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import hashlib
import pandas as pd
from .artifact_registry import get_artifact, resolve_artifact

class ArtifactError(RuntimeError):
    pass

@dataclass(frozen=True)
class ArtifactInspection:
    key: str
    path: str
    status: str
    rows: int | None = None
    columns: tuple[str, ...] = ()
    sha256: str | None = None
    reason: str = ''


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def read_artifact(root: Path, key: str, *, expected_hash: str | None = None,
                  required_columns: tuple[str, ...] = (), allow_empty: bool = False) -> pd.DataFrame:
    """Fail closed for absent, corrupt, unapproved-schema or wrong-hash files.

    CSV input is read in string-preserving mode to prevent identifiers, 'NA',
    booleans, and leading zeros from being silently reinterpreted. An explicit
    typed conversion is a *separate* metric contract decision.
    """
    spec = get_artifact(key)
    path = resolve_artifact(root, key)
    if not path.is_file():
        raise ArtifactError(f'Missing artifact: {spec.relative_path}')
    if not path.stat().st_size:
        raise ArtifactError(f'Empty artifact bytes: {spec.relative_path}')
    if expected_hash is not None and sha256_file(path) != expected_hash:
        raise ArtifactError(f'Hash mismatch: {spec.relative_path}')
    try:
        if spec.fmt == 'parquet':
            frame = pd.read_parquet(path, engine='pyarrow')
        else:
            frame = pd.read_csv(path, dtype='string', keep_default_na=False, na_filter=False,
                                encoding='utf-8-sig')
    except (Exception) as exc:
        raise ArtifactError(f'Unreadable {spec.fmt}: {spec.relative_path}: {type(exc).__name__}: {exc}') from exc
    if frame.columns.has_duplicates or any(not isinstance(c, str) for c in frame.columns):
        raise ArtifactError(f'Invalid column labels: {spec.relative_path}')
    missing = set(spec.required_columns).union(required_columns) - set(frame.columns)
    if missing:
        raise ArtifactError(f'Unsupported schema: {spec.relative_path}; missing {sorted(missing)}')
    if frame.empty and not allow_empty:
        raise ArtifactError(f'No data rows: {spec.relative_path}')
    return frame


def inspect_artifact(root: Path, key: str, *, expected_hash: str | None = None) -> ArtifactInspection:
    spec = get_artifact(key)
    path = resolve_artifact(root, key)
    try:
        frame = read_artifact(root, key, expected_hash=expected_hash,
                              allow_empty=(key == '06_final_issue_register'))
        return ArtifactInspection(key, str(spec.relative_path), 'VERIFIED_STRUCTURE',
                                  len(frame), tuple(frame.columns), sha256_file(path))
    except ArtifactError as exc:
        return ArtifactInspection(key, str(spec.relative_path), 'BLOCKED', reason=str(exc))


def verify_parquet_csv_pair(root: Path, parquet_key: str, csv_key: str) -> None:
    """Compare table values using explicit types, not pandas CSV inference.

    Optional utility for pairs known to represent the same table. CSV is an
    untyped text transport: coerce according to Parquet's column dtype, preserve
    nulls and literal strings, and reject any nonreversible representation.
    Neither mismatching values nor unsupported type conversions are ignored.
    """
    a = read_artifact(root, parquet_key)
    b = read_artifact(root, csv_key)
    if a.shape != b.shape or list(a.columns) != list(b.columns):
        raise ArtifactError('CSV/Parquet shape or column mismatch')
    for col in a:
        source = a[col]
        raw = b[col]
        if pd.api.types.is_bool_dtype(source):
            # String 'True' / 'False' are not numerical values.
            values = raw.map(lambda x: x if x in ('True','False') else None)
            invalid = raw.notna() & ~raw.isin(('True','False',''))
            if invalid.any():raise ArtifactError(f'{col}: invalid boolean token')
            rebuilt = values.map({'True':True,'False':False}).astype('boolean')
            eq = (source.astype('boolean').reset_index(drop=True).equals(rebuilt.reset_index(drop=True)))
        elif pd.api.types.is_numeric_dtype(source):
            candidate = pd.to_numeric(raw.replace('',pd.NA), errors='coerce')
            bad = raw.ne('') & raw.notna() & candidate.isna()
            if bad.any():raise ArtifactError(f'{col}: invalid numeric token')
            import numpy as np
            original = source.to_numpy(dtype=float,na_value=np.nan)
            restored = candidate.to_numpy(dtype=float,na_value=np.nan)
            eq = bool(np.array_equal(np.isnan(original),np.isnan(restored)) and np.allclose(original,restored,rtol=1e-12,atol=1e-9,equal_nan=True))
        else:
            # CSVs without an explicit source null marker cannot distinguish a
            # literal empty string and a missing cell. Do not certify them.
            if source.isna().any() and (source.fillna('').astype(str)=='').any():
                raise ArtifactError(f'{col}: ambiguous CSV null/empty string without null contract')
            eq = source.astype('string').reset_index(drop=True).equals(raw.astype('string').reset_index(drop=True))
        if not eq:
            raise ArtifactError(f'{col}: CSV/Parquet readback mismatch')
