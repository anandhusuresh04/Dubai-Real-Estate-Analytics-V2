"""Exact-grain metric contract and safe user-filter decisions."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum

class Operation(str, Enum):
    EXACT = 'exact'
    SUM = 'sum_disjoint'
    RATIO = 'ratio_from_numerator_denominator'

@dataclass(frozen=True)
class Metric:
    name: str
    artifact: str
    rq: str
    unit: str
    cohort: str
    grain: tuple[str, ...]
    filter_fields: tuple[str, ...]
    operation: Operation = Operation.EXACT
    numerator: str | None = None
    denominator: str | None = None
    caveat: str = ''

# 'exact' means a precomputed value is displayed at the artifact's recorded
# dimensions; it is NOT an instruction to calculate medians/indices in Streamlit.
METRICS = {m.name:m for m in [
 Metric('registered_count','market_yearly','RQ04','transactions','P0',('year',),('year',),Operation.SUM,caveat='Registered transactions, not unique properties'),
 Metric('registered_value_aed','market_yearly','RQ04','AED','P0',('year',),('year',),Operation.SUM,caveat='Nominal registered consideration, not market cap'),
 Metric('offplan_count_share','03_registration_annual','RQ05','percent','P0',('year','reg_type_label'),('year',),Operation.EXACT,caveat='Use declared Ready/Off-Plan denominator'),
 Metric('community_hhi','03_community_concentration_yearly','RQ04','0–1','P0 known geography',('year','universe_id'),('year','universe_id'),Operation.EXACT,caveat='Never recompute from incomplete top-community sample'),
 Metric('residential_median_psm','02_raw_residential_price_yearly','RQ01','AED/sqm','P1 Strict',('year',),('year',),Operation.EXACT,caveat='Transaction median, not ratio of medians'),
 Metric('matched_price_change','02_price_index_endpoint','RQ01','percent','P2 matched',('design','base_year','end_year'),('design','base_year','end_year'),Operation.EXACT,caveat='Restricted common support, not repeat sales'),
 Metric('nominal_budget_share','budget_accessibility','RQ03','percent','P1 Strict',('year','budget_aed'),('year','budget_aed'),Operation.EXACT,caveat='Observed transactions, not current affordability'),
 Metric('upper_tail_value_share','price_tail_concentration','RQ14','percent','P1 Strict',('year','tail_rule'),('year','tail_rule'),Operation.EXACT),
 Metric('community_matched_growth','04_growth_validated','RQ07','percent','P2 eligible community',('area_id','base_year','end_year'),('area_id','base_year','end_year'),Operation.EXACT,caveat='Only approved eligible communities'),
 Metric('community_dispersion','04_dispersion_yearly','RQ08','log spread','fixed eligible universe',('year','universe_id'),('year','universe_id'),Operation.EXACT),
 Metric('community_regime','04_activity_price_regimes','RQ09','category','supported community',('area_id','period'),('area_id','period'),Operation.EXACT),
 Metric('community_stability','04_price_stability','RQ13','historical dispersion','supported community',('area_id','window'),('area_id','window'),Operation.EXACT),
 Metric('ready_offplan_matched_gap','05_offplan_ready_matched_gap','RQ11','percent','P2 matched',('design','period'),('design','period'),Operation.EXACT,caveat='Observational; not a causal premium'),
 Metric('size_elasticity','05_size_price_linear_models','RQ10','elasticity','P1 Strict model sample',('property_type_label','model_id'),('property_type_label','model_id'),Operation.EXACT),
 Metric('bedroom_association','05_bedroom_adjusted','RQ12','percent','supported Ready Unit sample',('contrast','model_id'),('contrast','model_id'),Operation.EXACT,caveat='Only support-approved contrasts'),
 Metric('rq15_sensitivity','06_research_sensitivity','RQ15','scenario-specific','multiple declared',('rq_id','scenario'),('rq_id','scenario'),Operation.EXACT),
]}

class UnsupportedInteraction(ValueError): pass

def validate_filter(metric: str, filters: dict[str,object], *, available_columns: tuple[str,...] | None=None) -> Metric:
    if metric not in METRICS:raise UnsupportedInteraction(f'Unknown metric: {metric}')
    m=METRICS[metric]
    invalid=set(filters)-set(m.filter_fields)
    if invalid:raise UnsupportedInteraction(f'{metric}: filter(s) change or exceed approved grain: {sorted(invalid)}')
    if available_columns is not None:
        unavailable=set(filters)-set(available_columns)
        if unavailable:raise UnsupportedInteraction(f'{metric}: missing filter columns in artifact: {sorted(unavailable)}')
    if any(value is None for value in filters.values()):
        raise UnsupportedInteraction('Null filter selection is not an approved cohort')
    return m

def require_aggregation(metric: str, requested: Operation, *, disjoint: bool=False, has_denominators: bool=False):
    m=METRICS[metric]
    if requested==Operation.EXACT:return
    if requested != m.operation:raise UnsupportedInteraction(f'Cannot {requested} metric {metric}')
    if requested==Operation.SUM and not disjoint:raise UnsupportedInteraction('Rows not proven disjoint')
    if requested==Operation.RATIO and not has_denominators:raise UnsupportedInteraction('Numerator/denominator unavailable')
