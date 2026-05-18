"""Analyze crisis-warning threshold and ranking sensitivity from saved predictions."""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

MPLCONFIGDIR = ROOT / "experiments" / ".mplconfig"
MPLCONFIGDIR.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(MPLCONFIGDIR))

import matplotlib.pyplot as plt  # noqa: E402
import seaborn as sns  # noqa: E402

from experiments.common import (  # noqa: E402
    DEFAULT_CONFIG_PATH,
    DEFAULT_FIGURES_DIR,
    DEFAULT_RESULTS_DIR,
    DEFAULT_TABLES_DIR,
    dataframe_to_csv,
    horizons_from_config,
    load_config,
    output_dir_from_args,
    project_path,
)
from experiments.make_paper_tables import (  # noqa: E402
    _fmt_int,
    _horizon_label,
    result_note_context,
    write_markdown,
)


DEFAULT_THRESHOLDS = [0.05, 0.075, 0.10, 0.15, 0.20, 0.30, 0.40, 0.50, 0.60]
DEFAULT_TOP_PCTS = [0.01, 0.05, 0.10]
PALETTE = ["#0072B2", "#D55E00", "#009E73", "#E69F00", "#CC79A7"]


def _parse_float_list(value: str | None, default: list[float]) -> list[float]:
    if value is None:
        return list(default)
    parsed = [float(item.strip()) for item in str(value).split(",") if item.strip()]
    return sorted(set(parsed))


def read_csv_or_empty(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path, low_memory=False)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()


def load_predictions(results_dir: Path, horizons: Iterable[int]) -> pd.DataFrame:
    frames = []
    for horizon in horizons:
        frame = read_csv_or_empty(results_dir / f"crisis_predictions_h{horizon}.csv")
        if not frame.empty:
            frames.append(frame)
    if not frames:
        return pd.DataFrame()
    predictions = pd.concat(frames, ignore_index=True)
    required = {"horizon", "market", "tail_event", "crisis_probability"}
    missing = sorted(required - set(predictions.columns))
    if missing:
        raise ValueError(f"crisis prediction CSVs are missing columns: {', '.join(missing)}")
    return predictions


def classification_metrics(y_true: np.ndarray, probabilities: np.ndarray, threshold: float) -> dict[str, float]:
    y = np.asarray(y_true, dtype=int).reshape(-1)
    p = np.clip(np.asarray(probabilities, dtype=float).reshape(-1), 0.0, 1.0)
    if y.size != p.size:
        raise ValueError("y_true and probabilities must have the same length")
    flags = p >= float(threshold)
    flag_count = int(flags.sum())
    positive_count = int(y.sum())
    true_positive = int(y[flags].sum()) if flag_count else 0
    precision = true_positive / flag_count if flag_count else 0.0
    recall = true_positive / positive_count if positive_count else 0.0
    f1 = (2.0 * precision * recall / (precision + recall)) if (precision + recall) > 0.0 else 0.0
    row_count = int(y.size)
    return {
        "row_count": float(row_count),
        "positive_count": float(positive_count),
        "positive_rate": positive_count / row_count if row_count else math.nan,
        "threshold": float(threshold),
        "flag_count": float(flag_count),
        "flag_rate": flag_count / row_count if row_count else math.nan,
        "true_positive_count": float(true_positive),
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
    }


def ranking_metrics(
    y_true: np.ndarray,
    probabilities: np.ndarray,
    top_pcts: Iterable[float] = DEFAULT_TOP_PCTS,
) -> dict[str, float]:
    y = np.asarray(y_true, dtype=int).reshape(-1)
    p = np.asarray(probabilities, dtype=float).reshape(-1)
    if y.size != p.size:
        raise ValueError("y_true and probabilities must have the same length")
    result: dict[str, float] = {}
    row_count = int(y.size)
    positive_count = int(y.sum())
    base_rate = positive_count / row_count if row_count else math.nan
    order = np.argsort(-p, kind="mergesort") if row_count else np.asarray([], dtype=int)
    for pct in top_pcts:
        label = f"top_{int(round(float(pct) * 100))}"
        top_count = max(1, int(math.ceil(float(pct) * row_count))) if row_count else 0
        top_idx = order[:top_count]
        top_positive = int(y[top_idx].sum()) if top_count else 0
        precision = top_positive / top_count if top_count else math.nan
        recall = top_positive / positive_count if positive_count else 0.0
        lift = precision / base_rate if row_count and base_rate > 0 else math.nan
        result[f"{label}_count"] = float(top_count)
        result[f"{label}_positive_count"] = float(top_positive)
        result[f"{label}_precision"] = float(precision) if np.isfinite(precision) else math.nan
        result[f"{label}_recall"] = float(recall)
        result[f"{label}_lift"] = float(lift) if np.isfinite(lift) else math.nan
    return result


