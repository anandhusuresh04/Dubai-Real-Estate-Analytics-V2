"""Non-destructive quality validation for DLD registered sales transactions.

Dataset-level contract errors fail in strict mode; record-level anomalies are
reported as warnings. No data is dropped, rewritten, parsed in-place or imputed.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TYPE_CHECKING
import json

import numpy as np
import pandas as pd
from pandas.api.types import (
    is_bool_dtype, is_datetime64_any_dtype, is_numeric_dtype,
    is_object_dtype, is_string_dtype,
)

if TYPE_CHECKING:
    from src.loader import SourceInfo

REQUIRED_COLUMNS = (
    'transaction_id', 'instance_date', 'reg_type_label', 'area_id',
    'area_name_en', 'project_name', 'master_project_name', 'building_name',
    'property_type_label', 'property_sub_type', 'usage_label', 'rooms_bucket',
    'has_parking', 'area_sqm', 'price_aed', 'price_psf', 'procedure_id',
    'procedure_name_en', 'is_pre_registration', 'quality_flags',
)
CATEGORY_DOMAINS = {
    'reg_type_label': frozenset(('Ready', 'Off-Plan')),
    'property_type_label': frozenset(('Unit', 'Villa', 'Land', 'Building')),
    'usage_label': frozenset(('Residential', 'Commercial', 'Other')),
}
QUALITY_BITS = {1: 'low_price', 2: 'invalid_area', 4: 'psf_outlier',
                8: 'missing_both_core_values', 16: 'invalid_date'}
KNOWN_BITS_MASK = sum(QUALITY_BITS)
SQFT_PER_SQM = 10.76391041671


class DataValidationError(ValueError):
    """Dataset-level critical errors discovered by project schema validation."""


@dataclass(frozen=True)
class Finding:
    code: str
    severity: str  # error or warning or info
    count: int
    message: str
    examples: tuple[str, ...] = ()


@dataclass
class ValidationReport:
    row_count: int
    column_count: int
    generated_at_utc: str
    source_sha256: str | None = None
    findings: list[Finding] = field(default_factory=list)
    column_profile: list[dict[str, Any]] = field(default_factory=list)
    category_counts: dict[str, dict[str, int]] = field(default_factory=dict)
    quality_flags: dict[str, Any] = field(default_factory=dict)
    monthly_completeness: pd.DataFrame = field(default_factory=pd.DataFrame)
    yearly_completeness: pd.DataFrame = field(default_factory=pd.DataFrame)
    procedure_mapping: pd.DataFrame = field(default_factory=pd.DataFrame)
    area_mapping: pd.DataFrame = field(default_factory=pd.DataFrame)
    psf_exceptions: pd.DataFrame = field(default_factory=pd.DataFrame)

    @property
    def errors(self) -> list[Finding]:
        return [f for f in self.findings if f.severity == 'error']

    @property
    def warnings(self) -> list[Finding]:
        return [f for f in self.findings if f.severity == 'warning']

    @property
    def passed(self) -> bool:
        return not self.errors

    def summary(self) -> dict[str, Any]:
        return {
            'rows': self.row_count, 'columns': self.column_count,
            'source_sha256': self.source_sha256,
            'passed': self.passed,
            'errors': [asdict(f) for f in self.errors],
            'warnings': [asdict(f) for f in self.warnings],
        }

    def export(self, directory: str | Path) -> None:
        """Persist diagnostics without including raw transaction-level PII."""
        folder = Path(directory)
        folder.mkdir(parents=True, exist_ok=True)
        (folder / 'validation_summary.json').write_text(
            json.dumps(self.summary(), indent=2, ensure_ascii=False), encoding='utf-8'
        )
        pd.DataFrame(self.column_profile).to_csv(folder / 'column_profile.csv', index=False)
        self.monthly_completeness.to_csv(folder / 'data_quality_monthly.csv', index=False)
        self.yearly_completeness.to_csv(folder / 'data_quality_yearly.csv', index=False)
        self.area_mapping.to_csv(folder / 'area_mapping_exceptions.csv', index=False)
        self.procedure_mapping.to_csv(folder / 'procedure_mapping_exceptions.csv', index=False)
        self.psf_exceptions.to_csv(folder / 'psf_exceptions.csv', index=False)
        (folder / 'quality_flags.json').write_text(
            json.dumps(self.quality_flags, indent=2), encoding='utf-8'
        )
        (folder / 'category_counts.json').write_text(
            json.dumps(self.category_counts, indent=2), encoding='utf-8'
        )


def _sample(series: pd.Series, n: int = 5) -> tuple[str, ...]:
    return tuple(str(v)[:120] for v in series.dropna().drop_duplicates().head(n).tolist())


def _add(report: ValidationReport, code: str, severity: str,
         count: int, message: str, examples: tuple[str, ...] = ()) -> None:
    if count:
        report.findings.append(Finding(code, severity, int(count), message, examples))


def _is_text(s: pd.Series) -> bool:
    return bool(is_string_dtype(s.dtype) or is_object_dtype(s.dtype) or
                isinstance(s.dtype, pd.CategoricalDtype))


def _numeric(s: pd.Series) -> tuple[pd.Series, pd.Series]:
    """Use a temporary conversion for diagnostics; never alter caller's data."""
    if is_bool_dtype(s.dtype):
        numeric = pd.Series(np.nan, index=s.index, dtype='float64')
    else:
        numeric = pd.to_numeric(s, errors='coerce')
    bad = s.notna() & numeric.isna()
    return numeric, bad


