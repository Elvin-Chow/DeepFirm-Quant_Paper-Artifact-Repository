"""Shared helpers for the independent paper experiment scripts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Iterable, Sequence

import numpy as np
import pandas as pd
import yaml

from backend.services import BENCHMARKS, PortfolioAnalysisService
from data_pipeline import MarketAligner, SmartFetcher
from models.crisis_warning_artifact_hash import compute_artifact_hash, sha256_file
from models.market_validation import MarketMode
from models.risk_engine import RiskEngine


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "experiments" / "paper_eval_config.yaml"
DEFAULT_PORTFOLIOS_PATH = PROJECT_ROOT / "experiments" / "portfolios" / "holdout_portfolios.yaml"
DEFAULT_RESULTS_DIR = PROJECT_ROOT / "experiments" / "results"
DEFAULT_FIGURES_DIR = PROJECT_ROOT / "experiments" / "figures"
DEFAULT_TABLES_DIR = PROJECT_ROOT / "experiments" / "tables"


@dataclass(frozen=True)
class HoldoutPortfolio:
    name: str
    market: MarketMode
    tickers: list[str]
    weights: list[float]
    benchmark: str
    description: str


class ExperimentConfigError(ValueError):
    """Raised when experiment configuration is invalid."""


def parse_bool(value: object) -> bool:
    """Parse a CLI/config boolean without accepting ambiguous strings."""
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    raise ExperimentConfigError(f"expected boolean value, got {value!r}")


def project_path(value: str | Path, base: Path = PROJECT_ROOT) -> Path:
    """Resolve a path relative to the repository root."""
    path = Path(value)
    if path.is_absolute():
        return path
    return base / path


def load_yaml(path: str | Path) -> dict[str, Any]:
    """Load a YAML object from disk."""
    resolved = project_path(path)
    with resolved.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}
    if not isinstance(payload, dict):
        raise ExperimentConfigError(f"{resolved} must contain a YAML object")
    return payload


def load_config(path: str | Path = DEFAULT_CONFIG_PATH) -> dict[str, Any]:
    """Load and lightly normalize the paper evaluation config."""
    config = load_yaml(path)
    config.setdefault("dates", {})
    config.setdefault("crisis_warning", {})
    config.setdefault("allocation", {})
    config.setdefault("outputs", {})
    return config


def config_path(config: dict[str, Any], key: str, default: Path) -> Path:
    """Resolve a path value from the outputs/config root."""
    value = config.get(key)
    if value is None:
        value = config.get("outputs", {}).get(key, default)
    return project_path(value)


def output_dir_from_args(
    output_dir: str | Path | None,
    config: dict[str, Any],
    key: str = "results_dir",
    default: Path = DEFAULT_RESULTS_DIR,
) -> Path:
    """Resolve an output directory from CLI override, config, or default."""
    if output_dir:
        return project_path(output_dir)
    return config_path(config, key, default)


def parse_date(value: object, field_name: str) -> date:
    """Parse an ISO date from config."""
    ts = pd.to_datetime(value, errors="coerce")
    if pd.isna(ts):
        raise ExperimentConfigError(f"{field_name} must be an ISO date")
    return ts.date()


def experiment_dates(config: dict[str, Any]) -> tuple[date, date]:
    dates = config.get("dates", {})
    start = parse_date(dates.get("start_date"), "dates.start_date")
    end = parse_date(dates.get("end_date"), "dates.end_date")
    if end < start:
        raise ExperimentConfigError("dates.end_date must be on or after dates.start_date")
    return start, end


def horizons_from_config(config: dict[str, Any]) -> list[int]:
    horizons = config.get("crisis_warning", {}).get("horizons", config.get("horizons", [1, 5]))
    values = [int(item) for item in horizons]
    invalid = [item for item in values if item not in {1, 5}]
    if invalid:
        raise ExperimentConfigError(f"unsupported crisis horizons: {invalid}")
    return values


def normalize_weights(weights: Sequence[float] | None, n_assets: int) -> list[float]:
    """Return full-investment weights, falling back to equal weights."""
    return [float(value) for value in RiskEngine._normalize_weights(list(weights or []), n_assets)]


def _portfolio_from_payload(payload: dict[str, Any], default_market: str | None = None) -> HoldoutPortfolio:
    required = {"name", "tickers", "weights", "benchmark", "description"}
    missing = sorted(required - set(payload))
    if missing:
        raise ExperimentConfigError(f"holdout portfolio is missing fields: {', '.join(missing)}")
    market = str(payload.get("market") or default_market or "").strip().lower()
    if market not in {"us", "hk", "cn", "jp", "tw"}:
        raise ExperimentConfigError(f"unsupported holdout market: {market!r}")
    tickers = [str(item).strip() for item in payload["tickers"] if str(item).strip()]
    if not tickers:
        raise ExperimentConfigError(f"{payload['name']} must include at least one ticker")
    weights = normalize_weights(payload.get("weights"), len(tickers))
    return HoldoutPortfolio(
        name=str(payload["name"]).strip(),
        market=market,  # type: ignore[arg-type]
        tickers=tickers,
        weights=weights,
        benchmark=str(payload["benchmark"]).strip(),
        description=str(payload["description"]).strip(),
    )


def load_holdout_portfolios(path: str | Path = DEFAULT_PORTFOLIOS_PATH) -> list[HoldoutPortfolio]:
    """Load holdout portfolios from the paper YAML file."""
    payload = load_yaml(path)
    raw_portfolios: list[HoldoutPortfolio] = []
    if isinstance(payload.get("portfolios"), list):
        for item in payload["portfolios"]:
            if not isinstance(item, dict):
                raise ExperimentConfigError("holdout portfolios must be YAML objects")
            raw_portfolios.append(_portfolio_from_payload(item))
    else:
        markets = payload.get("markets", {})
        if not isinstance(markets, dict):
            raise ExperimentConfigError("holdout YAML must contain markets or portfolios")
        for market, entries in markets.items():
            if not isinstance(entries, list):
                raise ExperimentConfigError(f"market {market} must contain a portfolio list")
            for item in entries:
                if not isinstance(item, dict):
                    raise ExperimentConfigError("holdout portfolios must be YAML objects")
                raw_portfolios.append(_portfolio_from_payload(item, default_market=str(market)))

    names = [portfolio.name for portfolio in raw_portfolios]
    duplicates = sorted({name for name in names if names.count(name) > 1})
    if duplicates:
        raise ExperimentConfigError(f"duplicate holdout portfolio names: {', '.join(duplicates)}")
    return raw_portfolios


def market_counts(portfolios: Iterable[HoldoutPortfolio]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for portfolio in portfolios:
        counts[portfolio.market] = counts.get(portfolio.market, 0) + 1
    return counts


def ticker_set_key(tickers: Sequence[str]) -> tuple[str, ...]:
    return tuple(sorted(str(ticker).strip().upper() for ticker in tickers))


def ensure_directory(path: str | Path) -> Path:
    resolved = project_path(path)
    resolved.mkdir(parents=True, exist_ok=True)
    return resolved


def dataframe_to_csv(frame: pd.DataFrame, path: str | Path) -> Path:
    resolved = project_path(path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(resolved, index=False)
    return resolved


def write_json(path: str | Path, payload: dict[str, Any]) -> Path:
    resolved = project_path(path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    with resolved.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, default=json_default)
    return resolved


def json_default(value: object) -> object:
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        numeric = float(value)
        return numeric if np.isfinite(numeric) else None
    if isinstance(value, (pd.Timestamp,)):
        return value.isoformat()
    if isinstance(value, Path):
        return str(value)
    return str(value)


def make_fetcher(api_key: str | None, allow_sandbox_data: bool) -> SmartFetcher:
    return SmartFetcher(api_key=api_key, allow_sandbox_data=allow_sandbox_data)


def fetch_portfolio_prices(
    portfolio: HoldoutPortfolio,
    start_date: date,
    end_date: date,
    api_key: str | None,
    allow_sandbox_data: bool,
) -> tuple[pd.DataFrame, SmartFetcher]:
    """Fetch aligned close prices for one holdout portfolio."""
    fetcher = make_fetcher(api_key, allow_sandbox_data)
    risk_engine = RiskEngine(fetcher=fetcher, aligner=MarketAligner())
    price_df = risk_engine._fetch_prices(
        portfolio.tickers,
        start_date,
        end_date,
        market_mode=portfolio.market,
    )
    return price_df, fetcher


def fetch_benchmark_returns(
    service: PortfolioAnalysisService,
    fetcher: SmartFetcher,
    symbol: str,
    start_date: date,
    end_date: date,
    market: MarketMode,
) -> pd.Series:
    """Fetch benchmark log returns through the backend's benchmark provider logic."""
    benchmark_symbol = symbol or BENCHMARKS.get(market, BENCHMARKS["us"])[0]
    frame = service.fetch_benchmark_prices(fetcher, benchmark_symbol, start_date, end_date, market)
    prices = frame.set_index("Date")["Close"]
    prices.index = pd.to_datetime(prices.index).tz_localize(None).normalize()
    return np.log(prices / prices.shift(1)).dropna()


