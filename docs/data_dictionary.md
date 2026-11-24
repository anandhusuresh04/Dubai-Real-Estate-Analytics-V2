# Dubai Residential Market Intelligence V2 — Data Dictionary & Semantic Contract

**Document version:** 1.0 (2026-11-23)  
**Status:** Pre-implementation source contract; some publisher definitions require live source confirmation  
**Repository destination:** `docs/data_dictionary.md`  
**Source file:** `data/raw/dld_sales_transactions.parquet`  
**Frozen SHA-256:** `8294c3dd83dde2e16e64eaf1ef155a1ad14ec16b6b39384561777afb8425417e`  
**Research specification:** [`research_plan.md`](research_plan.md)  
**Audit reference:** [`data_audit.md`](data_audit.md)

> **Read first:** This file documents registered **sale transactions**, not advertised listings, the housing stock, unique dwellings, households, leases or rent. Each row represents a transaction record, with `transaction_id` as the record identifier. There is **no stable physical-unit ID** to construct a repeat-sales index or holding periods. Raw source fields must remain unchanged. Observed associations must not be described as causal premiums or investment opportunities.

## 1. Evidence status and provenance

### 1.1 Evidence hierarchy

- **S — Snapshot-verified:** File existence and the SHA-256 above have been checked in the working container. The snapshot audit previously examined the full Parquet dataset and produced the empirical counts in this document. These counts still need to be reproduced by the **V2 pipeline** on the user's machine before they become automated regression-test expectations.
- **A — Previously audited:** Rows, null counts, category distributions, date range and bitmask prevalence below are from the prior complete-file audit, `Dubai_Transactions_Deep_Data_Audit.md` (2026-11-23). Not inferred from a handful of notebook printouts.
- **D — Documented/claimed source semantics:** Field meanings are based on the previous audit's interpretation of the publisher's data dictionary and on source labels. Where the precise upstream definition cannot be proven from the records alone, the definition is marked **source verification required**.
- **P — Project convention:** Data types, derived features, cohort rules and KPI formulas proposed here are *our own* reproducible definitions, not original raw variables.

