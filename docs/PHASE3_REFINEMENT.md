# Dubai Real Estate Analytics V2 — Phase 3 refinement

This targeted update builds on Phase 3 and **does not replace the full application**. It updates only the six shared analytical presentation/audit modules listed in the installer, adds focused tests, and preserves all `app_core/`, `src/`, `notebooks/`, `data/`, and `reports/` research artifacts. Use your already-installed Phase 1–3 project.

## Confirmed defects and changes

1. **Notebook 05 coefficient table**: `05_size_price_linear_models` contains `property_type_label`, `outcome`, `beta`, uncertainty fields, and model sample information. The Phase 3 catalog incorrectly expected `elasticity`, `size_coefficient`, or `beta_area`. It now uses `beta` and an exact `outcome` facet (default `log_price`); duplicate coefficient cells, unexpected outcomes, and nonnumeric coefficients are rejected. Crucially, coefficient publication is *claim-sensitive*. An RQ-level QUALIFIED outcome does not release a coefficient. The local audit separately reports `technical_schema=READY_WITHHELD` when the source table is technically valid but unpublished.
2. **Eight previously withheld exhibits** (three RQ01, one RQ07, three RQ11, one RQ12) remain blocked by the final individual-claim register and empty independently audited source-to-claim bindings. This is intentional, not a broken chart. `size_elasticity` is likewise withheld as an inferential coefficient; all nine should remain unavailable until genuine individual publication permissions and independently audited claim-source bindings are supplied. No flags are changed.
3. **Research tables**: correct four-value unpacking is maintained; long restriction, decision, and source fields can be read in a full-length row-detail expander. Research provenance SHA-256 is copyable; eligibility and bedroom codes have presentation-only descriptions.
4. **Charts**: quarterly date ticks are sparse and horizontal; community dispersion endpoints are plotted as observations without implying intervening annual measurements; the signed 2021–2025 registration contribution is described as a change, not a total; physical-size classes are labeled with Notebook 02's exact fixed sqm bin boundaries; budget amounts are readable and correctly described as cumulative thresholds; 1%/10% upper-tail value shares are defined; population cohorts are marked nonadditive.
5. **Community exploration**: source-verified community names are applied consistently in selector labels and chart legends where a nonconflicting mapping exists; missing or conflicting names safely fall back to source IDs.
6. **Support diagnostics**: single-row parking feasibility is a compact support card, explicitly **NOT ESTIMABLE**; bedroom support labels remain distinct from withheld coefficients. Repeated unreleased charts are consolidated into one qualified-permission notice when all source-to-claim bindings are absent.
7. **UI**: evidence tables adjust height to data, support full-text inspection and do not re-estimate statistics; responsive CSS is refined for 900px and 720px widths.

## Local installation

Download the ZIP into `E:\DataAnalytics\Projects\`, and extract into **`E:\DataAnalytics\Projects\Dubai_V2_Phase3_Refinement_Package`**, outside the main project tree (to prevent duplicate pytest collection). Stop the Streamlit server with Ctrl+C.

```powershell
$project = 'E:\DataAnalytics\Projects\Dubai_Real_Estate_Analytics_V2'
$installer = 'E:\DataAnalytics\Projects\Dubai_V2_Phase3_Refinement_Package\Install_Phase3_Refinement.ps1'
powershell -ExecutionPolicy Bypass -File $installer -ProjectRoot $project -DryRun
powershell -ExecutionPolicy Bypass -File $installer -ProjectRoot $project
```

The installer backs up existing target files under `phase3_refinement_backup_YYYYMMDD_HHMMSS/`. Do not remove the backup until all local checks pass. Only these project files are created/replaced: `app/analytics/catalog.py`, `charts.py`, `render.py`, `app/theme/phase3.py`, `scripts/check_phase3_dashboard.py`, `tests/dashboard/test_phase3_refinement.py`, `docs/PHASE3_REFINEMENT.md`.

## Required local acceptance checks

```powershell
conda activate dubai-v2
python -m pytest -q -W error
python scripts/attest_dashboard_upstream.py --root .
python scripts/check_phase3_dashboard.py --root .
streamlit run app.py
```

Inspect `reports/tables/dashboard_phase3_coverage.json` after the audit. The *technical_schema* field for `size_elasticity` should read `READY_WITHHELD`, assuming the exported Notebook 05 table has the confirmed schema and passes the independent digest gate. Do **not** use this field as permission to publish its coefficients. With the current unreleased individual claims, a **28/37 publication-ready** result is expected, rather than 37/37.

Manually inspect all six pages at 100% browser zoom, try a narrower window, check community name labels, change year and categorical selectors, read a full restriction, and confirm source CSV downloads. Any unexpected traceback or changed exhibit count requires investigation before deployment.

## Verification limitations

The package was compiled and tested in a container using the original Phase 1, Phase 2, Phase 2 visual-refresh, Phase 3 packages and archived `src/`, notebooks and research tests. **The user's Windows-generated aggregate Parquet/CSV files were not available for independent byte-level/row-level inspection here.** Local tests use controlled fixtures; actual dashboard KPI and chart-value validation requires the commands above. Streamlit was not installed in the build container, so a live browser screenshot and small-screen visual inspection were not possible. No scientific release flags, cohorts, estimators, research exports, or data were altered.
