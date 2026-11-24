# Dubai Residential Market Intelligence V2 — Research Plan

**Status:** Pre-implementation research specification (v1.0; subject to the explicit feasibility gates below)  
**Prepared:** 2026-11-23  
**Primary analytical window:** Full calendar years 2010–2025; emphasis on 2020–2025 and 2021–2025  
**2026 policy:** Provisional, *not* part of full-year comparisons; limited to clearly flagged monitoring and same-month YTD comparisons after coverage checks  
**Primary artifact:** `docs/research_plan.md`  
**Source snapshot:** `data/raw/dld_sales_transactions.parquet` (SHA-256 `8294c3dd83dde2e16e64eaf1ef155a1ad14ec16b6b39384561777afb8425417e`)  
**Known snapshot:** 1,382,848 transactions, 20 fields, 1975-01-01–2026-11-02, 244 communities; approximately 1,094,417 in the publisher-flag-zero residential Unit/Villa population (all years). Verify all counts locally before publication.  
**Audience:** real estate research teams, credit/market risk analysts, strategy consultants, and market intelligence professionals. **Not:** a live property recommender, investment-return forecast, or causal study of developers.

---

## 0. Executive research charter

### Central decision question

> How much of Dubai's observed residential price movement reflects within-comparable-segment changes versus changes in the composition of transactions, and which geographic and market-structure signals remain credible after coverage, quality, and uncertainty checks?

**Value proposition:** A defensible, reproducible market-intelligence product that helps readers avoid mistaking a shift toward smaller/off-plan/new-community transactions for a uniform change in the value of comparable homes.

**Final deliverable contract:** (i) 15 pre-specified investigations with explicit conclusions or inconclusive status; (ii) six prioritized flagship investigations; (iii) five Streamlit views built from versioned analytical tables; (iv) 4–6 evidence-qualified findings in an executive brief; (v) documented limitations, tests, and reproducible SQL/Python pipeline.

### Questions we do *not* promise to answer

No “undervalued deals,” causal amenity premiums, developer distress, speculative buyer motives, rental yields, flipping/holding periods, price appreciation of *the same* property, property-stock turnover, or investor ROI. The available data are **registered sales transactions**, without property-unit IDs, current asking prices, rents, ownership chains, financing, amenities beyond recorded parking, building age/condition, or geospatial coordinates. An area identifier is not a property identifier.

### Non-negotiable interpretation rules

1. Every KPI specifies population, time window, statistic, units, and denominator. An all-sales transaction count is not directly comparable to a residential-only price median without a clear label.
2. Recorded transaction price is not an asking price, future value, or independent estimate of fair value. “Ready” does not by itself mean “resale.” “Off-plan” does not establish speculation or distress.
3. No causality from comparisons or adjusted regressions; report **associations**, remaining confounding, uncertainty, and coverage.
4. Group medians describe *separate distributions*: `median(price/area) != median(price)/median(area)` in general. Never imply both medians describe the same hypothetical home.
5. `quality_flags == 0` is a **publisher-defined policy**, not proof of perfect data. Preserve nonzero records in the raw layer and measure their influence.
6. Missing is not false. Preserve nulls in names, rooms, parking, procedures, and geography. Group `area_id` first; names are labels, not keys.
7. Exclude 2026 from historical full-year conclusions; separately display provisional coverage signals. This snapshot has major 2026 missingness changes in building, parking, and procedure fields.
8. A chart is not an analytical result by itself. The underlying numerical table, cohort counts, uncertainty, method, and code must be available.
9. If a planned question fails its feasibility or coverage gate, mark it **inconclusive** or **exploratory**. Do not silently change its definition to obtain a compelling result.

---

## 1. Source facts, provenance and version control

