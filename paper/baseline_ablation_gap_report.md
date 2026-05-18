# Baseline and Ablation Status Report

Date: 2026-05-18

Scope: inspected `experiments/run_crisis_external_eval.py`, `experiments/run_crisis_baseline_eval.py`, `experiments/run_allocation_oos_eval.py`, `experiments/make_paper_tables.py`, `experiments/make_paper_figures.py`, `tests/test_experiments_framework.py`, `experiments/common.py`, `experiments/metrics.py`, `experiments/paper_eval_config.yaml`, `experiments/README.md`, `paper/latex/main.tex`, `paper/table_3_baseline_comparison.md`, `paper/table_5_ablation.md`, and current files under `experiments/results/`.

## Executive Finding

Crisis-warning baselines are now implemented in the experiment harness and have generated current paper outputs. The prior gap, namely the absence of historical-threshold, logistic-regression, random-forest, gradient-boosting, and frozen-XGBoost comparison rows, is closed for the main paper run.

The implementation is experiment-only. It does not retrain or overwrite the frozen crisis-warning artifacts and does not change production backend/frontend behavior.

Allocation baseline comparisons remain supported through `allocation_oos_metrics.csv`. Allocation ablation remains a coarse strategy-level delta table, not a component-level causal ablation of every Smart-policy submodule.

## Current Crisis Baseline Implementation

Script:

```bash
python experiments/run_crisis_baseline_eval.py \
  --config experiments/paper_eval_config.yaml \
  --output-dir experiments/results \
  --allow-sandbox-data false
```

Current outputs in `experiments/results/`:

- `baseline_predictions_h1.csv`: 41,148 rows, 9 columns.
- `baseline_predictions_h5.csv`: 40,938 rows, 9 columns.
- `baseline_metrics.csv`: 300 rows, 16 columns.
- `baseline_training_summary.csv`: 228 rows, 11 columns.
- `baseline_eval_skipped.csv`: 2 rows, 6 columns.
- `baseline_audit_summary.json`: records sandbox status, date range, portfolio count, prediction rows, metric rows, skipped rows, test ratio, baseline names, and frozen artifact hashes.

Baselines represented in the current output:

- `frozen_calibrated_xgboost`
- `frozen_raw_xgboost_without_calibration`
- `historical_tail_threshold`
- `logistic_regression`
- `random_forest`
- `gradient_boosting`

The baseline audit summary reports 82,086 total prediction rows, 300 metric rows, 2 skipped rows, `test_ratio=0.20`, and `allow_sandbox_data=false`.

## Baseline Protocol

For each available holdout portfolio and each configured horizon, the baseline script rebuilds the same point-in-time feature and label frame used by the crisis external evaluation. It splits rows chronologically into the first 80% for baseline fitting and the final 20% for evaluation.

Non-frozen classifiers are trained only on the first 80% of the portfolio's own feature rows. The frozen calibrated and raw XGBoost artifact outputs are sliced to the same final 20% windows for comparability. The historical-tail-threshold baseline predicts a warning when the current historical horizon return breaches the current tail threshold.

Metrics are computed at portfolio, market, and global scope with the same crisis classification metrics used elsewhere in the paper: row count, positive event count, positive rate, ROC-AUC, PR-AUC, Brier score, log-loss, calibration error, precision@0.60, recall@0.60, and top-decile lift.

## Current Baseline Result Summary

`paper/table_3_baseline_comparison.md` and the LaTeX manuscript report the global final-window comparison:

- H1 `frozen_calibrated_xgboost`: 6,858 rows, ROC-AUC 0.6055, PR-AUC 0.0905, Brier 0.0504, log-loss 0.2055, recall@0.60 0.0027, top-decile lift 2.0210.
- H1 `frozen_raw_xgboost_without_calibration`: ROC-AUC 0.6095 and PR-AUC 0.0992, but weaker probability quality with Brier 0.2084 and log-loss 0.6081.
- H5 `frozen_calibrated_xgboost`: 6,823 rows, ROC-AUC 0.6014, PR-AUC 0.0642, Brier 0.0460, log-loss 0.1914, recall@0.60 0.0000, top-decile lift 2.0523.
- H5 `frozen_raw_xgboost_without_calibration`: ROC-AUC 0.6122 and PR-AUC 0.0726, but weaker probability quality with Brier 0.2066 and log-loss 0.6012.

