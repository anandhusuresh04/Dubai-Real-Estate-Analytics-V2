"""Audited upstream file registry. This module never creates research data.

The registry distinguishes research-plan names from observed notebook export names.
An artifact is never considered verified merely because it is listed here.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

SOURCE_SHA256 = '8294c3dd83dde2e16e64eaf1ef155a1ad14ec16b6b39384561777afb8425417e'
Format = Literal['parquet', 'csv']

@dataclass(frozen=True)
class Artifact:
    key: str
    filename: str
    fmt: Format
    owner: str
    grain: str
    required_columns: tuple[str, ...] = ()
    rq: tuple[str, ...] = ()
    status: str = 'UNVERIFIED_ON_DISK'
    @property
    def relative_path(self) -> Path:
        directory = 'data/aggregates' if self.fmt == 'parquet' else 'reports/tables'
        return Path(directory) / self.filename


def _p(key: str, owner: str, grain: str, rqs: str, required=(), filename: str | None = None) -> Artifact:
    return Artifact(key, filename or f'{key}.parquet', 'parquet', owner, grain,
                    tuple(required), tuple(rqs.split(',')))


def _c(key: str, owner: str, grain: str, rqs: str, required=(), filename: str | None = None) -> Artifact:
    return Artifact(key, filename or f'{key}.csv', 'csv', owner, grain,
                    tuple(required), tuple(rqs.split(',')))

# Export names derived from the actual code in the uploaded executed notebooks.
# Notebook 01's Parquet names are intentionally NOT prefixed with '01_'.
ARTIFACTS: dict[str, Artifact] = {a.key: a for a in [
    _p('market_yearly','01','year','RQ04,RQ05',('year','n_transactions')),
    _p('market_quarterly','01','year-quarter','RQ04'),
    _p('property_mix_yearly','01','year × property_type','RQ04,RQ05'),
    _p('registration_mix_yearly','01','year × registration','RQ05'),
    _p('registration_growth_contributions','01','registration change','RQ05'),
    _p('community_concentration_yearly','01','year × community universe','RQ04'),
    _p('budget_accessibility','01','year × nominal budget','RQ03'),
    _p('price_tail_concentration','01','year × tail policy','RQ14'),
    _c('01_market_summary','01','year','RQ04,RQ05',('year','n_transactions')),
    _c('01_budget_summary','01','year × nominal budget','RQ03'),
    _c('01_price_tail_summary','01','year × tail policy','RQ14'),
    _c('01_research_findings','01','claim','RQ03,RQ04,RQ05,RQ14'),
    _p('02_price_index_endpoint','02','design × endpoint comparison','RQ01'),
    _p('02_price_index_historical','02','design × year','RQ01'),
    _p('02_price_index_historical_coverage','02','design × year','RQ01'),
    _p('02_price_index_specification_sensitivity','02','design × sensitivity','RQ01'),
    _p('02_raw_residential_price_yearly','02','year × P1 Strict','RQ01'),
    _p('02_price_mix_decomposition','02','comparable strata','RQ01'),
    _p('02_area_mix_decomposition','02','size strata','RQ02'),
    _p('02_residential_size_mix','02','year × segment','RQ02'),
    _c('02_price_research_decisions','02','RQ decision','RQ01,RQ02'),
    _p('03_activity_period_panel','03','period × supported cohort','RQ04'),
    _p('03_registration_annual','03','year × registration','RQ05'),
    _p('03_registration_growth_contributions','03','registration × growth','RQ05'),
    _p('03_community_concentration_yearly','03','year × geography universe','RQ04'),
    _p('03_community_universe_sensitivity','03','year × geography policy','RQ04'),
    _p('03_activity_geography_coverage','03','period × geography status','RQ04'),
    _p('03_activity_lead_lag_validation','03','chronological fold','RQ06'),
    _c('03_research_findings','03','claim','RQ04,RQ05,RQ06'),
    _p('04_identity_registry','04','area_id','RQ07,RQ08,RQ09,RQ13'),
    _p('04_yearly_profile','04','area_id × year','RQ07,RQ09'),
    _p('04_activity_year_panel','04','area_id × year','RQ09'),
    _p('04_growth_validated','04','eligible community','RQ07'),
    _p('04_matching_decisions','04','area_id × gate','RQ07'),
    _p('04_growth_ineligible','04','ineligible community','RQ07'),
    _p('04_dispersion_yearly','04','year × fixed community universe','RQ08'),
    _p('04_activity_price_regimes','04','area_id × regime','RQ09'),
    _p('04_price_stability','04','area_id × window','RQ13'),
    _p('04_stability_reliability','04','area_id × support gate','RQ13'),
    _c('04_research_findings','04','claim','RQ07,RQ08,RQ09,RQ13'),
    _p('05_offplan_ready_matched_gap','05','matched stratum design','RQ11'),
    _p('05_registration_matching_coverage','05','registration × design','RQ11'),
    _p('05_registration_matched_cells','05','area × year × type × size × bedrooms','RQ11'),
    _p('05_registration_cluster_uncertainty','05','bootstrap design','RQ11'),
    _p('05_registration_gap_yearly','05','year × matched design','RQ11'),
    _p('05_size_price_binned','05','type × area band × registration','RQ10'),
    _p('05_size_price_linear_models','05','property type × model','RQ10'),
    _p('05_size_price_nonlinear_models','05','property type × model','RQ10'),
    _p('05_bedroom_contrast_support','05','bedroom contrast × gate','RQ12'),
    _p('05_bedroom_adjusted','05','bedroom contrast × model','RQ12'),
    _p('05_parking_overlap_feasibility','05','parking × community','RQ12'),
    _c('05_research_findings','05','claim','RQ10,RQ11,RQ12'),
    _p('06_source_provenance','06','run','RQ15'),
    _p('06_integrated_population_selection','06','cohort × selection','RQ15'),
    _p('06_quality_policy_sensitivity','06','RQ × eligibility policy','RQ15'),
    _p('06_temporal_quality_sensitivity','06','month × source field','RQ15'),
    _p('06_research_sensitivity','06','RQ × scenario','RQ15'),
    _p('06_final_research_decisions','06','RQ','RQ01,RQ02,RQ03,RQ04,RQ05,RQ06,RQ07,RQ08,RQ09,RQ10,RQ11,RQ12,RQ13,RQ14,RQ15',('rq_id','final_status')),
    _p('06_claim_evidence_register','06','RQ','RQ15',('rq_id','final_status')),
    _p('06_subclaim_evidence_register','06','claim','RQ15',('rq_id','published','final_publication_status')),
    _p('06_dashboard_readiness','06','page × RQ','RQ15',('page','rq','publishable')),
    _p('06_reproducibility_acceptance','06','run','RQ15',('release_status','ready_for_qualified_publication')),
    _p('06_final_issue_register','06','issue','RQ15'),
    _p('06_export_manifest','06','export','RQ15'),
    _p('06_research_findings','06','RQ','RQ15'),
    _p('06_finalization_checks','06','check','RQ15',('check','passed')),
    _p('06_figure_validation','06','figure','RQ15'),
    _p('06_registration_gap_independent','06','matched method','RQ11'),
    _p('06_price_index_independent','06','matched design','RQ01'),
]}


def get_artifact(key: str) -> Artifact:
    if key not in ARTIFACTS:
        raise KeyError(f'Artifact not allowlisted: {key}')
    return ARTIFACTS[key]


def resolve_artifact(root: Path, key: str) -> Path:
    """Resolve an allowlisted literal filename, never user-supplied paths."""
    root = Path(root).resolve()
    path = (root / get_artifact(key).relative_path).resolve()
    if not path.is_relative_to(root):
        raise ValueError('Artifact escaped repository root')
    return path
