"""Run external holdout evaluation for fixed crisis warning artifacts."""

from __future__ import annotations

import argparse
import json
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
    DEFAULT_PORTFOLIOS_PATH,
    DEFAULT_RESULTS_DIR,
    HoldoutPortfolio,
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
from experiments.metrics import crisis_metric_rows  # noqa: E402
from models.crisis_warning_engine import (  # noqa: E402
    CrisisWarningArtifact,
    CrisisWarningArtifactStore,
    CrisisWarningEngine,
    TargetMethod,
)
from models.ml_risk_engine import MLRiskEngine  # noqa: E402
from models.risk_engine import RiskEngine  # noqa: E402
from models.xgboost_runtime import import_xgboost  # noqa: E402


PREDICTION_COLUMNS = [
    "date",
    "horizon",
    "portfolio_name",
    "market",
    "tickers",
    "weights",
    "benchmark",
    "future_horizon_return",
    "tail_threshold",
    "tail_event",
    "raw_probability",
    "crisis_probability",
    "warning_level",
    "source",
    "source_detail",
    "data_warnings",
    "eval_warning",
]

SHAP_COLUMNS = [
    "date",
    "horizon",
    "portfolio_name",
    "market",
    "feature",
    "feature_value",
    "shap_value",
]

CRISIS_PORTFOLIO_METRIC_COLUMNS = [
    "horizon",
    "market",
    "portfolio_name",
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

CRISIS_MARKET_METRIC_COLUMNS = [
    column
    for column in CRISIS_PORTFOLIO_METRIC_COLUMNS
    if column != "portfolio_name"
]


def _manual_eval_frame(
    price_df: pd.DataFrame,
    weights: np.ndarray,
    horizon: int,
    tail_quantile: float,
    target_method: TargetMethod,
    fixed_threshold: float | None,
) -> tuple[pd.DataFrame, pd.Series, pd.DataFrame]:
    prices = MLRiskEngine._normalize_price_frame(price_df)
    portfolio_returns = CrisisWarningEngine.portfolio_returns(prices, weights)
    features = MLRiskEngine.build_feature_frame(prices, weights)
    label_frame = CrisisWarningEngine.build_label_frame(
        features=features,
        portfolio_returns=portfolio_returns,
        horizon=horizon,
        tail_quantile=tail_quantile,
        target_method=target_method,
        fixed_threshold=fixed_threshold,
    )
    feature_values = label_frame[CrisisWarningEngine.feature_columns].to_numpy(dtype=float)
    if label_frame.empty or not np.isfinite(feature_values).all():
        raise ValueError("holdout evaluation frame has no complete finite feature rows")
    return features, portfolio_returns, label_frame


def build_eval_frame(
    price_df: pd.DataFrame,
    weights: np.ndarray,
    horizon: int,
    tail_quantile: float,
    target_method: TargetMethod,
    fixed_threshold: float | None,
) -> tuple[pd.DataFrame, pd.Series, pd.DataFrame, str]:
    """Build PIT features/labels, relaxing only training-class gates for holdout eval."""
    try:
        features, portfolio_returns, label_frame = CrisisWarningEngine.build_training_frame(
            price_df=price_df,
            weights=weights,
            horizon=horizon,
            tail_quantile=tail_quantile,
            target_method=target_method,
            fixed_threshold=fixed_threshold,
        )
        return features, portfolio_returns, label_frame, ""
    except ValueError as exc:
        message = str(exc)
        relaxable = (
            "positive tail events" in message
            or "both positive and negative" in message
            or "complete training rows" in message
        )
        if not relaxable:
            raise
        features, portfolio_returns, label_frame = _manual_eval_frame(
            price_df=price_df,
            weights=weights,
            horizon=horizon,
            tail_quantile=tail_quantile,
            target_method=target_method,
            fixed_threshold=fixed_threshold,
        )
        return features, portfolio_returns, label_frame, f"degraded_holdout_frame: {message}"


def predict_frame(
    artifact: CrisisWarningArtifact,
    label_frame: pd.DataFrame,
) -> tuple[np.ndarray, np.ndarray]:
    feature_names = artifact.feature_names
    CrisisWarningEngine.validate_feature_schema(feature_names, CrisisWarningEngine.feature_columns)
    features = label_frame[feature_names].replace([np.inf, -np.inf], np.nan)
    if features.isna().any().any():
        raise ValueError("holdout crisis warning feature frame contains non-finite values")
    raw = np.asarray(artifact.model.predict_proba(features)[:, 1], dtype=float)
    if artifact.calibration is None:
        calibrated = raw.copy()
    else:
        calibrated = np.asarray([artifact.calibration.predict(value) for value in raw], dtype=float)
    return np.clip(raw, 0.0, 1.0), np.clip(calibrated, 0.0, 1.0)


def prediction_rows(
    portfolio: HoldoutPortfolio,
    horizon: int,
    label_frame: pd.DataFrame,
    raw_probabilities: np.ndarray,
    probabilities: np.ndarray,
    source: str,
    source_detail: str,
    data_warnings: list[str],
    eval_warning: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    joined_warnings = " | ".join([*data_warnings, *([eval_warning] if eval_warning else [])])
    tickers = ",".join(portfolio.tickers)
    weights = ",".join(f"{weight:.8f}" for weight in portfolio.weights)
    for idx, (date_idx, row) in enumerate(label_frame.iterrows()):
        probability = float(probabilities[idx])
        rows.append(
            {
                "date": pd.Timestamp(date_idx).date().isoformat(),
                "horizon": int(horizon),
                "portfolio_name": portfolio.name,
                "market": portfolio.market,
                "tickers": tickers,
                "weights": weights,
                "benchmark": portfolio.benchmark,
                "future_horizon_return": float(row["future_horizon_return"]),
                "tail_threshold": float(row["tail_threshold"]),
                "tail_event": int(row["tail_event"]),
                "raw_probability": float(raw_probabilities[idx]),
                "crisis_probability": probability,
                "warning_level": CrisisWarningEngine.warning_level(probability),
                "source": source,
                "source_detail": source_detail,
                "data_warnings": joined_warnings,
                "eval_warning": eval_warning,
            }
        )
    return rows


def native_contribution_rows(
    artifact: CrisisWarningArtifact,
    label_frame: pd.DataFrame,
    portfolio: HoldoutPortfolio,
    horizon: int,
    max_rows: int,
) -> list[dict[str, Any]]:
    """Return native XGBoost contribution rows for SHAP-style driver plots."""
    if max_rows <= 0 or label_frame.empty:
        return []
    try:
        xgb = import_xgboost()
        feature_names = artifact.feature_names
        sample = label_frame.tail(min(int(max_rows), len(label_frame)))
        matrix = xgb.DMatrix(sample[feature_names], feature_names=feature_names)
        contribs = np.asarray(artifact.model.get_booster().predict(matrix, pred_contribs=True), dtype=float)
        if contribs.ndim != 2 or contribs.shape[1] != len(feature_names) + 1:
            return []
    except Exception:
        return []

    rows: list[dict[str, Any]] = []
    values = sample[feature_names].to_numpy(dtype=float)
    for row_idx, date_idx in enumerate(sample.index):
        for feature_idx, feature in enumerate(feature_names):
            rows.append(
                {
                    "date": pd.Timestamp(date_idx).date().isoformat(),
                    "horizon": int(horizon),
                    "portfolio_name": portfolio.name,
                    "market": portfolio.market,
                    "feature": feature,
                    "feature_value": float(values[row_idx, feature_idx]),
                    "shap_value": float(contribs[row_idx, feature_idx]),
                }
            )
    return rows


def run(config: dict[str, Any], output_dir: Path, allow_sandbox_data: bool) -> dict[str, Any]:
    start_date, end_date = experiment_dates(config)
    crisis_config = config.get("crisis_warning", {})
    horizons = horizons_from_config(config)
    tail_quantile = float(crisis_config.get("tail_quantile", 0.05))
    target_method: TargetMethod = str(crisis_config.get("target_method", "dynamic_quantile"))  # type: ignore[assignment]
    fixed_threshold = crisis_config.get("fixed_threshold")
    fixed_threshold = None if fixed_threshold is None else float(fixed_threshold)
    write_shap_drivers = parse_bool(crisis_config.get("write_shap_drivers", True))
    max_shap_rows = int(crisis_config.get("max_shap_rows_per_portfolio", 500))

    portfolio_path = config_path(config, "holdout_portfolios", DEFAULT_PORTFOLIOS_PATH)
    artifact_root = config_path(config, "artifact_root", ROOT / "artifacts" / "crisis_warning")
    portfolios = load_holdout_portfolios(portfolio_path)
    api_key = config.get("api_key")

    output_dir.mkdir(parents=True, exist_ok=True)
    store = CrisisWarningArtifactStore(artifact_root=artifact_root)
    artifacts = {horizon: store.ensure(horizon) for horizon in horizons}

    prediction_rows_by_horizon: dict[int, list[dict[str, Any]]] = {horizon: [] for horizon in horizons}
    shap_rows: list[dict[str, Any]] = []
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
                        "stage": "fetch_prices",
                        "error": str(exc),
                    }
                )
            continue

        weights = RiskEngine._normalize_weights(portfolio.weights, len(portfolio.tickers))
        for horizon in horizons:
            try:
                _, _, label_frame, eval_warning = build_eval_frame(
                    price_df=price_df,
                    weights=weights,
                    horizon=horizon,
                    tail_quantile=tail_quantile,
                    target_method=target_method,
                    fixed_threshold=fixed_threshold,
                )
                artifact = artifacts[horizon]
                raw_probabilities, probabilities = predict_frame(artifact, label_frame)
                prediction_rows_by_horizon[horizon].extend(
                    prediction_rows(
                        portfolio=portfolio,
                        horizon=horizon,
                        label_frame=label_frame,
                        raw_probabilities=raw_probabilities,
                        probabilities=probabilities,
                        source=fetcher.last_source,
                        source_detail=fetcher.last_source_detail,
                        data_warnings=list(fetcher.data_warnings),
                        eval_warning=eval_warning,
                    )
                )
                if write_shap_drivers:
                    shap_rows.extend(
                        native_contribution_rows(
                            artifact=artifact,
                            label_frame=label_frame,
                            portfolio=portfolio,
                            horizon=horizon,
                            max_rows=max_shap_rows,
                        )
                    )
            except Exception as exc:
                skipped_rows.append(
                    {
                        "portfolio_name": portfolio.name,
                        "market": portfolio.market,
                        "horizon": horizon,
                        "stage": "evaluate",
                        "error": str(exc),
                    }
                )

    prediction_frames: list[pd.DataFrame] = []
    for horizon in horizons:
        frame = pd.DataFrame(prediction_rows_by_horizon[horizon], columns=PREDICTION_COLUMNS)
        dataframe_to_csv(frame, output_dir / f"crisis_predictions_h{horizon}.csv")
        if not frame.empty:
            prediction_frames.append(frame)

    all_predictions = (
        pd.concat(prediction_frames, ignore_index=True)
        if prediction_frames
        else pd.DataFrame(columns=PREDICTION_COLUMNS)
    )
    metrics_by_portfolio = pd.DataFrame(
        crisis_metric_rows(
            all_predictions,
            ["horizon", "market", "portfolio_name"],
        ),
        columns=CRISIS_PORTFOLIO_METRIC_COLUMNS,
    )
    metrics_by_market = pd.DataFrame(
        crisis_metric_rows(
            all_predictions,
            ["horizon", "market"],
        ),
        columns=CRISIS_MARKET_METRIC_COLUMNS,
    )
    dataframe_to_csv(metrics_by_portfolio, output_dir / "crisis_metrics_by_portfolio.csv")
    dataframe_to_csv(metrics_by_market, output_dir / "crisis_metrics_by_market.csv")
    dataframe_to_csv(pd.DataFrame(shap_rows, columns=SHAP_COLUMNS), output_dir / "crisis_shap_drivers.csv")
    dataframe_to_csv(pd.DataFrame(skipped_rows), output_dir / "crisis_eval_skipped.csv")

    audit = artifact_audit_summary(artifact_root, horizons=horizons)
    audit["run"] = {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "allow_sandbox_data": bool(allow_sandbox_data),
        "portfolio_count": len(portfolios),
        "prediction_rows": int(len(all_predictions)),
        "skipped_rows": int(len(skipped_rows)),
    }
    write_json(output_dir / "artifact_audit_summary.json", audit)
    return audit["run"]


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run crisis warning external holdout evaluation.")
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
