import math
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from experiments.common import (
    DEFAULT_CONFIG_PATH,
    DEFAULT_PORTFOLIOS_PATH,
    load_config,
    load_holdout_portfolios,
    market_counts,
    ticker_set_key,
)
from experiments.metrics import crisis_classification_metrics
from experiments.run_allocation_oos_eval import RETURNS_COLUMNS
from experiments.run_crisis_external_eval import PREDICTION_COLUMNS
from experiments.run_paired_delta_summary import paired_allocation_rows, paired_crisis_rows
from experiments.run_threshold_sensitivity import (
    classification_metrics as threshold_classification_metrics,
    ranking_metrics,
    threshold_sensitivity_rows,
)
from scripts.train_crisis_warning_model import DOMAIN_PRESETS


class ExperimentsFrameworkTests(unittest.TestCase):
    def test_paper_config_parses(self) -> None:
        config = load_config(DEFAULT_CONFIG_PATH)

        self.assertEqual(config["crisis_warning"]["horizons"], [1, 5])
        self.assertFalse(config["allow_sandbox_data"])
        self.assertEqual(config["outputs"]["results_dir"], "experiments/results")

    def test_holdout_portfolios_cover_markets_and_do_not_duplicate_training_sets(self) -> None:
        holdouts = load_holdout_portfolios(DEFAULT_PORTFOLIOS_PATH)
        counts = market_counts(holdouts)

        self.assertEqual(set(counts), {"us", "hk", "cn", "jp", "tw"})
        for market in counts:
            self.assertGreaterEqual(counts[market], 4)

        training_sets = {
            ticker_set_key(portfolio.tickers)
            for portfolio in DOMAIN_PRESETS["diversified_global"]
        }
        for portfolio in holdouts:
            self.assertNotIn(ticker_set_key(portfolio.tickers), training_sets)
            self.assertTrue(portfolio.name)
            self.assertTrue(portfolio.description)
            self.assertTrue(portfolio.benchmark)
            self.assertEqual(len(portfolio.tickers), len(portfolio.weights))
            self.assertAlmostEqual(sum(portfolio.weights), 1.0, places=8)

    def test_crisis_metrics_single_class_labels_return_nan_for_auc(self) -> None:
        metrics = crisis_classification_metrics(
            y_true=[0, 0, 0, 0],
            probabilities=[0.05, 0.10, 0.20, 0.30],
        )

        self.assertEqual(metrics["row_count"], 4.0)
        self.assertEqual(metrics["positive_event_count"], 0.0)
        self.assertTrue(math.isnan(metrics["roc_auc"]))
        self.assertTrue(math.isnan(metrics["pr_auc"]))
        self.assertTrue(math.isnan(metrics["top_decile_lift"]))
        self.assertFalse(math.isnan(metrics["brier_score"]))
        self.assertFalse(math.isnan(metrics["log_loss"]))

    def test_required_output_csv_columns_are_stable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            prediction_path = tmp_path / "crisis_predictions_h1.csv"
            returns_path = tmp_path / "allocation_oos_returns.csv"

            pd.DataFrame(columns=PREDICTION_COLUMNS).to_csv(prediction_path, index=False)
            pd.DataFrame(columns=RETURNS_COLUMNS).to_csv(returns_path, index=False)

            prediction_columns = pd.read_csv(prediction_path).columns.tolist()
            returns_columns = pd.read_csv(returns_path).columns.tolist()

        for column in [
            "date",
            "horizon",
            "portfolio_name",
            "market",
            "tail_event",
            "crisis_probability",
        ]:
            self.assertIn(column, prediction_columns)
        for column in [
            "date",
            "portfolio_name",
            "market",
            "strategy",
            "daily_return",
            "cumulative_return",
        ]:
            self.assertIn(column, returns_columns)

    def test_threshold_sensitivity_metrics_are_deterministic(self) -> None:
        y_true = [1, 0, 1, 0, 0]
        probabilities = [0.90, 0.80, 0.70, 0.20, 0.10]

        classified = threshold_classification_metrics(y_true, probabilities, threshold=0.75)
        ranked = ranking_metrics(y_true, probabilities, top_pcts=[0.40])

        self.assertEqual(classified["row_count"], 5.0)
        self.assertEqual(classified["positive_count"], 2.0)
        self.assertEqual(classified["flag_count"], 2.0)
        self.assertAlmostEqual(classified["precision"], 0.5)
        self.assertAlmostEqual(classified["recall"], 0.5)
        self.assertAlmostEqual(classified["f1"], 0.5)
        self.assertEqual(ranked["top_40_count"], 2.0)
        self.assertEqual(ranked["top_40_positive_count"], 1.0)
        self.assertAlmostEqual(ranked["top_40_precision"], 0.5)
        self.assertAlmostEqual(ranked["top_40_recall"], 0.5)
        self.assertAlmostEqual(ranked["top_40_lift"], 1.25)

    def test_threshold_sensitivity_rows_cover_requested_scopes(self) -> None:
        predictions = pd.DataFrame(
            {
                "horizon": [1, 1, 1, 1],
                "market": ["us", "us", "us", "us"],
                "tail_event": [1, 0, 0, 1],
                "crisis_probability": [0.9, 0.6, 0.4, 0.2],
            }
        )

        rows = threshold_sensitivity_rows(predictions, thresholds=[0.50], top_pcts=[0.50])
        scopes = {str(row["scope"]) for row in rows}

        self.assertEqual(scopes, {"global", "horizon", "market", "horizon_market"})
        self.assertEqual(len(rows), 4)
        for row in rows:
            self.assertIn("precision", row)
            self.assertIn("recall", row)
            self.assertIn("f1", row)
            self.assertIn("top_50_lift", row)

    def test_paired_crisis_delta_bootstrap_uses_inner_joined_portfolios(self) -> None:
        rows = []
        labels = {
            "portfolio_a": [0, 1, 0, 1],
            "portfolio_b": [0, 0, 1, 1],
        }
        dates = pd.date_range("2026-01-01", periods=4, freq="D")
        for portfolio_name, y_values in labels.items():
            for idx, tail_event in enumerate(y_values):
                rows.append(
                    {
                        "date": dates[idx].date().isoformat(),
                        "horizon": 1,
                        "portfolio_name": portfolio_name,
                        "baseline": "frozen_calibrated_xgboost",
                        "tail_event": tail_event,
                        "probability": 0.9 if tail_event else 0.1,
                    }
                )
                rows.append(
                    {
                        "date": dates[idx].date().isoformat(),
                        "horizon": 1,
                        "portfolio_name": portfolio_name,
                        "baseline": "logistic_regression",
                        "tail_event": tail_event,
                        "probability": 0.1 if tail_event else 0.9,
                    }
                )
        rows.append(
            {
                "date": dates[0].date().isoformat(),
                "horizon": 1,
                "portfolio_name": "reference_only",
                "baseline": "frozen_calibrated_xgboost",
                "tail_event": 1,
                "probability": 0.9,
            }
        )
        summary = pd.DataFrame(
            paired_crisis_rows(
                pd.DataFrame(rows),
                horizons=[1],
                n_bootstrap=25,
                seed=7,
                comparators=["logistic_regression"],
            )
        )

        self.assertEqual(set(summary["metric"]), {"roc_auc", "pr_auc", "brier_score", "log_loss", "top_decile_lift"})
        self.assertTrue(summary["unit_count"].eq(2).all())
        self.assertTrue(summary["dropped_unit_count"].eq(1).all())
        self.assertTrue((summary["point_delta"] > 0).all())
        brier = summary[summary["metric"].eq("brier_score")].iloc[0]
        self.assertEqual(
            brier["delta_formula"],
            "comparator - reference (positive means reference is lower/better)",
        )
        self.assertEqual(brier["finite_bootstrap_count"], 25)

    def test_paired_allocation_delta_bootstrap_handles_turnover_direction(self) -> None:
        allocation = pd.DataFrame(
            [
                {
                    "portfolio_name": "portfolio_a",
                    "market": "us",
                    "strategy": "smart_policy_oos_guard",
                    "sharpe": 1.0,
                    "model_score": 70.0,
                    "benchmark_excess_return": 0.10,
                    "turnover": 0.10,
                },
                {
                    "portfolio_name": "portfolio_a",
                    "market": "us",
                    "strategy": "equal_weight",
                    "sharpe": 0.6,
                    "model_score": 60.0,
                    "benchmark_excess_return": 0.02,
                    "turnover": 0.40,
                },
                {
                    "portfolio_name": "portfolio_b",
                    "market": "us",
                    "strategy": "smart_policy_oos_guard",
                    "sharpe": 1.2,
                    "model_score": 72.0,
                    "benchmark_excess_return": 0.12,
                    "turnover": 0.20,
                },
                {
                    "portfolio_name": "portfolio_b",
                    "market": "us",
                    "strategy": "equal_weight",
                    "sharpe": 0.7,
                    "model_score": 62.0,
                    "benchmark_excess_return": 0.03,
                    "turnover": 0.50,
                },
                {
                    "portfolio_name": "reference_only",
                    "market": "us",
                    "strategy": "smart_policy_oos_guard",
                    "sharpe": 1.1,
                    "model_score": 71.0,
                    "benchmark_excess_return": 0.11,
                    "turnover": 0.15,
                },
            ]
        )

        summary = pd.DataFrame(
            paired_allocation_rows(
                allocation,
                n_bootstrap=25,
                seed=7,
                comparators=["equal_weight"],
            )
        )

        self.assertEqual(set(summary["metric"]), {"sharpe", "model_score", "benchmark_excess_return", "turnover"})
        self.assertTrue(summary["unit_count"].eq(2).all())
        self.assertTrue(summary["dropped_unit_count"].eq(1).all())
        self.assertTrue((summary["point_delta"] > 0).all())
        turnover = summary[summary["metric"].eq("turnover")].iloc[0]
        self.assertEqual(
            turnover["delta_formula"],
            "comparator - reference (positive means reference is lower/better)",
        )
        self.assertAlmostEqual(turnover["point_delta"], 0.30)


if __name__ == "__main__":
    unittest.main()
