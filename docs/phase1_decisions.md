# Phase 1 — evidence, chart-source matrix, and go/no-go policy

## Directly inspected sources

- The uploaded `src.zip` contains the validated `loader`, `validation`, `cleaning`, `features`, `statistics`, `visualization`, `config` and `analysis` packages.
- The uploaded `notebooks.zip` contains seven executed notebooks; all code cells have execution counts and no saved Python error outputs. **This archive contains an older Notebook 06 execution, so the latest separately uploaded `(7)` notebook is the final source for release-gate definitions.**
- The uploaded `tests.zip` contains existing research tests, including Notebook 06 tests.
- The source snapshot is available separately and has the prescribed frozen SHA-256.
- `sql/`, root `app/`, `scripts/build_aggregates.py` and `scripts/run_pipeline.py` **are absent from the uploaded ZIPs**. The user says the existing scripts are empty placeholders. This was not independently inspectable, so **do not remove, overwrite or integrate** those scripts until local review.
- Physical research exports (`data/aggregates/`, `reports/tables/`, `reports/figures/`) were not uploaded. The registry lists *declared* upstream outputs, **not verified disk files**. Their actual columns/types, duplicates, hashes and values must be inspected locally before Phase 2.

## Precise page-to-artifact contract (initial minimal chart set)

| Page | UI feature | Actual source file(s) | Filter dimensions | Mathematical contract / restriction |
|---|---|---|---|---|
| Intelligence Brief | P0 registered sales count/value | `data/aggregates/market_yearly.parquet` | year | Count and AED value in P0; monetary values nominal; different price cohorts not globally filtered |
| Intelligence Brief | Off-Plan share | `data/aggregates/03_registration_annual.parquet` | year, declared registration metric | Share from Ready+Off-Plan parent; no averaged percent |
| Intelligence Brief | Matched growth headline | `data/aggregates/02_price_index_endpoint.parquet` | supported design/base/end comparison | Selected matched population, not same-home appreciation; show coverage and caveat |
| Intelligence Brief | Evidence and caveat | `data/aggregates/06_subclaim_evidence_register.parquet` + `06_dashboard_readiness.parquet` | claim/RQ only | No unsupported headline when `published=False` |
| Market Dynamics | Annual and quarterly counts/registered value | `market_yearly.parquet`, `market_quarterly.parquet`, `03_activity_period_panel.parquet` | stored year/quarter | Add only disjoint counts and sums; do not mix P0 and P1 |
| Market Dynamics | Property/registration mix | `property_mix_yearly.parquet`, `03_registration_annual.parquet`, `03_registration_growth_contributions.parquet` | year, stored category | Shares use actual denominators; Ready does not mean verified resale |
| Market Dynamics | Geographic concentration | `03_community_concentration_yearly.parquet`, `03_community_universe_sensitivity.parquet`, `03_activity_geography_coverage.parquet` | year, stored geographic universe | Do not recompute HHI from top areas or silently omit unknown geography |
| Price Reality | Raw vs matched index | `02_raw_residential_price_yearly.parquet`, `02_price_index_historical.parquet`, `02_price_index_historical_coverage.parquet` | only stored year/design | Never combine unmatched medians or invent a missing index period |
| Price Reality | Endpoint design explorer | `02_price_index_endpoint.parquet`, `02_price_index_specification_sensitivity.parquet` | stored design/reference years | Precomputed fixed group weights and coverage; noncausal |
| Price Reality | Size composition | `02_area_mix_decomposition.parquet`, `02_residential_size_mix.parquet` | only stored comparison/segment | Mean-log decomposition does not decompose median area |
| Price Reality | Nominal budget | `budget_accessibility.parquet`, `01_budget_summary.csv` | precomputed thresholds and years | Registered transaction shares; not listing availability or income affordability |
| Price Reality | Upper-tail value | `price_tail_concentration.parquet`, `01_price_tail_summary.csv` | predefined tail/year | Distinguish within-year percentile from nominal AED cutoff |
| Community Intelligence | Search/identity | `04_identity_registry.parquet`, `04_yearly_profile.parquet` | area_id, available year | Names are labels, not stable joins; no synthetic centroid |
| Community Intelligence | Matched growth and support | `04_growth_validated.parquet`, `04_matching_decisions.parquet`, `04_growth_ineligible.parquet` | eligible area_id, supported period | Unsupported area is INSUFFICIENT EVIDENCE, never zero or poor performance |
| Community Intelligence | Dispersion and regimes | `04_dispersion_yearly.parquet`, `04_activity_price_regimes.parquet` | stored universe/area | Fixed submarket and population, not liquidity or rental return |
| Community Intelligence | Price stability | `04_price_stability.parquet`, `04_stability_reliability.parquet` | supported area/window | No interpolation of missing years |
| Market Structure | Ready/Off-Plan adjusted gap | `05_offplan_ready_matched_gap.parquet`, `05_registration_matching_coverage.parquet`, `05_registration_cluster_uncertainty.parquet` | only stored design/window | Observational, separate side-specific parent coverage, cluster-conditional interval |
| Market Structure | Annual gap | `05_registration_gap_yearly.parquet` | stored year | Year-specific baskets; not directly identical yearly cohorts |
| Market Structure | Size-price | `05_size_price_binned.parquet`, `05_size_price_linear_models.parquet` | stored Unit/Villa/model | Raw bin medians do not form an individual-property curve |
| Market Structure | Bedroom contrasts | `05_bedroom_contrast_support.parquet`, `05_bedroom_adjusted.parquet` | support-approved contrast | Withhold unsupported 3BR/4BR/5+BR effects; parking not estimable |
| Research Reliability | Source/cohort chain | `06_source_provenance.parquet`, `06_integrated_population_selection.parquet` | stored cohort | Counts and exclusions require identified population |
| Research Reliability | Missingness and policy sensitivity | `06_temporal_quality_sensitivity.parquet`, `06_quality_policy_sensitivity.parquet`, `06_research_sensitivity.parquet` | precomputed scenario/year/month | 2026 provisional; sensitivity not causal identification |
| Research Reliability | Claim catalog, permissions, issues | `06_final_research_decisions.parquet`, `06_claim_evidence_register.parquet`, `06_subclaim_evidence_register.parquet`, `06_final_issue_register.parquet` | exact RQ/claim | RQ-level scientific eligibility **is not** claim-level publication approval |
| Research Reliability | Provenance and release | `06_reproducibility_acceptance.parquet`, `06_export_manifest.parquet`, `06_finalization_checks.parquet` | run ID only | Must show actual saved values, not claim tests were run in app |