def _numeric_field(report: ValidationReport, df: pd.DataFrame,
                   name: str, *, integer: bool = False,
                   allow_negative: bool = False, positive: bool = False) -> pd.Series:
    s = df[name]
    numeric, bad = _numeric(s)
    if not is_numeric_dtype(s.dtype) or is_bool_dtype(s.dtype):
        _add(report, f'{name}_dtype', 'error', 1,
             f'{name} must be numeric in the raw Parquet schema; got {s.dtype}. '
             'Do not silently parse values during loading.')
    _add(report, f'{name}_unparseable', 'warning', bad.sum(),
         f'{name} contains non-null values that cannot be represented numerically.', _sample(s[bad]))
    arr = numeric.to_numpy(dtype='float64', na_value=np.nan)
    finite = pd.Series(np.isfinite(arr), index=df.index)
    _add(report, f'{name}_nonfinite', 'warning', (s.notna() & ~finite).sum(),
         f'{name} contains NaN/Inf or non-finite values.')
    _add(report, f'{name}_negative', 'warning', (finite & (numeric < 0)).sum(),
         f'{name} has negative values; check intended cohort rules.') if not allow_negative else None
    if positive:
        _add(report, f'{name}_zero', 'warning', (finite & (numeric == 0)).sum(),
             f'{name} has zero values: invalid for per-unit pricing.')
    if integer:
        non_integer = finite & (numeric % 1 != 0)
        _add(report, f'{name}_fractional', 'warning', non_integer.sum(),
             f'{name} contains fractional values but represents an integer code.')
    return numeric


def _boolean_field(report: ValidationReport, df: pd.DataFrame, name: str) -> None:
    s = df[name]
    if is_bool_dtype(s.dtype):
        return
    # Parquet nullable Booleans can materialize as object containing real
    # Python bool and None. These values are valid; do not cast to bool.
    valid_values = s.map(lambda x: pd.isna(x) or isinstance(x, (bool, np.bool_)))
    invalid = ~valid_values
    if invalid.any():
        _add(report, f'{name}_dtype', 'error', 1,
             f'{name} is not Boolean-compatible (dtype {s.dtype}). Do not cast strings.')
        _add(report, f'{name}_invalid', 'warning', invalid.sum(),
             f'{name} has values other than true/false/null.', _sample(s[invalid]))
    elif not is_object_dtype(s.dtype):
        _add(report, f'{name}_dtype', 'warning', 1,
             f'{name} uses unusual dtype {s.dtype}, but values are valid Boolean/null.')