**Input:** `data/raw/dld_sales_transactions.parquet`, a snapshot of registered Dubai real estate sales; publisher/project source: [Dubai Real Estate Data — Hugging Face](https://huggingface.co/datasets/dubairealestatedata/dubai-real-estate-sales-transactions), with [source dictionary](https://huggingface.co/datasets/dubairealestatedata/dubai-real-estate-sales-transactions/blob/main/DATA_DICTIONARY.md). Verify current publisher attribution and CC BY 4.0 licensing in `docs/data_dictionary.md` before public release. Do not present the publisher as an independently audited DLD export. Dataset dates are registration dates, not necessarily listing or contract dates.

**Initial audit observations to reproduce (not hardcoded acceptance rules):** Unique `transaction_id` count equals row count; `quality_flags=0` for 1,354,155 rows; 1,113,178 residential Unit/Villa rows before flag filtering; 1,094,417 after; missing `building_name` 408,903 (29.57%); `project_name` 284,699 (20.59%); `rooms_bucket` 281,078 (20.33%); `has_parking` 43,942 (3.18%). Missing parking is concentrated in 2026; building names are nearly entirely missing March–October 2026; 26,971 records have missing procedures, all dated 2026 and classified `Ready`. Audit and snapshot checksum must be reproduced by `00_Data_Quality_Audit.ipynb` and stored in `reports/tables/dataset_manifest.csv` and `data_quality_monthly.parquet`.

**Field inventory:** `transaction_id`, `instance_date`, `reg_type_label`, `area_id`, `area_name_en`, `project_name`, `master_project_name`, `building_name`, `property_type_label`, `property_sub_type`, `usage_label`, `rooms_bucket`, `has_parking`, `area_sqm`, `price_aed`, `price_psf`, `procedure_id`, `procedure_name_en`, `is_pre_registration`, `quality_flags`. The `rooms_bucket` code `5` is top-coded (5+), not necessarily exactly five bedrooms; `0` indicates studio where the source dictionary supports it. `price_psf` is derived/rounded, not an independent measure.

**Publisher quality-bit interpretation to verify against dictionary:** bit 1 low price, bit 2 missing/invalid area, bit 4 segment-based price/ft² percentile outlier, bit 8 both core metrics missing, bit 16 invalid date. Bit flags may co-occur. Some flags use full-dataset percentile boundaries: do **not** treat them as point-in-time safe predictors in a forecasting experiment.

**Snapshot contract:** record raw filename, SHA-256, file bytes, record count, min/max dates, ingestion UTC timestamp, tool versions, filter definitions, and run ID on every full pipeline run. The 2010–2025 window is frozen for this project; newer snapshots require a new run ID and revised evidence tables.

---

## 2. Canonical analytical populations and metric definitions

### 2.1 Populations — no universal one-size-fits-all `clean_df`

| Population ID | Definition | Use | Mandatory caveat |
|---|---|---|---|
| `P0_ALL_SALES` | All rows with unique transaction ID, valid parsable registration date and finite nonnegative `price_aed`; publish excluded count separately | Registered transaction counts, registered gross value, activity/concentration | Includes Unit, Villa, Land, Building, Residential/Commercial/Other; business-definition and procedure mix must be disclosed |
| `P1_RESIDENTIAL_CORE` | `P0` ∩ `usage_label='Residential'` ∩ `property_type_label IN ('Unit','Villa')` ∩ finite positive price and area, sensible positive derived AED/sqm | Residential core pricing & size analysis | Reconcile before/after publisher flags; reject infinite metrics; no silent imputation |
| `P1_STRICT` | `P1_RESIDENTIAL_CORE` ∩ `quality_flags=0` | Default historical residential price metrics and price indices | Excludes publisher-marked outliers; sensitivity to flags is mandatory |
| `P2_KNOWN_SEGMENT` | `P1_STRICT` with nonmissing `area_id`, `reg_type_label`, valid rooms bucket where needed; positive area | Comparable-segment analyses | Report coverage vs `P1_STRICT` by year and category |
| `P3_AMENITY_KNOWN` | `P1_STRICT` historical cohort with valid nonmissing parking/rooms and adequate overlap | RQ12 only | Never interpret missing `has_parking` as `False`; 2026 excluded |
| `P4_2026_PROVISIONAL` | Separate 2026 snapshot cohort using same KPI-specific rules | Completeness monitoring and matched-month provisional counts | **Not** part of full-year historical ranking or longitudinal model fitting |

Do not coerce missing `area_id` into a fake community. Report orphaned geography explicitly. Do not equate `procedure_name_en` with authoritative readiness when it is missing.

### 2.2 Canonical formulas

- `price_per_sqm = price_aed / area_sqm` for positive, finite `price_aed` and `area_sqm`; `price_per_sqft = price_aed / (area_sqm * 10.76391041671)`. Verify against publisher `price_psf` to agreed rounding tolerance; source `price_psf` is a QA reference, not the primary measure.
- `registered_value_aed = SUM(price_aed)` on the explicitly chosen population; not market cap, stock value, investment flow, or developer revenue.
- `transaction_count = COUNT(DISTINCT transaction_id)` only after uniqueness validation, otherwise fail the input contract; `COUNT(*)` should then agree.
- `offplan_count_share = N(Off-Plan)/N(Ready or Off-Plan)` within a named cohort and time period. Separately `offplan_value_share = SUM(Off-Plan value)/SUM(Ready + Off-Plan value)`. Explicitly disclose unknown/other labels; no silent denominator shrinkage.
- `median_psm = MEDIAN(price_per_sqm)` at *transaction level*; `median_total_aed = MEDIAN(price_aed)`; `median_area_sqm = MEDIAN(area_sqm)`. Provide `n`, P25/P75, and missingness with each important metric.
- `growth = (index_t / index_base - 1) * 100`, only when denominators are positive and dates/cohorts align. For index chaining: `index_t = index_(t-1) * exp(weighted_mean(log(median_t,g/median_(t-1),g)))` for valid common cells `g`. Specify weight base in output.
- All share denominators and coverage populations must be exported with numerator/denominator; do not use chart values as primary calculation sources.

### 2.3 Unit of analysis, windows and minimum eligibility

- **Transaction** for sale-count, value and distribution analysis; **community-year or community-quarter** for area studies; **matched comparable segment-period** for adjusted indices; never imply a panel of identical dwellings.
- Primary full years: 2010–2025. Recent comparisons: 2021 vs 2025; 2020–2025. Monthly/quarterly analysis only if positive, adequate coverage and consistent classification.
- **Proposed screening thresholds, to be validated before locking:** per-cell median uses `n>=30` *per side* of a comparison; sensitivity tests `n>=20, 50, 100`. Annual community ranking requires >=100 eligible transactions in each evaluated endpoint year plus >=3 eligible intermediate years; compare alternative thresholds. These are pragmatic stability screens, not proofs of statistical significance.
- Document small, changing, or zero-coverage communities; do not silently assume missing trade activity means a fall in price. Where area IDs appear/disappear, report entrants/exits separately from matched-area results.
- Main descriptive findings use 95% intervals where useful (transaction bootstrap where independent units are plausible; clustered or block resampling for dependent community/time analysis). State the sampling-unit and assumptions. Large administrative datasets are not a random sample of all properties: intervals measure conditional statistical variability, **not all systematic biases**.

---

## 3. Six flagship investigations (greater depth) and full 15-question research register

**Priority classification:** Flagship = RQ01, RQ02, RQ04, RQ07, RQ11, RQ15. Core = RQ03, RQ05, RQ08, RQ09, RQ10, RQ13, RQ14. Exploratory = RQ06, RQ12. All 15 must receive a result, supported partial result, or an explicit inconclusive decision. Avoid maximizing the number of 'positive' findings.

### RQ01 — Does residential price appreciation persist after adjusting for transaction composition? **FLAGSHIP**

- **Decision use:** Can a market team trust headline AED/sqm growth as evidence of changing prices within comparable segments?
- **Estimand:** Indexed change in median transaction AED/sqm under a fixed reference segment mix, **not** a repeat-sales or exact constant-quality property index.
- **Population/window:** `P2_KNOWN_SEGMENT`, full 2010–2025; primary comparison 2021–2025.
- **Segment keys:** `area_id × property_type_label × reg_type_label × rooms_bucket × area_band`; bins for size must be predeclared from training/reference-period distribution or stable domain-based rules, never recalculated per target year. Test coarser alternatives to avoid sparse cells.
- **Method:** Compute annual medians and counts per segment. Calculate raw transaction-median index; fixed-base matched common-segment geometric index weighted by reference-year counts; compare to coarser-strata and chain-linked variants. Restrict matched sets to documented eligible common cohorts and publish excluded-share by period. For the flagship 2021–2025 estimate, use the same 2021 base weights and matched set; do not conflate cohort changes with index movements. Separate whole-window index from pairwise illustration.
- **Validation:** >=30 transactions in each comparison segment; sensitivity >=20/50/100, alternative size bins, flag policy, ready/off-plan strata, fixed geographic universe; bootstrap where defensible. Report index coverage `matched transactions / eligible transactions` for both endpoints and weight concentration.
- **Outputs:** `price_index_raw_adjusted.parquet`, `price_index_coverage.parquet`, plot indexed raw vs matched and contribution/coverage companion; 1-page methodological note.
- **Pass/fail:** Publish a numerical 'adjusted appreciation' finding only with adequate cohort coverage and stable direction across plausible specifications; if not, report estimated *matched-cohort* change with explicit narrow scope, or mark inconclusive.
- **Do not conclude:** Exact same-home appreciation, causal inflation effects, or that a gap is entirely a unit-size effect.

### RQ02 — Are typical sold homes becoming smaller because of shifting sales mix or within-segment area change? **FLAGSHIP**

- **Estimand:** Change in observed transaction-level median area, plus a **separate** decomposable average/size-band share measure; medians do not additively decompose.
- **Population/window:** `P1_STRICT`, 2010–2025, emphasis 2021–2025; strata property type, rooms, reg type, geography.
- **Method:** Decompose **mean log(area_sqm)** into between-cell share and within-cell change on a common-cell set (Kitagawa/Oaxaca-style symmetric decomposition); independently report median and quantile shifts. Sensitivity to excluding new/lost communities and missing-bedroom strata; do not claim the decomposition exactly explains median change.
- **Validation:** Make decomposition terms sum to the change in the defined log-area estimand (rounding tolerance). Publish common-cell coverage and a cohort-by-year size-mix table.
- **Outputs:** `area_mix_decomposition.parquet`, `area_distribution_by_segment.parquet`, shift-share waterfall plus property-type/bedroom distributions.
- **Do not conclude:** Floorplans of identical building models shrank or builders intentionally reduced unit size.

### RQ03 — What can a fixed *nominal* purchase budget buy across different communities and years? **CORE**

- **Estimand:** Share of registered residential transactions <= AED 1m/1.5m/2m; conditional median area and bedroom mix within each budget; area/segment coverage.
- **Population/window:** `P1_STRICT` 2010–2025; primary 2021 vs 2025; segment-ready/unit comparisons as robustness.
- **Method:** Transaction-budget eligibility; distribution of size/bedrooms among transactions within budget, with n and valid-bedroom share; separate fixed community/segment universe and community-specific results.
- **Validation:** Multiple budget levels and changed nominal thresholds; never claim residents' income affordability. External CPI is out of scope unless sourced, versioned, and documented separately.
- **Outputs:** `budget_accessibility.parquet`, threshold curves and comparable-community table.
- **Do not conclude:** Mortgage affordability, purchasing power *adjusted for income*, supply available on the market, or what an individual can purchase today.

### RQ04 — Is growth in registered transactions broadly distributed or concentrated in a few communities? **FLAGSHIP**

- **Estimand:** Annual distribution of counts and registered sale value across `area_id`; HHI (`sum(share_i^2)`), top-5/top-10 shares, active community count, share growth and the entrant/exit contribution.
- **Population/window:** `P0_ALL_SALES` 2010–2025 (separate `P1_STRICT` sensitivity); include unknown geography as an explicitly disclosed bucket/exclusion reconciliation.
- **Method:** Year x area aggregate count and value; separately compare balanced-area panel versus unrestricted annual community universe; compute concentration changes and show whether they are driven by new communities.
- **Validation:** Annual counts/values reconcile to their labeled global totals; shares sum to 100% within specified geography policy; rerun for residential only and stable geography.
- **Outputs:** `community_concentration_yearly.parquet`, `area_share_yearly.parquet`, HHI + top-10-share charts.
- **Do not conclude:** Investor concentration, monopoly, population displacement, or building-stock concentration.

### RQ05 — Is off-plan growth a shift in market composition or part of broad expansion? **CORE**

- **Estimand:** Ready/off-plan contributions to registered sales-count/value change and share, split by property type and named populations.
- **Population/window:** `P0_ALL_SALES` and `P1_STRICT` reported distinctly; 2010–2025; primary 2020–2025.
- **Method:** Yearly `N`, `SUM(price_aed)`, category shares; additive count-growth decomposition by registration type. Show residential-vs-all difference and procedure-code composition where available.
- **Validation:** Categories and totals reconcile; procedure taxonomy cross-tab by year; 2026 excluded from final full-year trends, and missing procedure risks displayed separately.
- **Outputs:** `registration_mix_yearly.parquet`, count-growth bridge, count-share vs value-share chart.
- **Do not conclude:** Speculation, financial distress, end-user/investor motives, or share of total housing stock.

### RQ06 — Does transaction activity contain information about later price movements? **EXPLORATORY**

- **Estimand:** Conditional association/predictive incremental value of lagged quarterly count growth for *subsequent* adjusted price change, not a causal demand effect.
- **Population/window:** Eligible community-quarter `P1_STRICT` panel in 2013–2025, retaining only stable-coverage areas with sufficient quarterly counts.
- **Method:** Compare naive persistence-only benchmark to a lagged activity/price model; use chronological expanding-window validation and community effects where feasible. Explicitly guard against same-quarter overlap and lookahead.
- **Validation:** No cross-period leakage; compare out-of-time MAE/directional accuracy with naive baseline; cluster/block uncertainty; do not promote isolated lag significance.
- **Outputs:** `activity_lead_lag_validation.parquet`, rolling holdout results.
- **Kill switch:** If series are sparse, coefficients unstable, or there is no repeated out-of-time improvement, publish 'no reliable predictive evidence' and keep this question descriptive.

### RQ07 — Which communities show persistent composition-adjusted historical price growth? **FLAGSHIP**

- **Estimand:** Within-area matched-segment price change and time consistency, not investor returns.
- **Population/window:** `P2_KNOWN_SEGMENT`, 2018–2025 with 2021–2025 focus.
- **Method:** Community-level fixed-weight matched indices using a manageable set of strata; annual/rolling growth and downside history. Rank only areas meeting prespecified continuity, cohort coverage, and minimum-count rules; keep 'insufficient evidence' separate from 'poor performer'.
- **Validation:** Minimum >=100 eligible records in both endpoints and >=3 intermediate years; matched coverage > threshold selected from diagnostic feasibility screen (provisional target >=60%, documented); sensitivity to flag policy, bedroom missingness, and time window. Rank stability tested using confidence intervals/bootstraps and alternative specifications.
- **Outputs:** `community_growth_validated.parquet` (estimate, n, matched coverage, uncertainty, eligibility and rank stability), growth persistence quadrant, appendix for ineligible communities.
- **Do not conclude:** 'Best investments' or extrapolate historic returns into future.

### RQ08 — Are more and less expensive residential communities converging or diverging? **CORE**

- **Estimand:** Dispersion of fixed-universe community price indices/log AED/sqm, P90/P10 (or log quantile gap) over time, and exploratory baseline-price versus later change relation.
- **Population/window:** `P2_KNOWN_SEGMENT`, common eligible communities 2015–2025.
- **Method:** Cross-area dispersion on matched eligible area/segment cohort; equal-area and transaction-weighted measures shown separately. Explicitly control area entry/exit bias by holding the universe fixed.
- **Validation:** Stable-direction checks across years, universe criteria, and weight choice; no equating median community distribution with all Dubai transactions.
- **Outputs:** `community_dispersion_yearly.parquet`, distribution and convergence visuals.
- **Do not conclude:** Wealth inequality, gentrification, household welfare, or quality-adjusted house-price inequality.

### RQ09 — Which community activity/price regimes can be identified without overclaiming liquidity? **CORE**

- **Estimand:** Two-axis classification based on adjusted price-index growth and change in registered count within a fixed window.
- **Population/window:** Stable eligible residential communities, 2021–2025, `P1_STRICT` + RQ07 adjustment.
- **Method:** Predeclare quadrants as +/- changes around zero, with optional descriptive relative-to-city thresholds *separately*; do not mine thresholds after seeing top communities. Each observation carries n, confidence/coverage and year-window metadata.
- **Validation:** Suppress low-quality quadrants and show near-zero/uncertain status; sensitivity to 3-year vs 5-year changes and all-sales vs residential volumes.
- **Outputs:** `community_regimes.parquet`, interactive scatter with uncertainty/coverage tooltips.
- **Do not conclude:** Inventory liquidity, price discovery efficiency, absorption, or resale speed without stock/listing data.

### RQ10 — Is AED/sqm systematically related to unit size, and how does the relation vary? **CORE**

- **Estimand:** Conditional size-price elasticity (association) from `log(price_per_sqm) ~ f(log(area_sqm)) + year + community + reg_type + property_type + bedrooms` (fit feasible category specification and report inference limits).
- **Population/window:** `P1_STRICT`, 2015–2025; Units and Villas separately; zero/unknown rooms handled transparently.
- **Method:** Quantile-bin descriptive profiles and nonlinear spline/piecewise regression; inspect collinearity and support. An optional alternative `log(price_aed)` model checks consistency but has different estimand.
- **Validation:** Outlier and size-trimming sensitivity, alternative functional forms, sample sizes per property type, time-stratified estimates.
- **Outputs:** `size_price_relationship.parquet`, conditional effect curves with support shading.
- **Do not conclude:** Causal 'small-unit premium' or same-floorplan pricing.

### RQ11 — How much of the ready–off-plan price gap remains within comparable segments? **FLAGSHIP**

- **Estimand:** Conditional adjusted log AED/sqm gap between registered ready and off-plan groups; not a transaction-ready project completion or cash-flow-adjusted discount.
- **Population/window:** `P2_KNOWN_SEGMENT`, primary 2020–2025; 2026 separate/provisional.
- **Method:** Unadjusted annual/area gap then matched/coarsened-exact strata (`area_id × year/quarter × type × rooms × size_band`) with sufficient observations on both sides, and an adjusted regression with fixed effects on an overlapping sample. Distinguish matched-group descriptive gaps from regression coefficients; report overlap/coverage.
- **Validation:** Both groups >=30 per cell primary; 20/50 sensitivity; alternative time granularity, flag policies, `Unit` vs `Villa`, balanced overlap; investigate procedure distributions and high-value tails. Interval for log-gap correctly converted with `100*(exp(beta)-1)`.
- **Outputs:** `offplan_ready_adjusted.parquet`, raw vs adjusted gaps with coverage and segment-count panel.
- **Kill switch:** If overlap/metadata are poor, report only descriptive differences; no forced 'discount' claims.
- **Do not conclude:** Developer distress, forced sales, or economic opportunity without payment-schedule/quality data.

### RQ12 — Are bedroom and parking price differences visible after adjustment? **EXPLORATORY**

- **Estimand:** Conditional associations of bedroom categories and recorded parking status with `log(price_aed)` and `log(price_per_sqm)`, **separately**.
- **Population/window:** `P3_AMENITY_KNOWN`, 2015–2025; focus Ready residential Units, with nonmissing `rooms_bucket`, known `has_parking` and sufficient observed overlap; report sample loss and representativeness.
- **Method:** Stratify on community-year/quarter, type, size range; regression with appropriate controls and cluster-robust SEs where feasible. Treat `rooms_bucket=5` as 5+; never silently assume missing parking = no parking.
- **Validation:** Compare unadjusted vs adjusted, period/region stability, building fixed effects only if historical name coverage and normalized IDs permit; missingness sensitivity and common-support diagnostics.
- **Outputs:** `amenity_associations.parquet` including coefficient, interval, valid n, coverage, specification ID, interpretability caveat.
- **Kill switch:** If parking is too confounded or insufficiently populated, downgrade to descriptive conditional contrasts and label uncertainty; do not claim return on investing in parking.

### RQ13 — Which communities have more or less stable *recorded* historical prices? **CORE**

- **Estimand:** Variability and drawdowns of comparable-segment/community **price indices**, distinguishing sampling noise from actual movement.
- **Population/window:** Established communities with adequate quarterly/annual coverage in `P2_KNOWN_SEGMENT`, 2015–2025.
- **Method:** Rolling volatility of quarterly/annual adjusted log changes, worst observed window and number of eligible periods; compare bootstrapped reliability and volatility under alternative smoothing windows.
- **Validation:** Minimum continuity; avoid ranking thin areas as most volatile. Distinguish nominal recorded-price volatility from total investment return or downside probability.
- **Outputs:** `community_price_stability.parquet`, stability-growth scatter, historical drawdown table.

### RQ14 — Is a growing share of registered sale value associated with the upper transaction-price tail? **CORE**

- **Estimand:** Yearly value share held by within-year top 10%/1% of eligible transactions; separately share above fixed nominal AED thresholds and real price quantiles.
- **Population/window:** `P1_STRICT` 2010–2025; `P0_ALL_SALES` as clearly labeled sensitivity.
- **Method:** Annual transaction-level quantiles and contribution to gross registered value. Distinguish **relative within-year percentile tails** from **fixed nominal high-end thresholds**; both answer different questions. Control for property-type composition.
- **Validation:** Threshold definition and cohort fixed, count/value reconcile; inflation-adjusted long-run claims only if CPI sourced separately.
- **Outputs:** `price_tail_concentration.parquet`, top-decile value share and threshold-share series.
- **Do not conclude:** Wealth distribution of buyers, luxury stock concentration, real (inflation-adjusted) growth without deflation.

### RQ15 — Which conclusions survive data-quality, missingness and coverage changes? **FLAGSHIP / CROSS-CUTTING**

- **Estimand:** Sensitivity of RQ01, RQ04, RQ05, RQ07, RQ11 to explicit eligibility, flags, coverage and classification policies; observed missingness and provenance breaks.
- **Population/window:** `P0`, `P1`, `P1_STRICT`, `P2`, `P4`; 2010–2026 with separate 2026 provisional page.
- **Method:** Monthly completeness (parking, building, project, rooms, procedure, geography), quality-bit distribution by year/segment, exclusion waterfall, strict vs alternate flags, current-year same-month comparison warnings. Generate a claim-by-claim robustness matrix.
- **Validation:** Published cohort counts reconcile independently; zero missing values introduced by faulty Boolean/text casting; 2026 fields correctly flagged; summary values trace to saved tables.
- **Outputs:** `data_quality_monthly.parquet`, `cleaning_waterfall.parquet`, `research_sensitivity.parquet`, data confidence page and explicit source-coverage note.
- **Do not conclude:** A missingness jump proves an upstream policy change; we observe a coverage break, not its cause.

---

## 4. Method decision ledger (freeze before analysis, amend transparently)

| ID | Locked choice | Why | Change protocol |
|---|---|---|---|
| D01 | Primary full-year window 2010–2025 | Avoid sparse old years and incomplete 2026 | Changes require versioned plan amendment |
| D02 | Area key `area_id` | Avoid spelling/casing geography splits | Maintain named ID-label lookup and conflict report |
| D03 | Transaction-level median, count, value | Robust and clearly interpretable descriptive metrics | Never swap mean/median unnoticed |
| D04 | Separate all-sales and residential-pricing populations | Different valid denominators | Cohort definitions versioned in `config.yaml` |
| D05 | Primary residential strict flags = 0 plus alternatives | Quality policy should be transparent | Store sensitivity policy IDs |
| D06 | Matched and weighted price indices labeled as approximate | No unique physical-unit identifier | Never call repeat-sales/constant-quality |
| D07 | Missingness-preserving parsing | Previous project destroyed parking and name nulls | Unit tests enforce |
| D08 | Community rank requires continuity and credible cohort coverage | Limit spurious extremes | Final screening rules frozen after feasibility gate |
| D09 | Causal and investment claims excluded | Not supported by fields | New external-source plan required |
| D10 | Streamlit reads precomputed outputs only | Reproducible, fast, consistent metric definitions | App may filter within precomputed grain; no silent recomputation |
| D11 | Primary price comparisons nominal AED | No inflation/income source currently in dataset | Add CPI only through separately documented external-data extension |
| D12 | Exploratory RQ06/RQ12 may be inconclusive | High assumption and overlap risk | Report fail/limited result; no cherry-picking |

### Pre-analysis feasibility gate (before research code)

Produce `reports/tables/feasibility_gate.csv` with, for each RQ: input population row count, distinct year/community/segment counts, missingness by period, min median cell n, common-cell coverage, presence/absence of needed fields, `PASS / CONDITIONAL / NO_GO`, reason and alternative. Before doing any regression/ranking: compute 2021/2025 matched coverage for 3 proposed segment granularities and 20/30/50 transaction thresholds. Select **one primary** granularity/threshold by a documented rule balancing detail and coverage, then freeze its ID. Alternative versions become robustness tests, not opportunities to select an exciting headline. Provisional 60% coverage is a *target* for useful broad claims, not a license to hide uncovered transactions.

---

## 5. Technical implementation and file/output contract

### Research-to-code map

| Stage | Source implementation | Notebook | Export(s) | Streamlit page |
|---|---|---|---|---|
| Input contracts, flags, completeness | `src/loader.py`, `src/validation.py`, `src/cleaning.py` | `00_Data_Quality_Audit.ipynb` | `dataset_manifest`, `cleaning_waterfall`, `data_quality_monthly` | 05 Reliability |
| Feature engineering and transaction KPIs | `src/features.py`, `src/analysis/market.py` | `01_Market_Overview.ipynb` | `market_yearly`, `market_quarterly`, `budget_accessibility`, `price_tail_concentration` | 01 Market Overview, 02 Price Reality |
| Adjusted prices, size composition | `src/analysis/pricing.py`, `src/statistics.py` | `02_Price_Composition.ipynb` | `price_index_raw_adjusted`, `price_index_coverage`, `area_mix_decomposition`, `size_price_relationship` | 02 Price Reality |
| Concentration, off-plan contribution, lead-lag | `src/analysis/market.py`, `src/analysis/market_structure.py` | `03_Market_Activity.ipynb` | `community_concentration_yearly`, `registration_mix_yearly`, `activity_lead_lag_validation` | 01 Market Overview, 04 Market Structure |
| Community persistence, divergence, regimes, stability | `src/analysis/communities.py` | `04_Community_Intelligence.ipynb` | `community_growth_validated`, `community_dispersion_yearly`, `community_regimes`, `community_price_stability` | 03 Community Intelligence |
| Ready/off-plan and amenity contrasts | `src/analysis/market_structure.py`, `src/statistics.py` | `05_Market_Structure.ipynb` | `offplan_ready_adjusted`, `amenity_associations` | 04 Market Structure |
| Sensitivity and conclusion checks | `src/statistics.py`, `src/validation.py` | `06_Robustness_Validation.ipynb` | `research_sensitivity`, `claim_evidence_register` | 05 Reliability + all page footnotes |

All exported analytical datasets should be stored under `data/aggregates/` (Parquet by default). Human-facing summary tables under `reports/tables/` (CSV and/or Markdown). Charts under `reports/figures/`. Avoid hardcoded counts or insight text in Streamlit; read precomputed `metric_id`, `cohort_id`, `method_id`, period, `n`, `coverage`, and caution fields from aggregates.

### Minimum output-table schema

Each fact/aggregate should carry: `run_id`, `snapshot_sha256`, `cohort_id`, `method_id`, `period/grain`, segment keys, metric name/value, unit, numerator and denominator where meaningful, `n_transactions`, `coverage_pct` where relevant, computation/validation status, and an explanatory caveat. Do not force `numerator` and `denominator` for non-ratio estimands; use null and a definition field.

### SQL and Python responsibility split

- **DuckDB SQL (`sql/`)**: audited filtering views, annual/quarterly volume and registered-value aggregates, grouped medians/quantiles, coverage and concentration inputs. All SQL must be saved and runnable, not merely embedded inside presentation code.
- **Pandas / NumPy / Statsmodels / SciPy (`src/`)**: fixed-weight index computations, decompositions, statistical estimation, resampling/uncertainty and validation. Avoid duplicate KPI formulas across Python and SQL.
- **Jupyter**: orchestrated research narrative, tables, chart interpretation, diagnostics, and links to code; no hidden one-off cleaning.
- **Streamlit / Plotly**: interaction, well-defined filters, caveats, and drilldowns; no retraining, no long-running bootstrap or ad hoc multi-million-row scan on each UI action.

### Required baseline test suite

- `test_validation.py`: exact expected columns, ID uniqueness, numeric/date integrity, flag bits, missing-preserving strings/booleans, 2026 missingness warning generation.
- `test_cleaning.py`: known synthetic cases (null parking, zero area, string `"False"`, zero/NaN price, fake area names, missing date), exclusion waterfall reconciliation, raw nonmutation.
- `test_features.py`: AED/sqm arithmetic, square-foot conversion, size-band boundary behavior, year/quarter correctness, top-coded rooms semantics.
- `test_analysis.py`: counts and value reconcile across aggregation levels; shares sum to 100% within denominator; no accidental mixing of P0 and P1; decomposition identity; index weights and matching reproducible.
- `test_statistics.py`: model design matrix and overlap checks, adjusted gap exponentiation, time-split integrity, interval metadata, deterministic resampling with fixed seed.
- Add data-contract tests comparing `run_pipeline.py` exports with Streamlit-ready aggregation exports and expected schemas.

### Reproduction commands (targets, implement during engineering)

```powershell
conda activate dubai-v2
python -m pytest -q
python scripts/run_pipeline.py
python scripts/build_aggregates.py
streamlit run app/Home.py
```

These commands are **intended final entry points**; they will not run until scripts and app are implemented. Pin successful environment versions to a reproducible lockfile/environment export before publishing.

---

## 6. Reporting format: every RQ follows the same evidence contract

For each RQ, notebook and final report must show these **nine items**, in order:

1. **Decision and hypothesis:** what comparison is being made and why it matters.
2. **Population:** cohort ID, time window, count, geographic/property coverage, excluded share.
3. **Operational metric/estimand:** precise formula and unit.
4. **Method and assumptions:** group keys, weights, controls, missingness, thresholds, confidence method.
5. **Primary result:** estimate and magnitude, with baseline/comparator.
6. **Reliability:** confidence/uncertainty, sample and coverage, sensitivity results, material failures.
7. **Interpretation:** what the evidence supports in business language.
8. **What it cannot prove:** one or two explicit limitations.
9. **Decision implication:** a possible monitoring or planning action conditional on the result, not an automatic investment recommendation.

**Evidence-status taxonomy:** `SUPPORTED` (clear eligible result, stable to key alternatives), `CONDITIONAL` (result relies on restrictive cohorts/specifications), `INCONCLUSIVE` (uncertainty, missingness, weak overlap, or conflicting variants), `NOT_FEASIBLE` (required data absent). Unsupported hypotheses are valid analytical outcomes.

**Claim-evidence register:** `reports/tables/claim_evidence_register.csv` with `claim_id`, `rq_id`, plain-English claim, estimate/unit, `cohort_id`, `method_id`, date range, evidence-table path, robustness status, limitations, confidence/status and whether approved for executive summary. A claim can only appear in the README/executive summary/app headline if its evidence record is approved.

---

## 7. Five-page Streamlit information architecture

| Page | Primary questions | What user can interact with | Required cautions |
|---|---|---|---|
| `01_Market_Overview` | RQ04, RQ05, RQ14 + basic KPIs | Year range, P0 vs P1 clearly labeled, registration/property category, area | Registered transactions ≠ housing supply or investor demand; value ≠ stock value |
| `02_Price_Reality` | RQ01, RQ02, RQ03, RQ10 | Raw vs adjusted index, fixed-weight base, approved segment views, budget | Same-unit comparison unavailable; matched coverage and exclusions shown |
| `03_Community_Intelligence` | RQ07, RQ08, RQ09, RQ13 | Community comparisons and uncertainty/coverage filters | Sample eligibility, regime uncertainty; no investment ranking |
| `04_Market_Structure` | RQ05, RQ11, RQ12 | Registration type, ready/off-plan raw vs adjusted differences, amenity subgroups | Adjusted association ≠ causal discount/premium; incomplete 2026 metadata |
| `05_Data_Reliability` | RQ15 | Year/month, field completeness, quality-flag policy, sensitivity scenario | Snapshot and publication coverage, 2026 provisional status |

Global UI must show data snapshot date, most recent registration date, analytical denominator, and tooltip links to methods. Handle unavailable combinations gracefully: no fabricated zeroes, extrapolation, or hidden filter relaxation. A community with insufficient evidence displays **insufficient evidence**.

---

## 8. Implementation stages and acceptance gates

| Gate | Deliverables | Acceptance condition (stop otherwise) |
|---|---|---|
| G0: Environment and input freeze | environment, snapshot SHA, `data_dictionary.md`, this plan | Raw checksum matches, dependencies import, source terms validated |
| G1: Data contracts | `loader`, `validation`, `cleaning`, `features`, tests and `feasibility_gate.csv` | Reproduces raw/clean counts within documented definitions; missing values preserved; all row losses auditable |
| G2: Foundational metrics | annual/quarterly P0 and P1 tables, RQ03/04/05/14 | Every volume/value/shares reconciliation passes; year coverage complete; 2026 isolated |
| G3: Price/structure analyses | RQ01/02/07/08/09/10/11/13 | Fixed-weight index methods and coverage verified; every headline estimate has sensitivity/eligibility fields |
| G4: Conditional/exploratory | RQ06/RQ12 and full RQ15 sensitivity | Exploratory results explicitly pass or fail; no opportunistic promotion of unstable signals |
| G5: Published evidence | 7 notebooks, approved claim register, executive brief | Each approved claim reproducible from an exported table and method ID |
| G6: Streamlit release | five pages, user filters, run metadata and deployment | Figures reconcile to saved tables; no arbitrary filters create unsupported comparisons |

### Schedule dependency order (not calendar promises)

`G0 → G1 → G2 → G3 → G4 → G5 → G6`. Build a minimalist Streamlit shell earlier if useful for UI testing, but **no market conclusions** until approved evidence exists. Keep a single source of truth for cohort selection and KPI formulas.

---

## 9. Risks, early-warning tests and fallbacks

| Risk | Early detection | Response before it becomes a mid-project blocker |
|---|---|---|
| Too many sparse matched cells | Precompute counts/coverage for 3 segment granularities and thresholds | Freeze coarser primary index, keep detailed variant exploratory |
| 2026 metadata discontinuity | Monthly missingness matrix by field/procedure | Isolate 2026 provisional, exclude from primary historical conclusions |
| Incomplete bedrooms/parking | Cohort loss and overlap by year/community | Report restricted historical findings or mark RQ12 inconclusive |
| New/retired communities | Area-ID continuity audit | Matched geographic panel + entrant/exit breakdown |
| Quality flag P1–P99 filtering changes tails | Compare strict vs unflagged valid-valued scenarios | Publish sensitivity; do not claim flags are independent of prices |
| Extreme values/price unit mistakes | Finite/range tests + compare calculated AED/sqft with `price_psf` | Quarantine and report exceptions; investigate before metric use |
| False statistical precision | Examine clustering, multiple community comparisons, and changing population | Report robust intervals/coverage; suppress unjustified ranking |
| Regression cannot identify 'premium' causally | Overlap diagnostics, control variables available | Report adjusted association only; no developer or consumer causal claims |
| Activity signal does not validate | Chronological benchmark in RQ06 | Publish null predictive value, not an invented forecasting benefit |
| Streamlit performance or deployment | Precompute aggregates, verify app startup separately | Keep app on small derived tables, cache reads; restrict expensive filters |
| Research question proliferation | Scope lock: these 15 IDs, six flagships | New questions require explicit versioned change request |

---

## 10. Publication standard and definition of success

**Success means:** every one of the 15 questions has a transparent answer or documented limitation; at least six flagship investigations are examined with prespecified robustness checks; the central price-composition story is reproducible; community comparisons expose eligibility and uncertainty; the final app loads approved tables; README, report, charts and dashboard agree numerically; the method can be reproduced on the frozen source snapshot; claims never exceed fields available in the dataset.

**Failure conditions to avoid:** 15 attractive plots with no defined estimands; combining all-sales count with residential median without labels; 2026 annual comparisons against full 2025; claiming ready=secondary resale; interpreting raw off-plan gap as financial distress; falsely treating unknown parking as no parking; claiming causal bedroom/parking effects; ranking extreme low-volume communities as winners; relabeling regression residuals as investment opportunities; hiding negative/inconclusive results.

### Immediate next work package

1. Verify the SHA and raw schema locally in `00_Data_Quality_Audit.ipynb` (the current `.ipynb` files were created as empty placeholders; initialize valid notebook JSON first).
2. Finish `docs/data_dictionary.md` and register column types, enumerations, null policy and quality bit flags.
3. Implement `src/loader.py`, `src/validation.py`, synthetic tests, snapshot manifest and completeness diagnostics.
4. Execute the feasibility gate to freeze segment granularity, sample thresholds, and coverage policy for RQ01/RQ07/RQ11.
5. Only then write `cleaning.py` / `features.py` and begin research outputs.

**Versioning:** Any changes to population, key formula, primary estimator, threshold, or outcome definition must be recorded in a brief change log with reason, date, and impact on prior outputs. Never overwrite a prior result silently.

---

### Research plan change log

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026-11-23 | Initial pre-implementation evidence-based 15-RQ specification anchored to audited dataset snapshot |
