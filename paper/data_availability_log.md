# Data Availability Log

This log records real-market data access issues during paper experiments. Sandbox or synthetic substitutions are not used for paper numbers.

## Scope and Redistribution Notes

- Paper commands use `--allow-sandbox-data false`.
- Live provider data is not redistributed as a raw vendor dataset in this package. Generated experiment outputs, skip files, and provenance fields are included as reproducibility artifacts.
- The root `DATA.md` file summarizes the public-release boundary between included paper artifacts and excluded local runtime caches.
- Yahoo Finance and AKShare availability can change across reruns because of provider outages, rate limits, cooldown behavior, symbol coverage, and vendor-side corrections.
- Provider failures are treated as data availability limitations and are recorded as skipped rows. They are not imputed with sandbox data for paper metrics.
- Public archive DOI, repository URL, and Git commit SHA: TODO to be supplied by the authors after release.

## Crisis External Evaluation - 2026-05-18

Command:

```bash
python experiments/run_crisis_external_eval.py --config experiments/paper_eval_config.yaml --output-dir experiments/results --allow-sandbox-data false
```

### Initial Sandbox-Limited Attempt

- Result: completed with `prediction_rows=0` and `skipped_rows=40`.
- Cause: DNS resolution failures for Yahoo Finance domains such as `query1.finance.yahoo.com`, `query2.finance.yahoo.com`, and `fc.yahoo.com`.
- Paper status: not used for paper metrics.

### Network-Enabled Attempt

- Result: completed with `prediction_rows=68324` and `skipped_rows=2`.
- Sandbox data: disabled.
- Generated skip file: `experiments/results/crisis_eval_skipped.csv`.

Skipped rows:

| Portfolio | Market | Horizon | Stage | Reason |
|---|---|---:|---|---|
| cn_broad_factor_etf | CN | 1 | fetch_prices | Unable to fetch real A-share price data for `159915`; AKShare was in provider cooldown and Yahoo A-share fallback returned 404 for `159915.SS`. |
| cn_broad_factor_etf | CN | 5 | fetch_prices | Unable to fetch real A-share price data for `159915`; AKShare was in provider cooldown and Yahoo A-share fallback returned 404 for `159915.SS`. |

Interpretation:

- Crisis-warning metrics cover 19 of 20 holdout portfolios for each horizon.
- The CN broad factor ETF sleeve is unavailable for both horizons under real-data constraints and must be reported as a data availability limitation.

## Zero-Security-Overlap Crisis Supplement - 2026-05-18

Commands:

```bash
python experiments/run_crisis_external_eval.py --config experiments/zero_overlap_supplement_config.yaml --output-dir experiments/results_zero_overlap --allow-sandbox-data false
```

```bash
python experiments/run_threshold_sensitivity.py --config experiments/zero_overlap_supplement_config.yaml --results-dir experiments/results_zero_overlap --tables-dir experiments/tables_zero_overlap --figures-dir experiments/figures_zero_overlap --paper-dir paper/zero_overlap_supplement
```

- Result: completed with `prediction_rows=36114` and `skipped_rows=0`.
- Sandbox data: disabled.
- Generated skip file: `experiments/results_zero_overlap/crisis_eval_skipped.csv`.

Interpretation:

- The zero-security-overlap supplement is a crisis-warning-only supplement.
- It does not include zero-overlap baseline comparison, allocation OOS, or allocation ablation runs.
- No unavailable provider rows were observed in the zero-overlap crisis-warning run recorded in the current package.

## Crisis Baseline Evaluation - 2026-05-18

Command:

```bash
python experiments/run_crisis_baseline_eval.py --config experiments/paper_eval_config.yaml --output-dir experiments/results --allow-sandbox-data false
```

- Result: completed with `prediction_rows=82086`, `metric_rows=300`, and `skipped_rows=2`.
- Sandbox data: disabled.
- Generated skip file: `experiments/results/baseline_eval_skipped.csv`.

Skipped rows:

| Portfolio | Market | Horizon | Stage | Reason |
|---|---|---:|---|---|
| cn_broad_factor_etf | CN | 1 | fetch_prices | Unable to fetch real A-share price data for `159915`; AKShare was unavailable or in provider cooldown and Yahoo A-share fallback returned 404 for `159915.SS`. |
| cn_broad_factor_etf | CN | 5 | fetch_prices | Unable to fetch real A-share price data for `159915`; AKShare was unavailable or in provider cooldown and Yahoo A-share fallback returned 404 for `159915.SS`. |

Interpretation:

- Crisis baseline comparison uses the leakage-guarded final 20% holdout window for available portfolios.
- It covers 19 of 20 holdout portfolios per horizon in this run.
- The skipped CN portfolio must be treated as a data availability limitation, not as a negative model result.

## Allocation OOS Evaluation - 2026-05-18

Command:

```bash
python experiments/run_allocation_oos_eval.py --config experiments/paper_eval_config.yaml --output-dir experiments/results --allow-sandbox-data false
```

- Result: completed with `evaluated_portfolios=19`, `strategy_rows=114`, `return_rows=42420`, and `skipped_rows=1`.
- Sandbox data: disabled.
- Generated skip file: `experiments/results/allocation_oos_skipped.csv`.

Skipped rows:

| Portfolio | Market | Stage | Reason |
|---|---|---|---|
| cn_broad_factor_etf | CN | evaluate | Unable to fetch real A-share price data for `159915`; AKShare provider cooldown and Yahoo A-share fallback returned 404 for `159915.SS`. |

Provider warning:

- During the run, AKShare CSI 300 benchmark fetch for `000300` timed out once. The script completed and produced aligned benchmark returns; any benchmark alignment conclusions should be tied to generated output and tests rather than the transient warning alone.