def _mapping_exceptions(df: pd.DataFrame, id_col: str, label_col: str) -> pd.DataFrame:
    complete = df[[id_col, label_col]].dropna()
    if complete.empty:
        return pd.DataFrame(columns=[id_col, label_col, 'count', 'issue'])
    pairs = complete.groupby([id_col, label_col], observed=True, dropna=False).size().rename('count').reset_index()
    ids = pairs.groupby(id_col, observed=True)[label_col].transform('size') > 1
    labels = pairs.groupby(label_col, observed=True)[id_col].transform('size') > 1
    result = pairs[ids | labels].copy()
    if not result.empty:
        result['issue'] = np.select([ids.loc[result.index] & labels.loc[result.index],
                                     ids.loc[result.index]],
                                    ['id_and_label_ambiguous', 'id_multiple_labels'],
                                    default='label_multiple_ids')
    else:
        result['issue'] = pd.Series(dtype='object')
    return result


def _completeness(df: pd.DataFrame, valid_dates: pd.Series, freq: str) -> pd.DataFrame:
    columns = ['building_name', 'project_name', 'master_project_name',
               'rooms_bucket', 'has_parking', 'procedure_id',
               'procedure_name_en', 'is_pre_registration',
               'area_id', 'area_name_en', 'price_psf']
    temp = df.loc[valid_dates.notna(), columns].copy()
    periods = valid_dates[valid_dates.notna()].dt.tz_localize(None).dt.to_period(freq).astype(str)
    temp.insert(0, 'period', periods.to_numpy())
    missing = temp[columns].isna().groupby(temp['period']).sum()
    rows = temp.groupby('period').size().rename('transactions')
    out = rows.to_frame().join(missing.add_suffix('_missing_n'))
    for name in columns:
        out[f'{name}_missing_pct'] = (100 * out[f'{name}_missing_n'] / out['transactions']).round(4)
    out = out.reset_index()
    out.insert(1, 'provisional_2026', out['period'].str.startswith('2026'))
    return out


