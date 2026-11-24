# Dubai Real Estate Analytics V2 — Phase 2 installation

**Scope:** six-page design-system and navigation skeleton. No research charts, statistical models, or empirical fixtures.

## Compatibility and no-overwrite installation

1. Extract the ZIP to a *temporary* folder. Review existing root `app.py`, `app/`, and `.streamlit/config.toml` before copying. This deliverable does not contain or replace existing `app_core/`, `src/`, `notebooks/`, research exports, or Phase 1 tests.
2. Copy the new `app.py` to the project root **only if you have no existing app.py**. If one exists, review/merge its entry point rather than replacing it.
3. Merge the supplied `app/` package into the existing project `app/` directory. Existing same-named files require review; the package adds `app/components/`, `app/pages/`, `app/theme/` and supporting files. Keep any existing working page code until explicitly migrated.
4. Copy `tests/dashboard/test_phase2_skeleton.py` to the project `tests/dashboard/` folder.
5. The optional `.streamlit/config.toml` can be installed when no existing config exists. If one exists, merge the theme values and preserve unrelated settings.
6. Ensure your active `dubai-v2` environment includes Streamlit's programmatic navigation API (`st.Page` / `st.navigation`) and `pandas`/`pyarrow` for existing Phase 1 checks. Recommended Streamlit **>=1.37**.

Run from the repository root:

```powershell
conda activate dubai-v2
python -m pytest -q -W error
python scripts/audit_dashboard_artifacts.py --root . --out reports/tables/dashboard_phase1_inventory.json
streamlit run app.py
```

The Phase 2 shell shows its six navigation entries and research permission state. **Analytical data is intentionally not rendered.** A missing or failed Notebook 06 release validation must not appear as approved. The shell remains navigable and shows an evidence-withheld explanation.

## Separation of responsibilities

- `app.py`: entry point and native Streamlit navigation, no research analytics.
- `app/navigation.py`: six immutable page specifications.
- `app/runtime.py`: fail-closed, read-only Phase 1 `Permissions` / `validate_06_release_pair` integration.
- `app/components/`: presentation-only modules; HTML content is escaped.
- `app/theme/styles.py`: central CSS and responsiveness.
- `app/pages/`: six Phase 2 functional page shells; Phase 3 populates approved analytical content.
- `app_core/`: remains the existing Phase 1 scientific contract and approved-data boundary.

There are no new SQL queries, pipeline scripts, source modules, notebook edits, or statistical calculations.

## Scientific limitations preserved

Dashboard shell approval is **not** permission to display all 36 research claims. Claim-level authorization must be checked using `app.runtime.require_claim()` and existing Phase 1 metric access at the point of actual data presentation. Inconclusive RQ06 and not-estimable parking are not model outputs that may be displayed as reliable effects. A SUPPORTED or QUALIFIED RQ-level status does not authorize an unverified subclaim.

## Verification boundary

The current build environment may lack Streamlit/PyArrow and therefore cannot run a live server or inspect your Windows aggregate files. The automated Phase 2 tests exercise the page registry, presentation escaping, scientific gates, and six pages through a fake Streamlit interface. Run the local command above for a real launch; retain the Phase 1 artifact inventory as scientific acceptance evidence.
