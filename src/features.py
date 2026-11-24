"""Deterministic, non-destructive research features for DLD sales transactions.

Only defined features from docs/data_dictionary.md are created. No statistical
model, imputation, arbitrary size bands, or whole-dataset filtering occurs.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.cleaning import COHORT_COLUMNS
from src.validation import SQFT_PER_SQM

ROOM_LABELS = {0: "Studio", 1: "1BR", 2: "2BR", 3: "3BR", 4: "4BR", 5: "5+BR"}


def engineer_features(cleaned: pd.DataFrame) -> pd.DataFrame:
    """Add correct price, date, registration and amenity features to all rows.

    Price-per-area features require positive finite price *and* area. The
    publisher's ``price_psf`` is kept untouched for independent QA. No fixed
    budget/size cohorts are applied until the relevant research specification.
    """
    required = {"price_aed", "area_sqm", "price_psf", "transaction_date",
                "rooms_bucket", "has_parking", "reg_type_label", *COHORT_COLUMNS}
    missing = sorted(required - set(cleaned.columns))
    if missing:
        raise ValueError(f"Feature prerequisites missing: {missing}; run clean_transactions first")
    new_columns = {"price_per_sqm", "price_per_sqft_calculated", "year", "month", "quarter",
                   "year_quarter", "bedroom_label", "parking_status", "registration_known", "is_offplan"}
    overlapping = new_columns & set(cleaned.columns)
    if overlapping:
        raise ValueError(f"Refusing to overwrite existing feature columns: {sorted(overlapping)}")

    out = cleaned.copy(deep=True)
    price = pd.to_numeric(cleaned["price_aed"], errors="coerce")
    area = pd.to_numeric(cleaned["area_sqm"], errors="coerce")
    valid = (np.isfinite(price) & np.isfinite(area) & price.gt(0) & area.gt(0))
    psm = pd.Series(np.nan, index=cleaned.index, dtype="float64")
    psm.loc[valid] = (price.loc[valid] / area.loc[valid]).astype("float64")
    out["price_per_sqm"] = psm
    out["price_per_sqft_calculated"] = psm / SQFT_PER_SQM

    dates = cleaned["transaction_date"]
    if not isinstance(dates.dtype, pd.DatetimeTZDtype):
        raise TypeError("transaction_date must be the normalized timezone-aware datetime from clean_transactions")
    out["year"] = dates.dt.year.astype("Int64")
    out["month"] = dates.dt.month.astype("Int64")
    out["quarter"] = dates.dt.quarter.astype("Int64")
    yq = dates.dt.strftime("%Y-Q")
    out["year_quarter"] = (yq + out["quarter"].astype("string")).astype("string")

    rooms = pd.to_numeric(cleaned["rooms_bucket"], errors="coerce")
    out["bedroom_label"] = rooms.map(ROOM_LABELS).astype("string")
    parking = pd.Series(pd.NA, index=cleaned.index, dtype="string")
    true_mask = cleaned["has_parking"].map(lambda v: isinstance(v, (bool, np.bool_)) and bool(v))
    false_mask = cleaned["has_parking"].map(lambda v: isinstance(v, (bool, np.bool_)) and not bool(v))
    parking.loc[true_mask] = "Yes"
    parking.loc[false_mask] = "No"
    out["parking_status"] = parking

    out["registration_known"] = cleaned["reg_type_label"].isin(("Ready", "Off-Plan"))
    offplan = pd.Series(pd.NA, index=cleaned.index, dtype="boolean")
    offplan.loc[cleaned["reg_type_label"].eq("Ready")] = False
    offplan.loc[cleaned["reg_type_label"].eq("Off-Plan")] = True
    out["is_offplan"] = offplan
    if len(out) != len(cleaned) or not out.index.equals(cleaned.index):
        raise AssertionError("Unexpected row/index change during feature engineering")
    return out