def _group_iter(predictions: pd.DataFrame) -> Iterable[tuple[str, dict[str, object], pd.DataFrame]]:
    yield "global", {"horizon": None, "market": None}, predictions
    for horizon, group in predictions.groupby("horizon", sort=True, dropna=False):
        yield "horizon", {"horizon": int(horizon), "market": None}, group
    for market, group in predictions.groupby("market", sort=True, dropna=False):
        yield "market", {"horizon": None, "market": market}, group
    for (horizon, market), group in predictions.groupby(["horizon", "market"], sort=True, dropna=False):
        yield "horizon_market", {"horizon": int(horizon), "market": market}, group


def threshold_sensitivity_rows(
    predictions: pd.DataFrame,
    thresholds: Iterable[float] = DEFAULT_THRESHOLDS,
    top_pcts: Iterable[float] = DEFAULT_TOP_PCTS,
) -> list[dict[str, object]]:
    if predictions.empty:
        return []
    rows: list[dict[str, object]] = []
    for scope, keys, group in _group_iter(predictions):
        y = group["tail_event"].astype(int).to_numpy()
        p = group["crisis_probability"].astype(float).to_numpy()
        rank = ranking_metrics(y, p, top_pcts=top_pcts)
        for threshold in thresholds:
            row: dict[str, object] = {"scope": scope, **keys}
            row.update(classification_metrics(y, p, float(threshold)))
            row.update(rank)
            rows.append(row)
    return rows


def threshold_table(metrics: pd.DataFrame) -> pd.DataFrame:
    if metrics.empty:
        return pd.DataFrame(
            columns=[
                "scope",
                "horizon",
                "threshold",
                "row_count",
                "positive_count",
                "flag_rate",
                "flag_count",
                "precision",
                "recall",
                "f1",
                "top_10_precision",
                "top_10_recall",
                "top_10_lift",
            ]
        )
    table = metrics[metrics["scope"].isin(["global", "horizon"])].copy()
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
    present = [column for column in columns if column in table.columns]
    table = table[present].sort_values(["scope", "horizon", "threshold"], na_position="first")
    for column in [
        "row_count",
        "positive_count",
        "flag_count",
        "top_1_count",
        "top_5_count",
        "top_10_count",
    ]:
        if column in table.columns:
            table[column] = table[column].astype("Int64")
    return table


def write_paper_markdown(table: pd.DataFrame, paper_dir: Path, results_dir: Path) -> Path:
    ctx = result_note_context(results_dir)
    note = (
        f"Computed from {_fmt_int(ctx['crisis_prediction_rows'])} real-data holdout crisis "
        f"prediction rows with sandbox disabled across {_horizon_label(ctx['crisis_horizons'])}. "
        f"The threshold-sensitivity source file contains {_fmt_int(ctx['threshold_metric_rows'])} "
        f"metric rows; this paper table reports global and horizon-level rows. {ctx['crisis_skip_note']} "
        "The 0.60 threshold is a conservative operating point; top-percentile columns "
        "summarize ranking surveillance behavior."
    )
    path = paper_dir / "table_threshold_sensitivity.md"
    write_markdown(
        path,
        "Table 6. Threshold Sensitivity and Ranking Surveillance",
        table,
        note,
        empty_message="No threshold-sensitivity rows were produced for this result directory.",
    )
    return path


