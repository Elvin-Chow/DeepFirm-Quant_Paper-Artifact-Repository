# Data Availability and Public Release Boundary

This repository is prepared as a paper reproducibility package. It includes the data artifacts that can be released with the paper and excludes local runtime caches that may contain provider-sourced raw market data.

## Included Public Artifacts

The following files are intended to be public in the GitHub repository:

- Experiment configs:
  - `experiments/paper_eval_config.yaml`
  - `experiments/zero_overlap_supplement_config.yaml`
  - `experiments/portfolios/*.yaml`
- Generated paper result files:
  - `experiments/results/*.csv`
  - `experiments/results/*.json`
  - `experiments/results_zero_overlap/*.csv`
  - `experiments/results_zero_overlap/*.json`
- Generated paper tables and figures:
  - `experiments/tables/*.csv`
  - `experiments/tables_zero_overlap/*.csv`
  - `experiments/figures/*.png`
  - `experiments/figures_zero_overlap/*.png`
- Paper-facing Markdown tables, reports, logs, and manifests under `paper/`.
- Frozen crisis-warning artifacts under `artifacts/crisis_warning/global_h1/` and `artifacts/crisis_warning/global_h5/`.

These artifacts are derived from the paper pipeline and are needed for result inspection, hash verification, and paper reproduction.

## Excluded Local Runtime Data

The following are intentionally excluded from git:

- `cache/`
- `data/`
- `*.parquet`
- `*.sqlite`, `*.sqlite3`, and `*.db`
- Python, test, Node, and LaTeX build caches

The current workspace contains provider cache files under `cache/fetcher_results/` and `cache/http_cache.sqlite`. Those files are useful locally, but they are not treated as a redistributable raw market-data dataset.

## Provider Policy

Paper experiments use live public-market data access paths such as Yahoo Finance and AKShare with:

```yaml
allow_sandbox_data: false
api_key: null
```

If a provider fails, the experiment records skipped rows instead of substituting sandbox or synthetic data. The detailed record is maintained in:

- `paper/data_availability_log.md`
- `experiments/results/crisis_eval_skipped.csv`
- `experiments/results/baseline_eval_skipped.csv`
- `experiments/results/allocation_oos_skipped.csv`
- `experiments/results_zero_overlap/crisis_eval_skipped.csv`

## Reproduction Note

Because provider availability, rate limits, symbol coverage, and vendor corrections can change over time, regenerated raw inputs may differ from the original runtime cache. The released CSV/JSON/PNG/Markdown outputs and `paper/result_hash_manifest.md` provide the stable inspection record for the submitted paper package.
