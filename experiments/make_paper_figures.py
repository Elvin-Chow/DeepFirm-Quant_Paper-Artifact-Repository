"""Generate publication-style figures from paper experiment CSVs."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

MPLCONFIGDIR = ROOT / "experiments" / ".mplconfig"
MPLCONFIGDIR.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(MPLCONFIGDIR))

import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import seaborn as sns  # noqa: E402
from sklearn.metrics import auc, precision_recall_curve, roc_curve  # noqa: E402

from experiments.common import (  # noqa: E402
    DEFAULT_CONFIG_PATH,
    DEFAULT_FIGURES_DIR,
    DEFAULT_RESULTS_DIR,
    horizons_from_config,
    load_config,
    output_dir_from_args,
    project_path,
)
from experiments.run_threshold_sensitivity import plot_threshold_sensitivity  # noqa: E402


PALETTE = ["#E69F00", "#56B4E9", "#009E73", "#0072B2", "#D55E00", "#CC79A7"]


def setup_style() -> None:
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


def read_csv_or_empty(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, low_memory=False)


def placeholder(path: Path, title: str, message: str) -> None:
    fig, ax = plt.subplots(figsize=(7.0, 3.8))
    ax.axis("off")
    ax.text(0.5, 0.62, title, ha="center", va="center", fontsize=13, weight="bold")
    ax.text(0.5, 0.42, message, ha="center", va="center", fontsize=10)
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def plot_framework_architecture(output_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(11.0, 6.2))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 8)
    ax.axis("off")

    bands = [
        (0.35, 5.75, 11.3, 1.55, "#E8EDF2", "Data and Provenance"),
        (0.35, 3.85, 11.3, 1.55, "#E8F2EE", "Tail-Risk Warning"),
        (0.35, 1.95, 11.3, 1.55, "#FFF4E5", "Leakage-Guarded Allocation"),
        (0.35, 0.35, 11.3, 1.30, "#F4F4F5", "Audit Trail"),
    ]
    for x, y, w, h, color, label in bands:
        ax.add_patch(
            FancyBboxPatch(
                (x, y),
                w,
                h,
                boxstyle="round,pad=0.02,rounding_size=0.08",
                facecolor=color,
                edgecolor="none",
            )
        )
        ax.text(x + 0.18, y + h - 0.28, label, fontsize=9, weight="bold", color="#334155")

    boxes = [
        ("Market data\nUS/HK/CN/JP/TW", 0.8, 6.15, "#FFFFFF"),
        ("Calendar alignment\nand price quality", 3.0, 6.15, "#FFFFFF"),
        ("Point-in-time\nfeature frame", 5.35, 6.15, "#FFFFFF"),
        ("Dynamic trailing\nquantile labels", 7.75, 6.15, "#FFFFFF"),
        ("Frozen XGBoost\nh1/h5 artifacts", 1.0, 4.25, "#FFFFFF"),
        ("Calibrated tail-risk\nprobability", 3.45, 4.25, "#FFFFFF"),
        ("Warning level and\nSHAP drivers", 5.95, 4.25, "#FFFFFF"),
        ("External holdout\nmetrics", 8.35, 4.25, "#FFFFFF"),
        ("Train-window\nrisk state", 1.0, 2.35, "#FFFFFF"),
        ("Smart policy\ncontrols", 3.25, 2.35, "#FFFFFF"),
        ("Black-Litterman\nposterior weights", 5.55, 2.35, "#FFFFFF"),
        ("OOS guard and\nbenchmark scoring", 8.1, 2.35, "#FFFFFF"),
        ("Artifact hash", 1.2, 0.55, "#FFFFFF"),
        ("Schema hash", 3.3, 0.55, "#FFFFFF"),
        ("Provider warnings", 5.35, 0.55, "#FFFFFF"),
        ("Command log", 7.8, 0.55, "#FFFFFF"),
        ("Paper tables\nand figures", 9.65, 0.55, "#FFFFFF"),
    ]
    for label, x, y, color in boxes:
        ax.add_patch(
            FancyBboxPatch(
                (x, y),
                1.8,
                0.72,
                boxstyle="round,pad=0.04,rounding_size=0.06",
                facecolor=color,
                edgecolor="#CBD5E1",
                linewidth=0.9,
            )
        )
        ax.text(x + 0.9, y + 0.36, label, ha="center", va="center", fontsize=8.2, color="#111827")

    arrows = [
        ((2.6, 6.51), (2.95, 6.51)),
        ((4.8, 6.51), (5.3, 6.51)),
        ((7.15, 6.51), (7.7, 6.51)),
        ((6.25, 6.12), (2.0, 5.0)),
        ((2.8, 4.61), (3.4, 4.61)),
        ((5.25, 4.61), (5.9, 4.61)),
        ((7.75, 4.61), (8.3, 4.61)),
        ((4.15, 4.2), (3.75, 3.1)),
        ((2.8, 2.71), (3.2, 2.71)),
        ((5.05, 2.71), (5.5, 2.71)),
        ((7.35, 2.71), (8.05, 2.71)),
        ((9.0, 4.2), (9.0, 3.1)),
        ((8.95, 2.35), (8.95, 1.30)),
    ]
    for start, end in arrows:
        ax.add_patch(
            FancyArrowPatch(
                start,
                end,
                arrowstyle="-|>",
                mutation_scale=10,
                linewidth=1.2,
                color="#64748B",
                connectionstyle="arc3,rad=0.0",
            )
        )

    ax.text(
        6.0,
        7.65,
        "Auditable Explainable AI Framework for Multi-Market Tail-Risk Warning and Bayesian Allocation",
        ha="center",
        va="center",
        fontsize=12,
        weight="bold",
        color="#0F172A",
    )
    ax.text(
        6.0,
        0.16,
        "Frozen artifacts are evaluated without retraining; unavailable real-market data is logged rather than replaced with sandbox data.",
        ha="center",
        va="center",
        fontsize=8,
        color="#475569",
    )
    fig.tight_layout()
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)


def load_predictions(results_dir: Path, horizons: list[int]) -> pd.DataFrame:
    frames = []
    for horizon in horizons:
        frame = read_csv_or_empty(results_dir / f"crisis_predictions_h{horizon}.csv")
        if not frame.empty:
            frames.append(frame)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def plot_roc_pr(predictions: pd.DataFrame, output_path: Path) -> None:
    if predictions.empty:
        placeholder(output_path, "ROC and PR by Horizon", "No crisis prediction rows available.")
        return
    fig = plt.figure(figsize=(9.2, 4.3))
    grid = fig.add_gridspec(2, 2, height_ratios=[0.14, 1.0], hspace=0.10, wspace=0.24)
    legend_axes = [fig.add_subplot(grid[0, 0]), fig.add_subplot(grid[0, 1])]
    axes = [fig.add_subplot(grid[1, 0]), fig.add_subplot(grid[1, 1])]
    for color_idx, (horizon, group) in enumerate(predictions.groupby("horizon", sort=True)):
        y = group["tail_event"].astype(int).to_numpy()
        p = group["crisis_probability"].astype(float).to_numpy()
        if np.unique(y).size != 2:
            continue
        fpr, tpr, _ = roc_curve(y, p)
        precision, recall, _ = precision_recall_curve(y, p)
        color = PALETTE[color_idx % len(PALETTE)]
        axes[0].plot(fpr, tpr, label=f"h{horizon} AUC={auc(fpr, tpr):.2f}", color=color, linewidth=2.0)
        axes[1].plot(recall, precision, label=f"h{horizon} AP={auc(recall, precision):.2f}", color=color, linewidth=2.0)
    axes[0].plot([0, 1], [0, 1], color="#999999", linestyle="--", linewidth=1.0)
    axes[0].set_xlabel("False positive rate")
    axes[0].set_ylabel("True positive rate")
    axes[0].set_title("ROC")
    axes[1].set_xlabel("Recall")
    axes[1].set_ylabel("Precision")
    axes[1].set_title("Precision-recall")
    for ax, legend_ax in zip(axes, legend_axes):
        handles, labels = ax.get_legend_handles_labels()
        legend_ax.axis("off")
        legend_ax.legend(handles, labels, frameon=False, fontsize=8, loc="center left", ncols=2)
        ax.set_xlim(0.0, 1.0)
        ax.set_ylim(0.0, 1.02)
    fig.subplots_adjust(left=0.08, right=0.98, top=0.96, bottom=0.12, hspace=0.10, wspace=0.24)
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)


def plot_calibration(predictions: pd.DataFrame, output_path: Path) -> None:
    if predictions.empty:
        placeholder(output_path, "Calibration by Horizon", "No crisis prediction rows available.")
        return
    fig = plt.figure(figsize=(5.3, 4.45))
    grid = fig.add_gridspec(2, 1, height_ratios=[0.16, 1.0], hspace=0.04)
    legend_ax = fig.add_subplot(grid[0])
    ax = fig.add_subplot(grid[1])
    ax.plot([0, 1], [0, 1], color="#888888", linestyle="--", linewidth=1.0, label="ideal")
    for color_idx, (horizon, group) in enumerate(predictions.groupby("horizon", sort=True)):
        temp = group.copy()
        temp["bin"] = pd.cut(temp["crisis_probability"], bins=np.linspace(0.0, 1.0, 11), include_lowest=True)
        points = temp.groupby("bin", observed=True).agg(
            mean_probability=("crisis_probability", "mean"),
            event_rate=("tail_event", "mean"),
            row_count=("tail_event", "size"),
        )
        points = points[points["row_count"] > 0]
        if points.empty:
            continue
        ax.plot(
            points["mean_probability"],
            points["event_rate"],
            marker="o",
            linewidth=2.0,
            color=PALETTE[color_idx % len(PALETTE)],
            label=f"h{horizon}",
        )
    ax.set_xlabel("Mean predicted probability")
    ax.set_ylabel("Observed tail-event rate")
    ax.set_title("Calibration")
    ax.set_xlim(0.0, 1.0)
    ax.set_ylim(0.0, 1.0)
    handles, labels = ax.get_legend_handles_labels()
    legend_ax.axis("off")
    legend_ax.legend(handles, labels, frameon=False, loc="center left", ncols=3)
    fig.subplots_adjust(left=0.14, right=0.98, top=0.96, bottom=0.12, hspace=0.04)
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)


def plot_shap(shap_frame: pd.DataFrame, output_path: Path) -> None:
    if shap_frame.empty:
        placeholder(output_path, "Top Crisis Drivers", "No SHAP/native contribution rows available.")
        return
    summary = (
        shap_frame.assign(abs_shap=shap_frame["shap_value"].abs())
        .groupby(["horizon", "feature"], as_index=False)["abs_shap"]
        .mean()
    )
    top_features = (
        summary.groupby("feature")["abs_shap"]
        .mean()
        .sort_values(ascending=False)
        .head(12)
        .index
    )
    plot_frame = summary[summary["feature"].isin(top_features)]
    order = (
        plot_frame.groupby("feature")["abs_shap"]
        .mean()
        .sort_values(ascending=True)
        .index
    )
    fig = plt.figure(figsize=(7.8, 5.25))
    grid = fig.add_gridspec(2, 1, height_ratios=[0.14, 1.0], hspace=0.04)
    legend_ax = fig.add_subplot(grid[0])
    ax = fig.add_subplot(grid[1])
    sns.barplot(
        data=plot_frame,
        y="feature",
        x="abs_shap",
        hue="horizon",
        order=order,
        palette=PALETTE[: max(1, plot_frame["horizon"].nunique())],
        ax=ax,
    )
    ax.set_xlabel("Mean absolute native contribution")
    ax.set_ylabel("")
    ax.set_title("Top Crisis Warning Drivers")
    handles, labels = ax.get_legend_handles_labels()
    if ax.legend_ is not None:
        ax.legend_.remove()
    legend_ax.axis("off")
    legend_ax.legend(handles, labels, title="Horizon", frameon=False, loc="center left", ncols=2)
    fig.subplots_adjust(left=0.26, right=0.98, top=0.96, bottom=0.10, hspace=0.04)
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)


def plot_allocation_curves(returns_frame: pd.DataFrame, output_path: Path) -> None:
    if returns_frame.empty:
        placeholder(output_path, "OOS Allocation Curves", "No allocation OOS returns available.")
        return
    temp = returns_frame.sort_values(["strategy", "portfolio_name", "date"]).copy()
    temp["step"] = temp.groupby(["strategy", "portfolio_name"]).cumcount()
    summary = temp.groupby(["strategy", "step"], as_index=False)["cumulative_return"].mean()
    fig = plt.figure(figsize=(8.6, 4.75))
    grid = fig.add_gridspec(2, 1, height_ratios=[0.18, 1.0], hspace=0.02)
    legend_ax = fig.add_subplot(grid[0])
    ax = fig.add_subplot(grid[1])
    for color_idx, (strategy, group) in enumerate(summary.groupby("strategy", sort=True)):
        ax.plot(
            group["step"],
            group["cumulative_return"],
            label=strategy,
            color=PALETTE[color_idx % len(PALETTE)],
            linewidth=1.9,
        )
    ax.axhline(0.0, color="#777777", linewidth=0.8)
    ax.set_xlabel("OOS trading day")
    ax.set_ylabel("Mean cumulative log return")
    handles, labels = ax.get_legend_handles_labels()
    legend_ax.axis("off")
    legend_ax.legend(handles, labels, frameon=False, fontsize=8, ncols=3, loc="center left")
    fig.suptitle("Holdout OOS Allocation Performance", fontsize=12, y=0.99)
    fig.subplots_adjust(left=0.09, right=0.98, top=0.88, bottom=0.14, hspace=0.02)
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)


def plot_ablation(ablation_frame: pd.DataFrame, output_path: Path) -> None:
    if ablation_frame.empty:
        placeholder(output_path, "Ablation Summary", "No ablation metrics available.")
        return
    summary = ablation_frame.groupby("ablation", as_index=False).agg(
        delta_cumulative_return=("delta_cumulative_return", "mean"),
        delta_model_score=("delta_model_score", "mean"),
    )
    summary = summary.sort_values("delta_cumulative_return")
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 4.4), sharey=True)
    sns.barplot(
        data=summary,
        y="ablation",
        x="delta_cumulative_return",
        color=PALETTE[2],
        ax=axes[0],
    )
    sns.barplot(
        data=summary,
        y="ablation",
        x="delta_model_score",
        color=PALETTE[1],
        ax=axes[1],
    )
    axes[0].axvline(0.0, color="#777777", linewidth=0.9)
    axes[1].axvline(0.0, color="#777777", linewidth=0.9)
    axes[0].set_xlabel("Delta cumulative return")
    axes[1].set_xlabel("Delta model score")
    axes[0].set_ylabel("")
    axes[1].set_ylabel("")
    axes[0].set_title("Return ablation")
    axes[1].set_title("Score ablation")
    fig.tight_layout()
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)


def run(config: dict[str, Any], results_dir: Path, figures_dir: Path) -> dict[str, int]:
    setup_style()
    figures_dir.mkdir(parents=True, exist_ok=True)
    horizons = horizons_from_config(config)
    predictions = load_predictions(results_dir, horizons)
    shap_frame = read_csv_or_empty(results_dir / "crisis_shap_drivers.csv")
    allocation_returns = read_csv_or_empty(results_dir / "allocation_oos_returns.csv")
    ablation = read_csv_or_empty(results_dir / "ablation_metrics.csv")
    threshold_metrics = read_csv_or_empty(results_dir / "threshold_sensitivity_metrics.csv")

    outputs = {
        "framework_architecture.png": lambda path: plot_framework_architecture(path),
        "roc_pr_by_horizon.png": lambda path: plot_roc_pr(predictions, path),
        "calibration_by_horizon.png": lambda path: plot_calibration(predictions, path),
        "shap_top_drivers.png": lambda path: plot_shap(shap_frame, path),
        "allocation_oos_curves.png": lambda path: plot_allocation_curves(allocation_returns, path),
        "ablation_summary.png": lambda path: plot_ablation(ablation, path),
        "threshold_sensitivity.png": lambda path: plot_threshold_sensitivity(threshold_metrics, path),
    }
    for filename, plotter in outputs.items():
        plotter(figures_dir / filename)
    return {filename: int((figures_dir / filename).exists()) for filename in outputs}


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate paper figures from experiment CSVs.")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH))
    parser.add_argument("--results-dir", default=None)
    parser.add_argument("--output-dir", default=None)
    return parser


def main() -> int:
    args = make_parser().parse_args()
    config = load_config(args.config)
    results_dir = output_dir_from_args(args.results_dir, config, key="results_dir", default=DEFAULT_RESULTS_DIR)
    figures_dir = output_dir_from_args(args.output_dir, config, key="figures_dir", default=DEFAULT_FIGURES_DIR)
    summary = run(config, project_path(results_dir), project_path(figures_dir))
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