def plot_threshold_sensitivity(metrics: pd.DataFrame, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sns.set_theme(
        style="whitegrid",
        context="paper",
        rc={
            "figure.dpi": 160,
            "savefig.dpi": 220,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "font.family": "DejaVu Sans",
        },
    )
    horizon = metrics[metrics["scope"].eq("horizon")].copy()
    if horizon.empty:
        fig, ax = plt.subplots(figsize=(7.0, 3.8))
        ax.axis("off")
        ax.text(0.5, 0.55, "Threshold Sensitivity", ha="center", va="center", weight="bold")
        ax.text(0.5, 0.42, "No threshold metrics available.", ha="center", va="center")
        fig.tight_layout()
        fig.savefig(output_path, bbox_inches="tight")
        plt.close(fig)
        return

    horizon["horizon_label"] = "h" + horizon["horizon"].astype(int).astype(str)
    panels = [
        ("precision", "Precision"),
        ("recall", "Recall"),
        ("f1", "F1"),
        ("flag_rate", "Flag rate"),
    ]
    fig = plt.figure(figsize=(9.4, 6.55))
    grid = fig.add_gridspec(3, 2, height_ratios=[0.18, 1.0, 1.0], hspace=0.42, wspace=0.22)
    legend_ax = fig.add_subplot(grid[0, :])
    axes = np.asarray(
        [
            [fig.add_subplot(grid[1, 0]), fig.add_subplot(grid[1, 1])],
            [fig.add_subplot(grid[2, 0]), fig.add_subplot(grid[2, 1])],
        ]
    )
    for idx, (metric, title) in enumerate(panels):
        ax = axes.flat[idx]
        for color_idx, (horizon_label, group) in enumerate(horizon.groupby("horizon_label", sort=True)):
            ax.plot(
                group["threshold"],
                group[metric],
                marker="o",
                linewidth=1.9,
                markersize=3.5,
                color=PALETTE[color_idx % len(PALETTE)],
                label=horizon_label,
            )
        ax.axvline(0.60, color="#777777", linestyle="--", linewidth=0.9)
        ax.set_title(title)
        ax.set_ylim(bottom=0.0)
        if metric in {"precision", "recall", "f1", "flag_rate"}:
            ax.set_ylabel(metric.replace("_", " "))
        ax.set_xlabel("Crisis probability threshold" if idx >= 2 else "")
    handles, labels = axes.flat[0].get_legend_handles_labels()
    legend_ax.axis("off")
    legend_ax.legend(handles, labels, frameon=False, title="Horizon", loc="center left", ncol=max(1, len(labels)))
    fig.suptitle("Threshold Sensitivity on Real-Data Holdout Predictions", fontsize=12, weight="bold", y=0.99)
    fig.text(
        0.5,
        0.01,
        "Sandbox disabled; lower thresholds improve recall but raise flag volume. Dashed line marks the conservative 0.60 threshold.",
        ha="center",
        fontsize=8,
        color="#475569",
    )
    fig.subplots_adjust(left=0.08, right=0.98, top=0.88, bottom=0.10, hspace=0.42, wspace=0.22)
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)


def skipped_summary(results_dir: Path) -> str:
    skipped = read_csv_or_empty(results_dir / "crisis_eval_skipped.csv")
    if skipped.empty:
        return "No crisis external evaluation skips were recorded."
    portfolios = skipped["portfolio_name"].nunique() if "portfolio_name" in skipped.columns else 0
    horizons = skipped["horizon"].nunique() if "horizon" in skipped.columns else 0
    return f"Skipped rows: {len(skipped)} across {portfolios} portfolio(s) and {horizons} horizon(s)."


def run(
    config: dict[str, Any],
    results_dir: Path,
    tables_dir: Path,
    figures_dir: Path,
    paper_dir: Path,
    thresholds: Iterable[float] = DEFAULT_THRESHOLDS,
) -> dict[str, Any]:
    horizons = horizons_from_config(config)
    predictions = load_predictions(results_dir, horizons)
    metrics = pd.DataFrame(threshold_sensitivity_rows(predictions, thresholds=thresholds))
    metrics_path = dataframe_to_csv(metrics, results_dir / "threshold_sensitivity_metrics.csv")
    table = threshold_table(metrics)
    table_path = dataframe_to_csv(table, tables_dir / "table_threshold_sensitivity.csv")
    paper_path = write_paper_markdown(table, paper_dir, results_dir)
    figure_path = figures_dir / "threshold_sensitivity.png"
    plot_threshold_sensitivity(metrics, figure_path)
    return {
        "prediction_rows": int(len(predictions)),
        "metric_rows": int(len(metrics)),
        "table_rows": int(len(table)),
        "metrics_path": str(metrics_path),
        "table_path": str(table_path),
        "paper_path": str(paper_path),
        "figure_path": str(figure_path),
    }


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run threshold-sensitivity analysis from crisis predictions.")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH))
    parser.add_argument("--results-dir", default=None)
    parser.add_argument("--tables-dir", default=None)
    parser.add_argument("--figures-dir", default=None)
    parser.add_argument("--paper-dir", default=str(ROOT / "paper"))
    parser.add_argument("--thresholds", default=None)
    return parser


def main() -> int:
    args = make_parser().parse_args()
    config = load_config(args.config)
    results_dir = output_dir_from_args(args.results_dir, config, key="results_dir", default=DEFAULT_RESULTS_DIR)
    tables_dir = output_dir_from_args(args.tables_dir, config, key="tables_dir", default=DEFAULT_TABLES_DIR)
    figures_dir = output_dir_from_args(args.figures_dir, config, key="figures_dir", default=DEFAULT_FIGURES_DIR)
    thresholds = _parse_float_list(args.thresholds, DEFAULT_THRESHOLDS)
    summary = run(
        config=config,
        results_dir=project_path(results_dir),
        tables_dir=project_path(tables_dir),
        figures_dir=project_path(figures_dir),
        paper_dir=project_path(args.paper_dir),
        thresholds=thresholds,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
