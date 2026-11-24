"""Pure, explicit research statistics for Dubai registered-sale transaction data.

No IO, filtering by cohort, inferred property quality, or automatic rankings.
The caller must choose its analytical population and matching columns. A matched
median movement is NOT a constant-quality / repeat-sales appreciation index.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class MatchedPriceResult:
    """Conditional fixed-base basket result for the observable matched groups."""
    base_year: int
    end_year: int
    min_group_n: int
    matched_groups: int
    matched_base_n: int
    matched_end_n: int
    parent_base_n: int
    parent_end_n: int
    coverage_base_pct: float
    coverage_end_pct: float
    effective_groups: float
    largest_base_weight_pct: float
    weighted_log_change: float
    change_pct: float


def _ensure_positive_int(name: str, n: int) -> None:
    if isinstance(n, bool) or not isinstance(n, (int, np.integer)) or n < 1:
        raise ValueError(f"{name} must be a positive integer")


def _validate_columns(frame: pd.DataFrame, cols: Sequence[str]) -> None:
    if not isinstance(frame, pd.DataFrame):
        raise TypeError("Expected pandas DataFrame")
    missing = sorted(set(cols) - set(frame.columns))
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    if not frame.columns.is_unique:
        raise ValueError("Duplicate DataFrame columns")


def ratio_coverage(numerator: int | float, denominator: int | float) -> float:
    """Return percentage, undefined (NaN) iff denominator is zero.

    Negative, nonfinite or numerator>denominator is always an error.
    """
    n, d = float(numerator), float(denominator)
    if not (np.isfinite(n) and np.isfinite(d)) or min(n, d) < 0 or n > d:
        raise ValueError("Invalid coverage counts: require 0 <= numerator <= denominator and finite values")
    if d == 0:
        return float("nan")
    return 100.0 * n / d


def check_count_value_identity(count: Sequence[float], mean_value: Sequence[float], total_value: Sequence[float], *, atol: float = 1e-6, rtol: float = 1e-10) -> bool:
    """Check count * mean = aggregate value without changing inputs."""
    n, m, t = (np.asarray(v, dtype=float) for v in (count, mean_value, total_value))
    if n.shape != m.shape or n.shape != t.shape or not (np.isfinite(n).all() and np.isfinite(m).all() and np.isfinite(t).all()):
        return False
    return bool(np.all(n >= 0) and np.allclose(n * m, t, atol=atol, rtol=rtol))


def fixed_weighted_log_change(base: Sequence[float], end: Sequence[float], weights: Sequence[float]) -> float:
    """Weighted log price ratio; requires strictly positive prices and normalized weights."""
    a, b, w = (np.asarray(v, dtype=float) for v in (base, end, weights))
    if a.ndim != 1 or not (a.shape == b.shape == w.shape) or len(a) == 0:
        raise ValueError("Require three equally sized nonempty one-dimensional arrays")
    if not (np.isfinite(a).all() and np.isfinite(b).all() and np.isfinite(w).all()):
        raise ValueError("Nonfinite price or weight")
    if np.any(a <= 0) or np.any(b <= 0) or np.any(w < 0) or not np.isclose(w.sum(), 1.0, rtol=0, atol=1e-10):
        raise ValueError("Prices must be positive; weights nonnegative and sum to one")
    return float(np.dot(w, np.log(b) - np.log(a)))


def complete_calendar_activity(frame: pd.DataFrame, *, area_col: str = "area_key", year_col: str = "year", count_col: str = "transactions", start_year: int, end_year: int, areas: Sequence | None = None) -> pd.DataFrame:
    """Full community-year grid, zero-filled for *known absent* recorded transactions.

    Output change percentages are NaN whenever the prior calendar count is zero.
    Zero fill assumes the caller supplied the complete source/activity population.
    """
    _validate_columns(frame, [area_col, year_col, count_col])
    if start_year > end_year:
        raise ValueError("start_year must not exceed end_year")
    x = frame[[area_col, year_col, count_col]].copy()
    if x[[area_col, year_col]].isna().any().any() or x.duplicated([area_col, year_col]).any():
        raise ValueError("Missing or duplicated community-year identifiers")
    if not pd.to_numeric(x[count_col], errors="coerce").notna().all() or not np.isfinite(x[count_col].to_numpy(dtype=float)).all() or (x[count_col] < 0).any():
        raise ValueError("Nonnegative finite activity counts required")
    if (~x[year_col].between(start_year, end_year)).any():
        raise ValueError("Input contains years outside the explicitly requested window")
    universe = list(pd.unique(x[area_col])) if areas is None else list(areas)
    if len(universe) != len(set(universe)) or any(pd.isna(v) for v in universe):
        raise ValueError("areas must be unique and nonmissing")
    if not set(x[area_col]).issubset(set(universe)):
        raise ValueError("Input contains communities outside the declared universe")
    grid = pd.MultiIndex.from_product([universe, range(start_year, end_year + 1)], names=[area_col, year_col]).to_frame(index=False)
    out = grid.merge(x, on=[area_col, year_col], how="left", validate="one_to_one")
    out[count_col] = out[count_col].fillna(0)
    out["previous_calendar_n"] = out.groupby(area_col, sort=False)[count_col].shift(1)
    out["yoy_delta_n"] = out[count_col] - out["previous_calendar_n"]
    out["yoy_pct"] = np.where(out["previous_calendar_n"].gt(0), 100 * (out[count_col] / out["previous_calendar_n"] - 1), np.nan)
    assert np.isclose(out[count_col].sum(), x[count_col].sum())
    return out


def matched_group_median_change(frame: pd.DataFrame, *, group_cols: Sequence[str], base_year: int, end_year: int, min_group_n: int = 30, year_col: str = "year", price_col: str = "price_per_sqm", parent_base_n: int | None = None, parent_end_n: int | None = None) -> tuple[MatchedPriceResult | None, pd.DataFrame]:
    """Fixed-base weighted matched GROUP MEDIAN changes for two endpoints.

    Each group must have at least min_group_n observed positive-price transactions
    in *both* years. Returns (None, empty table) when no groups qualify.
    Parent denominators must explicitly refer to the caller's chosen cohort;
    otherwise they default to this supplied feature-eligible frame.
    Missing matching keys are excluded, with resulting coverage reported.
    """
    _ensure_positive_int("min_group_n", min_group_n)
    keys = list(group_cols)
    if not keys or len(set(keys)) != len(keys) or year_col in keys or price_col in keys:
        raise ValueError("group_cols must be unique, nonempty and exclude year/price")
    if base_year == end_year:
        raise ValueError("Distinct endpoint years required")
    _validate_columns(frame, [*keys, year_col, price_col])
    sub = frame.loc[frame[year_col].isin([base_year, end_year])].copy()
    parents = {yr: int((sub[year_col] == yr).sum()) for yr in (base_year, end_year)}
    parent0 = parents[base_year] if parent_base_n is None else parent_base_n
    parent1 = parents[end_year] if parent_end_n is None else parent_end_n
    for name, n in [("parent_base_n", parent0), ("parent_end_n", parent1)]:
        if isinstance(n, bool) or not isinstance(n, (int, np.integer)) or n < 0:
            raise ValueError(f"{name} must be a nonnegative integer")
    # Invalid price observations cannot be silently counted in the matched numerator.
    good_price = pd.to_numeric(sub[price_col], errors="coerce")
    if (sub[price_col].notna() & (~np.isfinite(good_price.to_numpy(dtype=float)) | good_price.le(0))).any():
        raise ValueError("Nonmissing prices must be positive and finite; select a valid pricing cohort")
    sub = sub.dropna(subset=[*keys, price_col])
    if sub.empty:
        return None, pd.DataFrame()
    counts = sub.groupby([*keys, year_col], observed=True, dropna=False).agg(n=(price_col, "size"), median_psm=(price_col, "median")).reset_index()
    nwide = counts.pivot(index=keys, columns=year_col, values="n").fillna(0)
    medianwide = counts.pivot(index=keys, columns=year_col, values="median_psm")
    n0 = nwide[base_year] if base_year in nwide else pd.Series(0, index=nwide.index)
    n1 = nwide[end_year] if end_year in nwide else pd.Series(0, index=nwide.index)
    good = n0.ge(min_group_n) & n1.ge(min_group_n)
    if not good.any():
        return None, pd.DataFrame()
    n0 = n0.loc[good].astype(int)
    n1 = n1.loc[good].astype(int)
    m0 = medianwide.loc[good, base_year].astype(float)
    m1 = medianwide.loc[good, end_year].astype(float)
    total0, total1 = int(n0.sum()), int(n1.sum())
    w = n0.to_numpy(dtype=float) / total0
    delta = fixed_weighted_log_change(m0.to_numpy(), m1.to_numpy(), w)
    result = MatchedPriceResult(base_year, end_year, min_group_n, len(n0), total0, total1, int(parent0), int(parent1), ratio_coverage(total0, parent0), ratio_coverage(total1, parent1), float(1 / np.square(w).sum()), float(w.max() * 100), delta, float(np.expm1(delta) * 100))
    detail = n0.rename("base_n").to_frame().assign(end_n=n1, base_median_psm=m0, end_median_psm=m1, base_weight=w, log_change=np.log(m1 / m0)).reset_index()
    return result, detail


def conditional_matched_bootstrap(frame: pd.DataFrame, detail: pd.DataFrame, *, group_cols: Sequence[str], base_year: int, end_year: int, year_col: str = "year", price_col: str = "price_per_sqm", replicates: int = 600, seed: int = 42, ci: float = 0.95) -> pd.DataFrame:
    """Percentile CI for selected-group fixed-reference weighted median changes.

    Resamples transactions *within each supported group and year*. Matched group
    support and base weights are held fixed; this does not capture geography,
    property quality, selection, dependence among transactions, or causal effects.
    """
    _ensure_positive_int("replicates", replicates)
    if replicates < 100 or not 0 < ci < 1:
        raise ValueError("Require >=100 replicates and 0 < ci < 1")
    keys = list(group_cols)
    _validate_columns(frame, [*keys, year_col, price_col])
    _validate_columns(detail, [*keys, "base_weight", "base_n", "end_n"])
    if detail.empty or detail.duplicated(keys).any():
        raise ValueError("detail must contain unique supported groups")
    w = detail["base_weight"].to_numpy(dtype=float)
    if not np.isfinite(w).all() or (w < 0).any() or not np.isclose(w.sum(), 1, atol=1e-10):
        raise ValueError("Weights must be nonnegative and sum to one")
    candidates = frame.loc[frame[year_col].isin([base_year, end_year])].dropna(subset=[*keys, price_col])
    lookup = {k if isinstance(k, tuple) else (k,): np.asarray(g[price_col], dtype=float) for k, g in candidates.groupby([*keys, year_col], observed=True, dropna=False)}
    rng = np.random.default_rng(seed)
    log_changes = np.zeros(replicates, dtype=float)
    for i, row in detail.reset_index(drop=True).iterrows():
        key = tuple(row[k] for k in keys)
        base = lookup.get((*key, base_year))
        end = lookup.get((*key, end_year))
        if base is None or end is None or len(base) != int(row["base_n"]) or len(end) != int(row["end_n"]):
            raise ValueError(f"Missing or inconsistent matched bootstrap group {key}")
        if not (np.isfinite(base).all() and np.isfinite(end).all()) or np.any(base <= 0) or np.any(end <= 0):
            raise ValueError("Bootstrap inputs require finite positive prices")
        for j in range(replicates):
            med0 = np.median(base[rng.integers(0, len(base), len(base))])
            med1 = np.median(end[rng.integers(0, len(end), len(end))])
            log_changes[j] += w[i] * np.log(med1 / med0)
    changes = 100 * np.expm1(log_changes)
    alpha = (1 - ci) / 2
    return pd.DataFrame([{
        "base_year": base_year, "end_year": end_year, "replicates": replicates,
        "seed": seed, "confidence_level": ci,
        "ci_low_pct": float(np.quantile(changes, alpha)),
        "ci_high_pct": float(np.quantile(changes, 1 - alpha)),
        "bootstrap_median_pct": float(np.median(changes)),
        "interpretation": "conditional on observed matched groups and fixed base weights",
    }])