def validate_transactions(
    df: pd.DataFrame, *, source_info: 'SourceInfo | None' = None,
    strict: bool = False, max_psf_exceptions: int = 1000,
) -> ValidationReport:
    """Validate source contract and compute non-destructive audit diagnostics.

    Strict mode raises for structural failures: absent required fields, duplicate
    IDs, wrong physical column types, invalid identifiers or empty data.
    Record-level anomalies are warnings, to preserve evidence for per-cohort QA.
    All full-data checks are calculated before emitting the report.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError('validate_transactions requires a pandas DataFrame')
    report = ValidationReport(
        row_count=len(df), column_count=len(df.columns),
        generated_at_utc=datetime.now(timezone.utc).isoformat(),
        source_sha256=getattr(source_info, 'sha256', None),
    )
    if df.empty:
        _add(report, 'empty_dataset', 'error', 1, 'Source contains no transaction rows or columns.')
    if not df.columns.is_unique:
        _add(report, 'duplicate_columns', 'error', 1, 'Source has duplicate column names.')
    missing_cols = sorted(set(REQUIRED_COLUMNS) - set(df.columns))
    extra_cols = sorted(set(df.columns) - set(REQUIRED_COLUMNS))
    _add(report, 'missing_columns', 'error', len(missing_cols),
         f'Missing required source columns: {missing_cols}', tuple(missing_cols))
    _add(report, 'extra_columns', 'warning', len(extra_cols),
         f'New columns observed: {extra_cols}. Columns are retained.', tuple(extra_cols))
    if report.errors:
        if strict:
            raise DataValidationError('; '.join(f.message for f in report.errors))
        return report

    report.column_profile = [
        {'column': str(c), 'dtype': str(df[c].dtype), 'rows': len(df),
         'missing_n': int(df[c].isna().sum()),
         'missing_pct': round(100 * df[c].isna().mean(), 5),
         'non_null_unique': int(df[c].nunique(dropna=True))}
        for c in df.columns
    ]

    ids = df['transaction_id']
    if not (is_numeric_dtype(ids.dtype) or _is_text(ids)) or is_bool_dtype(ids.dtype):
        _add(report, 'transaction_id_dtype', 'error', 1,
             f'transaction_id must be an identifier, got {ids.dtype}')
    _add(report, 'transaction_id_null', 'error', ids.isna().sum(),
         'Null transaction IDs invalidate COUNT(DISTINCT) reconciliation.')
    duplicate = ids.notna() & ids.duplicated(keep=False)
    _add(report, 'transaction_id_duplicate', 'error', duplicate.sum(),
         'Repeated transaction IDs would overcount sales; inspect identifiers.', _sample(ids[duplicate]))

    raw_dates = df['instance_date']
    if not (is_datetime64_any_dtype(raw_dates.dtype) or _is_text(raw_dates)):
        _add(report, 'instance_date_dtype', 'error', 1,
             f'instance_date requires datetime or text ISO date source, got {raw_dates.dtype}')
    try:
        parsed = pd.to_datetime(raw_dates, errors='coerce', format='ISO8601', utc=True)
    except (ValueError, TypeError):
        parsed = pd.Series(pd.NaT, index=df.index, dtype='datetime64[ns, UTC]')
    _add(report, 'instance_date_missing', 'warning', raw_dates.isna().sum(),
         'Missing date; not eligible for calendar-based KPIs.')
    invalid_dates = raw_dates.notna() & parsed.isna()
    _add(report, 'instance_date_unparseable', 'warning', invalid_dates.sum(),
         'Unparseable registration dates; preserve raw values.', _sample(raw_dates[invalid_dates]))
    dates_outside = parsed.notna() & ((parsed.dt.year < 1975) | (parsed.dt.year > 2026))
    _add(report, 'instance_date_outside_snapshot', 'warning', dates_outside.sum(),
         'Dates outside 1975–2026 reference snapshot; could represent a new version.')

    for col, accepted in CATEGORY_DOMAINS.items():
        s = df[col]
        if not _is_text(s):
            _add(report, f'{col}_dtype', 'error', 1,
                 f'{col} must be categorical/text, got {s.dtype}')
        unknown = s.notna() & ~s.isin(accepted)
        _add(report, f'{col}_unknown', 'warning', unknown.sum(),
             f'{col} has unexpected categories; do not map silently.', _sample(s[unknown]))
        report.category_counts[col] = {str(k): int(v) for k, v in s.value_counts(dropna=False).items()}
        _add(report, f'{col}_null', 'warning', s.isna().sum(),
             f'{col} contains missing classifications that affect KPI denominators.')

    for col in ('area_name_en', 'project_name', 'master_project_name',
                'building_name', 'property_sub_type', 'procedure_name_en'):
        if not _is_text(df[col]):
            _add(report, f'{col}_dtype', 'error', 1,
                 f'{col} should be text/category, got {df[col].dtype}.')
    for col in ('area_id', 'procedure_id'):
        s = df[col]
        if not (is_numeric_dtype(s.dtype) or _is_text(s)) or is_bool_dtype(s.dtype):
            _add(report, f'{col}_dtype', 'error', 1,
                 f'{col} must preserve integer/text identifier values, got {s.dtype}.')

    rooms = _numeric_field(report, df, 'rooms_bucket', integer=True)
    bad_rooms = rooms.notna() & ~rooms.isin([0, 1, 2, 3, 4, 5])
    _add(report, 'rooms_bucket_outside_domain', 'warning', bad_rooms.sum(),
         'rooms_bucket must use 0=studio, 1..4 or 5=5+; no imputation.', _sample(df.loc[bad_rooms, 'rooms_bucket']))
    _numeric_field(report, df, 'price_aed', positive=True)
    _numeric_field(report, df, 'area_sqm', positive=True)
    _numeric_field(report, df, 'price_psf')
    psf_num = pd.to_numeric(df['price_psf'], errors='coerce')
    _add(report, 'price_psf_nonpositive', 'warning',
         (psf_num.notna() & (psf_num <= 0)).sum(),
         'price_psf is zero or negative: invalid as a positive unit-price metric.')
    _boolean_field(report, df, 'has_parking')
    _boolean_field(report, df, 'is_pre_registration')

    flags = _numeric_field(report, df, 'quality_flags', integer=True)
    flags_ok = flags.notna() & np.isfinite(flags.to_numpy(dtype='float64', na_value=np.nan)) & (flags >= 0) & (flags % 1 == 0)
    _add(report, 'quality_flags_invalid', 'error', (~flags_ok).sum(),
         'quality_flags must be non-null, finite, nonnegative integer bitmasks.')
    good = flags[flags_ok].astype('int64')
    report.quality_flags = {
        'value_counts': {str(k): int(v) for k, v in good.value_counts().items()},
        'bit_counts': {str(bit): int(((good & bit) != 0).sum()) for bit in QUALITY_BITS},
        'bit_meanings': {str(k): v for k, v in QUALITY_BITS.items()},
        'unknown_bits_n': int(((good & ~KNOWN_BITS_MASK) != 0).sum()),
    }
    _add(report, 'quality_flags_unknown_bits', 'warning', report.quality_flags['unknown_bits_n'],
         'Unknown quality flag bit(s): source codebook update required.')
    _add(report, 'publisher_quality_flags_nonzero', 'warning', (good != 0).sum(),
         'Publisher-marked records are retained in raw layer; apply cohort policy later.')

    for key, label in [('area_id', 'area_name_en'), ('procedure_id', 'procedure_name_en')]:
        exceptions = _mapping_exceptions(df, key, label)
        if key == 'area_id':
            report.area_mapping = exceptions
        else:
            report.procedure_mapping = exceptions
        _add(report, f'{key}_mapping_ambiguous', 'warning', len(exceptions),
             f'{key} and {label} do not form a consistent one-to-one mapping. '
             'This is a count of conflicting mapping pairs, not transactions.')
        mismatched_nulls = df[key].isna() ^ df[label].isna()
        _add(report, f'{key}_null_mismatch', 'warning', mismatched_nulls.sum(),
             f'Exactly one of {key}/{label} is missing; investigate source completeness.')

    # Derivation check: compare raw price_psf with price / sqft only when all
    # inputs are finite and positive. Do not overwrite either field.
    price = pd.to_numeric(df['price_aed'], errors='coerce')
    area = pd.to_numeric(df['area_sqm'], errors='coerce')
    psf = pd.to_numeric(df['price_psf'], errors='coerce')
    valid = np.isfinite(price) & np.isfinite(area) & np.isfinite(psf) & (price > 0) & (area > 0)
    expected = price[valid] / (area[valid] * SQFT_PER_SQM)
    # Small absolute tolerance prevents false failures for rounded small values.
    difference = (psf[valid] - expected).abs()
    pct = 100 * difference / expected
    bad_psf = (pct > 1.0) & (difference > 0.01)
    _add(report, 'price_psf_discrepancy', 'warning', bad_psf.sum(),
         'Reported price_psf differs from price_aed/(area_sqm*10.76391041671) by >1% and >0.01 AED/ft².')
    if bad_psf.any():
        subset = df.loc[bad_psf[bad_psf].index, ['transaction_id', 'price_aed', 'area_sqm', 'price_psf']].copy()
        subset['calculated_price_psf'] = expected[bad_psf]
        subset['absolute_difference'] = difference[bad_psf]
        subset['relative_error_pct'] = pct[bad_psf]
        report.psf_exceptions = subset.sort_values('relative_error_pct', ascending=False).head(max_psf_exceptions).reset_index(drop=True)
        if int(bad_psf.sum()) > max_psf_exceptions:
            _add(report, 'price_psf_exception_export_capped', 'warning', int(bad_psf.sum()) - max_psf_exceptions,
                 f'Only the largest {max_psf_exceptions} price_psf discrepancies are exported; total is reported.')

    if parsed.notna().any():
        report.monthly_completeness = _completeness(df, parsed, 'M')
        report.yearly_completeness = _completeness(df, parsed, 'Y')
        mask_2026 = parsed.dt.year.eq(2026)
        for col in ('building_name', 'has_parking', 'procedure_name_en'):
            missing_2026 = int(df.loc[mask_2026, col].isna().sum())
            _add(report, f'{col}_missing_2026', 'warning', missing_2026,
                 f'{col} is missing in 2026 transactions; treat 2026 as provisional.')
        missing_procedure = df['procedure_id'].isna() | df['procedure_name_en'].isna() | df['is_pre_registration'].isna()
        _add(report, 'procedure_completeness', 'warning', missing_procedure.sum(),
             'Missing procedure/pre-registration metadata; do not infer Ready=verified resale.')

    if strict and report.errors:
        raise DataValidationError('; '.join(f'{f.code}: {f.message}' for f in report.errors))
    return report
