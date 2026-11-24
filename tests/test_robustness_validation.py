"""Independent focused tests for notebook 06's actual (not copied) estimator functions.

These tests extract function definitions from the delivered notebook and exercise
small synthetic numerical oracles. They do NOT claim to verify the real DLD data.
"""
from __future__ import annotations

import ast
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

NOTEBOOK = Path(__file__).resolve().parents[1] / 'notebooks' / '06_Robustness_Validation.ipynb'


def _function(name: str, **bindings):
    notebook = json.loads(NOTEBOOK.read_text(encoding='utf-8'))
    for cell in notebook['cells']:
        if cell['cell_type'] != 'code':
            continue
        tree = ast.parse(''.join(cell['source']))
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name == name:
                isolated = ast.Module(body=[node], type_ignores=[])
                ns = {'np': np, 'pd': pd, **bindings}
                exec(compile(isolated, f'{NOTEBOOK.name}:{name}', 'exec'), ns)
                return ns[name]
    raise AssertionError(f'{name} not present in the delivered notebook')


def _small_raw():
    return pd.DataFrame({
        'transaction_id': [11, 12, 13, 14, 15],
        'instance_date': ['2025-01-01', '2025-03-01', '2025-05-01', '2026-01-01', '2025-06-01'],
        'price_aed': [1_000_000., 500_000., 0., 2_000_000., 1_200_000.],
        'area_sqm': [100., 50., 80., 200., 120.],
        'quality_flags': [0, 0, 0, 0, 4],
        'usage_label': ['Residential', 'Residential', 'Residential', 'Residential', 'Residential'],
        'property_type_label': ['Unit', 'Unit', 'Villa', 'Unit', 'Unit'],
        'reg_type_label': ['Ready', 'Off-Plan', 'Ready', 'Ready', 'Ready'],
        'area_id': [1., 1., 2., 1., 1.],
        'rooms_bucket': [1., 2., np.nan, 2., 1.],
        'has_parking': [True, False, None, True, None],
    })


def test_independent_cohort_flags_preserve_strict_and_2026_semantics():
    raw = _small_raw()
    fn = _function('independent_cohorts')
    flags, dates = fn(raw)
    assert flags.eligible_market_activity.tolist() == [True] * 5
    assert flags.eligible_residential_core.tolist() == [True, True, False, True, True]
    assert flags.eligible_residential_strict.tolist() == [True, True, False, True, False]
    assert flags.eligible_known_segment.tolist() == [True, True, False, True, False]
    assert flags.eligible_amenity_known.tolist() == [True, True, False, False, False]
    assert flags.eligible_2026_provisional.tolist() == [False, False, False, True, False]
    assert str(dates.dtype) == 'datetime64[ns, UTC]'


def test_reconstructed_strict_cohort_detects_duplicate_ids():
    raw = _small_raw(); raw.loc[1, 'transaction_id'] = 11
    flags, _ = _function('independent_cohorts')(raw)
    assert not flags.loc[0, 'eligible_market_activity']
    assert not flags.loc[1, 'eligible_market_activity']
    assert bool(flags.loc[3, 'eligible_2026_provisional'])


def _registration_frame():
    # Two supported cells with different effective pooled group weights.
    rows = []
    for area_id, ready_n, off_n, loggap in [(101, 35, 45, np.log(1.2)), (102, 42, 32, np.log(1.6))]:
        for reg, n, lg in [('Ready', ready_n, 0.), ('Off-Plan', off_n, loggap)]:
            for idx in range(n):
                rows.append({'area_id': float(area_id), 'audit_year': 2025,
                    'property_type_label': 'Unit', 'rooms_bucket': 1., 'audit_size_coarse': '50-100',
                    'reg_type_label': reg, 'audit_log_psm': lg, 'transaction_id': len(rows)+1})
    # Single-registration cell is deliberately excluded from matching.
    for _ in range(100):
        rows.append({'area_id': 103., 'audit_year': 2025, 'property_type_label': 'Villa',
                     'rooms_bucket': 2., 'audit_size_coarse': '100-200',
                     'reg_type_label': 'Ready', 'audit_log_psm': 10., 'transaction_id': len(rows)+1})
    return pd.DataFrame(rows)


def test_registration_gap_uses_only_supported_cells_and_pooled_weights():
    sample = _registration_frame()
    fn = _function('registration_gap_independent',
        frame_for=lambda *_: sample,
        _ratio=lambda n, d: 100 * n/d if d > 0 else np.nan)
    summary, strata = fn(threshold=30)
    assert summary.strata.iloc[0] == 2
    assert summary.communities.iloc[0] == 2
    assert summary.ready_n.iloc[0] == 35+42
    assert summary.offplan_n.iloc[0] == 45+32
    assert summary.ready_parent.iloc[0] == 35+42+100
    assert abs(strata.pooled_weight.sum()-1) < 1e-12
    expected = (80*np.log(1.2)+74*np.log(1.6))/(80+74)
    assert summary.log_gap.iloc[0] == pytest.approx(expected, abs=1e-12)
    assert summary.gap_pct.iloc[0] == pytest.approx(100*np.expm1(expected), abs=1e-10)


def test_registration_gap_empty_common_support_returns_no_estimate():
    sample = _registration_frame()
    fn = _function('registration_gap_independent',
        frame_for=lambda *_: sample,
        _ratio=lambda n, d: 100*n/d if d else np.nan)
    summary, strata = fn(threshold=300)
    assert summary.empty and strata.empty


def test_price_area_identity_on_within_group_regression():
    rng = np.random.default_rng(33)
    rows=[]
    for typ in ['Unit', 'Villa']:
        for area in [1, 2, 3]:
            for j in range(40):
                log_area = rng.uniform(3.6, 5.7)
                log_price = 12 + .85*log_area + .2*area
                rows.append({'property_type_label': typ, 'area_id': area,
                             'audit_year': 2025, 'reg_type_label': 'Ready',
                             'audit_log_area': log_area, 'audit_log_price': log_price,
                             'audit_log_psm': log_price-log_area})
    sample=pd.DataFrame(rows)
    fn=_function('size_model_identity', frame_for=lambda *_: sample)
    r=fn()
    assert len(r)==2
    assert np.allclose(r.total_price_beta, .85, atol=1e-12)
    assert np.allclose(r.psm_beta, -.15, atol=1e-12)
    assert np.allclose(r.identity_residual, 0., atol=1e-12)
