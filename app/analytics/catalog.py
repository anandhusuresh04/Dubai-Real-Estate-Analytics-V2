"""Explicit source-to-chart contracts; aliases reflect observed notebook export conventions.

No user-configurable column expressions, dynamic estimand recomputation, or invented
metrics. Unknown output schemas fail closed and show an actionable diagnostic.
"""
from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class Exhibit:
    id: str
    title: str
    artifact: str
    rq: str
    kind: str
    dimension: tuple[str,...]
    value: tuple[str,...]
    unit: str
    detail: str
    segment: tuple[str,...] = ()
    filters: tuple[str,...] = ()
    limited: str = ''
    claim_sensitive: bool = False
    min_rows: int = 1
    facets: tuple[str,...] = ()

# Candidate aliases are explicit synonyms for values in the notebooks, NOT a
# request to select arbitrary numerical columns or estimate missing statistics.
EXHIBITS: tuple[Exhibit,...] = (
    Exhibit('annual_count','Annual registered transactions','market_yearly','RQ04','line',('year',),('n_transactions',),'transactions','Registered transactions, not unique properties.'),
    Exhibit('annual_value','Nominal registered consideration','market_yearly','RQ04','bar',('year',),('recorded_gross_value_aed',),'AED','Recorded gross value; not a market capitalization.'),
    Exhibit('quarterly','Quarterly registered activity','market_quarterly','RQ04','line',('year_quarter','quarter_label','period'),('n_transactions',),'transactions','Quarter-level registered activity; incomplete periods must be identified.'),
    Exhibit('property_mix','Property-type registrations','property_mix_yearly','RQ04','line',('year',),('n_transactions','n'),'transactions','Separate transaction counts by recorded property type.',('property_group',),facets=('usage_group',)),
    Exhibit('registration_mix','Ready and Off-Plan registration mix','03_registration_annual','RQ05','line',('year',),('n_transactions','n','transaction_count'),'transactions','Registration-category descriptions, not inventory, demand, or construction completion.',('reg','reg_type_label','registration_type')),
    Exhibit('contributions','Registration growth contribution','03_registration_growth_contributions','RQ05','bar',('reg','reg_type_label','registration_type'),('delta','delta_n_transactions','count_contribution'),'transactions','Signed contribution to the precomputed 2021–2025 registered transaction-count change by Ready, Off-Plan and Unknown registration categories; not total transaction counts.'),
    Exhibit('concentration','Community transaction concentration','03_community_concentration_yearly','RQ04','line',('year',),('count_hhi','hhi','hhi_count'),'HHI','Only the stated geographical universe; do not infer a ranking.',filters=('universe_id',)),
    Exhibit('raw_price','Observed residential transaction price per m²','02_raw_residential_price_yearly','RQ01','line',('year',),('median_psm','median_price_psm','median_price_per_sqm','median_price_per_sqm_aed'),'AED/sqm','Raw P1 Strict observations; not a matched or inflation-adjusted index.'),
    Exhibit('matched_index','Fixed-design matched price index','02_price_index_historical','RQ01','line',('year',),('index_2021_100','index_value','matched_index','index'),'index','Only validated, precomputed designs and historical windows.',claim_sensitive=True),
    Exhibit('index_endpoint','Matched 2021–2025 price-change designs','02_price_index_endpoint','RQ01','bar',('design','design_id'),('change_pct','matched_change_pct','pct_change','price_change_pct','growth_pct'),'percent','Fixed endpoint matched comparisons with method-specific coverage.',claim_sensitive=True),
    Exhibit('index_coverage','Matching support and coverage','02_price_index_historical_coverage','RQ01','table',('year',),('coverage_pct','base_coverage_pct'),'percent','Only source-recorded matching coverage for each fixed year and design.',claim_sensitive=True),
    Exhibit('size_mix','Recorded residential size-category composition','02_residential_size_mix','RQ02','bar',('size_coarse','size_band','area_band'),('n','n_transactions','share_pct','transaction_share_pct'),'transactions','Fixed physical-area bands (m²) from Notebook 02, selected by year, property type, registration and bedroom-metadata availability; codes are bin identifiers, not bedroom counts.',facets=('year','property_type_label','reg_type_label','room_known')),
    Exhibit('budget','Nominal purchase budget mix','budget_accessibility','RQ03','line',('year',),('within_budget_pct','share_pct','transaction_share_pct','budget_share_pct'),'percent','Cumulative share at or below each nominal AED transaction-budget threshold; threshold series overlap and do not sum to 100%. Not household affordability.',('budget_aed','budget_band'),facets=('property_type',)),
    Exhibit('tail','Upper-tail consideration concentration','price_tail_concentration','RQ14','line',('year',),('tail_value_share_pct','value_share_pct'),'percent','Fraction of nominal consideration recorded in the highest-price transaction tail; 0.01 means top 1% and 0.1 means top 10%, not interchangeable populations. Precomputed thresholds only.',('tail_fraction','tail_rule'),facets=('property_type',)),
    Exhibit('community_activity','Community registrations over time','04_activity_year_panel','RQ09','line',('year',),('p0_transactions','n_transactions','n','transaction_count'),'transactions','Historical registered activity for a selected recorded community.',('area_key',),('area_key',)),
    Exhibit('community_prices','Community price history (reported)','04_yearly_profile','RQ07','line',('year',),('median_psm','median_price_per_sqm','median_price_psm'),'AED/sqm','Descriptive price histories; not matched growth, not forecasts.',('area_key',),('area_key',)),
    Exhibit('community_eligibility','Community matching eligibility','04_matching_decisions','RQ07','table',('area_key',),('matched_price_eligible','decision'),'eligibility','Eligibility decisions before any matched community comparison. Not a ranking.'),
    Exhibit('community_growth','Eligible matched community growth','04_growth_validated','RQ07','bar',('area_name','area_key'),('change_pct','growth_pct','matched_growth_pct','price_change_pct'),'percent','Only communities passing the complete matching and endpoint support gates.',claim_sensitive=True),
    Exhibit('community_dispersion','Community price dispersion','04_dispersion_yearly','RQ08','line',('year',),('log_p90_p10','sd_log_medians','dispersion','log_price_dispersion'),'log spread','Precomputed fixed-universe dispersion, not investment risk.',facets=('universe','submarket_reg','size_band')),
    Exhibit('community_regimes','Community activity–price regimes','04_activity_price_regimes','RQ09','table',('area_key',),('regime','regime_label','classification'),'category','Recorded historical regime labels, not a predictive classification.'),
    Exhibit('stability','Historical community price stability','04_price_stability','RQ13','table',('area_key',),('sd_log_link','stability','stability_score'),'source units','Research-defined historical stability, not volatility-based investment risk.'),
    Exhibit('raw_reg_gap','Ready vs Off-Plan registered counts','03_registration_annual','RQ05','bar',('reg','reg_type_label','registration_type'),('n','n_transactions'),'transactions','Descriptive registration mix; not a causal price comparison.',facets=('year',)),
    Exhibit('matched_gap','Ready vs Off-Plan matched price gap','05_registration_gap_yearly','RQ11','line',('year',),('gap_pct','matched_gap_pct','price_gap_pct'),'percent','Qualified contemporaneous gap under common support, not a causal premium.',claim_sensitive=True),
    Exhibit('matched_gap_summary','Matched Ready–Off-Plan design summary','05_offplan_ready_matched_gap','RQ11','table',('design','method','estimand'),('gap_pct','gap_percent','premium_pct'),'percent','Report exactly as the validated research design defines it.',claim_sensitive=True),
    Exhibit('gap_uncertainty','Matched-gap uncertainty and support','05_registration_cluster_uncertainty','RQ11','table',('design','method'),('ci_low_pct','ci_lower_pct','ci_lo_pct'),'percent','Community-cluster uncertainty from the frozen research; noncausal, and only if individually published.',claim_sensitive=True),
    Exhibit('size_price','Recorded property size and price','05_size_price_binned','RQ10','scatter',('median_area',),('median_price',),'AED','Precomputed property-type and coarse-size bins, not raw transaction observations.',('property_type_label',),('property_type_label',),facets=('reg_type_label',)),
    Exhibit('size_elasticity','Size–price model coefficients','05_size_price_linear_models','RQ10','table',('property_type_label',),('beta',),'log–log slope','Within-community/year/registration fixed-effect log–log association (beta). Select outcome: log_price or log_psm. Not a causal enlargement effect.',claim_sensitive=True,facets=('outcome',)),
    Exhibit('bedrooms','Bedroom contrast support decisions','05_bedroom_contrast_support','RQ12','table',('term','contrast'),('decision','supported','eligible','status'),'eligibility','Gate results are diagnostics; this view does not publish withheld bedroom coefficients.'),
    Exhibit('bedroom_estimate','Authorized bedroom coefficients','05_bedroom_adjusted','RQ12','table',('term',),('association_pct',),'percent','Only support-qualified contrasts with an individually authorized claim; no parking or unsupported bedroom result.',claim_sensitive=True),
    Exhibit('parking','Parking overlap feasibility','05_parking_overlap_feasibility','RQ12','table',('parent_n','area_key','area_id'),('overlap_communities','decision','n'),'support diagnostic','Feasibility evidence only. No parking premium is estimable.'),
    Exhibit('selection','Population-selection cohorts','06_integrated_population_selection','RQ15','bar',('cohort','stage','selection'),('n','count','n_transactions'),'transactions','Audited selection cohorts; P2 and P3 are parallel populations, not additive. No sum of cohorts.'),
    Exhibit('quality','Core versus strict cohort sensitivity','06_quality_policy_sensitivity','RQ15','line',('year',),('median_psm',),'AED/sqm','Precomputed cohort-specific median price per sqm. Never pool cohort medians.',('cohort',)),
    Exhibit('temporal_quality','Monthly source-field missingness','06_temporal_quality_sensitivity','RQ15','line',('month',),('missing_pct',),'percent','Observed monthly metadata missingness; historical (2010–2025), not a publisher-policy inference.',('field',),facets=('year',)),
    Exhibit('sensitivity','Independent sensitivity evidence','06_research_sensitivity','RQ15','table',('rq','rq_id'),('scenario','status','difference'),'scenario','Sensitivity records with research-defined support.'),
    Exhibit('decisions','RQ01–RQ15 scientific decisions','06_final_research_decisions','RQ15','table',('rq_id',),('final_status',),'decision','Final Notebook 06 research decisions.'),
    Exhibit('claim_registry','Published and withheld claim registry','06_subclaim_evidence_register','RQ15','table',('upstream_claim_id',),('final_publication_status',),'permission','Publication permissions are read only; withheld claims must not be presented as established.'),
    Exhibit('source','Frozen dataset provenance','06_source_provenance','RQ15','table',('sha256',),('checksum_passed',),'provenance','Source frozen research evidence, not live market feeds.'),
)

