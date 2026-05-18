# Reproducibility README

Updated: 2026-05-18 HKT

This file summarizes the current reproducibility package for the IEEE Access manuscript. It is written to separate verified local facts from author actions that still require an archival release.

## 1. Artifact Identification

- Paper title: "An Auditable Explainable AI Framework for Multi-Market Tail-Risk Warning and Leakage-Guarded Bayesian Portfolio Allocation".
- Project/artifact name: DeepFirm Quant paper reproducibility package.
- Artifact purpose: reproduce the paper's frozen crisis-warning evaluation, final-window baseline comparison, leakage-guarded allocation OOS evaluation, threshold sensitivity analysis, uncertainty summary, generated paper tables, generated figures, and result hash manifest.
- Current package scope: source code, `requirements.txt`, `requirements-dev.txt`, release documentation (`README.md`, `DATA.md`, `RELEASE_CHECKLIST.md`, `CITATION.cff`), frontend `package.json` and `package-lock.json`, frozen crisis-warning artifacts under `artifacts/crisis_warning/global_h1/` and `artifacts/crisis_warning/global_h5/`, experiment configs and scripts under `experiments/`, generated CSV/JSON/PNG/Markdown/LaTeX paper outputs, and the local IEEE Access manuscript package under `paper/latex/`.
- Not yet included: public repository URL, immutable archive DOI, Code Ocean capsule DOI, Zenodo DOI, and Git commit SHA. These are TODO items for the authors because the current workspace is not a git repository.

## 2. Dependencies

### Python Requirements

The current reproducibility/runtime dependency file is `requirements.txt`.

Important pinned packages in `requirements.txt`:

| Package | Version |
|---|---:|
| pandas | 2.3.3 |
| numpy | 2.3.5 |
| xgboost | 3.2.0 |
| scikit-learn | 1.8.0 |
| shap | 0.51.0 |
| yfinance | 1.2.2 |
| akshare | 1.18.55 |
| pandas_market_calendars | 5.3.2 |

### Frozen Artifact Training Metadata

The frozen artifact metadata records the dependency versions present when the distributed crisis-warning artifacts were produced.

| Horizon | Metadata file | numpy | pandas | xgboost |
|---|---|---:|---:|---:|
| H1 | `artifacts/crisis_warning/global_h1/training_metadata.json` | 2.4.4 | 3.0.2 | 3.2.0 |
| H5 | `artifacts/crisis_warning/global_h5/training_metadata.json` | 2.4.4 | 3.0.2 | 3.2.0 |

Version difference statement: `requirements.txt` pins `numpy==2.3.5` and `pandas==2.3.3`, while the frozen artifact training metadata records `numpy==2.4.4` and `pandas==3.0.2`. Both sources record `xgboost==3.2.0`. Therefore, `requirements.txt` should be treated as the current reproduction and inference environment for the provided frozen artifacts, not as an exact reconstruction of the original artifact-training environment. Paper reproduction should validate the frozen artifact hashes rather than retrain them. Any retraining release should record a separate fully frozen training environment.

### Node Frontend Dependencies

- Frontend package file: `frontend/package.json`.
- Lockfile: `frontend/package-lock.json`.
- Runtime stack: Next.js 16.2.6, React 18.2.0, TypeScript, Tailwind CSS, Recharts, and lucide-react.

## 3. Hardware and Software

The following values were read from the local machine on 2026-05-18 HKT.

| Item | Value |
|---|---|
| Workspace path | `/Users/zhouhongyi/Documents/VS_Code/DeepFirm-Quant-Paper-2026` |
| OS | macOS 26.3.1, build 25D771280a |
| Kernel | Darwin 25.3.0, arm64 |
| Machine model | MacBook Air, model identifier Mac16,13 |
| Chip | Apple M4 |
| CPU cores | 10 total, 4 performance and 6 efficiency |
| Memory | 16 GB |
| Python | Python 3.13.9 |
| pip | pip 25.3 from `/opt/anaconda3/lib/python3.13/site-packages/pip` |
| Node.js | v24.14.0 |
| npm | 11.9.0 |
| Git state | `git rev-parse --is-inside-work-tree` returned `fatal: not a git repository` |
| System LaTeX | `pdflatex` not found on PATH |
| Tectonic | `tectonic` not found on PATH in the current shell |

Additional dedicated GPU/accelerator details: to be reported by authors.

## 4. Installation and Deployment Steps

Create a Python virtual environment from the project root:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Install frontend dependencies:

```bash
cd frontend
npm install
cd ..
```

Optional backend launch:

```bash
PYTHONPATH=. .venv/bin/python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

Optional frontend launch:

```bash
cd frontend
npm run dev
```

Then open `http://localhost:3000`. The frontend defaults to `http://localhost:8000` for the backend API. On macOS, XGBoost may require an OpenMP runtime such as `libomp.dylib` before training or loading XGBoost artifacts.