The current interpretation is deliberately narrow: calibration improves probability quality, while raw XGBoost scores retain slightly stronger ranking metrics in this final-window sample.

## Skipped Baseline Rows

`baseline_eval_skipped.csv` has 2 rows:

- `cn_broad_factor_etf`, H1 and H5, skipped at price-fetch stage because ticker `159915` remained unavailable.

This is a data-availability limitation. It is not replaced with sandbox or synthetic data.

## Allocation Baselines and Ablation

Allocation OOS outputs are current and supported:

- `allocation_oos_returns.csv`: 42,420 rows, 9 columns.
- `allocation_oos_metrics.csv`: 114 rows, 32 columns.
- `allocation_oos_skipped.csv`: 1 row, 4 columns.

Supported strategies:

- `equal_weight`
- `inverse_volatility`
- `mean_variance`
- `raw_black_litterman`
- `smart_policy`
- `smart_policy_oos_guard`

The allocation ablation output is also current:

- `ablation_metrics.csv`: 114 rows, 12 columns.
- `paper/table_5_ablation.md`: strategy-level deltas relative to Smart policy with OOS guard.

Important interpretation: the `ablation` column contains strategy names. It supports a coarse strategy comparison, including Smart policy versus Smart policy with OOS guard. It does not isolate individual Smart-policy components such as risk signal, regime signal, anomaly signal, adaptive penalties, or min/max weight adaptation.

## Paper Table Support

`experiments/make_paper_tables.py` now builds CSV and Markdown tables from the active result directory:

- `experiments/tables/table_baseline_comparison.csv`
- `paper/table_3_baseline_comparison.md`
- `experiments/tables/table_allocation_metrics.csv`
- `paper/table_4_allocation_oos.md`
- `experiments/tables/table_ablation.csv`
- `paper/table_5_ablation.md`

The table notes are result-driven and correctly mark zero-overlap supplement baseline/allocation/ablation tables as not run.

## Remaining Risks

- Baseline comparison uses a chronological final-20% split per portfolio. A purged or embargoed baseline protocol would be stronger, but the current protocol is explicit and leakage-aware for this applied paper.
- Baseline classifiers are trained within each available holdout portfolio rather than on a separate pooled training universe. This is acceptable as a simple final-window comparator, but it should not be presented as a production challenger-model study.
- The main baseline run is not zero-security-overlap; the zero-overlap supplement is crisis-warning-only and does not include baseline, allocation, or ablation evidence.
- Component-level Smart-policy ablations are not implemented. Add them only if the manuscript makes causal claims about individual Smart-policy submodules.
- "Without audit metadata" and "without data-quality filtering" are not meaningful causal ablations in the current experiment harness; audit metadata is part of the reproducibility contract, not a predictive feature path.
- Provider availability remains a practical limitation for some China A-share tickers. Paper numbers must continue to use real data only and log skips instead of substituting sandbox data.

## Bottom Line

Ready for paper use:

- Crisis baseline comparison through `baseline_metrics.csv`, `baseline_predictions_h1.csv`, `baseline_predictions_h5.csv`, `baseline_training_summary.csv`, and `baseline_audit_summary.json`.
- Allocation baseline comparison through `allocation_oos_metrics.csv`.
- Coarse allocation strategy ablation through `ablation_metrics.csv`, `table_ablation.csv`, `paper/table_5_ablation.md`, and `ablation_summary.png`.

Still not claimed:

- Strict zero-security-overlap baseline comparison.
- Purged/embargoed challenger-model validation.
- Component-level causal Smart-policy ablations.
