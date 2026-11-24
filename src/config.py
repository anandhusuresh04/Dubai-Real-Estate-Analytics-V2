"""Research defaults for Dubai Real Estate Analytics V2.

This module never reads a dataset or changes cohort eligibility. The loader is
still authoritative for source-path resolution and source metadata. Constants
here are explicit *defaults*, not rules that silently filter transactions.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.loader import DEFAULT_SOURCE, PROJECT_ROOT, resolve_source_path

SNAPSHOT_SHA256 = "8294c3dd83dde2e16e64eaf1ef155a1ad14ec16b6b39384561777afb8425417e"
HISTORICAL_START_YEAR = 2010
HISTORICAL_END_YEAR = 2025
PRIMARY_BASE_YEAR = 2021
PRIMARY_END_YEAR = 2025
PROVISIONAL_YEAR = 2026
NOMINAL_BUDGET_THRESHOLDS_AED = (1_000_000, 1_500_000, 2_000_000)

# Physical size bands are taken from the approved Notebook 02 specification.
# They are descriptive intervals, not a quality-adjustment guarantee.
COARSE_AREA_BANDS_SQM = {
    "Unit": (0, 45, 65, 90, 125, 175, 250, float("inf")),
    "Villa": (0, 150, 225, 300, 400, 550, 750, 1100, float("inf")),
}
FINE_AREA_BANDS_SQM = {
    "Unit": (0, 35, 45, 55, 65, 80, 90, 110, 125, 150, 175, 225, 300, float("inf")),
    "Villa": (0, 120, 150, 185, 225, 265, 300, 350, 400, 475, 550, 650,
              750, 925, 1100, 1500, float("inf")),
}

# Order matters: these are the actual Notebook 02 designs A–E.
MATCHING_DESIGNS = {
    "A_broad": ("area_id", "property_type_label", "reg_type_label"),
    "B_bedrooms": ("area_id", "property_type_label", "reg_type_label", "rooms_bucket"),
    "C_size_only": ("area_id", "property_type_label", "reg_type_label", "size_coarse"),
    "D_size_bedrooms": ("area_id", "property_type_label", "reg_type_label", "size_coarse", "rooms_bucket"),
    "E_fine_bedrooms": ("area_id", "property_type_label", "reg_type_label", "size_fine", "rooms_bucket"),
}


@dataclass(frozen=True)
class ResearchPaths:
    """Resolved destinations; *constructing* this object creates nothing."""

    root: Path = PROJECT_ROOT

    def __post_init__(self) -> None:
        object.__setattr__(self, "root", Path(self.root).expanduser().resolve())

    @property
    def raw_source(self) -> Path:
        return resolve_source_path(DEFAULT_SOURCE, root=self.root)

    @property
    def aggregates(self) -> Path:
        return self.root / "data" / "aggregates"

    @property
    def tables(self) -> Path:
        return self.root / "reports" / "tables"

    @property
    def figures(self) -> Path:
        return self.root / "reports" / "figures"

    @property
    def notebooks(self) -> Path:
        return self.root / "notebooks"


def research_paths(root: str | Path | None = None) -> ResearchPaths:
    """Return paths without doing IO or creating directories."""
    return ResearchPaths(PROJECT_ROOT if root is None else Path(root))


def validate_year_window(start_year: int, end_year: int, *, allow_provisional: bool = False) -> tuple[int, int]:
    """Check a requested historical window without filtering the source."""
    if isinstance(start_year, bool) or isinstance(end_year, bool) or not isinstance(start_year, int) or not isinstance(end_year, int):
        raise TypeError("Years must be Python integers (not booleans)")
    upper = PROVISIONAL_YEAR if allow_provisional else HISTORICAL_END_YEAR
    if not (HISTORICAL_START_YEAR <= start_year <= end_year <= upper):
        raise ValueError(f"Year window must satisfy {HISTORICAL_START_YEAR} <= start <= end <= {upper}")
    return start_year, end_year
