"""Run leakage-guarded crisis-warning baseline comparisons for the paper."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.common import (  # noqa: E402
    DEFAULT_CONFIG_PATH,
    DEFAULT_PORTFOLIOS_PATH,
    DEFAULT_RESULTS_DIR,
    artifact_audit_summary,
    config_path,
    dataframe_to_csv,
    experiment_dates,
    fetch_portfolio_prices,
    horizons_from_config,
    load_config,
    load_holdout_portfolios,
    output_dir_from_args,
    parse_bool,
    project_path,
    write_json,
)
from experiments.metrics import crisis_classification_metrics  # noqa: E402
from experiments.run_crisis_external_eval import build_eval_frame, predict_frame  # noqa: E402
from models.crisis_warning_engine import CrisisWarningArtifactStore, TargetMethod  # noqa: E402
from models.risk_engine import RiskEngine  # noqa: E402


BASELINE_PREDICTION_COLUMNS = [
    "date",
    "horizon",
    "portfolio_name",
    "market",
    "baseline",
    "tail_event",
    "probability",
    "source",
    "source_detail",
]

BASELINE_METRIC_COLUMNS = [
    "scope",
    "horizon",
    "market",
    "portfolio_name",
    "baseline",
    "row_count",
    "positive_event_count",
    "positive_rate",
    "roc_auc",
    "pr_auc",
    "brier_score",
    "log_loss",
    "calibration_error",
    "precision_at_0_60",
    "recall_at_0_60",
    "top_decile_lift",
]

BASELINE_TRAINING_COLUMNS = [
    "horizon",
    "market",
    "portfolio_name",
    "baseline",
    "train_row_count",
    "test_row_count",
    "train_positive_count",
    "test_positive_count",
    "test_start",
    "test_end",
    "note",
]

BASELINE_SKIPPED_COLUMNS = [
    "portfolio_name",
    "market",
    "horizon",
    "baseline",
    "stage",
    "error",
]

MODEL_BASELINES = {
    "logistic_regression",
    "random_forest",
    "gradient_boosting",
}


def _baseline_models() -> dict[str, Any]:
    return {
        "logistic_regression": make_pipeline(
            StandardScaler(),
            LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42),
        ),
        "random_forest": RandomForestClassifier(
            n_estimators=200,
            min_samples_leaf=20,
            class_weight="balanced_subsample",
            random_state=42,
            n_jobs=1,
        ),
        "gradient_boosting": GradientBoostingClassifier(random_state=42),
    }


def _split_label_frame(
    label_frame: pd.DataFrame,
    test_ratio: float,
    min_train_rows: int,
    min_test_rows: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if label_frame.empty:
        raise ValueError("label frame is empty")
    split_idx = int(math.floor(len(label_frame) * (1.0 - float(test_ratio))))
    train = label_frame.iloc[:split_idx].copy()
    test = label_frame.iloc[split_idx:].copy()
    if len(train) < int(min_train_rows):
        raise ValueError(f"not enough training rows for baseline fit: {len(train)}")
    if len(test) < int(min_test_rows):
        raise ValueError(f"not enough test rows for baseline evaluation: {len(test)}")
    return train, test


def _historical_tail_probability(test: pd.DataFrame, horizon: int) -> np.ndarray:
    return_col = f"portfolio_return_{int(horizon)}d"
    if return_col not in test.columns:
        raise ValueError(f"missing historical-return feature {return_col}")
    return (test[return_col].to_numpy(dtype=float) <= test["tail_threshold"].to_numpy(dtype=float)).astype(float)


def _fit_predict_probability(
    baseline: str,
    train: pd.DataFrame,
    test: pd.DataFrame,
    feature_names: list[str],
) -> tuple[np.ndarray, str]:
    y_train = train["tail_event"].astype(int).to_numpy()
    x_train = train[feature_names].to_numpy(dtype=float)
    x_test = test[feature_names].to_numpy(dtype=float)
    if np.unique(y_train).size < 2:
        prevalence = float(y_train.mean()) if y_train.size else 0.0
        return np.full(len(test), prevalence, dtype=float), "constant_probability_due_single_class_training"
    model = _baseline_models()[baseline]
    model.fit(x_train, y_train)
    probabilities = model.predict_proba(x_test)[:, 1]
    return np.clip(np.asarray(probabilities, dtype=float), 0.0, 1.0), ""


def _prediction_rows(
    label_frame: pd.DataFrame,
    probabilities: np.ndarray,
    *,
    horizon: int,
    portfolio_name: str,
    market: str,
    baseline: str,
    source: str,
    source_detail: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for idx, (date_idx, row) in enumerate(label_frame.iterrows()):
        rows.append(
            {
                "date": pd.Timestamp(date_idx).date().isoformat(),
                "horizon": int(horizon),
                "portfolio_name": portfolio_name,
                "market": market,
                "baseline": baseline,
                "tail_event": int(row["tail_event"]),
                "probability": float(probabilities[idx]),
                "source": source,
                "source_detail": source_detail,
            }
        )
    return rows


def _metric_rows(predictions: pd.DataFrame) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    group_specs = [
        ("portfolio", ["horizon", "market", "portfolio_name", "baseline"]),
        ("market", ["horizon", "market", "baseline"]),
        ("global", ["horizon", "baseline"]),
    ]
    if predictions.empty:
        return rows
    for scope, group_cols in group_specs:
        for group_key, group in predictions.groupby(group_cols, sort=True, dropna=False):
            if not isinstance(group_key, tuple):
                group_key = (group_key,)
            row: dict[str, Any] = {
                "scope": scope,
                "horizon": "",
                "market": "",
                "portfolio_name": "",
                "baseline": "",
            }
            row.update({column: value for column, value in zip(group_cols, group_key)})
            metrics = crisis_classification_metrics(
                group["tail_event"].astype(int).to_numpy(),
                group["probability"].to_numpy(dtype=float),
            )
            row.update(metrics)
            rows.append(row)
    return rows


def run(config: dict[str, Any], output_dir: Path, allow_sandbox_data: bool) -> dict[str, Any]:
    start_date, end_date = experiment_dates(config)
    crisis_config = config.get("crisis_warning", {})
    allocation_config = config.get("allocation", {})
    horizons = horizons_from_config(config)
    tail_quantile = float(crisis_config.get("tail_quantile", 0.05))
    target_method: TargetMethod = str(crisis_config.get("target_method", "dynamic_quantile"))  # type: ignore[assignment]
    fixed_threshold = crisis_config.get("fixed_threshold")
    fixed_threshold = None if fixed_threshold is None else float(fixed_threshold)
    test_ratio = float(crisis_config.get("baseline_test_ratio", allocation_config.get("test_ratio", 0.20)))
    min_train_rows = int(crisis_config.get("baseline_min_train_rows", 252))
    min_test_rows = int(crisis_config.get("baseline_min_test_rows", 60))

    portfolio_path = config_path(config, "holdout_portfolios", DEFAULT_PORTFOLIOS_PATH)
    artifact_root = config_path(config, "artifact_root", ROOT / "artifacts" / "crisis_warning")
    portfolios = load_holdout_portfolios(portfolio_path)
    api_key = config.get("api_key")

    output_dir.mkdir(parents=True, exist_ok=True)
    store = CrisisWarningArtifactStore(artifact_root=artifact_root)
    artifacts = {horizon: store.ensure(horizon) for horizon in horizons}

    prediction_rows_by_horizon: dict[int, list[dict[str, Any]]] = {horizon: [] for horizon in horizons}
    training_rows: list[dict[str, Any]] = []
    skipped_rows: list[dict[str, Any]] = []

    for portfolio in portfolios:
        try:
            price_df, fetcher = fetch_portfolio_prices(
                portfolio=portfolio,
                start_date=start_date,
                end_date=end_date,
                api_key=api_key,
                allow_sandbox_data=allow_sandbox_data,
            )
        except Exception as exc:
            for horizon in horizons:
                skipped_rows.append(
                    {
                        "portfolio_name": portfolio.name,
                        "market": portfolio.market,
                        "horizon": horizon,
                        "baseline": "all",
                        "stage": "fetch_prices",
                        "error": str(exc),
                    }
                )
            continue

        weights = RiskEngine._normalize_weights(portfolio.weights, len(portfolio.tickers))
        for horizon in horizons:
            try:
                _, _, label_frame, _ = build_eval_frame(
                    price_df=price_df,
                    weights=weights,
                    horizon=horizon,
                    tail_quantile=tail_quantile,
                    target_method=target_method,
                    fixed_threshold=fixed_threshold,
                )
                train, test = _split_label_frame(
                    label_frame=label_frame,
                    test_ratio=test_ratio,
                    min_train_rows=min_train_rows,
                    min_test_rows=min_test_rows,
                )
            except Exception as exc:
                skipped_rows.append(
                    {
                        "portfolio_name": portfolio.name,
                        "market": portfolio.market,
                        "horizon": horizon,
                        "baseline": "all",
                        "stage": "build_eval_frame",
                        "error": str(exc),
                    }
                )
                continue

            artifact = artifacts[horizon]
            feature_names = artifact.feature_names
            baseline_probabilities: dict[str, tuple[np.ndarray, str]] = {}

            try:
                _, calibrated = predict_frame(artifact, test)
                baseline_probabilities["frozen_calibrated_xgboost"] = (calibrated, "")
                raw, _ = predict_frame(artifact, test)
                baseline_probabilities["frozen_raw_xgboost_without_calibration"] = (
                    raw,
                    "ablation_of_calibration_layer",
                )
            except Exception as exc:
                skipped_rows.append(
                    {
                        "portfolio_name": portfolio.name,
                        "market": portfolio.market,
                        "horizon": horizon,
                        "baseline": "frozen_xgboost",
                        "stage": "predict",
                        "error": str(exc),
                    }
                )

            try:
                baseline_probabilities["historical_tail_threshold"] = (
                    _historical_tail_probability(test, horizon),
                    "current_historical_return_breaches_current_tail_threshold",
                )
            except Exception as exc:
                skipped_rows.append(
                    {
                        "portfolio_name": portfolio.name,
                        "market": portfolio.market,
                        "horizon": horizon,
                        "baseline": "historical_tail_threshold",
                        "stage": "predict",
                        "error": str(exc),
                    }
                )

            for baseline in sorted(MODEL_BASELINES):
                try:
                    probabilities, note = _fit_predict_probability(baseline, train, test, feature_names)
                    baseline_probabilities[baseline] = (probabilities, note)
                except Exception as exc:
                    skipped_rows.append(
                        {
                            "portfolio_name": portfolio.name,
                            "market": portfolio.market,
                            "horizon": horizon,
                            "baseline": baseline,
                            "stage": "fit_predict",
                            "error": str(exc),
                        }
                    )

            for baseline, (probabilities, note) in baseline_probabilities.items():
                prediction_rows_by_horizon[horizon].extend(
                    _prediction_rows(
                        label_frame=test,
                        probabilities=probabilities,
                        horizon=horizon,
                        portfolio_name=portfolio.name,
                        market=portfolio.market,
                        baseline=baseline,
                        source=fetcher.last_source,
                        source_detail=fetcher.last_source_detail,
                    )
                )
                training_rows.append(
                    {
                        "horizon": int(horizon),
                        "market": portfolio.market,
                        "portfolio_name": portfolio.name,
                        "baseline": baseline,
                        "train_row_count": int(len(train)),
                        "test_row_count": int(len(test)),
                        "train_positive_count": int(train["tail_event"].sum()),
                        "test_positive_count": int(test["tail_event"].sum()),
                        "test_start": pd.Timestamp(test.index.min()).date().isoformat(),
                        "test_end": pd.Timestamp(test.index.max()).date().isoformat(),
                        "note": note,
                    }
                )

    prediction_frames: list[pd.DataFrame] = []
    for horizon in horizons:
        frame = pd.DataFrame(prediction_rows_by_horizon[horizon], columns=BASELINE_PREDICTION_COLUMNS)
        dataframe_to_csv(frame, output_dir / f"baseline_predictions_h{horizon}.csv")
        if not frame.empty:
            prediction_frames.append(frame)

    all_predictions = (
        pd.concat(prediction_frames, ignore_index=True)
        if prediction_frames
        else pd.DataFrame(columns=BASELINE_PREDICTION_COLUMNS)
    )
    metrics_frame = pd.DataFrame(_metric_rows(all_predictions), columns=BASELINE_METRIC_COLUMNS)
    dataframe_to_csv(metrics_frame, output_dir / "baseline_metrics.csv")
    dataframe_to_csv(
        pd.DataFrame(training_rows, columns=BASELINE_TRAINING_COLUMNS),
        output_dir / "baseline_training_summary.csv",
    )
    dataframe_to_csv(
        pd.DataFrame(skipped_rows, columns=BASELINE_SKIPPED_COLUMNS),
        output_dir / "baseline_eval_skipped.csv",
    )

    audit = artifact_audit_summary(artifact_root, horizons=horizons)
    summary = {
        "allow_sandbox_data": bool(allow_sandbox_data),
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "portfolio_count": len(portfolios),
        "prediction_rows": int(len(all_predictions)),
        "metric_rows": int(len(metrics_frame)),
        "skipped_rows": int(len(skipped_rows)),
        "test_ratio": float(test_ratio),
        "baselines": sorted(
            {
                "frozen_calibrated_xgboost",
                "frozen_raw_xgboost_without_calibration",
                "historical_tail_threshold",
                *MODEL_BASELINES,
            }
        ),
        "artifact_hashes": {
            key: value.get("artifact_hash") for key, value in audit.get("horizons", {}).items()
        },
    }
    write_json(output_dir / "baseline_audit_summary.json", summary)
    return summary


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run crisis-warning baseline comparisons.")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH))
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--allow-sandbox-data", default=None)
    return parser


def main() -> int:
    args = make_parser().parse_args()
    config = load_config(args.config)
    allow_sandbox_data = parse_bool(
        args.allow_sandbox_data
        if args.allow_sandbox_data is not None
        else config.get("allow_sandbox_data", False)
    )
    output_dir = output_dir_from_args(args.output_dir, config, default=DEFAULT_RESULTS_DIR)
    summary = run(config=config, output_dir=project_path(output_dir), allow_sandbox_data=allow_sandbox_data)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
