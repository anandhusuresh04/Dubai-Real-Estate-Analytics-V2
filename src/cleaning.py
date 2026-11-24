"""Auditable, non-destructive cohort eligibility for Dubai DLD sales.

No transaction is deleted, imputed, winsorized, or relabeled here. This module
records suitability for different research questions; callers select cohorts
explicitly. Use src.validation on the original data before this stage.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.validation import REQUIRED_COLUMNS, DataValidationError, validate_transactions

COHORT_COLUMNS = (
    "eligible_market_activity", "eligible_residential_core",
    "eligible_residential_strict", "eligible_known_segment",
    "eligible_amenity_known", "eligible_2026_provisional",
)


def _numeric(s: pd.Series) -> pd.Series:
    """Temporary numeric view. Source series is never rewritten."""
    return pd.to_numeric(s, errors="coerce")


def _finite(s: pd.Series) -> pd.Series:
    return pd.Series(np.isfinite(_numeric(s).to_numpy(dtype="float64", na_value=np.nan)), index=s.index)


def _known_parking(s: pd.Series) -> pd.Series:
    # No astype(bool): bool(np.nan) and bool('False') are both True.
    return s.map(lambda x: isinstance(x, (bool, np.bool_)))


def clean_transactions(raw: pd.DataFrame, *, strict: bool = True) -> pd.DataFrame:
    """Return all source rows with normalized date and documented cohort flags.

    strict=True invokes the *existing* source validation contract and refuses
    critical schema, identifier, and physical-type failures. Record-level source
    anomalies remain in the returned data with False eligibility where relevant.
    A non-strict call still requires the 20 source columns, since computing
    missing fields by default would produce misleading eligibility results.

    No row order/index, raw value, or raw dtype is changed. The added
    ``transaction_date`` is a UTC-normalized technical representation of the
    registration date (source is date-only); no local transaction time is inferred.
    """
    if not isinstance(raw, pd.DataFrame):
        raise TypeError("clean_transactions requires a pandas DataFrame")
    missing = sorted(set(REQUIRED_COLUMNS) - set(raw.columns))
    if missing:
        raise DataValidationError(f"Missing source columns: {missing}")
    if not raw.columns.is_unique:
        raise DataValidationError("Duplicate source column names")
    if raw.empty:
        raise DataValidationError("Cannot construct cohorts from an empty source")
    if strict:
        validate_transactions(raw, strict=True)

    overlapping = {"transaction_date", "is_built_residential", *COHORT_COLUMNS} & set(raw.columns)
    if overlapping:
        raise DataValidationError(f"Derived columns already exist; refusing overwrite: {sorted(overlapping)}")

    out = raw.copy(deep=True)
    # Dates are interpreted as calendar registration dates, not exact timestamps.
    parsed = pd.to_datetime(raw["instance_date"], errors="coerce", format="ISO8601", utc=True)
    out["transaction_date"] = parsed
    date_ok = parsed.notna()
    year = parsed.dt.year

    price = _numeric(raw["price_aed"])
    area = _numeric(raw["area_sqm"])
    valid_price = _finite(raw["price_aed"]) & price.ge(0)
    valid_price_positive = valid_price & price.gt(0)
    valid_area = _finite(raw["area_sqm"]) & area.gt(0)
    flag = _numeric(raw["quality_flags"])
    flag_zero = flag.eq(0) & _finite(raw["quality_flags"])

    # Source schema only describes sales; preserve all property/usage types in P0.
    out["is_built_residential"] = raw["usage_label"].eq("Residential") & raw["property_type_label"].isin(("Unit", "Villa"))
    identifier_ok = raw["transaction_id"].notna() & ~raw["transaction_id"].duplicated(keep=False)
    out["eligible_market_activity"] = identifier_ok & date_ok & valid_price
    out["eligible_residential_core"] = (out["eligible_market_activity"] & out["is_built_residential"]
                                         & valid_price_positive & valid_area)
    out["eligible_residential_strict"] = out["eligible_residential_core"] & flag_zero

    room = _numeric(raw["rooms_bucket"])
    known_rooms = _finite(raw["rooms_bucket"]) & room.isin((0, 1, 2, 3, 4, 5))
    known_reg = raw["reg_type_label"].isin(("Ready", "Off-Plan"))
    # P2 is a usable feature cohort, not a declaration that size-band
    # boundaries or matched-cell coverage have already been validated.
    out["eligible_known_segment"] = (out["eligible_residential_strict"] & raw["area_id"].notna()
                                     & known_reg & known_rooms)
    out["eligible_amenity_known"] = (out["eligible_residential_strict"] & year.between(2015, 2025)
                                    & known_rooms & _known_parking(raw["has_parking"]))
    out["eligible_2026_provisional"] = out["eligible_market_activity"] & year.eq(2026)
    for name in ("is_built_residential", *COHORT_COLUMNS):
        out[name] = out[name].fillna(False).astype(bool)
    if len(out) != len(raw) or not out.index.equals(raw.index):
        raise AssertionError("Unexpected row/index change while deriving cohorts")
    return out


def cohort_audit(cleaned: pd.DataFrame) -> pd.DataFrame:
    """Report retained/excluded counts without pretending independent flags are sequential.

    Core and strict form a sequential funnel; remaining cohorts are subsets
    of strict or market-activity, and are identified by their true parent.
    """
    missing = [c for c in COHORT_COLUMNS if c not in cleaned.columns]
    if missing:
        raise ValueError(f"Missing cohort flags: {missing}")
    n = len(cleaned)
    stages = [
        ("P0_ALL_SALES", "eligible_market_activity", n, "raw source"),
        ("P1_RESIDENTIAL_CORE", "eligible_residential_core", int(cleaned["eligible_market_activity"].sum()), "P0_ALL_SALES"),
        ("P1_STRICT", "eligible_residential_strict", int(cleaned["eligible_residential_core"].sum()), "P1_RESIDENTIAL_CORE"),
        ("P2_KNOWN_SEGMENT", "eligible_known_segment", int(cleaned["eligible_residential_strict"].sum()), "P1_STRICT"),
        ("P3_AMENITY_KNOWN", "eligible_amenity_known", int(cleaned["eligible_residential_strict"].sum()), "P1_STRICT"),
        ("P4_2026_PROVISIONAL", "eligible_2026_provisional", int(cleaned["eligible_market_activity"].sum()), "P0_ALL_SALES"),
    ]
    result = []
    for label, col, input_n, parent in stages:
        retained = int(cleaned[col].sum())
        if retained > input_n:
            raise ValueError(f"{label} is not a subset of {parent}")
        result.append({"cohort_id": label, "parent": parent, "input_n": input_n,
                       "retained_n": retained, "excluded_n": input_n - retained})
    return pd.DataFrame(result)
