"""Research presentation utilities; plotting never creates research estimates.

All data, eligible populations, confidence intervals, coverage flags and labels
must be supplied by callers. No implicit sample selection or smoothing.
Matplotlib is imported lazily; functions return figures without showing them.
"""
from __future__ import annotations

from pathlib import Path
from typing import Sequence

import numpy as np
import pandas as pd


def _plt():
    import matplotlib.pyplot as plt
    return plt


def _required(frame: pd.DataFrame, *columns: str) -> None:
    if not isinstance(frame, pd.DataFrame) or not frame.columns.is_unique:
        raise ValueError("Expected DataFrame with unique columns")
    missing = set(columns) - set(frame.columns)
    if missing:
        raise ValueError(f"Missing plot columns: {sorted(missing)}")


def save_figure(fig, destination: str | Path, *, dpi: int = 160, close: bool = False) -> Path:
    """Save an existing Matplotlib Figure; never mutate source data.

    Only creates the explicitly requested destination's parent directory.
    Does not silently overwrite other research artifacts.
    """
    from matplotlib.figure import Figure
    if not isinstance(fig, Figure):
        raise TypeError("fig must be a matplotlib.figure.Figure")
    if isinstance(dpi, bool) or not isinstance(dpi, int) or dpi < 50:
        raise ValueError("dpi must be an integer >= 50")
    p = Path(destination).expanduser()
    if p.suffix.lower() not in {".png", ".svg", ".pdf"}:
        raise ValueError("Supported output extensions are .png, .svg and .pdf")
    p.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(p, dpi=dpi, bbox_inches="tight")
    if close:
        _plt().close(fig)
    return p


def plot_coverage(frame: pd.DataFrame, *, category: str, numerator: str, denominator: str, title: str, ax=None):
    """Plot *provided* matched/population counts, distinguishing undefined coverage.

    A zero denominator has no bar, not zero-percent coverage. Returns (fig, ax).
    """
    _required(frame, category, numerator, denominator)
    if frame[category].duplicated().any():
        raise ValueError("Category labels must be unique for this plot")
    a = pd.to_numeric(frame[numerator], errors="coerce").to_numpy(dtype=float)
    b = pd.to_numeric(frame[denominator], errors="coerce").to_numpy(dtype=float)
    if not (np.isfinite(a).all() and np.isfinite(b).all()) or (a < 0).any() or (b < 0).any() or (a > b).any():
        raise ValueError("Require finite 0 <= numerator <= denominator")
    values = np.divide(100*a, b, out=np.full(len(a), np.nan), where=b > 0)
    plt = _plt()
    if ax is None:
        fig, ax = plt.subplots(figsize=(max(7, min(16, 0.55 * len(a) + 3)), 4.8))
    else:
        fig = ax.figure
    xx = np.arange(len(frame))
    ax.bar(xx[np.isfinite(values)], values[np.isfinite(values)])
    for i in np.flatnonzero(~np.isfinite(values)):
        ax.text(i, 2, "N/A", ha="center", va="bottom", rotation=90, fontsize=8)
    ax.set_xticks(xx, frame[category].astype(str), rotation=45, ha="right")
    ax.set_ylim(0, 105)
    ax.set_ylabel("Observed coverage (%)")
    ax.set_title(title)
    ax.grid(axis="y", alpha=0.2)
    fig.tight_layout()
    return fig, ax


