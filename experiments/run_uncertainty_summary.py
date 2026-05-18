"""Generate cross-portfolio uncertainty summaries from saved paper results."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, brier_score_loss, log_loss, roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.common import (  # noqa: E402
    DEFAULT_CONFIG_PATH,
    DEFAULT_RESULTS_DIR,
    DEFAULT_TABLES_DIR,
    dataframe_to_csv,
    horizons_from_config,
    load_config,
    output_dir_from_args,
    project_path,
)
from experiments.make_paper_tables import read_csv_or_empty, write_markdown  # noqa: E402
from experiments.metrics import top_decile_lift  # noqa: E402


DEFAULT_BOOTSTRAPS = 500
DEFAULT_SEED = 20260518


def _safe_metric(value: float) -> float:
    return float(value) if np.isfinite(value) else math.nan


def _ci(values: list[float]) -> tuple[float, float]:
    finite = np.asarray([value for value in values if np.isfinite(value)], dtype=float)
    if finite.size == 0:
        return math.nan, math.nan
    return float(np.percentile(finite, 2.5)), float(np.percentile(finite, 97.5))


def _crisis_metrics(frame: pd.DataFrame) -> dict[str, float]:
    if frame.empty:
        return {
            "roc_auc": math.nan,
            "pr_auc": math.nan,
            "top_decile_lift": math.nan,
            "brier_score": math.nan,
            "log_loss": math.nan,
        }
    y = frame["tail_event"].astype(int).to_numpy()
    p = np.clip(frame["crisis_probability"].astype(float).to_numpy(), 1e-9, 1.0 - 1e-9)
    result = {
        "roc_auc": math.nan,
        "pr_auc": math.nan,
        "top_decile_lift": _safe_metric(top_decile_lift(y, p)),
        "brier_score": _safe_metric(brier_score_loss(y, p)),
        "log_loss": _safe_metric(log_loss(y, p, labels=[0, 1])),
    }
    if np.unique(y).size == 2:
        result["roc_auc"] = _safe_metric(roc_auc_score(y, p))
        result["pr_auc"] = _safe_metric(average_precision_score(y, p))
    return result


def _bootstrap_by_unit(
    frame: pd.DataFrame,
    unit_col: str,
    metric_fn: Callable[[pd.DataFrame], dict[str, float]],
    n_bootstrap: int,
    rng: np.random.Generator,
) -> dict[str, list[float]]:
    units = sorted(frame[unit_col].dropna().astype(str).unique())
    values: dict[str, list[float]] = {}
    if not units:
        return values
    groups = {unit: group for unit, group in frame.groupby(unit_col, sort=False)}
    for _ in range(int(n_bootstrap)):
        sampled_units = rng.choice(units, size=len(units), replace=True)
        sampled = pd.concat([groups[unit] for unit in sampled_units], ignore_index=True)
        metrics = metric_fn(sampled)
        for metric, value in metrics.items():
            values.setdefault(metric, []).append(value)
    return values


def _summary_rows(
    *,
    task: str,
    group: str,
    frame: pd.DataFrame,
    unit_col: str,
    metric_fn: Callable[[pd.DataFrame], dict[str, float]],
    n_bootstrap: int,
    rng: np.random.Generator,
    method: str,
) -> list[dict[str, object]]:
    point = metric_fn(frame)
    boot = _bootstrap_by_unit(frame, unit_col, metric_fn, n_bootstrap=n_bootstrap, rng=rng)
    unit_count = int(frame[unit_col].nunique()) if unit_col in frame.columns else 0
    rows = []
    for metric, point_estimate in point.items():
        lower, upper = _ci(boot.get(metric, []))
        rows.append(
            {
                "task": task,
                "group": group,
                "metric": metric,
                "point_estimate": point_estimate,
                "ci_lower": lower,
                "ci_upper": upper,
                "unit_count": unit_count,
                "row_count": int(len(frame)),
                "n_bootstrap": int(n_bootstrap),
                "method": method,
            }
        )
    return rows


def _load_crisis_predictions(results_dir: Path, horizons: list[int]) -> pd.DataFrame:
    frames = []
    for horizon in horizons:
        frame = read_csv_or_empty(results_dir / f"crisis_predictions_h{horizon}.csv")
        if not frame.empty:
            frames.append(frame)
    if not frames:
        return pd.DataFrame()
    predictions = pd.concat(frames, ignore_index=True)
    required = {"horizon", "portfolio_name", "tail_event", "crisis_probability"}
    missing = sorted(required - set(predictions.columns))
    if missing:
        raise ValueError(f"crisis prediction CSVs are missing columns: {', '.join(missing)}")
    return predictions


def _allocation_metric_fn(frame: pd.DataFrame) -> dict[str, float]:
    metrics = ["sharpe", "model_score", "benchmark_excess_return"]
    return {metric: _safe_metric(frame[metric].astype(float).mean()) for metric in metrics if metric in frame.columns}


def uncertainty_rows(
    results_dir: Path,
    horizons: list[int],
    n_bootstrap: int = DEFAULT_BOOTSTRAPS,
    seed: int = DEFAULT_SEED,
) -> list[dict[str, object]]:
    rng = np.random.default_rng(int(seed))
    rows: list[dict[str, object]] = []

    predictions = _load_crisis_predictions(results_dir, horizons)
    if not predictions.empty:
        for horizon, group in predictions.groupby("horizon", sort=True):
            rows.extend(
                _summary_rows(
                    task="crisis_warning",
                    group=f"horizon_{int(horizon)}d",
                    frame=group,
                    unit_col="portfolio_name",
                    metric_fn=_crisis_metrics,
                    n_bootstrap=n_bootstrap,
                    rng=rng,
                    method="portfolio bootstrap percentile CI over saved frozen-artifact predictions",
                )
            )

    allocation = read_csv_or_empty(results_dir / "allocation_oos_metrics.csv")
    if not allocation.empty:
        required = {"strategy", "portfolio_name"}
        missing = sorted(required - set(allocation.columns))
        if missing:
            raise ValueError(f"allocation_oos_metrics.csv is missing columns: {', '.join(missing)}")
        for strategy, group in allocation.groupby("strategy", sort=True):
            rows.extend(
                _summary_rows(
                    task="allocation",
                    group=str(strategy),
                    frame=group,
                    unit_col="portfolio_name",
                    metric_fn=_allocation_metric_fn,
                    n_bootstrap=n_bootstrap,
                    rng=rng,
                    method="portfolio bootstrap percentile CI over saved OOS metric rows",
                )
            )
    return rows


def uncertainty_table(summary: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "task",
        "group",
        "metric",
        "point_estimate",
        "ci_lower",
        "ci_upper",
        "unit_count",
        "row_count",
        "n_bootstrap",
        "method",
    ]
    if summary.empty:
        return pd.DataFrame(columns=columns)
    table = summary[columns].copy()
    return table.sort_values(["task", "group", "metric"])


def write_paper_table(table: pd.DataFrame, paper_dir: Path) -> Path:
    note = (
        "Uncertainty intervals are 2.5th to 97.5th percentile cross-portfolio bootstrap "
        "intervals over saved real-data outputs. Crisis rows resample portfolios within each "
        "horizon without retraining frozen artifacts. Allocation rows resample portfolio-level "
        "OOS metric rows within each strategy. Wide intervals should be read as limited applied "
        "evidence, not universal superiority."
    )
    path = paper_dir / "table_uncertainty_summary.md"
    write_markdown(
        path,
        "Table 7. Cross-Portfolio Uncertainty Summary",
        table,
        note,
        empty_message="No uncertainty rows were produced for this result directory.",
    )
    return path


def run(
    config: dict[str, Any],
    results_dir: Path,
    tables_dir: Path,
    paper_dir: Path,
    n_bootstrap: int = DEFAULT_BOOTSTRAPS,
    seed: int = DEFAULT_SEED,
) -> dict[str, Any]:
    horizons = horizons_from_config(config)
    summary = pd.DataFrame(
        uncertainty_rows(
            results_dir=results_dir,
            horizons=horizons,
            n_bootstrap=n_bootstrap,
            seed=seed,
        )
    )
    results_path = dataframe_to_csv(summary, results_dir / "uncertainty_summary.csv")
    table = uncertainty_table(summary)
    table_path = dataframe_to_csv(table, tables_dir / "table_uncertainty_summary.csv")
    paper_path = write_paper_table(table, paper_dir)
    return {
        "summary_rows": int(len(summary)),
        "table_rows": int(len(table)),
        "results_path": str(results_path),
        "table_path": str(table_path),
        "paper_path": str(paper_path),
        "n_bootstrap": int(n_bootstrap),
        "seed": int(seed),
    }


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build uncertainty summaries from saved paper result files.")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH))
    parser.add_argument("--results-dir", default=None)
    parser.add_argument("--tables-dir", default=None)
    parser.add_argument("--paper-dir", default=str(ROOT / "paper"))
    parser.add_argument("--bootstraps", type=int, default=DEFAULT_BOOTSTRAPS)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    return parser


def main() -> int:
    args = make_parser().parse_args()
    config = load_config(args.config)
    results_dir = output_dir_from_args(args.results_dir, config, key="results_dir", default=DEFAULT_RESULTS_DIR)
    tables_dir = output_dir_from_args(args.tables_dir, config, key="tables_dir", default=DEFAULT_TABLES_DIR)
    summary = run(
        config=config,
        results_dir=project_path(results_dir),
        tables_dir=project_path(tables_dir),
        paper_dir=project_path(args.paper_dir),
        n_bootstrap=args.bootstraps,
        seed=args.seed,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