## 5. Experiment Workflow

Paper results should be regenerated with sandbox data disabled. Provider failures must be logged as skips rather than replaced with sandbox or synthetic data.

Validate fixed artifacts:

```bash
python scripts/validate_crisis_warning_contract.py artifacts/crisis_warning/global_h1 artifacts/crisis_warning/global_h5
```

Run integrity tests:

```bash
python -m pytest tests/test_crisis_warning_engine.py tests/test_oos_allocation_integrity.py tests/test_oos_guard_thresholds.py tests/test_data_provenance_and_oos.py -q
```

Run experiment framework tests:

```bash
python -m pytest tests/test_experiments_framework.py -q
```

Generate crisis-warning predictions and metrics:

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

Build paper tables:

```bash
python experiments/make_paper_tables.py \
  --config experiments/paper_eval_config.yaml \
  --results-dir experiments/results \
  --output-dir experiments/tables \
  --paper-dir paper
```

Build paper figures:

```bash
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

Optional zero-security-overlap crisis-warning supplement:

```bash
python experiments/run_crisis_external_eval.py \
  --config experiments/zero_overlap_supplement_config.yaml \
  --output-dir experiments/results_zero_overlap \
  --allow-sandbox-data false
```

```bash
python experiments/run_threshold_sensitivity.py \
  --config experiments/zero_overlap_supplement_config.yaml \
  --results-dir experiments/results_zero_overlap \
  --tables-dir experiments/tables_zero_overlap \
  --figures-dir experiments/figures_zero_overlap \
  --paper-dir paper/zero_overlap_supplement
```

```bash
python experiments/make_paper_tables.py \
  --config experiments/zero_overlap_supplement_config.yaml \
  --results-dir experiments/results_zero_overlap \
  --output-dir experiments/tables_zero_overlap \
  --paper-dir paper/zero_overlap_supplement
```

```bash
python experiments/make_paper_figures.py \
  --config experiments/zero_overlap_supplement_config.yaml \
  --results-dir experiments/results_zero_overlap \
  --output-dir experiments/figures_zero_overlap
