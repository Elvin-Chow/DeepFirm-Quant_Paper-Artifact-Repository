"""Build paper-ready CSV and Markdown tables from experiment result files."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd
from pandas.errors import EmptyDataError

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.common import (  # noqa: E402
DEFAULT_CONFIG_PATH,
    DEFAULT_RESULTS_DIR,
    DEFAULT_TABLES_DIR,
    dataframe_to_csv,
    load_config,
    output_dir_from_args,
    project_path,
)


DEFAULT_PAPER_DIR = ROOT / "paper"


def read_csv_or_empty(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path, low_memory=False)
    except EmptyDataError:
        return pd.DataFrame()


def _format_value(value: object) -> str:
    if pd.isna(value):
        return ""
    if isinstance(value, float):
        if abs(value) >= 1000:
            return f"{value:,.0f}"
        return f"{value:.4f}"
    return str(value)


def markdown_table(frame: pd.DataFrame, empty_message: str = "No table rows were produced.") -> str:
    if frame.empty:
        return f"| status |\n|---|\n| {empty_message} |\n"
    columns = [str(column) for column in frame.columns]
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for _, row in frame.iterrows():
        lines.append("| " + " | ".join(_format_value(row[column]) for column in frame.columns) + " |")
    return "\n".join(lines) + "\n"


def write_markdown(
    path: Path,
    title: str,
    frame: pd.DataFrame,
    note: str = "",
    empty_message: str = "No table rows were produced.",
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    parts = [f"# {title}", "", markdown_table(frame, empty_message=empty_message)]
    if note:
        parts.extend(["", f"Note: {note}"])
    path.write_text("\n".join(parts).rstrip() + "\n", encoding="utf-8")


def _fmt_int(value: int | float | None) -> str:
    if value is None or pd.isna(value):
        return "0"
    return f"{int(value):,}"


def _unique_strings(frame: pd.DataFrame, column: str) -> list[str]:
    if frame.empty or column not in frame.columns:
        return []
    values = []
    for value in frame[column].dropna().astype(str):
        value = value.strip()
        if value and value not in values:
            values.append(value)
    return sorted(values)


def _horizon_label(values: list[int]) -> str:
    if not values:
        return "the configured horizons"
    labels = [f"{value}D" for value in sorted(set(values))]
    if len(labels) == 1:
        return f"{labels[0]} horizon"
    return f"{', '.join(labels[:-1])} and {labels[-1]} horizons"


def _prediction_summary(results_dir: Path) -> tuple[int, list[int]]:
    total_rows = 0
    horizons: list[int] = []
    for path in sorted(results_dir.glob("crisis_predictions_h*.csv")):
        frame = read_csv_or_empty(path)
        total_rows += len(frame)
        if not frame.empty and "horizon" in frame.columns:
            horizons.extend(int(value) for value in frame["horizon"].dropna().unique())
            continue
        stem = path.stem.rsplit("_h", maxsplit=1)[-1]
        if stem.isdigit():
            horizons.append(int(stem))
    return total_rows, sorted(set(horizons))


def _baseline_prediction_rows(results_dir: Path) -> int:
    total_rows = 0
    for path in sorted(results_dir.glob("baseline_predictions_h*.csv")):
        total_rows += len(read_csv_or_empty(path))
    return total_rows


def _skip_note(kind: str, skipped: pd.DataFrame) -> str:
    count = len(skipped)
    names = _unique_strings(skipped, "portfolio_name")
    if count == 0:
        return f"No {kind} rows were skipped."
    if names:
        return f"{_fmt_int(count)} skipped {kind} rows were logged for portfolios: {', '.join(names)}."
    return f"{_fmt_int(count)} skipped {kind} rows were logged."


def result_note_context(results_dir: Path) -> dict[str, object]:
    """Collect note fields from the current result directory, not fixed manuscript constants."""
    crisis_rows, horizons = _prediction_summary(results_dir)
    crisis_skipped = read_csv_or_empty(results_dir / "crisis_eval_skipped.csv")
    baseline_skipped = read_csv_or_empty(results_dir / "baseline_eval_skipped.csv")
    allocation_skipped = read_csv_or_empty(results_dir / "allocation_oos_skipped.csv")
    allocation_metrics = read_csv_or_empty(results_dir / "allocation_oos_metrics.csv")
    allocation_returns = read_csv_or_empty(results_dir / "allocation_oos_returns.csv")
    baseline_metrics = read_csv_or_empty(results_dir / "baseline_metrics.csv")
    ablation_metrics = read_csv_or_empty(results_dir / "ablation_metrics.csv")
    threshold_metrics = read_csv_or_empty(results_dir / "threshold_sensitivity_metrics.csv")

    return {
        "crisis_prediction_rows": crisis_rows,
        "crisis_horizons": horizons,
        "crisis_skip_note": _skip_note("crisis-warning", crisis_skipped),
        "baseline_prediction_rows": _baseline_prediction_rows(results_dir),
        "baseline_metric_rows": len(baseline_metrics),
        "baseline_skip_note": _skip_note("baseline-evaluation", baseline_skipped),
        "allocation_portfolio_count": (
            int(allocation_metrics["portfolio_name"].nunique())
            if not allocation_metrics.empty and "portfolio_name" in allocation_metrics.columns
            else 0
        ),
        "allocation_strategy_rows": len(allocation_metrics),
        "allocation_return_rows": len(allocation_returns),
        "allocation_skip_note": _skip_note("allocation", allocation_skipped),
        "ablation_rows": len(ablation_metrics),
        "threshold_metric_rows": len(threshold_metrics),
    }


def paper_notes(results_dir: Path, outputs: dict[str, pd.DataFrame]) -> dict[str, tuple[str, str]]:
    ctx = result_note_context(results_dir)
    crisis_rows = _fmt_int(ctx["crisis_prediction_rows"])  # type: ignore[arg-type]
    horizons = _horizon_label(ctx["crisis_horizons"])  # type: ignore[arg-type]
    threshold_rows = _fmt_int(ctx["threshold_metric_rows"])  # type: ignore[arg-type]
    baseline_prediction_rows = _fmt_int(ctx["baseline_prediction_rows"])  # type: ignore[arg-type]
    baseline_metric_rows = _fmt_int(ctx["baseline_metric_rows"])  # type: ignore[arg-type]
    allocation_portfolios = _fmt_int(ctx["allocation_portfolio_count"])  # type: ignore[arg-type]
    allocation_strategy_rows = _fmt_int(ctx["allocation_strategy_rows"])  # type: ignore[arg-type]
    allocation_return_rows = _fmt_int(ctx["allocation_return_rows"])  # type: ignore[arg-type]
    ablation_rows = _fmt_int(ctx["ablation_rows"])  # type: ignore[arg-type]

    baseline_empty = outputs["table_baseline_comparison.csv"].empty
    allocation_empty = outputs["table_allocation_metrics.csv"].empty
    ablation_empty = outputs["table_ablation.csv"].empty

    return {
        "table_1_artifact_summary.md": (
            "Frozen H1/H5 artifact directories were not retrained. Artifact and feature-schema hashes are validated against metadata before paper use; this table documents the audit contract rather than model performance.",
            "No artifact audit rows were produced for this result directory.",
        ),
        "table_2_crisis_metrics.md": (
            f"Metrics use {crisis_rows} real-data holdout predictions with sandbox disabled across {horizons}. {ctx['crisis_skip_note']} PR-AUC is emphasized alongside ROC-AUC because tail events are rare.",
            "No crisis-warning metric rows were produced for this result directory.",
        ),
        "table_3_baseline_comparison.md": (
            (
                "Baseline comparison was not run for this result directory; this table is retained only as a non-paper artifact for package completeness and should not be interpreted as zero-overlap supplement evidence."
                if baseline_empty
                else f"Baseline rows use {baseline_prediction_rows} real-data final-window holdout predictions with sandbox disabled. Non-frozen baselines train on the first 80% of each available portfolio and evaluate on the final 20%; frozen XGBoost is sliced to the same windows for fairness. The source baseline metrics file contains {baseline_metric_rows} rows. {ctx['baseline_skip_note']}"
            ),
            (
                "Not run for this supplement result directory."
                if baseline_empty
                else "No baseline comparison rows were produced for this result directory."
            ),
        ),
        "table_4_allocation_oos.md": (
            (
                "Allocation OOS evaluation was not run for this result directory; this table is retained only as a non-paper artifact for package completeness and should not be interpreted as zero-overlap supplement evidence."
                if allocation_empty
                else f"Values are means across {allocation_portfolios} real-data holdout portfolios, {allocation_strategy_rows} strategy rows, and {allocation_return_rows} OOS return rows with sandbox disabled. {ctx['allocation_skip_note']} Benchmark excess return remains negative for every listed strategy."
            ),
            (
                "Not run for this supplement result directory."
                if allocation_empty
                else "No allocation OOS rows were produced for this result directory."
            ),
        ),
        "table_5_ablation.md": (
            (
                "Allocation ablation was not run for this result directory; this table is retained only as a non-paper artifact for package completeness and should not be interpreted as zero-overlap supplement evidence."
                if ablation_empty
                else f"Deltas are strategy-level differences relative to Smart policy + OOS guard on the same allocation run. The source ablation metrics file contains {ablation_rows} rows. This is a coarse allocation ablation, not a causal decomposition of every Smart-policy submodule."
            ),
            (
                "Not run for this supplement result directory."
                if ablation_empty
                else "No allocation ablation rows were produced for this result directory."
            ),
        ),
        "table_threshold_sensitivity.md": (
            f"Computed from {crisis_rows} real-data holdout crisis prediction rows with sandbox disabled across {horizons}. The threshold-sensitivity source file contains {threshold_rows} metric rows; this paper table reports global and horizon-level rows. {ctx['crisis_skip_note']} The 0.60 threshold is a conservative operating point; top-percentile columns summarize ranking surveillance behavior.",
            "No threshold-sensitivity rows were produced for this result directory.",
        ),
    }


def artifact_table(results_dir: Path) -> pd.DataFrame:
    path = results_dir / "artifact_audit_summary.json"
    if not path.exists():
        return pd.DataFrame(
            columns=[
                "horizon",
                "model_version",
                "artifact_hash",
                "feature_schema_hash",
                "validation_status",
                "hash_matches_metadata",
            ]
        )
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    rows = []
    for key, item in sorted(payload.get("horizons", {}).items()):
        rows.append(
            {
                "horizon": key.upper(),
                "model_version": item.get("metadata_model_version", ""),
                "artifact_hash": item.get("artifact_hash", ""),
                "feature_schema_hash": item.get("feature_schema_hash", ""),
                "validation_status": item.get("metadata_validation_status", ""),
                "hash_matches_metadata": item.get("artifact_hash_matches_metadata", ""),
            }
        )
    return pd.DataFrame(rows)


def crisis_table(results_dir: Path) -> pd.DataFrame:
    frame = read_csv_or_empty(results_dir / "crisis_metrics_by_market.csv")
    if frame.empty:
        return pd.DataFrame(
            columns=[
                "horizon",
                "market",
                "roc_auc",
                "pr_auc",
                "brier_score",
                "log_loss",
                "calibration_error",
                "precision_at_0_60",
                "recall_at_0_60",
                "top_decile_lift",
                "positive_event_count",
                "row_count",
            ]
        )
    columns = [
        "horizon",
        "market",
        "roc_auc",
        "pr_auc",
        "brier_score",
        "log_loss",
        "calibration_error",
        "precision_at_0_60",
        "recall_at_0_60",
        "top_decile_lift",
        "positive_event_count",
        "row_count",
    ]
    return frame[[column for column in columns if column in frame.columns]].sort_values(
        ["horizon", "market"]
    )


def allocation_table(results_dir: Path) -> pd.DataFrame:
    frame = read_csv_or_empty(results_dir / "allocation_oos_metrics.csv")
    if frame.empty:
        return pd.DataFrame(
            columns=[
                "strategy",
                "portfolio_count",
                "cumulative_return",
                "annualized_volatility",
                "max_drawdown",
                "expected_shortfall",
                "sharpe",
                "information_ratio",
                "turnover",
                "benchmark_excess_return",
                "model_score",
            ]
        )
    metric_columns = [
        "cumulative_return",
        "annualized_volatility",
        "max_drawdown",
        "expected_shortfall",
        "sharpe",
        "information_ratio",
        "turnover",
        "benchmark_excess_return",
        "model_score",
    ]
    grouped = frame.groupby("strategy", sort=True)
    present_metric_columns = [column for column in metric_columns if column in frame.columns]
    table = grouped[present_metric_columns].mean(numeric_only=True).reset_index()
    table.insert(1, "portfolio_count", grouped["portfolio_name"].nunique().to_numpy())
    return table.sort_values("strategy")


def baseline_table(results_dir: Path) -> pd.DataFrame:
    frame = read_csv_or_empty(results_dir / "baseline_metrics.csv")
    columns = [
        "horizon",
        "baseline",
        "row_count",
        "positive_event_count",
        "roc_auc",
        "pr_auc",
        "brier_score",
        "log_loss",
        "calibration_error",
        "precision_at_0_60",
        "recall_at_0_60",
        "top_decile_lift",
    ]
    if frame.empty:
        return pd.DataFrame(columns=columns)
    global_frame = frame[frame.get("scope", "").eq("global")].copy()
    if global_frame.empty:
        return pd.DataFrame(columns=columns)
    return global_frame[[column for column in columns if column in global_frame.columns]].sort_values(
        ["horizon", "baseline"]
    )


def ablation_table(results_dir: Path) -> pd.DataFrame:
    frame = read_csv_or_empty(results_dir / "ablation_metrics.csv")
    if frame.empty:
        return pd.DataFrame(
            columns=[
                "ablation",
                "portfolio_count",
                "delta_cumulative_return",
                "delta_sharpe",
                "delta_information_ratio",
                "delta_model_score",
            ]
        )
    metric_columns = [
        "delta_cumulative_return",
        "delta_sharpe",
        "delta_information_ratio",
        "delta_model_score",
    ]
    grouped = frame.groupby("ablation", sort=True)
    present_metric_columns = [column for column in metric_columns if column in frame.columns]
    table = grouped[present_metric_columns].mean(numeric_only=True).reset_index()
    table.insert(1, "portfolio_count", grouped["portfolio_name"].nunique().to_numpy())
    return table.sort_values("ablation")


def threshold_sensitivity_table(results_dir: Path) -> pd.DataFrame:
    frame = read_csv_or_empty(results_dir / "threshold_sensitivity_metrics.csv")
    columns = [
        "scope",
        "horizon",
        "threshold",
        "row_count",
        "positive_count",
        "positive_rate",
        "flag_rate",
        "flag_count",
        "precision",
        "recall",
        "f1",
        "top_1_precision",
        "top_1_recall",
        "top_1_lift",
        "top_5_precision",
        "top_5_recall",
        "top_5_lift",
        "top_10_precision",
        "top_10_recall",
        "top_10_lift",
    ]
    if frame.empty:
        return pd.DataFrame(columns=columns)
    table = frame[frame["scope"].isin(["global", "horizon"])].copy()
    present = [column for column in columns if column in table.columns]
    return table[present].sort_values(["scope", "horizon", "threshold"], na_position="first")


def run(results_dir: Path, tables_dir: Path, paper_dir: Path = DEFAULT_PAPER_DIR) -> dict[str, Any]:
    tables_dir.mkdir(parents=True, exist_ok=True)
    outputs = {
        "table_artifact_summary.csv": artifact_table(results_dir),
        "table_crisis_metrics.csv": crisis_table(results_dir),
        "table_baseline_comparison.csv": baseline_table(results_dir),
        "table_allocation_metrics.csv": allocation_table(results_dir),
        "table_ablation.csv": ablation_table(results_dir),
        "table_threshold_sensitivity.csv": threshold_sensitivity_table(results_dir),
    }
    for filename, frame in outputs.items():
        dataframe_to_csv(frame, tables_dir / filename)
    notes = paper_notes(results_dir, outputs)
    markdown_outputs = {
        "table_1_artifact_summary.md": (
            "Table 1. Frozen Artifact Audit Summary",
            outputs["table_artifact_summary.csv"],
        ),
        "table_2_crisis_metrics.md": (
            "Table 2. Crisis Warning External Metrics by Market",
            outputs["table_crisis_metrics.csv"],
        ),
        "table_3_baseline_comparison.md": (
            "Table 3. Crisis Baseline Comparison",
            outputs["table_baseline_comparison.csv"],
        ),
        "table_4_allocation_oos.md": (
            "Table 4. Allocation OOS Performance",
            outputs["table_allocation_metrics.csv"],
        ),
        "table_5_ablation.md": (
            "Table 5. Allocation Strategy Ablation",
            outputs["table_ablation.csv"],
        ),
        "table_threshold_sensitivity.md": (
            "Table 6. Threshold Sensitivity and Ranking Surveillance",
            outputs["table_threshold_sensitivity.csv"],
        ),
    }
    for filename, (title, frame) in markdown_outputs.items():
        note, empty_message = notes[filename]
        write_markdown(project_path(paper_dir) / filename, title, frame, note, empty_message=empty_message)
    return {filename: int(len(frame)) for filename, frame in outputs.items()}


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build paper tables from experiment CSVs.")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH))
    parser.add_argument("--results-dir", default=None)
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--paper-dir", default=str(DEFAULT_PAPER_DIR))
    return parser


def main() -> int:
    args = make_parser().parse_args()
    config = load_config(args.config)
    results_dir = output_dir_from_args(args.results_dir, config, key="results_dir", default=DEFAULT_RESULTS_DIR)
    tables_dir = output_dir_from_args(args.output_dir, config, key="tables_dir", default=DEFAULT_TABLES_DIR)
    summary = run(project_path(results_dir), project_path(tables_dir), project_path(args.paper_dir))
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
