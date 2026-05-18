"""Generate paired delta uncertainty summaries from saved paper outputs."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

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
from experiments.metrics import crisis_classification_metrics  # noqa: E402


DEFAULT_BOOTSTRAPS = 500
DEFAULT_SEED = 20260518

CRISIS_REFERENCE = "frozen_calibrated_xgboost"
CRISIS_COMPARATORS = [
    "frozen_raw_xgboost_without_calibration",
    "historical_tail_threshold",
    "logistic_regression",
    "random_forest",
    "gradient_boosting",
]
CRISIS_METRICS = ["roc_auc", "pr_auc", "brier_score", "log_loss", "top_decile_lift"]

ALLOCATION_REFERENCE = "smart_policy_oos_guard"
ALLOCATION_COMPARATORS = [
    "equal_weight",
    "inverse_volatility",
    "mean_variance",
    "raw_black_litterman",
    "smart_policy",
]
ALLOCATION_METRICS = ["sharpe", "model_score", "benchmark_excess_return", "turnover"]

LOWER_IS_BETTER = {"brier_score", "log_loss", "turnover"}


def _finite_float(value: object) -> float:
    try:
        numeric = float(value)
    except Exception:
        return math.nan
    return numeric if np.isfinite(numeric) else math.nan


def _ci(values: list[float]) -> tuple[float, float, int]:
    finite = np.asarray([value for value in values if np.isfinite(value)], dtype=float)
    if finite.size == 0:
        return math.nan, math.nan, 0
    return float(np.percentile(finite, 2.5)), float(np.percentile(finite, 97.5)), int(finite.size)


def _delta(reference_value: float, comparator_value: float, metric: str) -> float:
    if not np.isfinite(reference_value) or not np.isfinite(comparator_value):
        return math.nan
    if metric in LOWER_IS_BETTER:
        return float(comparator_value - reference_value)
    return float(reference_value - comparator_value)


def _delta_formula(metric: str) -> str:
    if metric in LOWER_IS_BETTER:
        return "comparator - reference (positive means reference is lower/better)"
    return "reference - comparator (positive means reference is higher/better)"


def _interpretation(point_delta: float, ci_lower: float, ci_upper: float) -> str:
    if not np.isfinite(point_delta) or not np.isfinite(ci_lower) or not np.isfinite(ci_upper):
        return "undefined; metric or bootstrap interval is not finite"
    if ci_lower > 0.0:
        return "supports reference; percentile CI is entirely favorable"
    if ci_upper < 0.0:
        return "does not support reference; percentile CI is entirely unfavorable"
    if point_delta > 0.0:
        return "directionally favors reference, but CI crosses zero"
    if point_delta < 0.0:
        return "directionally favors comparator, but CI crosses zero"
    return "no directional difference; CI crosses zero"


def _require_columns(frame: pd.DataFrame, columns: set[str], name: str) -> None:
    missing = sorted(columns - set(frame.columns))
    if missing:
        raise ValueError(f"{name} is missing columns: {', '.join(missing)}")


def _validate_unique(frame: pd.DataFrame, keys: list[str], name: str) -> None:
    if frame.duplicated(keys).any():
        duplicate = frame.loc[frame.duplicated(keys, keep=False), keys].head(5)
        raise ValueError(f"{name} has duplicate rows for keys {keys}: {duplicate.to_dict('records')}")


def _load_required_csv(path: Path, required_columns: set[str]) -> pd.DataFrame:
    frame = read_csv_or_empty(path)
    if frame.empty:
        raise FileNotFoundError(f"required input is missing or empty: {path}")
    _require_columns(frame, required_columns, path.name)
    return frame


def _load_crisis_predictions(results_dir: Path, horizons: list[int]) -> pd.DataFrame:
    frames = []
    required = {"date", "horizon", "portfolio_name", "baseline", "tail_event", "probability"}
    for horizon in horizons:
        path = results_dir / f"baseline_predictions_h{int(horizon)}.csv"
        frame = _load_required_csv(path, required)
        frames.append(frame)
    predictions = pd.concat(frames, ignore_index=True)
    predictions["horizon"] = predictions["horizon"].astype(int)
    predictions["portfolio_name"] = predictions["portfolio_name"].astype(str)
    predictions["baseline"] = predictions["baseline"].astype(str)
    return predictions


def _validate_baseline_metrics(results_dir: Path) -> None:
    required = {
        "scope",
        "horizon",
        "portfolio_name",
        "baseline",
        "roc_auc",
        "pr_auc",
        "brier_score",
        "log_loss",
        "top_decile_lift",
    }
    frame = _load_required_csv(results_dir / "baseline_metrics.csv", required)
    expected = {CRISIS_REFERENCE, *CRISIS_COMPARATORS}
    observed = set(frame["baseline"].dropna().astype(str))
    missing = sorted(expected - observed)
    if missing:
        raise ValueError(f"baseline_metrics.csv does not contain expected baselines: {', '.join(missing)}")


def _load_allocation_metrics(results_dir: Path) -> pd.DataFrame:
    required = {"portfolio_name", "strategy", *ALLOCATION_METRICS}
    frame = _load_required_csv(results_dir / "allocation_oos_metrics.csv", required)
    frame["portfolio_name"] = frame["portfolio_name"].astype(str)
    frame["strategy"] = frame["strategy"].astype(str)
    return frame


def _crisis_metrics(frame: pd.DataFrame, probability_col: str) -> dict[str, float]:
    metrics = crisis_classification_metrics(
        frame["tail_event"].astype(int).to_numpy(),
        frame[probability_col].to_numpy(dtype=float),
    )
    return {metric: _finite_float(metrics.get(metric)) for metric in CRISIS_METRICS}


def _paired_prediction_frame(
    predictions: pd.DataFrame,
    *,
    horizon: int,
    reference: str,
    comparator: str,
) -> tuple[pd.DataFrame, dict[str, int]]:
    horizon_frame = predictions[predictions["horizon"].eq(int(horizon))].copy()
    reference_frame = horizon_frame[horizon_frame["baseline"].eq(reference)].copy()
    comparator_frame = horizon_frame[horizon_frame["baseline"].eq(comparator)].copy()
    keys = ["horizon", "portfolio_name", "date"]
    _validate_unique(reference_frame, keys, f"{reference} H{horizon} predictions")
    _validate_unique(comparator_frame, keys, f"{comparator} H{horizon} predictions")

    reference_units = set(reference_frame["portfolio_name"].dropna().astype(str))
    comparator_units = set(comparator_frame["portfolio_name"].dropna().astype(str))
    observed_units = reference_units | comparator_units

    reference_cols = keys + ["tail_event", "probability"]
    comparator_cols = keys + ["tail_event", "probability"]
    paired = reference_frame[reference_cols].merge(
        comparator_frame[comparator_cols],
        on=keys,
        how="inner",
        suffixes=("_reference", "_comparator"),
    )
    if not paired.empty and not paired["tail_event_reference"].equals(paired["tail_event_comparator"]):
        mismatch = paired.loc[
            ~paired["tail_event_reference"].eq(paired["tail_event_comparator"]),
            keys + ["tail_event_reference", "tail_event_comparator"],
        ].head(5)
        raise ValueError(
            f"tail_event mismatch between {reference} and {comparator} for H{horizon}: "
            f"{mismatch.to_dict('records')}"
        )
    if paired.empty:
        paired = pd.DataFrame(
            columns=keys + ["tail_event", "reference_probability", "comparator_probability"]
        )
    else:
        paired = paired.rename(
            columns={
                "tail_event_reference": "tail_event",
                "probability_reference": "reference_probability",
                "probability_comparator": "comparator_probability",
            }
        )
        paired = paired[keys + ["tail_event", "reference_probability", "comparator_probability"]]

    paired_units = set(paired["portfolio_name"].dropna().astype(str))
    counts = {
        "reference_unit_count": int(len(reference_units)),
        "comparator_unit_count": int(len(comparator_units)),
        "dropped_unit_count": int(len(observed_units) - len(paired_units)),
        "missing_reference_unit_count": int(len(comparator_units - reference_units)),
        "missing_comparator_unit_count": int(len(reference_units - comparator_units)),
        "reference_row_count": int(len(reference_frame)),
        "comparator_row_count": int(len(comparator_frame)),
        "paired_row_count": int(len(paired)),
        "reference_unpaired_row_count": int(len(reference_frame) - len(paired)),
        "comparator_unpaired_row_count": int(len(comparator_frame) - len(paired)),
    }
    return paired, counts


def _bootstrap_crisis_deltas(
    paired: pd.DataFrame,
    *,
    n_bootstrap: int,
    rng: np.random.Generator,
) -> dict[str, list[float]]:
    values: dict[str, list[float]] = {metric: [] for metric in CRISIS_METRICS}
    units = sorted(paired["portfolio_name"].dropna().astype(str).unique())
    if not units:
        return values
    groups = {unit: group for unit, group in paired.groupby("portfolio_name", sort=False)}
    for _ in range(int(n_bootstrap)):
        sampled_units = rng.choice(units, size=len(units), replace=True)
        sampled = pd.concat([groups[unit] for unit in sampled_units], ignore_index=True)
        reference_metrics = _crisis_metrics(sampled, "reference_probability")
        comparator_metrics = _crisis_metrics(sampled, "comparator_probability")
        for metric in CRISIS_METRICS:
            values[metric].append(_delta(reference_metrics[metric], comparator_metrics[metric], metric))
    return values


def paired_crisis_rows(
    predictions: pd.DataFrame,
    *,
    horizons: list[int],
    n_bootstrap: int = DEFAULT_BOOTSTRAPS,
    seed: int = DEFAULT_SEED,
    reference: str = CRISIS_REFERENCE,
    comparators: list[str] | None = None,
) -> list[dict[str, object]]:
    rng = np.random.default_rng(int(seed))
    rows: list[dict[str, object]] = []
    for horizon in horizons:
        for comparator in comparators or CRISIS_COMPARATORS:
            paired, counts = _paired_prediction_frame(
                predictions,
                horizon=int(horizon),
                reference=reference,
                comparator=comparator,
            )
            unit_count = int(paired["portfolio_name"].nunique()) if not paired.empty else 0
            if paired.empty:
                reference_metrics = {metric: math.nan for metric in CRISIS_METRICS}
                comparator_metrics = {metric: math.nan for metric in CRISIS_METRICS}
                boot = {metric: [] for metric in CRISIS_METRICS}
            else:
                reference_metrics = _crisis_metrics(paired, "reference_probability")
                comparator_metrics = _crisis_metrics(paired, "comparator_probability")
                boot = _bootstrap_crisis_deltas(paired, n_bootstrap=n_bootstrap, rng=rng)

            for metric in CRISIS_METRICS:
                point_delta = _delta(reference_metrics[metric], comparator_metrics[metric], metric)
                ci_lower, ci_upper, finite_bootstrap_count = _ci(boot.get(metric, []))
                rows.append(
                    {
                        "comparison_family": "crisis",
                        "horizon": f"H{int(horizon)}",
                        "reference": reference,
                        "comparator": comparator,
                        "metric": metric,
                        "point_delta": point_delta,
                        "ci_lower_2_5": ci_lower,
                        "ci_upper_97_5": ci_upper,
                        "unit_count": unit_count,
                        "dropped_unit_count": counts["dropped_unit_count"],
                        "missing_reference_unit_count": counts["missing_reference_unit_count"],
                        "missing_comparator_unit_count": counts["missing_comparator_unit_count"],
                        "reference_unit_count": counts["reference_unit_count"],
                        "comparator_unit_count": counts["comparator_unit_count"],
                        "paired_row_count": counts["paired_row_count"],
                        "reference_row_count": counts["reference_row_count"],
                        "comparator_row_count": counts["comparator_row_count"],
                        "reference_unpaired_row_count": counts["reference_unpaired_row_count"],
                        "comparator_unpaired_row_count": counts["comparator_unpaired_row_count"],
                        "n_bootstrap": int(n_bootstrap),
                        "finite_bootstrap_count": finite_bootstrap_count,
                        "seed": int(seed),
                        "delta_formula": _delta_formula(metric),
                        "positive_delta_means": "reference better",
                        "interpretation": _interpretation(point_delta, ci_lower, ci_upper),
                    }
                )
    return rows


def _paired_allocation_frame(
    allocation: pd.DataFrame,
    *,
    reference: str,
    comparator: str,
) -> tuple[pd.DataFrame, dict[str, int]]:
    reference_frame = allocation[allocation["strategy"].eq(reference)].copy()
    comparator_frame = allocation[allocation["strategy"].eq(comparator)].copy()
    _validate_unique(reference_frame, ["portfolio_name"], f"{reference} allocation metrics")
    _validate_unique(comparator_frame, ["portfolio_name"], f"{comparator} allocation metrics")

    reference_units = set(reference_frame["portfolio_name"].dropna().astype(str))
    comparator_units = set(comparator_frame["portfolio_name"].dropna().astype(str))
    observed_units = reference_units | comparator_units

    keep = ["portfolio_name"]
    if "market" in allocation.columns:
        keep.append("market")
    keep.extend(ALLOCATION_METRICS)
    paired = reference_frame[keep].merge(
        comparator_frame[keep],
        on="portfolio_name",
        how="inner",
        suffixes=("_reference", "_comparator"),
    )
    if "market_reference" in paired.columns and not paired["market_reference"].equals(paired["market_comparator"]):
        mismatch = paired.loc[
            ~paired["market_reference"].eq(paired["market_comparator"]),
            ["portfolio_name", "market_reference", "market_comparator"],
        ].head(5)
        raise ValueError(
            f"market mismatch between {reference} and {comparator}: {mismatch.to_dict('records')}"
        )

    paired_units = set(paired["portfolio_name"].dropna().astype(str))
    counts = {
        "reference_unit_count": int(len(reference_units)),
        "comparator_unit_count": int(len(comparator_units)),
        "dropped_unit_count": int(len(observed_units) - len(paired_units)),
        "missing_reference_unit_count": int(len(comparator_units - reference_units)),
        "missing_comparator_unit_count": int(len(reference_units - comparator_units)),
        "paired_row_count": int(len(paired)),
        "reference_row_count": int(len(reference_frame)),
        "comparator_row_count": int(len(comparator_frame)),
    }
    return paired, counts


def _allocation_metric_deltas(paired: pd.DataFrame, metric: str) -> np.ndarray:
    reference_values = paired[f"{metric}_reference"].map(_finite_float).to_numpy(dtype=float)
    comparator_values = paired[f"{metric}_comparator"].map(_finite_float).to_numpy(dtype=float)
    deltas = np.asarray(
        [_delta(reference_value, comparator_value, metric) for reference_value, comparator_value in zip(reference_values, comparator_values)],
        dtype=float,
    )
    return deltas[np.isfinite(deltas)]


def _bootstrap_mean_deltas(
    deltas: np.ndarray,
    *,
    n_bootstrap: int,
    rng: np.random.Generator,
) -> list[float]:
    if deltas.size == 0:
        return []
    values: list[float] = []
    for _ in range(int(n_bootstrap)):
        sampled = rng.choice(deltas, size=deltas.size, replace=True)
        values.append(float(np.mean(sampled)))
    return values


def paired_allocation_rows(
    allocation: pd.DataFrame,
    *,
    n_bootstrap: int = DEFAULT_BOOTSTRAPS,
    seed: int = DEFAULT_SEED,
    reference: str = ALLOCATION_REFERENCE,
    comparators: list[str] | None = None,
) -> list[dict[str, object]]:
    rng = np.random.default_rng(int(seed))
    rows: list[dict[str, object]] = []
    for comparator in comparators or ALLOCATION_COMPARATORS:
        paired, counts = _paired_allocation_frame(
            allocation,
            reference=reference,
            comparator=comparator,
        )
        for metric in ALLOCATION_METRICS:
            deltas = _allocation_metric_deltas(paired, metric) if not paired.empty else np.asarray([], dtype=float)
            point_delta = float(np.mean(deltas)) if deltas.size else math.nan
            boot = _bootstrap_mean_deltas(deltas, n_bootstrap=n_bootstrap, rng=rng)
            ci_lower, ci_upper, finite_bootstrap_count = _ci(boot)
            rows.append(
                {
                    "comparison_family": "allocation",
                    "horizon": "",
                    "reference": reference,
                    "comparator": comparator,
                    "metric": metric,
                    "point_delta": point_delta,
                    "ci_lower_2_5": ci_lower,
                    "ci_upper_97_5": ci_upper,
                    "unit_count": int(deltas.size),
                    "dropped_unit_count": counts["dropped_unit_count"],
                    "missing_reference_unit_count": counts["missing_reference_unit_count"],
                    "missing_comparator_unit_count": counts["missing_comparator_unit_count"],
                    "reference_unit_count": counts["reference_unit_count"],
                    "comparator_unit_count": counts["comparator_unit_count"],
                    "paired_row_count": counts["paired_row_count"],
                    "reference_row_count": counts["reference_row_count"],
                    "comparator_row_count": counts["comparator_row_count"],
                    "reference_unpaired_row_count": counts["reference_row_count"] - counts["paired_row_count"],
                    "comparator_unpaired_row_count": counts["comparator_row_count"] - counts["paired_row_count"],
                    "n_bootstrap": int(n_bootstrap),
                    "finite_bootstrap_count": finite_bootstrap_count,
                    "seed": int(seed),
                    "delta_formula": _delta_formula(metric),
                    "positive_delta_means": "reference better",
                    "interpretation": _interpretation(point_delta, ci_lower, ci_upper),
                }
            )
    return rows


def paired_delta_rows(
    results_dir: Path,
    horizons: list[int],
    n_bootstrap: int = DEFAULT_BOOTSTRAPS,
    seed: int = DEFAULT_SEED,
) -> list[dict[str, object]]:
    _validate_baseline_metrics(results_dir)
    predictions = _load_crisis_predictions(results_dir, horizons)
    allocation = _load_allocation_metrics(results_dir)
    rows = paired_crisis_rows(
        predictions,
        horizons=horizons,
        n_bootstrap=n_bootstrap,
        seed=seed,
    )
    rows.extend(
        paired_allocation_rows(
            allocation,
            n_bootstrap=n_bootstrap,
            seed=seed,
        )
    )
    return rows


def paired_delta_table(summary: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "comparison_family",
        "horizon",
        "reference",
        "comparator",
        "metric",
        "point_delta",
        "ci_lower_2_5",
        "ci_upper_97_5",
        "unit_count",
        "dropped_unit_count",
        "n_bootstrap",
        "delta_formula",
        "interpretation",
    ]
    if summary.empty:
        return pd.DataFrame(columns=columns)
    table = summary[columns].copy()
    return table.sort_values(["comparison_family", "horizon", "comparator", "metric"], na_position="first")


def write_paper_table(table: pd.DataFrame, paper_dir: Path) -> Path:
    note = (
        "Paired deltas use inner-joined saved outputs with portfolio_name as the bootstrap unit "
        f"and {DEFAULT_SEED} as the default seed. Positive point_delta always means the reference "
        "is better: reference minus comparator for higher-is-better metrics, and comparator minus "
        "reference for brier_score, log_loss, and turnover. Intervals are percentile bootstrap "
        "2.5/97.5 bounds; rows whose intervals cross zero should be treated as suggestive only."
    )
    path = paper_dir / "table_paired_delta_summary.md"
    write_markdown(
        path,
        "Table 8. Paired Delta Uncertainty Summary",
        table,
        note,
        empty_message="No paired delta rows were produced for this result directory.",
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
        paired_delta_rows(
            results_dir=results_dir,
            horizons=horizons,
            n_bootstrap=n_bootstrap,
            seed=seed,
        )
    )
    results_path = dataframe_to_csv(summary, results_dir / "paired_delta_summary.csv")
    table = paired_delta_table(summary)
    table_path = dataframe_to_csv(table, tables_dir / "table_paired_delta_summary.csv")
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
    parser = argparse.ArgumentParser(description="Build paired delta uncertainty from saved paper result files.")
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
