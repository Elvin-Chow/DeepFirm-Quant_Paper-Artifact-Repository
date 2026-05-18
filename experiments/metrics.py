"""Metrics used by the paper experiment scripts."""

from __future__ import annotations

import math
from typing import Iterable, Sequence

import numpy as np
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    log_loss,
    precision_score,
    recall_score,
    roc_auc_score,
)

from backend.services import PortfolioAnalysisService
from models.risk_engine import RiskEngine


def _as_float_array(values: Sequence[float] | np.ndarray) -> np.ndarray:
    return np.asarray(values, dtype=float).reshape(-1)


def _safe_nan(value: object) -> float:
    try:
        numeric = float(value)
    except Exception:
        return math.nan
    return numeric if np.isfinite(numeric) else math.nan


def expected_calibration_error(
    y_true: Sequence[int] | np.ndarray,
    probabilities: Sequence[float] | np.ndarray,
    n_bins: int = 10,
) -> float:
    """Compute equal-width expected calibration error."""
    y = _as_float_array(y_true)
    p = np.clip(_as_float_array(probabilities), 0.0, 1.0)
    if y.size == 0 or p.size == 0 or y.size != p.size:
        return math.nan
    bins = np.linspace(0.0, 1.0, int(n_bins) + 1)
    total = float(y.size)
    ece = 0.0
    for idx in range(int(n_bins)):
        left = bins[idx]
        right = bins[idx + 1]
        if idx == int(n_bins) - 1:
            mask = (p >= left) & (p <= right)
        else:
            mask = (p >= left) & (p < right)
        if not mask.any():
            continue
        ece += float(mask.mean()) * abs(float(y[mask].mean()) - float(p[mask].mean()))
    return float(ece) if total > 0 else math.nan


def top_decile_lift(
    y_true: Sequence[int] | np.ndarray,
    probabilities: Sequence[float] | np.ndarray,
) -> float:
    y = _as_float_array(y_true)
    p = _as_float_array(probabilities)
    if y.size == 0 or y.size != p.size:
        return math.nan
    base_rate = float(y.mean())
    if base_rate <= 0.0:
        return math.nan
    n_top = max(1, int(math.ceil(0.10 * y.size)))
    order = np.argsort(-p)
    return float(y[order[:n_top]].mean() / base_rate)


def crisis_classification_metrics(
    y_true: Sequence[int] | np.ndarray,
    probabilities: Sequence[float] | np.ndarray,
    threshold: float = 0.60,
) -> dict[str, float]:
    """Return paper metrics, preserving NaN when a metric is undefined."""
    y = _as_float_array(y_true).astype(int)
    p = np.clip(_as_float_array(probabilities), 1e-9, 1.0 - 1e-9)
    if y.size != p.size:
        raise ValueError("y_true and probabilities must have the same length")

    result: dict[str, float] = {
        "row_count": float(y.size),
        "positive_event_count": float(y.sum()) if y.size else 0.0,
        "positive_rate": float(y.mean()) if y.size else math.nan,
        "roc_auc": math.nan,
        "pr_auc": math.nan,
        "brier_score": math.nan,
        "log_loss": math.nan,
        "calibration_error": math.nan,
        "precision_at_0_60": math.nan,
        "recall_at_0_60": math.nan,
        "top_decile_lift": math.nan,
    }
    if y.size == 0:
        return result

    predictions = (p >= float(threshold)).astype(int)
    result["precision_at_0_60"] = float(precision_score(y, predictions, zero_division=0))
    result["recall_at_0_60"] = float(recall_score(y, predictions, zero_division=0))
    result["brier_score"] = float(brier_score_loss(y, p))
    result["log_loss"] = float(log_loss(y, p, labels=[0, 1]))
    result["calibration_error"] = expected_calibration_error(y, p)
    result["top_decile_lift"] = top_decile_lift(y, p)
    if np.unique(y).size == 2:
        result["roc_auc"] = float(roc_auc_score(y, p))
        result["pr_auc"] = float(average_precision_score(y, p))
    return result


def crisis_metric_rows(
    predictions: pd.DataFrame,
    group_cols: Iterable[str],
    probability_col: str = "crisis_probability",
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    if predictions.empty:
        return rows
    for group_key, group in predictions.groupby(list(group_cols), sort=True, dropna=False):
        if not isinstance(group_key, tuple):
            group_key = (group_key,)
        row = {column: value for column, value in zip(group_cols, group_key)}
        metrics = crisis_classification_metrics(
            group["tail_event"].astype(int).to_numpy(),
            group[probability_col].to_numpy(dtype=float),
        )
        row.update(metrics)
        rows.append(row)
    return rows


def strategy_performance_metrics(
    dates: pd.DatetimeIndex,
    strategy_daily: Sequence[float] | np.ndarray,
    benchmark_daily: Sequence[float] | np.ndarray,
    turnover: float = 0.0,
    risk_free_rate: float = 0.0,
) -> dict[str, object]:
    """Compute paper OOS allocation metrics for one strategy."""
    strategy_arr = _as_float_array(strategy_daily)
    benchmark_arr = _as_float_array(benchmark_daily)
    if strategy_arr.size != benchmark_arr.size:
        raise ValueError("strategy and benchmark daily returns must have the same length")
    if strategy_arr.size != len(dates):
        raise ValueError("dates length must match return arrays")

    strategy_frame = pd.DataFrame({"strategy": strategy_arr}, index=dates)
    benchmark_frame = pd.DataFrame({"benchmark": benchmark_arr}, index=dates)
    strategy_metrics = RiskEngine.compute_performance_metrics(
        strategy_frame,
        np.array([1.0]),
        risk_free_rate=risk_free_rate,
    )
    benchmark_metrics = RiskEngine.compute_performance_metrics(
        benchmark_frame,
        np.array([1.0]),
        risk_free_rate=risk_free_rate,
    )
    scored = PortfolioAnalysisService.score_oos_metrics(
        strategy_metrics,
        strategy_arr,
        benchmark_arr,
        benchmark_metrics,
    )
    score_payload = scored["score"]
    return {
        "row_count": int(strategy_arr.size),
        "cumulative_return": _safe_nan(strategy_metrics["cumulative_returns"][-1]),
        "benchmark_cumulative_return": _safe_nan(benchmark_metrics["cumulative_returns"][-1]),
        "benchmark_excess_return": _safe_nan(scored["excess_return"]),
        "annualized_return": _safe_nan(strategy_metrics["annualized_return"]),
        "annualized_volatility": _safe_nan(strategy_metrics["annualized_volatility"]),
        "max_drawdown": _safe_nan(strategy_metrics["max_drawdown"]),
        "expected_shortfall": _safe_nan(strategy_metrics["expected_shortfall"]),
        "sharpe": _safe_nan(strategy_metrics["sharpe_ratio"]),
        "information_ratio": _safe_nan(scored["information_ratio"]),
        "turnover": _safe_nan(turnover),
        "model_score": _safe_nan(score_payload.get("total_score")),
        "model_grade": str(score_payload.get("grade", "")),
        "model_score_risk_control": _safe_nan(score_payload.get("risk_control")),
        "model_score_profitability": _safe_nan(score_payload.get("profitability")),
        "model_score_alpha": _safe_nan(score_payload.get("alpha_capability")),
        "model_score_stability": _safe_nan(score_payload.get("stability")),
        "model_score_win_rate": _safe_nan(score_payload.get("win_rate")),
    }


def cumulative_from_log_returns(daily_returns: Sequence[float] | np.ndarray) -> np.ndarray:
    arr = _as_float_array(daily_returns)
    return np.exp(np.cumsum(arr)) - 1.0

