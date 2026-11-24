# V2 cleaning and feature stage: installation and verification

## Important source restriction

The three detailed QA reports `quality_flags.json`, `data_quality_yearly.csv`,
`psf_exceptions.csv` were **not supplied** in the conversation. The implementation
uses the previously supplied `validation_summary.json`, `column_profile.csv`,
`docs/research_plan.md`, and `docs/data_dictionary.md` plus existing
`src/loader.py` and `src/validation.py`. The detailed reports should be reviewed
**before treating final cohort rules as frozen**.

## Install from the extracted ZIP (project root, active dubai-v2 environment)

```powershell
$package = Join-Path $env:TEMP 'dubai_cleaning_features'
Expand-Archive -Path 'C:\Users\LOQ\OneDrive\Documents\dubai_v2_cleaning_features.zip' -DestinationPath $package -Force
Copy-Item "$package\src\cleaning.py" '.\src\cleaning.py' -Force
Copy-Item "$package\src\features.py" '.\src\features.py' -Force
Copy-Item "$package\tests\test_cleaning.py" '.\tests\test_cleaning.py' -Force
Copy-Item "$package\tests\test_features.py" '.\tests\test_features.py' -Force
Copy-Item "$package\tests\test_cleaning_snapshot.py" '.\tests\test_cleaning_snapshot.py' -Force
```

The two new unit test modules use a fixture named `source_frame` defined in the
included `tests/conftest.py`. The provided `conftest.py` retains the original
`valid_frame` fixture for prior tests. Back up and replace your existing
`tests/conftest.py` with the merged version **only if** it matches the previously
issued test suite and contains no local customization.

```powershell
Copy-Item '.\tests\conftest.py' '.\tests\conftest.py.bak' -Force
Copy-Item "$package\tests\conftest.py" '.\tests\conftest.py' -Force
python -m pytest -q -W error
```

Then run the research-population audit against the actual snapshot:

```powershell
@'
from pathlib import Path
from src.loader import load_and_validate
from src.cleaning import clean_transactions, cohort_audit
from src.features import engineer_features

raw, source, report = load_and_validate(strict=True)
cleaned = clean_transactions(raw)
featured = engineer_features(cleaned)
waterfall = cohort_audit(cleaned)
print('Source SHA256:', source.sha256)
print('Raw, cleaned, featured rows:', len(raw), len(cleaned), len(featured))
print(waterfall.to_string(index=False))
print('Unflagged population:', int((raw.quality_flags == 0).sum()))
print('Known parking in 2026:', int(cleaned.loc[cleaned.transaction_date.dt.year == 2026, 'has_parking'].notna().sum()))
path = Path('reports/tables/cohort_audit.csv')
path.parent.mkdir(parents=True, exist_ok=True)
waterfall.to_csv(path, index=False)
print('Saved:', path)
'@ | python -
```

The program does **not** write a cleaned Parquet file yet; review the cohort
counts and the three detailed QA reports before storing final research datasets.

## Design contract

- `clean_transactions(raw)`: preserves all raw records and fields; adds
  `transaction_date` and Boolean eligibility flags. Strict validation errors
  cause failure; ordinary source warnings do not trigger deletion.
- `cohort_audit(cleaned)`: transparent population counts. Each row explicitly
  identifies its parent population, rather than pretending all filters are one
  linear pipeline.
- `engineer_features(cleaned)`: computed price/sqm, calculated price/sqft,
  date dimensions, room/parking labels, registration features. Missing
  information remains missing. No arbitrary size bands or imputation.
- All project-wide source data remains unchanged.
