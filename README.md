# DeepFirm Quant Paper Experiments

Reproducibility package for the manuscript:

**"An Auditable Explainable AI Framework for Multi-Market Tail-Risk Warning and Leakage-Guarded Bayesian Portfolio Allocation"**

This repository is the manuscript-specific paper artifact repository for DeepFirm Quant. It is organized for reviewers, collaborators, and future readers who need to inspect or rerun the frozen paper experiments without mixing them into the main product repository.

## What Is Included

- Source code for the FastAPI backend, quantitative models, data pipeline, and optional Next.js frontend.
- Frozen crisis-warning artifacts:
  - `artifacts/crisis_warning/global_h1/`
  - `artifacts/crisis_warning/global_h5/`
- Paper experiment scripts, configs, portfolios, results, tables, and figures under `experiments/`.
- Human-readable paper artifacts, reproducibility notes, and the LaTeX manuscript package under `paper/`.
- Test coverage for artifact contracts, leakage guards, data provenance, and experiment framework behavior under `tests/`.
- Result hashes in `paper/result_hash_manifest.md`.

## Paper Scope

The paper evaluates DeepFirm Quant as an auditable financial ML framework rather than as a claim of universal predictive superiority. The frozen warning layer, generated result files, and allocation OOS evaluation are preserved so the paper's claims can be traced back to concrete artifacts.

Required global market scope: `us,hk,cn,jp,tw`

Main paper configuration:

- `experiments/paper_eval_config.yaml`
- `experiments/portfolios/holdout_portfolios.yaml`
- `artifacts/crisis_warning/global_h1/`
- `artifacts/crisis_warning/global_h5/`

Zero-security-overlap transfer check:

- `experiments/zero_overlap_supplement_config.yaml`
- `experiments/portfolios/zero_overlap_supplement_portfolios.yaml`
- `experiments/results_zero_overlap/`
- `experiments/tables_zero_overlap/`
- `experiments/figures_zero_overlap/`

## Data Availability

Public release contents include generated paper outputs such as CSV metrics, JSON audit summaries, PNG figures, Markdown tables, skip logs, configs, and frozen model artifacts.

Raw runtime provider caches under `cache/` are intentionally excluded from git. The paper uses live public market-data providers such as Yahoo Finance and AKShare with sandbox data disabled. Provider failures are recorded in skip files and in `paper/data_availability_log.md` rather than filled with synthetic data.

See `DATA.md` for the public-data boundary and redistribution notes.

## Quick Start

Use Python 3.11+ for the paper reproduction environment.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Optional development/test dependencies:

```bash
python -m pip install -r requirements-dev.txt
```

Validate the frozen artifact contracts:

```bash
python scripts/validate_crisis_warning_contract.py
```

Run the paper guardrail tests:

```bash
python -m pytest \
  tests/test_crisis_warning_engine.py \
  tests/test_crisis_warning_artifacts.py \
  tests/test_oos_allocation_integrity.py \
  tests/test_oos_guard_thresholds.py \
  tests/test_data_provenance_and_oos.py \
  tests/test_experiments_framework.py \
  -q
```

## Reproduce Paper Outputs

Paper numbers should be regenerated with sandbox data disabled.

```bash
python experiments/run_crisis_external_eval.py \
  --config experiments/paper_eval_config.yaml \
  --output-dir experiments/results \
  --allow-sandbox-data false
```

```bash
python experiments/run_crisis_baseline_eval.py \
  --config experiments/paper_eval_config.yaml \
  --output-dir experiments/results \
  --allow-sandbox-data false
```

```bash
python experiments/run_allocation_oos_eval.py \
  --config experiments/paper_eval_config.yaml \
  --output-dir experiments/results \
  --allow-sandbox-data false
```

```bash
python experiments/run_threshold_sensitivity.py \
  --config experiments/paper_eval_config.yaml \
  --results-dir experiments/results \
  --tables-dir experiments/tables \
  --figures-dir experiments/figures \
  --paper-dir paper
```

```bash
python experiments/run_uncertainty_summary.py \
  --config experiments/paper_eval_config.yaml \
  --results-dir experiments/results \
  --tables-dir experiments/tables \
  --paper-dir paper
```

```bash
python experiments/make_paper_tables.py \
  --config experiments/paper_eval_config.yaml \
  --results-dir experiments/results \
  --output-dir experiments/tables \
  --paper-dir paper
```

```bash
python experiments/make_paper_figures.py \
  --config experiments/paper_eval_config.yaml \
  --results-dir experiments/results \
  --output-dir experiments/figures
```

Regenerate the SHA-256 result manifest:

```bash
python experiments/generate_result_hash_manifest.py \
  --output paper/result_hash_manifest.md
```

The longer reproducibility guide is `paper/reproducibility_README.md`.

## Optional App Runtime

The application runtime is preserved because the paper framework comes from the DeepFirm Quant system.

Backend:

```bash
PYTHONPATH=. .venv/bin/python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Then open `http://localhost:3000`.

## Release Checklist

Before creating the public GitHub repository or release archive:

1. Confirm `cache/`, `.venv/`, `__pycache__/`, `.pytest_cache/`, `node_modules/`, and local editor files are not tracked.
2. Confirm no API keys, tokens, passwords, or private provider credentials are present.
3. Run artifact validation and the paper guardrail tests.
4. Regenerate `paper/result_hash_manifest.md`.
5. Create the GitHub repository, push the cleaned tree, and create the release tag.
6. If needed, create a Zenodo/Code Ocean/institutional archive DOI.
7. Confirm the repository URL, release tag, and archival-DOI status in the paper package.

See `RELEASE_CHECKLIST.md` for the full pre-publication checklist.

## License

Code is released under the MIT License. Third-party market data accessed through providers is not sublicensed by this repository; see `DATA.md`.
