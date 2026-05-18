# Experiment Protocol

Protocol updated on 2026-05-18 HKT after artifact validation, main crisis evaluation, crisis baseline evaluation, allocation OOS evaluation, threshold sensitivity, uncertainty summary, table generation, and result manifest generation.

## Research Question

Can a frozen, auditable, explainable tail-risk warning layer and a leakage-guarded Bayesian allocation policy provide reproducible decision-support evidence across US, HK, CN, JP, and TW holdout portfolios without retraining or using sandbox data?

This paper evaluates warning and allocation behavior. It does not claim to forecast returns, provide investment advice, or guarantee improved portfolio performance.

## Markets, Horizons, and Targets

- Markets: US, HK, CN, JP, TW.
- Crisis-warning horizons: 1D and 5D.
- Target: dynamic trailing quantile tail event.
- H1 target definition from frozen metadata: future 1D portfolio log return below trailing 5% historical 1D return threshold.
- H5 target definition from frozen metadata: future 5D portfolio log return below trailing 5% historical 5D return threshold.
- Tail quantile: 0.05.
- Probability threshold for warning metrics: 0.60.

## Frozen Artifacts

- H1 artifact: `artifacts/crisis_warning/global_h1/`
  - Artifact hash: `b807acefbc0c5774844331b7514791fd892f33a59846250728a64ca55506d6cd`
  - Validation status: `degraded_validation`
- H5 artifact: `artifacts/crisis_warning/global_h5/`
  - Artifact hash: `625482ed714b903cd94ebdfd47fc8d9b0b0e7e5282ccc6a3b9af290b537053d0`
  - Validation status: `degraded_validation`

The experiment protocol does not retrain these artifacts and does not overwrite files under either artifact directory.

## Holdout Portfolio Construction

- Holdout config: `experiments/portfolios/holdout_portfolios.yaml`
- Holdout portfolios: 20 total, 4 per market.
- Benchmarks:
  - US: SPY
  - HK: ^HSI
  - CN: 000300
  - JP: ^N225
  - TW: ^TWII

### Holdout-vs-Training Duplication Check

Command used:

```bash
python - <<'PY'
...
PY
```

Summary:

- Training-domain portfolio count in H1 metadata: 20.
- Holdout portfolio count: 20.
- Exact same-market duplicate ticker-set count: 0.
- Interpretation: holdout portfolios are not exact repeats of frozen training-domain portfolios.
- Limitation: several holdout portfolios share individual tickers with training-domain portfolios. The evaluation is therefore portfolio-level external validation, not a strict zero-security-overlap transfer test.

Maximum within-market ticker overlap observed:

| Market | Holdout portfolio | Max overlapping tickers with one training portfolio |
|---|---|---:|
| US | us_quality_tech_finance | 2 |
| US | us_ai_infrastructure_barbell | 1 |
| US | us_dividend_low_volatility | 0 |
| US | us_mid_small_sector_mix | 1 |
| HK | hk_platform_financial_core | 2 |
| HK | hk_consumption_insurance_mix | 2 |
| HK | hk_income_property_credit | 2 |
| HK | hk_china_etf_cross_asset | 3 |
| CN | cn_consumption_financial_core | 3 |
| CN | cn_new_energy_healthcare | 2 |
| CN | cn_state_owned_defensive | 2 |
| CN | cn_broad_factor_etf | 2 |
| JP | jp_auto_electronics_core | 3 |
| JP | jp_financial_industrial_mix | 1 |
| JP | jp_defensive_domestic | 3 |
| JP | jp_index_style_blend | 2 |
| TW | tw_semiconductor_platform_core | 3 |
| TW | tw_electronics_supply_chain | 2 |
| TW | tw_defensive_income_financials | 3 |
| TW | tw_index_factor_mix | 3 |

## Crisis-Warning Main Evaluation

Script:

```bash
python experiments/run_crisis_external_eval.py \
  --config experiments/paper_eval_config.yaml \
  --output-dir experiments/results \
  --allow-sandbox-data false
```

Expected outputs:

- `experiments/results/crisis_predictions_h1.csv`
- `experiments/results/crisis_predictions_h5.csv`
- `experiments/results/crisis_metrics_by_portfolio.csv`
- `experiments/results/crisis_metrics_by_market.csv`
- `experiments/results/artifact_audit_summary.json`
- Optional diagnostics: `experiments/results/crisis_shap_drivers.csv`, `experiments/results/crisis_eval_skipped.csv`

Metrics:

- Row count
- Positive event count
- Positive rate
- ROC-AUC
- PR-AUC
- Brier score
- Log-loss
- Calibration error
- Precision at 0.60
- Recall at 0.60
- Top-decile lift

## Crisis Baseline Comparison Protocol

Script:

```bash
python experiments/run_crisis_baseline_eval.py \
  --config experiments/paper_eval_config.yaml \
  --output-dir experiments/results \
  --allow-sandbox-data false
```

Current outputs:

- `experiments/results/baseline_predictions_h1.csv`
- `experiments/results/baseline_predictions_h5.csv`
- `experiments/results/baseline_metrics.csv`
- `experiments/results/baseline_training_summary.csv`
- `experiments/results/baseline_eval_skipped.csv`
- `experiments/results/baseline_audit_summary.json`

Baselines:

- Frozen calibrated XGBoost artifact.
- Frozen raw XGBoost output without the calibration layer.
- Historical tail-threshold baseline.
- Logistic regression.
- Random forest.
- Gradient boosting.

Protocol:

- Each available portfolio and horizon is split chronologically into an initial 80% training window and a final 20% evaluation window.
- Non-frozen baselines are fit only on the first 80% of that portfolio's point-in-time feature rows.
- Frozen calibrated and raw XGBoost outputs are sliced to the same final 20% rows for comparison.
- The historical-threshold baseline uses the current historical horizon return and current tail threshold; it does not use the future horizon return except as the evaluation label.
- The run is experiment-only and does not retrain or overwrite `artifacts/crisis_warning/global_h1/` or `artifacts/crisis_warning/global_h5/`.

Current result facts:

- Total baseline prediction rows: 82,086.
- Baseline metric rows: 300.
- Baseline training-summary rows: 228.
- Skipped baseline-evaluation rows: 2, covering `cn_broad_factor_etf` across H1/H5 due to provider availability failures.
- Sandbox data: disabled.

The current baseline comparison is a final-window applied comparator, not a purged or embargoed challenger-model validation.

## Allocation OOS Protocol

Script:

```bash
python experiments/run_allocation_oos_eval.py \
  --config experiments/paper_eval_config.yaml \
  --output-dir experiments/results \
  --allow-sandbox-data false
```

Strategies:

- Equal weight
- Inverse volatility
- Mean-variance
- Raw Black-Litterman
- Smart policy
- Smart policy with OOS guard

Metrics:

- Cumulative return
- Annualized volatility
- Max drawdown
- Expected Shortfall
- Sharpe ratio
- Information Ratio
- Turnover
- Benchmark excess return
- Model score / grade where available

Leakage checks:

- `policy_asof` must not exceed `train_asof`.
- OOS guard must not use test-window signals.
- Benchmark alignment must not use future fill or unbounded backfill.

## Allocation Ablation Protocol

Current output:

- `experiments/results/ablation_metrics.csv`

The allocation ablation is a strategy-level delta table. Each strategy is compared against `smart_policy_oos_guard` when that reference is present, otherwise against the configured reference fallback. This supports a coarse comparison of equal weight, inverse volatility, mean-variance, raw Black-Litterman, Smart policy, and Smart policy with OOS guard.

This is not a component-level causal ablation of each Smart-policy submodule. Component-level ablations should be added only if the manuscript claims causal contribution from individual signals or penalties.

## Data Availability and Failure Handling

- Paper experiments use real market data only.
- `allow_sandbox_data=false` is mandatory for paper numbers.
- Provider failures, incomplete markets, and quality warnings are logged to `paper/data_availability_log.md`.
- Failed markets or portfolios are not silently replaced by synthetic or sandbox data.

## Protocol Freeze Rule

After this document is updated, protocol changes are allowed only for clear implementation errors, dependency failures, or discovered leakage risks. Any change must be logged in `paper/paper_worklog.md` and reflected in this file.