def align_test_with_benchmark(
    test_returns: pd.DataFrame,
    benchmark_returns: pd.Series,
    fill_limit: int = 1,
) -> tuple[pd.DataFrame, pd.Series]:
    """Align test returns with benchmark returns using a bounded forward fill fallback."""
    common_idx = test_returns.index.intersection(benchmark_returns.index)
    if len(common_idx) >= 5:
        return test_returns.loc[common_idx], benchmark_returns.loc[common_idx]

    benchmark_aligned = benchmark_returns.reindex(test_returns.index).ffill(limit=fill_limit).dropna()
    common_idx = test_returns.index.intersection(benchmark_aligned.index)
    if len(common_idx) == 0:
        raise ValueError("benchmark and test returns share no overlapping dates")
    return test_returns.loc[common_idx], benchmark_aligned.loc[common_idx]


def artifact_audit_summary(
    artifact_root: str | Path,
    horizons: Iterable[int] = (1, 5),
) -> dict[str, Any]:
    """Return hash metadata for fixed production artifacts without modifying them."""
    root = project_path(artifact_root)
    summary: dict[str, Any] = {
        "artifact_root": str(root),
        "horizons": {},
    }
    for horizon in horizons:
        directory = root / f"global_h{int(horizon)}"
        metadata_path = directory / "training_metadata.json"
        feature_schema_path = directory / "feature_schema.json"
        item: dict[str, Any] = {
            "directory": str(directory),
            "exists": directory.exists(),
        }
        try:
            actual_hash, actual_files = compute_artifact_hash(directory)
            item["artifact_hash"] = actual_hash
            item["artifact_hash_files"] = actual_files
        except Exception as exc:
            item["hash_error"] = str(exc)
        if metadata_path.exists():
            with metadata_path.open("r", encoding="utf-8") as handle:
                metadata = json.load(handle)
            item["metadata_artifact_hash"] = metadata.get("artifact_hash", "")
            item["metadata_model_version"] = metadata.get("model_version", "")
            item["metadata_validation_status"] = metadata.get("validation_status", "")
            item["artifact_hash_matches_metadata"] = (
                item.get("artifact_hash") == item.get("metadata_artifact_hash")
            )
        if feature_schema_path.exists():
            item["feature_schema_hash"] = sha256_file(feature_schema_path)
        summary["horizons"][f"h{int(horizon)}"] = item
    return summary