**Original dataset references (confirm version/licensing before public release):**
- [Publisher dataset repository](https://huggingface.co/datasets/dubairealestatedata/dubai-real-estate-sales-transactions)
- [Publisher DATA_DICTIONARY.md](https://huggingface.co/datasets/dubairealestatedata/dubai-real-estate-sales-transactions/blob/main/DATA_DICTIONARY.md)
- Source described by the publisher as Dubai Land Department open-data transactions distributed via Dubai Pulse. Do not imply independent official validation by the project.

**License:** Prior audit recorded **CC BY 4.0** for the published dataset. Verify exact license and any attribution requirements against the dataset version used before GitHub deployment. The metadata includes a reference to an upstream DLD source, but it is not evidence of a direct live DLD API integration.

### 1.2 Immutable snapshot properties (A, except hash S)

| Property | Snapshot finding | Interpretation |
|---|---:|---|
| Physical records | 1,382,848 | Transaction rows, not unique units |
| Raw fields | 20 | Preserve original names and types on ingestion |
| Unique `transaction_id` | 1,382,848 | No duplicate IDs found by prior audit |
| Recorded date minimum | 1975-01-01 | Early years are sparse; not primary market-history coverage |
| Recorded date maximum | 2026-11-02 | 2026 is incomplete in calendar coverage |
| Distinct non-null communities | 244 | Based on source community identifiers/names |
| Parquet bytes | 22,819,023 | Source artifact, not decompressed DataFrame size |
| Primary full-year window (P) | 2010–2025 | 2026 separate provisional reporting |

**Version-lock rule:** For any replacement Parquet, recompute hash, size, row count, min/max dates, key categorical domains, and null profiles. A mismatch means a **new snapshot**; do not reuse previous acceptance counts as fixed truth.

## 2. Raw data dictionary — all 20 columns

**Type notation:** These are **required logical types in V2**, not claims about the exact Arrow physical storage type. Capture actual Parquet type, pandas dtype, and casting errors during ingestion in `dataset_manifest`. **Null counts and distinct counts are from the prior full-data audit (A).** Cardinality excludes nulls. An identifier is not a continuous numeric measurement even if stored as an integer.

| # | Raw column | V2 logical type | Meaning / permitted analytical use | Nulls | Non-null distinct | Governing caveat |
|---:|---|---|---|---:|---:|---|
| 1 | `transaction_id` | Identifier (string/int preserved) | Transaction **record** identifier; key for count/reconciliation | 0 | 1,382,848 | Not property ID, buyer ID or guaranteed ownership chain |
| 2 | `instance_date` | Date / datetime | Recorded transaction registration date | 0 | 6,167 | Not marketing/listing, contract-signing or handover date |
| 3 | `reg_type_label` | Category | Registration grouping: `Ready`, `Off-Plan` | 0 | 2 | `Ready` must **not** be relabeled `Resale`; 2026 procedure-field omissions need caution |
| 4 | `area_id` | Nullable identifier | Geographic community key | 148 | 244 | Preferred grouping key; not unit/building ID |
| 5 | `area_name_en` | Nullable text | Human-readable English community label | 148 | 244 | Display only; spelling or naming revisions may occur |
| 6 | `project_name` | Nullable text | Registered project name | 284,699 | 3,427 | Not a stable, normalized development entity; missingness is material |
| 7 | `master_project_name` | Nullable text | Master development/project grouping | 253,337 | 185 | Cannot assume every project maps perfectly to a master project |
| 8 | `building_name` | Nullable text | Registered building name | 408,903 | 4,701 | Massive 2026 coverage break; text ≠ guaranteed stable building identifier |
| 9 | `property_type_label` | Category | `Unit`, `Villa`, `Land`, `Building` | 0 | 4 | `Unit` includes non-residential categories; pair with `usage_label` |
| 10 | `property_sub_type` | Nullable category/text | More detailed property subtype | 198,042 | 35 | Audit possible subtypes before assuming `Unit` means flat/apartment |
| 11 | `usage_label` | Category | `Residential`, `Commercial`, `Other` | 0 | 3 | Usage may differ from legal occupancy/actual household use |
| 12 | `rooms_bucket` | Nullable ordinal category | Bedroom count bucket; `0` studio, `1`–`4` bedrooms, `5` = **5+** | 281,078 | 6 | Missing ≠ studio; five is top-coded, not exactly five bedrooms |
| 13 | `has_parking` | Nullable Boolean | Recorded parking inclusion/indicator | 43,942 | 2 | Unknown ≠ `False`; exact upstream parking semantics need verification |
| 14 | `area_sqm` | Nullable numeric, m² | Recorded area used in the transaction | 2 | 82,629 | Not guaranteed net usable area; zero/negative/extreme values require QA |
| 15 | `price_aed` | Numeric, AED | Registered transaction price/value | 0 | 317,557 | Not asking price, market value, annual revenue or return |
| 16 | `price_psf` | Nullable numeric, AED/ft² | Publisher-supplied or derived price per square foot | 186 | 301,822 | QA reference; do not use as independent valuation predictor |
| 17 | `procedure_id` | Nullable identifier | Registration procedure code | 26,971 | 18 | Requires source codebook to interpret each procedure |
| 18 | `procedure_name_en` | Nullable category/text | Human-readable procedure description | 26,971 | 18 | Procedure categories are not synonymous with property completion status |
| 19 | `is_pre_registration` | Nullable Boolean | Pre-registration indicator | 26,971 | 2 | Do not impute missing values from `reg_type_label` |
| 20 | `quality_flags` | Integer bitmask | Publisher's encoded record checks | 0 | 9 | `0` = no encoded condition triggered, **not guaranteed error-free** |

### 2.1 Observed categorical domains (A)

| Column | Observed values and row counts | Handling |
|---|---|---|
| `reg_type_label` | `Ready` 736,939; `Off-Plan` 645,909 | Validate exact labels; unknown new labels must be reported |
| `property_type_label` | `Unit` 1,066,079; `Villa` 179,189; `Land` 113,807; `Building` 23,773 | Never filter all-sales activity to housing without naming new cohort |
| `usage_label` | `Residential` 1,190,250; `Commercial` 132,317; `Other` 60,281 | Keep `Other` rather than silently mapping to residential |
| `rooms_bucket` | `0`: 239,132; `1`: 413,725; `2`: 262,904; `3`: 132,424; `4`: 46,978; `5`: 6,607; null: 281,078 | Use nullable integer and 5+ display label; no arbitrary median imputation for reporting |
| `has_parking` | Two non-null Boolean states; null: 43,942 | Explicit three-state representation: yes/no/unknown |

`property_sub_type` has **35** distinct observed non-null labels. The complete list must be exported by the V2 validation script rather than invented in this document. Likewise, `procedure_name_en` has **18** observed non-null categories: a subset appears below, not a claimed exhaustive enumeration.

**Observed procedure labels (examples from audit):** `Sell - Pre registration`, `Sell`, `Delayed Sell`, `Lease to Own Registration`, `Sell Development`, `Development Registration`, `Development Registration Pre-Registration`, `Lease to Own Registration Pre-Registration`, `Sale On Payment Plan`, `Delayed Development`, `Delayed Lease to Own Registration`, `Adding Land By Sell`, `Lease Development Registration`. All 18 unique pairs of code/name must be exported and checked by `validation.py`; absence of certain labels here does **not** mean they are invalid.

### 2.2 Geography and entity normalization

1. `area_id` is the primary community key; `area_name_en` is the preferred display label.
2. Preserve raw project/building/area text in original columns. If normalization is required, create separate `*_normalized` columns, never silently overwrite raw strings.
3. Do not convert missing geography to the literal strings `"Nan"`, `"None"`, `"Unknown"` or `"0"`. Keep genuine nulls; report geography-unknown transactions separately.
4. Test `area_id → area_name_en` mapping: one ID with multiple names or one name with multiple IDs requires an exception table, not ad hoc merging.
5. Identical building names in different communities are **not** evidence of the same building. No universal building entity key exists in the supplied columns.

## 3. Missingness, coverage and data-quality findings

### 3.1 Null profile, entire source snapshot (A)

| Field | Missing rows | Missing % |
|---|---:|---:|
| `building_name` | 408,903 | 29.570% |
| `project_name` | 284,699 | 20.588% |
| `rooms_bucket` | 281,078 | 20.326% |
| `master_project_name` | 253,337 | 18.320% |
| `property_sub_type` | 198,042 | 14.321% |
| `has_parking` | 43,942 | 3.178% |
| `procedure_id`, `procedure_name_en`, `is_pre_registration` (each) | 26,971 | 1.950% |
| `price_psf` | 186 | 0.013% |
| `area_id`, `area_name_en` (each) | 148 | 0.011% |
| `area_sqm` | 2 | <0.001% |
| `transaction_id`, `instance_date`, `reg_type_label`, `property_type_label`, `usage_label`, `price_aed`, `quality_flags` | 0 | 0% |

**Important:** These totals do not imply that missingness is random. Every analytical cohort must publish the loss of rows from its own field requirements. Missing-data indicators should be computed *before* optional complete-case restrictions.

### 3.2 2026 discontinuities (A)

- **Building name:** From March through October 2026, building names are missing for approximately 99.9–100% of transactions. This is a *coverage break*, not evidence buildings ceased to be recorded in the market.
- **Parking:** All 43,942 missing `has_parking` observations occur in 2026. In October 2026, the monthly missingness reached about 49.5%.
- **Procedures:** All 26,971 records with null `procedure_id`, `procedure_name_en` and `is_pre_registration` occur in 2026. These 26,971 records are labeled `Ready`; the relation is an anomaly to investigate, **not proof that Ready is wrong**.
- **Provisional policy:** Exclude 2026 from full-year historical comparisons and historical amenity regressions. Any 2026 same-month/YTD reporting must show actual date coverage, a completeness warning, and procedure/missingness context.

**Compulsory V2 output:** `data_quality_monthly.parquet` with `year`, `month`, `n`, missing count and missing rate for the relevant fields, plus source snapshot ID. A monthly chart based on yearly averages would obscure the discontinuity.

### 3.3 Source quality bitmask (D; verify publisher definitions)

| Bit (`quality_flags & bit != 0`) | Previously documented interpretation | Rows with bit set (A) | Treatment |
|---:|---|---:|---|
| 1 | Price below publisher floor | 427 | Flag, inspect and compare sensitivity |
| 2 | Missing or out-of-range area | 1,062 | Exclude from valid-price/area pricing metrics; retain for QA |
| 4 | Price/ft² outside publisher-defined segment/year P1–P99 range | 27,907 | Strict pricing cohort excludes; assess tail selection bias |
| 8 | Both principal fields missing | 0 | Maintain bit test in contract even if absent |
| 16 | Invalid date | 1 | Reject for time-series population, preserve audit record |

**Bitmask, not enum:** A record with `quality_flags = 5` has both bits 1 and 4; counts overlap across bits and cannot be simply summed. Snapshot raw value distribution: `0` 1,354,155; `4` 27,356; `2` 737; `5` 264; `6` 172; `7` 115; `3` 38; `1` 10; `16` 1. **28,693** records have nonzero flags. `quality_flags == 0` means *none of these publisher-coded conditions is flagged*; it does not mean every property field is correct.

**Look-ahead warning:** If the publisher's outlier thresholds are computed using a whole historical sample, flag-0 eligibility can embed information from future years. RQ06 time-based prediction should test a time-safe alternative filter that does not use future-derived thresholds.

### 3.4 Numeric plausibility (A)

| Field | Minimum | Median | P99 | Maximum | Warning |
|---|---:|---:|---:|---:|---|
| `price_aed` | 1 | 1,360,000 | 24,200,000 | 3,869,204,024 | Extreme bulk/recording cases possible; investigate rather than asserting reason |
| `area_sqm` | 0.01 | 96.10 | 2,809.78 | 342,103,430.80 | Clearly implausible extremes for ordinary residences; check cohort + flags |
| `price_psf` | 0.00 | 1,260.40 | 4,478.14 | 1,207,963.20 | Zero/invalid reference prices exist |

Source audit found `price_psf` approximately consistent with `price_aed / (area_sqm × 10.76391041671)`: median absolute relative error about **0.000196%** among comparable rows, with **108** rows differing by over 1% among **1,382,638** comparable records. This confirms it is largely a derived field but does **not** prove every row is consistent. Export outliers to a QA exceptions table.

## 4. Canonical research populations (P)

**Do not create one universal `clean_df` for all questions.** Cohorts are named and defined below; actual row counts must be computed by code and attached to every result.

| ID | Inclusion rules | Intended use | Why it matters |
|---|---|---|---|
| `P0_ALL_SALES` | Valid unique transaction identifier, parsable date, finite nonnegative sale value; preserve eligible registration categories and all property types | Sales count, registered value, activity concentration | Do not confuse all market sales with built-residential sales |
| `P1_RESIDENTIAL_CORE` | P0 AND `usage_label = Residential` AND `property_type_label IN (Unit,Villa)` AND finite positive price and area | Residential price/size metrics; alternate quality sensitivity | `Residential` alone still contains land/building types |
| `P1_STRICT` | P1_RESIDENTIAL_CORE AND `quality_flags = 0` | Default historical price levels, index/cohort research | Selected population, **not** “perfect records” |
| `P2_KNOWN_SEGMENT` | P1_STRICT AND non-null `area_id`, valid registration type, usable bedroom where required, valid size bins | Matched price comparisons and community models | Report missingness-driven eligibility losses by year |
| `P3_AMENITY_KNOWN` | P1_STRICT AND 2015–2025 AND valid known parking and bedroom values + overlap rules | Conditional amenity associations (RQ12) | No unknown-as-false; do not generalize to excluded transactions |
| `P4_2026_PROVISIONAL` | 2026 records under separately named KPI-specific eligibility rules | Coverage monitoring and transparent partial-year analysis | No full-year 2026-vs-2025 conclusions |

**Previous audit benchmark (A):** Residential Unit/Villa all-quality 1,113,178; flag-0 residential Unit/Villa 1,094,417. These counts are *all years*, not the 2010–2025 final sample. `P0` and `P1` definitions here add exact value/date checks, so implementation must reconcile rather than blindly hardcode those benchmark counts.

**Filtering audit:** At every stage export `stage`, `input_n`, `removed_n`, `retained_n`, `rule`, `cohort_id`; confirm `input_n = removed_n + retained_n`. Reconcile cohort-by-year, category, geography and registration-type shares before interpreting excluded populations.

## 5. Derived features and semantic definitions (P)

| Derived feature | Type / unit | Deterministic definition | Null / caveat |
|---|---|---|---|
| `price_per_sqm` | Float, AED/m² | `price_aed / area_sqm` | Only if both finite and >0; otherwise null; not the ratio of medians |
| `price_per_sqft_calculated` | Float, AED/ft² | `price_aed / (area_sqm * 10.76391041671)` | Verify against raw `price_psf`; do not silently replace raw value |
| `year` | Int | Calendar year of parsed `instance_date` | Null if unparseable; time-series cohort excludes invalid date |
| `month` | Int | Calendar month 1–12 | Source date is registration date |
| `quarter` | Int | Calendar quarter 1–4 | No partial year compared with a full year |
| `year_quarter` | Text | `YYYY-Qn` | Display grouping only; numeric year+quarter preferred for sorting |
| `is_residential_built` | Boolean | `(usage_label == 'Residential') AND (property_type_label IN ('Unit','Villa'))` | Eligibility flag; not an independent source category |
| `quality_policy` | Enum | `strict_flag0`, `core_value_valid`, etc. | Save with each output table; no untracked switching |
| `parking_status` | Nullable category | `Yes` if raw True; `No` if raw False; `Unknown` if missing | Never use `astype(bool)` on raw unknown values |
| `bedroom_label` | Nullable text | `0 → Studio`, `1..4 → 1BR..4BR`, `5 → 5+BR` | Unknown remains null/Unknown; code 5 is top-coded |
| `size_band` | Category | Predeclared bounded `area_sqm` intervals in `config.yaml` | Freeze thresholds after feasibility gate; no outcome-driven band choice |
| `nominal_budget_eligible_1m` | Boolean | `price_aed <= 1_000_000` (similarly 1.5m, 2m) within P1_STRICT | Not household affordability; no inferred incomes |
| `registration_known` | Boolean | `reg_type_label IN ('Ready','Off-Plan')` | Separate unknown category counts if source changes |
| `is_offplan` | Nullable Boolean | True for `Off-Plan`; False for `Ready`; null otherwise | Does not encode speculative motive |
| `transaction_count` | Count | Rows/count of distinct valid unique transaction IDs in a declared cohort | Always label cohort and denominator |
| `registered_value_aed` | Sum, AED | Sum of recorded `price_aed` in named eligible cohort | Not housing-market capitalization or sales revenue retained by developers |
| `median_psm` | AED/m² | Median **transaction-level** `price_per_sqm` | Does not equal `median(price_aed)/median(area_sqm)` |
| `median_total_price_aed` | AED | Median transaction-level `price_aed` | Not necessarily a matched property across years |
| `median_area_sqm` | m² | Median transaction-level `area_sqm` | Same caveat |
| `offplan_count_share_pct` | % | `100*N(Off-Plan)/(N(Off-Plan)+N(Ready))` | Explicit population and period; unknown reg types reported separately |
| `offplan_value_share_pct` | % | `100*SUM(value Off-Plan)/(SUM(value Off-Plan)+SUM(value Ready))` | Separate from count share |
| `community_hhi_count` | 0–1 | `SUM((community_count/total_known_geography_count)^2)` | Explicit geography-missing policy and sample universe |
| `matched_segment_index` | Index | Fixed-weight weighted geometric aggregation of matched-segment median AED/m² ratios, with a defined base | Not repeat-sales or pure constant-quality index; publish weights and coverage |
| `matched_coverage` | % | Eligible transactions within comparison-matched cells / all transactions in relevant base/endpoint cohort | Report separately for both endpoints |

**Price comparison units:** Use AED for transaction values and AED/m² for price per area. Always show `year`, `cohort_id`, sample `n` and comparison basis. Never attribute fixed-budget eligible transactions to available listings or household purchasing power.

**Statistical variable distinction:** `median_total_price`, `median_area`, and `median_psm` are *three distinct statistics*. An adjusted off-plan log coefficient must be converted to percentage with `100*(exp(beta)-1)` rather than simply treating `beta*100` as exact.

## 6. Research-to-field feasibility map

| Research question | Required source fields | Blocker / caution |
|---|---|---|
| RQ01 Composition-adjusted price change | `instance_date`, `price_aed`, `area_sqm`, `area_id`, `property_type_label`, `reg_type_label`, `rooms_bucket`, `quality_flags` | Matched-cell attrition; unobserved property quality |
| RQ02 Changing transaction sizes | `instance_date`, `area_sqm`, `property_type_label`, `reg_type_label`, `rooms_bucket`, `area_id` | No repeated floor plans/identical unit IDs |
| RQ03 Fixed nominal budget access | `instance_date`, `price_aed`, `area_sqm`, `rooms_bucket`, `area_id` | No income, mortgages or live listings |
| RQ04 Community concentration | `transaction_id`, `instance_date`, `area_id`, `price_aed` | Geography missingness and changing community universe |
| RQ05 Registration mix | `instance_date`, `reg_type_label`, `price_aed`, `property_type_label`, `usage_label` | Off-plan ≠ speculative investment |
| RQ06 Activity vs subsequent prices | `instance_date`, `area_id`, `price_aed`, `area_sqm`, segment fields | Strict time splits; sufficient quarterly observations |
| RQ07 Persistent community growth | `instance_date`, `area_id`, `price_aed`, `area_sqm`, segment fields | Minimum continuity, sample size, matched coverage |
| RQ08 Price convergence/divergence | `instance_date`, `area_id`, `price_aed`, `area_sqm`, segment fields | Fixed community universe to avoid entry/exit bias |
| RQ09 Community regimes | `instance_date`, `area_id`, `price_aed`, `area_sqm`, `transaction_id` | Activity counts ≠ inventory liquidity |
| RQ10 Size-price structure | `instance_date`, `price_aed`, `area_sqm`, `area_id`, property/room/reg fields | Association, not size premium causation |
| RQ11 Ready/off-plan price gap | `reg_type_label`, date, area, price, size, rooms, property type | Missing payment plans, exact property condition, completion status |
| RQ12 Amenity differences | `has_parking`, `rooms_bucket`, price, size, date, area, type | Missingness and confounding; 2026 parking unusable without caution |
| RQ13 Price stability | Date, community, price/area, segment fields | Sparse or unstable time series may preclude ranking |
| RQ14 Upper-tail concentration | `price_aed`, date, usage/type, flags | High-end sales ≠ wealth of buyers |
| RQ15 Sensitivity and reliability | All source fields + flags | Every published result must cite its applied rules |

**Unavailable fields (must not fabricate):** physical property ID, ownership/buyer identity, repeat-sale linkage, actual asking/listing price, days on market, rent, service charges, mortgage terms, household income, transaction financing, exact location coordinates, completion/handover date, developer cash flows, unit floor/view/condition and independently appraised fair value.

## 7. Mandatory schema and validation contract for implementation

### 7.1 Ingestion (`src/loader.py`, `src/validation.py`)

1. Resolve data path from the **project root** (not current shell working directory).
2. Validate SHA, file existence and readability, record `pyarrow`/`duckdb`/`pandas` versions.
3. Validate presence of **all 20 named source columns** and record extra columns without silently discarding them.
4. Read actual Parquet physical types into `dataset_manifest`; cast to nullable analytics types only in a **separate** transformation layer.
5. Verify IDs are non-null and unique; date parsing is controlled and invalid dates are audited.
6. Validate known categorical domains and enumerate unexpected values. Do not silently map new labels to existing ones.
7. Validate two-way `area_id` ↔ `area_name_en` consistency and `procedure_id` ↔ `procedure_name_en` mapping; preserve exceptions.
8. Report exact null counts/rates by **year/month and property/registration cohort**, not only global percentages.
9. Check finite/nonnegative or positive requirements according to the population, not through universal destructive filtering.
10. Check `price_psf` against recalculated AED/ft² for valid records; export exceptions with transaction IDs and error measures.
11. Decode quality flags bitwise, preserve raw bitmask, report co-occurring flags and flag rates by period.
12. For every cohort export an exclusion waterfall and ensure all counts and values reconcile.

### 7.2 Test cases that must pass (`tests/`)

- `has_parking`: raw null stays null; raw False stays False; strings `"False"`/`"True"` only mapped under explicitly declared parser rules.
- `rooms_bucket`: `0` remains studio, null stays unknown, `5` becomes *5+* display label.
- Null geography/building names remain null under normalization; blank strings can be converted to null in derived normalized fields.
- `quality_flags=5` activates bits 1 and 4; bit counts may overlap; 0 activates none.
- Price-per-sqm returns null for invalid denominator; no infinite derived features.
- `COUNT(*) == COUNT(DISTINCT transaction_id)` after key validation; aggregations reconcile to the same cohort.
- Raw ↔ derived `price_psf` comparisons use sqm-to-sqft factor 10.76391041671 and tolerances rather than exact float equality.
- All 2026 completeness results are flagged provisional; 2026 not accidentally included in 2010–2025 full-year research.
- A matched-segment result reports both 2021 and 2025 coverage; index weights sum to one within declared matched set.
- No output silently uses `Ready` as a proxy for verified resale or `Off-Plan` as direct evidence of speculation.

### 7.3 Required provenance in every exported table

`source_sha256`, `source_max_date`, `run_id`, `generated_at_utc`, `cohort_id`, `quality_policy_id`, `method_id`, `period_start`, `period_end`, `n_transactions`, `coverage_pct` (if applicable), `metric_unit` (where practical), and an explicit `provisional_2026` flag if applicable.

## 8. Source confirmation register — investigate, don't assume

| Item | Why source confirmation is needed | Current status |
|---|---|---|
| Official meaning of `reg_type_label` and `is_pre_registration` | Avoid equating marketing status, pre-registration and handover | Pending source definition verification |
| Exact meaning of `has_parking` | May refer to recorded parking inclusion rather than actual usable parking space | Pending source definition verification |
| Interpretation and domain of `procedure_id` | 18 observed categories; classifications must be auditable | Pending full source-codebook check |
| Quality-bit rules and precise percentile strata | Impacts price tails and time-series exclusions | Previously documented; independently reconfirm before publication |
| `area_sqm` measurement basis | Saleable versus registered area may vary by subtype/procedure | Not established from file alone |
| Publisher version and license attribution | Required for reproducibility and legal attribution | Prior audit cites CC BY 4.0; reconfirm current metadata |
| 2026 change in building/procedure coverage | Could reflect source/extraction change, but dataset alone does not establish why | Observed discontinuity; cause unknown |
| Exact Arrow physical column types | Needed for stable loader contract | Read and export using V2 loader; logical types specified here |

## 9. Maintenance and change control

- **Never overwrite the source snapshot.** Derived data belongs in `data/interim/`, `data/processed/` or `data/aggregates/`; source remains in `data/raw/`.
- No new source field, domain remapping, unit conversion, cohort eligibility change or outlier-policy change without a versioned amendment to this document, associated test and regeneration of downstream output tables.
- Every V2 analysis must refer to an explicit `cohort_id`, statistic, units, period, date coverage and known-field coverage.
- When source documentation contradicts a project inference, update the dictionary with the verbatim factual source meaning (within citation/quotation limits), record the correction and rerun affected calculations.
- When data is insufficient, report `INCONCLUSIVE` or `NOT_FEASIBLE`. Do not replace missing measurements with a stronger claim.

### Change log

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-11-23 | Initial 20-field source dictionary, null/domain profile, quality-bit definitions, named cohorts, engineered-feature contract, tests, and source-confirmation ledger, aligned to the V2 research plan |
