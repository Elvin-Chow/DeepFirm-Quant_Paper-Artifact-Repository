# Paper Experiment Framework

This directory is an independent paper-evaluation harness. It does not retrain
models, overwrite production artifacts, or change backend/frontend behavior.

## Protocol

- Fixed artifacts: `artifacts/crisis_warning/global_h1/` and `artifacts/crisis_warning/global_h5/`
- Holdout portfolios: `experiments/portfolios/holdout_portfolios.yaml`
- Main config: `experiments/paper_eval_config.yaml`
- Default outputs:
  - `experiments/results/`
  - `experiments/figures/`
  - `experiments/tables/`
  - generated Markdown tables under `paper/`

The crisis-warning scripts load the existing frozen artifacts, rebuild
point-in-time features and labels for holdout portfolios, and score the fixed
models out of sample. The crisis-baseline script trains only experiment-local
final-window comparators. The allocation script runs holdout walk-forward
comparisons across equal weight, inverse volatility, mean-variance, raw
Black-Litterman, Smart policy, and Smart policy with the OOS guard.

Paper numbers require real provider data. Keep `--allow-sandbox-data false` for
submission artifacts; sandbox data is only acceptable for local smoke tests.

## Complete Command Chain

Validate fixed artifacts first:

```bash
python scripts/validate_crisis_warning_contract.py artifacts/crisis_warning/global_h1 artifacts/crisis_warning/global_h5
```

Run integrity tests:

```bash
python -m pytest tests/test_crisis_warning_engine.py tests/test_oos_allocation_integrity.py tests/test_oos_guard_thresholds.py tests/test_data_provenance_and_oos.py -q
```

Run the experiment framework tests:

```bash
python -m pytest tests/test_experiments_framework.py -q
```

Generate crisis warning predictions and metrics:

```bash
python experiments/run_crisis_external_eval.py \
  --config experiments/paper_eval_config.yaml \
  --output-dir experiments/results \
  --allow-sandbox-data false
```

Generate crisis baseline comparisons:

```bash
python experiments/run_crisis_baseline_eval.py \
  --config experiments/paper_eval_config.yaml \
  --output-dir experiments/results \
  --allow-sandbox-data false
```

Generate allocation OOS metrics:

```bash
python experiments/run_allocation_oos_eval.py \
  --config experiments/paper_eval_config.yaml \
  --output-dir experiments/results \
  --allow-sandbox-data false
```

Generate threshold sensitivity metrics, table, and figure:

```bash
python experiments/run_threshold_sensitivity.py \
  --config experiments/paper_eval_config.yaml \
  --results-dir experiments/results \
  --tables-dir experiments/tables \
  --figures-dir experiments/figures \
  --paper-dir paper
```

Generate uncertainty summaries:

```bash
python experiments/run_uncertainty_summary.py \
  --config experiments/paper_eval_config.yaml \
  --results-dir experiments/results \
  --tables-dir experiments/tables \
  --paper-dir paper
```

Build paper tables and figures:

```bash
python experiments/make_paper_tables.py \
  --config experiments/paper_eval_config.yaml \
  --results-dir experiments/results \
  --output-dir experiments/tables \
  --paper-dir paper

python experiments/make_paper_figures.py \
  --config experiments/paper_eval_config.yaml \
  --results-dir experiments/results \
  --output-dir experiments/figures
```

Generate the result hash manifest:

```bash
python experiments/generate_result_hash_manifest.py \
  --output paper/result_hash_manifest.md
```

This workspace is not a git repository, so the manifest reports Git SHA as
unavailable. A final release/archive should provide a Git SHA or DOI if the
authors need immutable submission provenance beyond the SHA-256 file manifest.

All scripts are rerunnable and overwrite files with the same experiment names.

## Current Main Result Files

`experiments/results/`:

- `crisis_predictions_h1.csv`: 34,238 rows.
- `crisis_predictions_h5.csv`: 34,086 rows.
- `crisis_metrics_by_portfolio.csv`: 38 rows.
- `crisis_metrics_by_market.csv`: 10 rows.
- `crisis_shap_drivers.csv`: 264,292 rows.
- `crisis_eval_skipped.csv`: 2 rows.
- `artifact_audit_summary.json`.
- `baseline_predictions_h1.csv`: 41,148 rows.
- `baseline_predictions_h5.csv`: 40,938 rows.
- `baseline_metrics.csv`: 300 rows.
- `baseline_training_summary.csv`: 228 rows.
- `baseline_eval_skipped.csv`: 2 rows.
- `baseline_audit_summary.json`.
- `allocation_oos_returns.csv`: 42,420 rows.
- `allocation_oos_metrics.csv`: 114 rows.
- `allocation_oos_skipped.csv`: 1 row.
- `ablation_metrics.csv`: 114 rows.
- `threshold_sensitivity_metrics.csv`: 162 rows.
- `uncertainty_summary.csv`: 28 rows.

`experiments/figures/`:

- `framework_architecture.png`
- `roc_pr_by_horizon.png`
- `calibration_by_horizon.png`
- `threshold_sensitivity.png`
- `shap_top_drivers.png`
- `allocation_oos_curves.png`
- `ablation_summary.png`

`experiments/tables/`:

- `table_artifact_summary.csv`
- `table_crisis_metrics.csv`
- `table_baseline_comparison.csv`
- `table_allocation_metrics.csv`
- `table_ablation.csv`
- `table_threshold_sensitivity.csv`
- `table_uncertainty_summary.csv`

Generated paper artifacts:

- `paper/table_1_artifact_summary.md`
- `paper/table_2_crisis_metrics.md`
- `paper/table_3_baseline_comparison.md`
- `paper/table_4_allocation_oos.md`
- `paper/table_5_ablation.md`
- `paper/table_threshold_sensitivity.md`
- `paper/table_uncertainty_summary.md`
- `paper/result_hash_manifest.md`

## Interpretation Boundaries

- Crisis baselines are final-window comparators, not production challenger-model validation.
- Allocation ablation is strategy-level, not component-level.
- Provider failures are logged as skipped rows; they are not filled with sandbox data.
- Result hashes cover file bytes, but a final author release should still include a repository archive, Git SHA, DOI, or equivalent immutable identifier.
