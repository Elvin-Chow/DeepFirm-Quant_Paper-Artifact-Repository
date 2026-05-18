"""Run holdout out-of-sample allocation comparisons for the paper."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.services import PortfolioAnalysisService  # noqa: E402
from experiments.common import (  # noqa: E402
    DEFAULT_CONFIG_PATH,
    DEFAULT_PORTFOLIOS_PATH,
    DEFAULT_RESULTS_DIR,
    HoldoutPortfolio,
    align_test_with_benchmark,
    config_path,
    dataframe_to_csv,
    experiment_dates,
    fetch_benchmark_returns,
    fetch_portfolio_prices,
    load_config,
    load_holdout_portfolios,
    output_dir_from_args,
    parse_bool,
    project_path,
)
from experiments.metrics import cumulative_from_log_returns, strategy_performance_metrics  # noqa: E402
from models.allocation_policy import AllocationPolicyEngine, AllocationPolicyResult  # noqa: E402
from models.portfolio_opt import BayesianOptimizer  # noqa: E402
from models.risk_engine import RiskEngine  # noqa: E402


RETURNS_COLUMNS = [
    "date",
    "portfolio_name",
    "market",
    "strategy",
    "daily_return",
    "cumulative_return",
    "benchmark_daily_return",
    "benchmark_cumulative_return",
    "decision_policy",
]

METRICS_COLUMNS = [
    "portfolio_name",
    "market",
    "strategy",
    "decision_policy",
    "policy_asof",
    "policy_confidence",
    "policy_max_weight",
    "policy_min_weight",
    "policy_turnover_penalty",
    "policy_concentration_penalty",
    "policy_risk_level",
    "policy_regime",
    "policy_anomaly_impact",
    "oos_leakage_guard",
    "row_count",
    "cumulative_return",
    "benchmark_cumulative_return",
    "benchmark_excess_return",
    "annualized_return",
    "annualized_volatility",
    "max_drawdown",
    "expected_shortfall",
    "sharpe",
    "information_ratio",
    "turnover",
    "model_score",
    "model_grade",
    "model_score_risk_control",
    "model_score_profitability",
    "model_score_alpha",
    "model_score_stability",
    "model_score_win_rate",
]

ABLATION_COLUMNS = [
    "portfolio_name",
    "market",
    "ablation",
    "reference_strategy",
    "cumulative_return",
    "delta_cumulative_return",
    "sharpe",
    "delta_sharpe",
    "information_ratio",
    "delta_information_ratio",
    "model_score",
    "delta_model_score",
]


@dataclass
class StrategyPath:
    strategy: str
    dates: pd.DatetimeIndex
    daily_returns: np.ndarray
    benchmark_daily: np.ndarray
    turnover: float
    decision_policy: str = ""
    allocation_policy: AllocationPolicyResult | None = None


def _normalize(weights: np.ndarray) -> np.ndarray:
    weights = np.asarray(weights, dtype=float)
    weights = np.nan_to_num(weights, nan=0.0, posinf=0.0, neginf=0.0)
    weights = np.clip(weights, 0.0, None)
    total = float(weights.sum())
    if total <= 1e-12:
        return np.ones(len(weights), dtype=float) / len(weights)
    return weights / total


def _turnover(weights_by_rebalance: list[np.ndarray], initial_weights: np.ndarray) -> float:
    if not weights_by_rebalance:
        return 0.0
    previous = _normalize(initial_weights)
    total = 0.0
    for weights in weights_by_rebalance:
        current = _normalize(weights)
        total += float(np.abs(current - previous).sum())
        previous = current
    return total


def _inverse_vol_weights(returns_df: pd.DataFrame) -> np.ndarray:
    vol = returns_df.std().to_numpy(dtype=float)
    inv_vol = 1.0 / np.maximum(vol, 1e-12)
    return _normalize(inv_vol)


def _fixed_weight_path(
    strategy: str,
    test_df: pd.DataFrame,
    benchmark_daily: np.ndarray,
    weights: np.ndarray,
) -> StrategyPath:
    daily = test_df.to_numpy(dtype=float) @ _normalize(weights)
    return StrategyPath(
        strategy=strategy,
        dates=test_df.index,
        daily_returns=daily,
        benchmark_daily=benchmark_daily,
        turnover=0.0,
    )


def _walk_forward_weights(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    rebalance_days: int,
    weight_fn: Callable[[pd.DataFrame, np.ndarray | None], np.ndarray],
    initial_weights: np.ndarray,
) -> tuple[np.ndarray, list[np.ndarray]]:
    chunks: list[np.ndarray] = []
    weights_by_rebalance: list[np.ndarray] = []
    cursor = 0
    previous_weights: np.ndarray | None = None
    while cursor < len(test_df):
        rolling_train = pd.concat([train_df, test_df.iloc[:cursor]]).tail(max(252, len(train_df)))
        weights = _normalize(weight_fn(rolling_train, previous_weights))
        segment = test_df.iloc[cursor : cursor + rebalance_days]
        chunks.append(segment.to_numpy(dtype=float) @ weights)
        weights_by_rebalance.append(weights)
        previous_weights = weights
        cursor += rebalance_days
    if not chunks:
        raise RuntimeError("walk-forward evaluation produced no segments")
    return np.concatenate(chunks), weights_by_rebalance


def inverse_volatility_path(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    benchmark_daily: np.ndarray,
    rebalance_days: int,
    initial_weights: np.ndarray,
) -> StrategyPath:
    daily, weights = _walk_forward_weights(
        train_df=train_df,
        test_df=test_df,
        rebalance_days=rebalance_days,
        initial_weights=initial_weights,
        weight_fn=lambda rolling, _prev: _inverse_vol_weights(rolling),
    )
    return StrategyPath(
        strategy="inverse_volatility",
        dates=test_df.index,
        daily_returns=daily,
        benchmark_daily=benchmark_daily,
        turnover=_turnover(weights, initial_weights),
    )


def mean_variance_path(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    benchmark_daily: np.ndarray,
    rebalance_days: int,
    initial_weights: np.ndarray,
    optimizer: BayesianOptimizer,
    config: dict[str, Any],
) -> StrategyPath:
    n_assets = test_df.shape[1]

    def solve(rolling: pd.DataFrame, previous: np.ndarray | None) -> np.ndarray:
        prior_returns, cov_matrix = RiskEngine.prepare_optimization_inputs(rolling, n_assets)
        prior = previous if previous is not None else initial_weights
        return optimizer.optimize_weights(
            prior_returns,
            cov_matrix,
            prior_weights=prior,
            risk_aversion=float(config.get("risk_aversion", 2.5)),
            max_weight=float(config.get("max_weight", 0.40)),
            min_weight=float(config.get("min_weight", 0.02)),
            turnover_penalty=float(config.get("turnover_penalty", 0.005)),
            concentration_penalty=float(config.get("concentration_penalty", 0.005)),
        )

    daily, weights = _walk_forward_weights(
        train_df=train_df,
        test_df=test_df,
        rebalance_days=rebalance_days,
        initial_weights=initial_weights,
        weight_fn=solve,
    )
    return StrategyPath(
        strategy="mean_variance",
        dates=test_df.index,
        daily_returns=daily,
        benchmark_daily=benchmark_daily,
        turnover=_turnover(weights, initial_weights),
    )


def black_litterman_daily(
    portfolio: HoldoutPortfolio,
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    rebalance_days: int,
    optimizer: BayesianOptimizer,
    config: dict[str, Any],
    controls: dict[str, float],
) -> tuple[np.ndarray, np.ndarray, list[np.ndarray], list[np.ndarray]]:
    """Return prior and raw BL walk-forward daily returns plus rebalance weights."""
    n_assets = len(portfolio.tickers)
    chunks_prior: list[np.ndarray] = []
    chunks_raw: list[np.ndarray] = []
    weights_prior: list[np.ndarray] = []
    weights_raw: list[np.ndarray] = []
    cursor = 0
    while cursor < len(test_df):
        rolling_train = pd.concat([train_df, test_df.iloc[:cursor]]).tail(max(252, len(train_df)))
        prior_returns, cov_matrix = RiskEngine.prepare_optimization_inputs(rolling_train, n_assets)
        result = optimizer.optimize_with_views(
            tickers=portfolio.tickers,
            prior_returns=prior_returns,
            cov_matrix=cov_matrix,
            views=[],
            risk_aversion=float(config.get("risk_aversion", 2.5)),
            weights=portfolio.weights,
            max_weight=float(controls["max_weight"]),
            min_weight=float(controls["min_weight"]),
            turnover_penalty=float(controls["turnover_penalty"]),
            concentration_penalty=float(controls["concentration_penalty"]),
            market_caps=None,
            n_observations=len(rolling_train),
        )
        segment = test_df.iloc[cursor : cursor + rebalance_days]
        prior_weights = np.asarray(result.prior_weights, dtype=float)
        raw_weights = np.asarray(result.raw_posterior_weights, dtype=float)
        chunks_prior.append(segment.to_numpy(dtype=float) @ prior_weights)
        chunks_raw.append(segment.to_numpy(dtype=float) @ raw_weights)
        weights_prior.append(prior_weights)
        weights_raw.append(raw_weights)
        cursor += rebalance_days

    if not chunks_raw:
        raise RuntimeError("Black-Litterman walk-forward produced no segments")
    return (
        np.concatenate(chunks_prior),
        np.concatenate(chunks_raw),
        weights_prior,
        weights_raw,
    )


def raw_black_litterman_path(
    portfolio: HoldoutPortfolio,
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    benchmark_daily: np.ndarray,
    rebalance_days: int,
    optimizer: BayesianOptimizer,
    config: dict[str, Any],
    initial_weights: np.ndarray,
) -> StrategyPath:
    controls = {
        "max_weight": float(config.get("max_weight", 0.40)),
        "min_weight": float(config.get("min_weight", 0.02)),
        "turnover_penalty": float(config.get("turnover_penalty", 0.005)),
        "concentration_penalty": float(config.get("concentration_penalty", 0.005)),
    }
    _, raw_daily, _, raw_weights = black_litterman_daily(
        portfolio=portfolio,
        train_df=train_df,
        test_df=test_df,
        rebalance_days=rebalance_days,
        optimizer=optimizer,
        config=config,
        controls=controls,
    )
    return StrategyPath(
        strategy="raw_black_litterman",
        dates=test_df.index,
        daily_returns=raw_daily,
        benchmark_daily=benchmark_daily,
        turnover=_turnover(raw_weights, initial_weights),
    )


def smart_policy_controls(
    portfolio: HoldoutPortfolio,
    price_df: pd.DataFrame,
    train_df: pd.DataFrame,
    config: dict[str, Any],
) -> AllocationPolicyResult:
    policy_price_df = price_df.loc[: train_df.index[-1]]
    return AllocationPolicyEngine.resolve_from_prices(
        tickers=portfolio.tickers,
        price_df=policy_price_df,
        weights=portfolio.weights,
        mode="smart",
        requested_max_weight=float(config.get("max_weight", 0.40)),
        requested_min_weight=float(config.get("min_weight", 0.02)),
        requested_turnover_penalty=float(config.get("turnover_penalty", 0.005)),
        requested_concentration_penalty=float(config.get("concentration_penalty", 0.005)),
        asof_date=train_df.index[-1].strftime("%Y-%m-%d"),
        oos_leakage_guard=True,
    )


def smart_policy_paths(
    portfolio: HoldoutPortfolio,
    price_df: pd.DataFrame,
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    benchmark_daily: np.ndarray,
    rebalance_days: int,
    optimizer: BayesianOptimizer,
    service: PortfolioAnalysisService,
    config: dict[str, Any],
    initial_weights: np.ndarray,
    risk_free_rate: float,
) -> tuple[StrategyPath, StrategyPath]:
    policy = smart_policy_controls(portfolio, price_df, train_df, config)
    controls = {
        "max_weight": float(policy.max_weight),
        "min_weight": float(policy.min_weight),
        "turnover_penalty": float(policy.turnover_penalty)
        * (252.0 / max(float(len(train_df)), 30.0)),
        "concentration_penalty": float(policy.concentration_penalty)
        * (252.0 / max(float(len(train_df)), 30.0)),
    }
    prior_daily, raw_daily, prior_weights, raw_weights = black_litterman_daily(
        portfolio=portfolio,
        train_df=train_df,
        test_df=test_df,
        rebalance_days=rebalance_days,
        optimizer=optimizer,
        config=config,
        controls=controls,
    )
    prior_metrics = RiskEngine.compute_performance_metrics(
        pd.DataFrame({"strategy": prior_daily}, index=test_df.index),
        np.array([1.0]),
        risk_free_rate=risk_free_rate,
    )
    raw_metrics = RiskEngine.compute_performance_metrics(
        pd.DataFrame({"strategy": raw_daily}, index=test_df.index),
        np.array([1.0]),
        risk_free_rate=risk_free_rate,
    )
    bench_metrics = RiskEngine.compute_performance_metrics(
        pd.DataFrame({"benchmark": benchmark_daily}, index=test_df.index),
        np.array([1.0]),
        risk_free_rate=risk_free_rate,
    )
    prior_scored = service.score_oos_metrics(prior_metrics, prior_daily, benchmark_daily, bench_metrics)
    raw_scored = service.score_oos_metrics(raw_metrics, raw_daily, benchmark_daily, bench_metrics)
    decision_weights, decision_policy = service.select_oos_guard_weights(
        np.asarray(prior_weights[-1], dtype=float),
        np.asarray(raw_weights[-1], dtype=float),
        prior_metrics,
        raw_metrics,
        float(prior_scored["score"]["total_score"]),
        float(raw_scored["score"]["total_score"]),
        True,
        raw_excess_return=float(raw_scored["excess_return"]),
        raw_information_ratio=float(raw_scored["information_ratio"]),
        ml_risk_level=policy.risk_level,
        regime=policy.regime,
        anomaly_impact=policy.anomaly_impact,
    )
    if decision_policy == "defensive_blend":
        guarded_daily = 0.40 * prior_daily + 0.60 * raw_daily
    elif decision_policy == "balanced_blend":
        guarded_daily = 0.50 * prior_daily + 0.50 * raw_daily
    else:
        guarded_daily = raw_daily.copy()

    raw_path = StrategyPath(
        strategy="smart_policy",
        dates=test_df.index,
        daily_returns=raw_daily,
        benchmark_daily=benchmark_daily,
        turnover=_turnover(raw_weights, initial_weights),
        decision_policy="raw",
        allocation_policy=policy,
    )
    guarded_path = StrategyPath(
        strategy="smart_policy_oos_guard",
        dates=test_df.index,
        daily_returns=guarded_daily,
        benchmark_daily=benchmark_daily,
        turnover=float(np.abs(_normalize(decision_weights) - initial_weights).sum()),
        decision_policy=decision_policy,
        allocation_policy=policy,
    )
    return raw_path, guarded_path


def returns_rows(portfolio: HoldoutPortfolio, path: StrategyPath) -> list[dict[str, Any]]:
    strategy_cumulative = cumulative_from_log_returns(path.daily_returns)
    benchmark_cumulative = cumulative_from_log_returns(path.benchmark_daily)
    rows: list[dict[str, Any]] = []
    for idx, date_idx in enumerate(path.dates):
        rows.append(
            {
                "date": pd.Timestamp(date_idx).date().isoformat(),
                "portfolio_name": portfolio.name,
                "market": portfolio.market,
                "strategy": path.strategy,
                "daily_return": float(path.daily_returns[idx]),
                "cumulative_return": float(strategy_cumulative[idx]),
                "benchmark_daily_return": float(path.benchmark_daily[idx]),
                "benchmark_cumulative_return": float(benchmark_cumulative[idx]),
                "decision_policy": path.decision_policy,
            }
        )
    return rows


def metrics_row(
    portfolio: HoldoutPortfolio,
    path: StrategyPath,
    risk_free_rate: float,
) -> dict[str, Any]:
    metrics = strategy_performance_metrics(
        dates=path.dates,
        strategy_daily=path.daily_returns,
        benchmark_daily=path.benchmark_daily,
        turnover=path.turnover,
        risk_free_rate=risk_free_rate,
    )
    row: dict[str, Any] = {
        "portfolio_name": portfolio.name,
        "market": portfolio.market,
        "strategy": path.strategy,
        "decision_policy": path.decision_policy,
    }
    if path.allocation_policy is not None:
        row.update(
            {
                "policy_asof": path.allocation_policy.policy_asof,
                "policy_confidence": path.allocation_policy.confidence,
                "policy_max_weight": path.allocation_policy.max_weight,
                "policy_min_weight": path.allocation_policy.min_weight,
                "policy_turnover_penalty": path.allocation_policy.turnover_penalty,
                "policy_concentration_penalty": path.allocation_policy.concentration_penalty,
                "policy_risk_level": path.allocation_policy.risk_level,
                "policy_regime": path.allocation_policy.regime,
                "policy_anomaly_impact": path.allocation_policy.anomaly_impact,
                "oos_leakage_guard": path.allocation_policy.oos_leakage_guard,
            }
        )
    row.update(metrics)
    return row


def ablation_rows(metrics_frame: pd.DataFrame) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if metrics_frame.empty:
        return rows
    for portfolio_name, group in metrics_frame.groupby("portfolio_name", sort=True):
        reference = group[group["strategy"] == "smart_policy_oos_guard"]
        if reference.empty:
            reference = group[group["strategy"] == "raw_black_litterman"]
        if reference.empty:
            continue
        ref = reference.iloc[0]
        for _, row in group.iterrows():
            rows.append(
                {
                    "portfolio_name": portfolio_name,
                    "market": row["market"],
                    "ablation": row["strategy"],
                    "reference_strategy": ref["strategy"],
                    "cumulative_return": row["cumulative_return"],
                    "delta_cumulative_return": row["cumulative_return"] - ref["cumulative_return"],
                    "sharpe": row["sharpe"],
                    "delta_sharpe": row["sharpe"] - ref["sharpe"],
                    "information_ratio": row["information_ratio"],
                    "delta_information_ratio": row["information_ratio"] - ref["information_ratio"],
                    "model_score": row["model_score"],
                    "delta_model_score": row["model_score"] - ref["model_score"],
                }
            )
    return rows


def enabled_baselines(config: dict[str, Any]) -> dict[str, bool]:
    baselines = config.get("baselines", {})
    return {
        "equal_weight": parse_bool(baselines.get("equal_weight", True)),
        "inverse_volatility": parse_bool(baselines.get("inverse_volatility", True)),
        "mean_variance": parse_bool(baselines.get("mean_variance", True)),
        "raw_black_litterman": parse_bool(baselines.get("raw_black_litterman", True)),
        "smart_policy": parse_bool(baselines.get("smart_policy", True)),
        "smart_policy_oos_guard": parse_bool(baselines.get("smart_policy_oos_guard", True)),
    }


def evaluate_portfolio(
    portfolio: HoldoutPortfolio,
    price_df: pd.DataFrame,
    benchmark_returns: pd.Series,
    config: dict[str, Any],
    optimizer: BayesianOptimizer,
    service: PortfolioAnalysisService,
) -> list[StrategyPath]:
    returns_df = RiskEngine.sanitize_returns(RiskEngine.compute_log_returns(price_df))
    train_df, raw_test_df = RiskEngine.split_returns(returns_df, float(config.get("test_ratio", 0.20)))
    test_df, aligned_benchmark = align_test_with_benchmark(raw_test_df, benchmark_returns)
    benchmark_daily = aligned_benchmark.to_numpy(dtype=float)
    initial_weights = RiskEngine._normalize_weights(portfolio.weights, len(portfolio.tickers))
    rebalance_days = int(config.get("rebalance_days", 21))
    baselines = enabled_baselines(config)

    paths: list[StrategyPath] = []
    if baselines["equal_weight"]:
        equal = np.ones(len(portfolio.tickers), dtype=float) / len(portfolio.tickers)
        paths.append(_fixed_weight_path("equal_weight", test_df, benchmark_daily, equal))
    if baselines["inverse_volatility"]:
        paths.append(inverse_volatility_path(train_df, test_df, benchmark_daily, rebalance_days, initial_weights))
    if baselines["mean_variance"]:
        paths.append(
            mean_variance_path(
                train_df,
                test_df,
                benchmark_daily,
                rebalance_days,
                initial_weights,
                optimizer,
                config,
            )
        )
    if baselines["raw_black_litterman"]:
        paths.append(
            raw_black_litterman_path(
                portfolio,
                train_df,
                test_df,
                benchmark_daily,
                rebalance_days,
                optimizer,
                config,
                initial_weights,
            )
        )
    if baselines["smart_policy"] or baselines["smart_policy_oos_guard"]:
        smart_raw, smart_guard = smart_policy_paths(
            portfolio=portfolio,
            price_df=price_df,
            train_df=train_df,
            test_df=test_df,
            benchmark_daily=benchmark_daily,
            rebalance_days=rebalance_days,
            optimizer=optimizer,
            service=service,
            config=config,
            initial_weights=initial_weights,
            risk_free_rate=float(config.get("risk_free_rate", 0.0) or 0.0),
        )
        if baselines["smart_policy"]:
            paths.append(smart_raw)
        if baselines["smart_policy_oos_guard"]:
            paths.append(smart_guard)
    return paths


def run(config: dict[str, Any], output_dir: Path, allow_sandbox_data: bool) -> dict[str, Any]:
    start_date, end_date = experiment_dates(config)
    allocation_config = config.get("allocation", {})
    portfolio_path = config_path(config, "holdout_portfolios", DEFAULT_PORTFOLIOS_PATH)
    portfolios = load_holdout_portfolios(portfolio_path)
    api_key = config.get("api_key")
    risk_free_rate = float(allocation_config.get("risk_free_rate", 0.0) or 0.0)

    output_dir.mkdir(parents=True, exist_ok=True)
    optimizer = BayesianOptimizer()
    service = PortfolioAnalysisService(optimizer=optimizer)
    returns_payload: list[dict[str, Any]] = []
    metrics_payload: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []

    for portfolio in portfolios:
        try:
            price_df, fetcher = fetch_portfolio_prices(
                portfolio=portfolio,
                start_date=start_date,
                end_date=end_date,
                api_key=api_key,
                allow_sandbox_data=allow_sandbox_data,
            )
            benchmark_returns = fetch_benchmark_returns(
                service=service,
                fetcher=fetcher,
                symbol=portfolio.benchmark,
                start_date=start_date,
                end_date=end_date,
                market=portfolio.market,
            )
            paths = evaluate_portfolio(
                portfolio=portfolio,
                price_df=price_df,
                benchmark_returns=benchmark_returns,
                config=allocation_config,
                optimizer=optimizer,
                service=service,
            )
        except Exception as exc:
            skipped.append(
                {
                    "portfolio_name": portfolio.name,
                    "market": portfolio.market,
                    "stage": "evaluate",
                    "error": str(exc),
                }
            )
            continue

        for path in paths:
            returns_payload.extend(returns_rows(portfolio, path))
            metrics_payload.append(metrics_row(portfolio, path, risk_free_rate))

    returns_frame = pd.DataFrame(returns_payload, columns=RETURNS_COLUMNS)
    metrics_frame = pd.DataFrame(metrics_payload, columns=METRICS_COLUMNS)
    ablation_frame = pd.DataFrame(ablation_rows(metrics_frame), columns=ABLATION_COLUMNS)
    dataframe_to_csv(returns_frame, output_dir / "allocation_oos_returns.csv")
    dataframe_to_csv(metrics_frame, output_dir / "allocation_oos_metrics.csv")
    dataframe_to_csv(ablation_frame, output_dir / "ablation_metrics.csv")
    dataframe_to_csv(pd.DataFrame(skipped), output_dir / "allocation_oos_skipped.csv")
    return {
        "portfolio_count": len(portfolios),
        "evaluated_portfolios": int(metrics_frame["portfolio_name"].nunique()) if not metrics_frame.empty else 0,
        "strategy_rows": int(len(metrics_frame)),
        "return_rows": int(len(returns_frame)),
        "skipped_rows": int(len(skipped)),
        "allow_sandbox_data": bool(allow_sandbox_data),
    }


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run allocation OOS holdout evaluation.")
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