def plot_observed_series(frame: pd.DataFrame, *, x: str, y: str, title: str, ylabel: str, connect_consecutive: bool = False, ax=None):
    """Plot observed points; default does NOT imply values between observations.

    If connect_consecutive=True, x must be numeric years and only genuinely
    consecutive years with nonmissing y will be joined. Never interpolates.
    """
    _required(frame, x, y)
    if frame[x].isna().any() or frame[x].duplicated().any():
        raise ValueError("Series x must be complete and unique")
    d = frame[[x, y]].sort_values(x).copy()
    yr = pd.to_numeric(d[x], errors="coerce").to_numpy(dtype=float)
    val = pd.to_numeric(d[y], errors="coerce").to_numpy(dtype=float)
    if not np.isfinite(yr).all() or np.isinf(val).any():
        raise ValueError("Year and values must be numeric; y may be missing but not infinite")
    plt = _plt()
    if ax is None:
        fig, ax = plt.subplots(figsize=(9, 4.5))
    else:
        fig = ax.figure
    ax.scatter(yr[np.isfinite(val)], val[np.isfinite(val)], zorder=3)
    if connect_consecutive:
        if (yr != np.round(yr)).any():
            raise ValueError("Consecutive links require integer calendar years")
        for i in range(1, len(yr)):
            if yr[i] - yr[i-1] == 1 and np.isfinite(val[i]) and np.isfinite(val[i-1]):
                ax.plot(yr[i-1:i+1], val[i-1:i+1], linewidth=1.4)
    ax.set(xlabel="Calendar year", ylabel=ylabel, title=title)
    ax.grid(alpha=0.2)
    fig.tight_layout()
    return fig, ax


def plot_conditional_intervals(frame: pd.DataFrame, *, label: str, estimate: str, low: str, high: str, title: str, xlabel: str = "Estimated change (%)", ax=None):
    """Plot precomputed conditional intervals, not significance/rank claims.

    Missing intervals remain visually withheld rather than being drawn at zero.
    """
    _required(frame, label, estimate, low, high)
    d = frame[[label, estimate, low, high]].copy()
    if d[label].isna().any() or d[label].duplicated().any():
        raise ValueError("Interval labels must be unique and nonmissing")
    for c in [estimate, low, high]:
        d[c] = pd.to_numeric(d[c], errors="coerce")
    known = d[[estimate, low, high]].notna().all(axis=1)
    a, lo, hi = (d.loc[known, c].to_numpy(dtype=float) for c in [estimate, low, high])
    if not (np.isfinite(a).all() and np.isfinite(lo).all() and np.isfinite(hi).all()) or (lo > a).any() or (hi < a).any():
        raise ValueError("Intervals must be finite and contain the point estimate")
    plt = _plt()
    if ax is None:
        fig, ax = plt.subplots(figsize=(9, max(3.5, 0.38 * len(d) + 1.8)))
    else:
        fig = ax.figure
    yy = np.arange(len(d))
    ax.errorbar(a, yy[known.to_numpy()], xerr=np.vstack([a - lo, hi - a]), fmt="o", capsize=3, linestyle="none")
    for i in np.flatnonzero(~known.to_numpy()):
        ax.text(0, i, "not estimable", color="gray", va="center", fontsize=8)
    ax.axvline(0, color="gray", linestyle="--", linewidth=0.8)
    ax.set_yticks(yy, d[label].astype(str))
    ax.invert_yaxis()
    ax.set(xlabel=xlabel, title=title)
    ax.grid(axis="x", alpha=0.2)
    fig.tight_layout()
    return fig, ax


def plot_budget_curve(frame: pd.DataFrame, *, budget_col: str = "budget_aed", share_col: str = "share_pct", group_col: str = "community", title: str = "Nominal recorded-sale budget distribution", ax=None):
    """Show *provided* cumulative budget shares with monotonicity checks."""
    _required(frame, budget_col, share_col, group_col)
    plt = _plt()
    if ax is None:
        fig, ax = plt.subplots(figsize=(9, 5))
    else:
        fig = ax.figure
    for group, part in frame.groupby(group_col, observed=True, dropna=False):
        sub = part.sort_values(budget_col)
        x = pd.to_numeric(sub[budget_col], errors="coerce").to_numpy(dtype=float)
        y = pd.to_numeric(sub[share_col], errors="coerce").to_numpy(dtype=float)
        if not (np.isfinite(x).all() and np.isfinite(y).all()) or np.any(np.diff(x) <= 0) or np.any(np.diff(y) < -1e-9) or np.any((y < 0) | (y > 100)):
            raise ValueError(f"Invalid cumulative budget curve for {group}")
        ax.plot(x, y, marker="o", label=str(group))
    ax.set(xlabel="Recorded transaction price threshold (AED)", ylabel="Share at or below threshold (%)", title=title, ylim=(0, 105))
    ax.legend(fontsize=8)
    ax.grid(alpha=0.2)
    fig.tight_layout()
    return fig, ax
