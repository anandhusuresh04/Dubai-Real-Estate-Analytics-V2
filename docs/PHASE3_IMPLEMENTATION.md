# Phase 3 — Evidence-first analytical dashboard

## What is actually provided

Six research-specific Streamlit pages replace Phase 2 skeleton renders while preserving
native navigation, the existing navy/teal UI shell, and the frozen Notebook 06 scientific
publication gate. Plotly is used only to visualize **precomputed approved source rows**;
no raw transactions are loaded by the web app and no matched index, median, causal
coefficient, forecast, parking premium, or rental yield is calculated in Streamlit.

### Scientific publication constraint discovered in the original Notebook 06

`06_Robustness_Validation(7).ipynb` initializes `subclaim_evidence['published'] = False`
for all individual upstream claims, and does not promote these flags in its finalization
section. RQ-level dashboard readiness and `APPROVED_WITH_QUALIFICATIONS` **do not**
authorize any particular matched-price growth, community growth, matched Ready/Off-Plan
gap, or bedroom estimate. Those panels are deliberately withheld unless BOTH a future
frozen subclaim release and a reviewed exhibit-to-claim binding authorize them.
`CLAIM_EXHIBIT_BINDINGS` in `app/analytics/catalog.py` is intentionally empty.
Do not hand-edit this mapping to make results appear. It must be reviewed against the
research evidence and release process before a future scientific update.

### Source artifacts not included in this delivery

The archive contains historical source notebooks and the Phase 1/2 scaffolding, but the
69 generated aggregate Parquet/CSV files from the user's Windows project were NOT
included. Therefore a trustworthy test against actual per-file schemas, cell values,
complete chart availability, and real browser visuals could NOT be completed here.
The dashboard will report unavailable schemas and withheld charts rather than invent
values. See `PHASE3_EXHIBIT_MATRIX.csv` for every intended source contract.

## Safe installation — no duplicate package inside pytest root

1. Stop Streamlit (`Ctrl+C`). Keep `Dubai_Real_Estate_Analytics_V2` unchanged.
2. Download `Dubai_V2_Dashboard_Phase3.zip` to Downloads, then extract to
   `E:\DataAnalytics\Projects\Dubai_V2_Phase3_Package` (a sibling, **not** the project).
3. From PowerShell run:

   ```powershell
   $project = 'E:\DataAnalytics\Projects\Dubai_Real_Estate_Analytics_V2'
   $installer = 'E:\DataAnalytics\Projects\Dubai_V2_Phase3_Package\Install_Phase3.ps1'
   powershell -ExecutionPolicy Bypass -File $installer -ProjectRoot $project -DryRun
   powershell -ExecutionPolicy Bypass -File $installer -ProjectRoot $project
   ```

4. Validate existing research source and contract regressions:

   ```powershell
   cd $project
   conda activate dubai-v2
   python -m pytest -q -W error
   python scripts/audit_dashboard_artifacts.py --root . --out reports/tables/dashboard_phase1_inventory.json
   ```

5. Generate a new **local upstream byte-integrity snapshot** ONLY after confirming
   that the above suite and Phase 1 inventory passed. The snapshot binds the frozen
   original source hash, original export files, and observed schemas/byte hashes:

   ```powershell
   python scripts/attest_dashboard_upstream.py --root .
   python scripts/check_phase3_dashboard.py --root .
   ```

   The attestation script does **not** overwrite existing attestations and refuses
   missing artifacts by default. It may perform a one-time full SHA-256 scan of the
   original raw source solely to verify provenance; the dashboard itself never scans
   the raw source.

6. Launch:

   ```powershell
   streamlit run app.py
   ```

7. Inspect all pages, the actual charts, the unsupported/withheld states, and
   browser widths around 1440px, 1024px and 390px. Also review the JSON coverage
   report in `reports/tables/dashboard_phase3_coverage.json` to see the **actual**
   charts supported by your local schemas and publication restrictions.

## Physical/source attestations are NOT scientific approvals

The local `dashboard_upstream_attestation.json` is a deterministic byte-hash binding
produced after independent CSV/Parquet row/cell readback (when paired exports exist),
physical source hash verification, and Notebook 06 release verification. It is not
an independent replication of an estimate, nor evidence that an individually withheld
finding may be published. Only the preserved Phase 1 `app_core` gates can authorize
an RQ, and only the original Notebook 06 subclaim release plus a separately reviewed
source-specific binding can authorize an interpretive claim.

## Publication and filtering rules

- Show P0 historical registered transaction counts and nominal value at recorded years;
  never conflate these with stock, listings, demand, or market capitalization.
- Use P1 Strict observed residential transaction price per square metre only as a raw,
  descriptive series. No average-of-medians or mean of separately computed indices.
- Fixed matching designs and estimands remain immutable; no slider creates new ones.
- Display exact source counts/amounts, with selectors subsetting already computed rows.
  Unsupported categories, duplicate chart grains, and unknown schemas are blocked.
- Community eligibility must be true and individually permitted for growth exhibits.
- Bedroom support tables are descriptive diagnostic records; adjusted bedroom
  coefficients remain gated. Parking only reports overlap feasibility; no premium.
- No research values are shipped as test fixtures. All test values are tiny explicitly
  artificial values used only to assert software behavior.
- The app never displays RQ06 forecasting or investment recommendations.

## Verification done in this execution environment

- Phase 1 + Phase 2 + Phase 3 focused test suite: **60 passed**.
- Archived original `src/`, `tests/`, and notebook snapshot plus dashboard tests:
  **162 passed, 4 skipped** (some original tests require dependencies unavailable here).
- Python source compilation passed.
- Actual `streamlit run app.py`: **NOT run** because Streamlit is not installed here.
- Actual local research aggregate readback and dashboard screenshot: **NOT verified**;
  the user's generated aggregate CSV/Parquet files were not provided in this runtime.

**Delivery status:** full six-page source implementation, **conditional publication and
visual acceptance**. Final empirical completeness must be assessed using the local
Phase 3 coverage report; this is not a claim that all requested charts have been
shown or individually authorized.