BY_ID={e.id:e for e in EXHIBITS}
PAGE_EXHIBITS = {
 'intelligence_brief':('annual_count','annual_value','registration_mix','raw_price','decisions'),
 'market_dynamics':('annual_count','annual_value','quarterly','registration_mix','property_mix','contributions','concentration'),
 'price_reality':('raw_price','matched_index','index_endpoint','index_coverage','size_mix','budget','tail'),
 'community_intelligence':('community_activity','community_prices','community_eligibility','community_growth','community_dispersion','community_regimes','stability'),
 'market_structure':('raw_reg_gap','matched_gap','matched_gap_summary','gap_uncertainty','size_price','size_elasticity','bedrooms','bedroom_estimate','parking'),
 'research_reliability':('source','selection','temporal_quality','quality','sensitivity','decisions','claim_registry'),
}
assert len(BY_ID)==len(EXHIBITS)

# Optional, explicitly precomputed column-level metric switching. A selection
# changes neither cohort nor statistical estimator, and never mixes units.
MEASURE_OPTIONS: dict[str, tuple[tuple[str,str,str],...]] = {
 'property_mix': (('n_transactions','Transactions','transactions'),
                  ('recorded_gross_value_aed','Nominal consideration','AED'),
                  ('count_share_pct','Transaction share','percent'),
                  ('value_share_pct','Consideration share','percent')),
 'registration_mix': (('n','Registered transactions','transactions'),
                      ('value_aed','Nominal consideration','AED'),
                      ('count_share','Transaction share','fraction'),
                      ('value_share','Value share','fraction')),
 'raw_price': (('median_psm','Observed median price per m²','AED/sqm'),
               ('mean_psm','Observed mean price per m²','AED/sqm')),
 'concentration': (('count_hhi','Transaction-count HHI','HHI'),
                   ('value_hhi','Consideration-value HHI','HHI')),
 'size_price': (('median_price','Median registered price','AED'),
                ('median_psm','Median price per m²','AED/sqm')),
 'quality': (('median_psm','Median transaction price per m²','AED/sqm'),
             ('n','Cohort transactions','transactions')),
 'annual_count': (('n_transactions','Transaction count','transactions'),),
}

# Explicit subclaim-to-exhibit lineage must be audited separately. The provided
# Notebook 06 finalization does not grant any source-specific subclaim releases.
# Never infer a binding simply because a claim belongs to the same RQ.
CLAIM_EXHIBIT_BINDINGS: dict[str,tuple[str,...]] = {}