```

## 6. Expected Outputs

| Output | Type | Paper mapping |
|---|---|---|
| `experiments/results/artifact_audit_summary.json` | JSON | Frozen artifact audit evidence for Table 1 |
| `experiments/tables/table_artifact_summary.csv` | CSV | `paper/table_1_artifact_summary.md`; LaTeX Table "Frozen Artifact Audit Summary" |
| `experiments/results/crisis_predictions_h1.csv` | CSV | H1 prediction source for crisis metrics, ROC/PR, calibration, SHAP-style driver summaries |
| `experiments/results/crisis_predictions_h5.csv` | CSV | H5 prediction source for crisis metrics, ROC/PR, calibration, SHAP-style driver summaries |
| `experiments/results/crisis_metrics_by_portfolio.csv` | CSV | Portfolio-level crisis-warning evaluation |
| `experiments/results/crisis_metrics_by_market.csv` | CSV | Market-level crisis-warning evaluation; `paper/table_2_crisis_metrics.md`; LaTeX crisis metrics table |
| `experiments/results/crisis_shap_drivers.csv` | CSV | SHAP-style driver figure source |
| `experiments/results/crisis_eval_skipped.csv` | CSV | Data availability limitation evidence for skipped crisis-warning rows |
| `experiments/results/baseline_metrics.csv` | CSV | `paper/table_3_baseline_comparison.md`; LaTeX baseline comparison table |
| `experiments/results/baseline_predictions_h1.csv` and `baseline_predictions_h5.csv` | CSV | Final-window baseline prediction source files |
| `experiments/results/baseline_training_summary.csv` | CSV | Baseline training-window audit support |
| `experiments/results/baseline_audit_summary.json` | JSON | Baseline comparison run audit support |
| `experiments/results/allocation_oos_returns.csv` | CSV | OOS allocation curve figure source |
| `experiments/results/allocation_oos_metrics.csv` | CSV | `paper/table_4_allocation_oos.md`; LaTeX allocation OOS table |
| `experiments/results/allocation_oos_skipped.csv` | CSV | Allocation data availability limitation evidence |
| `experiments/results/ablation_metrics.csv` | CSV | `paper/table_5_ablation.md`; allocation ablation figure |
| `experiments/results/threshold_sensitivity_metrics.csv` | CSV | `paper/table_threshold_sensitivity.md`; threshold sensitivity figure |
| `experiments/results/uncertainty_summary.csv` | CSV | `paper/table_uncertainty_summary.md`; uncertainty discussion |
| `experiments/figures/framework_architecture.png` | PNG | LaTeX Figure 1 |
| `experiments/figures/roc_pr_by_horizon.png` | PNG | LaTeX ROC/PR figure |
| `experiments/figures/calibration_by_horizon.png` | PNG | LaTeX calibration figure |
| `experiments/figures/threshold_sensitivity.png` | PNG | LaTeX threshold sensitivity figure |
| `experiments/figures/shap_top_drivers.png` | PNG | LaTeX SHAP-style driver figure |
| `experiments/figures/allocation_oos_curves.png` | PNG | LaTeX allocation OOS curve figure |
| `experiments/figures/ablation_summary.png` | PNG | LaTeX ablation figure |
| `paper/table_*.md`, `paper/table_threshold_sensitivity.md`, `paper/table_uncertainty_summary.md` | Markdown | Human-readable table sources used to assemble the manuscript |
| `paper/latex/main.tex` | LaTeX | IEEE Access source manuscript |
| `paper/latex/main.pdf` | PDF | Locally regenerated manuscript PDF from the current LaTeX source |
| `paper/result_hash_manifest.md` | Markdown | SHA-256 byte hashes for key result, table, figure, Markdown, dependency/config, README, and LaTeX artifacts |

## 7. Runtime Notes

Runtime facts available from the current paper status/report files:

- Full test suite status recorded in `paper/final_status_report.md`: `python -m pytest -q` passed with 209 tests.
- Artifact contract validation recorded in `paper/final_status_report.md`: `scripts/validate_crisis_warning_contract.py` passed for both frozen artifacts.
- Main crisis-warning run: 68,324 prediction rows and 2 skipped rows with sandbox disabled.
- Main baseline run: 82,086 final-window prediction rows, 300 metric rows, 228 training-summary rows, and 2 skipped baseline-evaluation rows with sandbox disabled.
- Main allocation OOS run: 19 evaluated portfolios, 114 strategy rows, 42,420 return rows, and 1 skipped row with sandbox disabled.
- Threshold sensitivity run: 68,324 prediction rows and 162 metric rows.
- Zero-security-overlap crisis supplement: 36,114 prediction rows and 0 skipped crisis-warning rows with sandbox disabled.
- Uncertainty summary: 28 rows with 500 cross-portfolio bootstrap resamples.
- Result hash manifest: 109 rows in the last recorded generation.
- Current shell check: no system `pdflatex`, `latexmk`, `xelatex`, or `tectonic` executable is on PATH. After explicit user approval, the temporary Tectonic 0.16.9 macOS arm64 binary under `/private/tmp/` was run outside the sandbox and successfully regenerated `paper/latex/main.pdf`.
- Source/PDF state: current `paper/latex/main.tex` and `paper/latex/main.pdf` are synchronized as of the current readiness pass. A TeX Live `pdflatex`/BibTeX compatibility pass remains useful on the final submission machine.
- Wall-clock runtime by command: to be measured by authors on the archival execution machine.

## 8. Reproducibility Limits

- Real-time data suppliers are not archived in this package. Yahoo Finance and AKShare availability, rate limits, cooldown behavior, and corrections can change between runs.
- AKShare/Yahoo failures are part of the reproducibility record. The current data log records CN fetch failures and skip files rather than filling those rows.
- No sandbox or synthetic data is used for paper numbers. When real provider data fails and `--allow-sandbox-data false` is set, affected portfolios or horizons are skipped and logged.
- The package does not include raw vendor redistribution rights for all live market data used through providers.
- The frozen H1/H5 artifacts are distributed and hash-validated, but their metadata validation status is `degraded_validation`.
- The current workspace is not a git repository, so no Git SHA is available from this local directory.
- The current reproducibility environment in `requirements.txt` differs from the frozen artifact training metadata for numpy and pandas. See the dependency section above.
- Public repository URL, release DOI, Zenodo DOI, Code Ocean DOI, and final Git commit SHA are TODO author-provided archival fields.
- A final PDF recompile is only needed after archive metadata, repository fields, or LaTeX source text change again.

## 9. Archival Recommendation

Before submission, create an immutable archival package using one of the following routes:

- GitHub release plus Zenodo DOI.
- Code Ocean capsule with DOI.
- Institutional archive or equivalent repository that assigns a DOI and preserves source files, frozen artifacts, generated results, and environment metadata.

Recommended archive contents:

- Source tree with `requirements.txt`, `frontend/package.json`, and `frontend/package-lock.json`.
- Frozen artifacts under `artifacts/crisis_warning/global_h1/` and `artifacts/crisis_warning/global_h5/`.
- Experiment configs, scripts, generated CSV/JSON/PNG/Markdown/LaTeX outputs, and `paper/result_hash_manifest.md`.
- This `paper/reproducibility_README.md`.
- A release note stating the Git commit SHA and DOI.

After the release is created, replace the TODO placeholders in `paper/latex/main.tex` and the paper package with the public repository URL, Git commit SHA, and archive DOI.