**Contract precision:** The listed filter names denote the intended keys, not an assertion that every upstream file has those column names. The artifact audit must inspect actual schema and assign an `UNSUPPORTED_FILTER` result whenever a required field is absent. V1 should implement only combinations confirmed by physical files; it must not invent missing columns.

## What is required before Phase 2

1. Run the read-only inventory against the Windows project; inspect any `BLOCKED` artifacts and determine whether they are critical or optional for the proposed first page.
2. Verify the actual Notebook 06 manifest's file-hash bindings to its final CSV/Parquet outputs; separately verify upstream artifact lineage. A plain file existence test is insufficient.
3. Lock an explicit per-chart field mapping based on each real schema; never infer unknown columns merely from a filename.
4. Decide which qualified *subclaims* are release-authorized. Notebook 06's parent-level dashboard flags do not establish that every numerical interpretation is published.
5. Define actual KPI `value`/`numerator`/`denominator` columns from the inspected output tables; ensure filter controls cannot change the estimand.
6. Check source/publication licensing before external deployment.

## SQL/scripts recommendation

- **SQL:** optional for research build/reconciliation; unnecessary for the read-only Streamlit runtime. No need to create a live database.
- **`scripts/build_aggregates.py`:** if empty, keep as unused placeholder or retire in a separate tidy-up. Don't implement duplicate estimators or compete with the seven notebooks.
- **`scripts/run_pipeline.py`:** if empty, likewise optional. A future rebuild orchestrator must be separately designed and tested, never called on every dashboard session.
- **Existing `app/`:** contents not supplied. Reuse it as the eventual UI root after a direct local inspection; do not copy new pages into it during Phase 1.
- **New `app_core/`:** intentionally separate policy/data-access layer. It can be imported by any future app directory without relocating the validated `src/` code.

## Phase 1 status

**Implemented and testable:** allowlisted paths, read-only data access, explicit metric/filter/aggregation rules, claim-level permissions, Notebook 06 manifest integrity checks, and fail-closed inventory CLI.

**Not verified in this environment:** the Windows aggregate CSV/Parquet files and schemas, upstream artifact hashes, complete `app/`/`sql/`/`scripts/` contents, and the full local pytest suite. **Do not designate Phase 2's data contract as production-certified until the actual local inventory is reviewed.**
