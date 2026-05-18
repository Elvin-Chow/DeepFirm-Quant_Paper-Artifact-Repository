# Paper Worklog

Project: DeepFirm Quant paper evaluation workspace
Title: An Auditable Explainable AI Framework for Multi-Market Tail-Risk Warning and Leakage-Guarded Bayesian Portfolio Allocation
Timezone: Asia/Hong_Kong

## 2026-05-18 15:17 HKT - Stage 0 Initialization

### Current Stage

Stage 0 - central workbench initialization and artifact/test validation.

### Commands Run

- `pwd`
- `git rev-parse HEAD`
- `git status --short`
- `sed -n '1,240p' README.md`
- `sed -n '1,260p' experiments/README.md`
- `sed -n '1,260p' experiments/paper_eval_config.yaml`
- `sed -n '1,260p' experiments/portfolios/holdout_portfolios.yaml`
- `sed -n '1,260p' artifacts/crisis_warning/global_h1/training_metadata.json`
- `sed -n '1,260p' artifacts/crisis_warning/global_h5/training_metadata.json`
- `jq '{artifact_hash, validation_status, is_global_complete, domain_coverage_status, covered_market_scope, training_market_scope, covered_training_markets, domain_portfolio_count, total_training_rows: ([.domain_market_coverage[].training_rows] | add), total_positive_events: ([.domain_market_coverage[].positive_events] | add), total_validation_positive_events: ([.domain_market_coverage[].validation_positive_events] | add), domain_market_coverage}' artifacts/crisis_warning/global_h1/training_metadata.json`
- `jq '{artifact_hash, validation_status, is_global_complete, domain_coverage_status, covered_market_scope, training_market_scope, covered_training_markets, domain_portfolio_count, total_training_rows: ([.domain_market_coverage[].training_rows] | add), total_positive_events: ([.domain_market_coverage[].positive_events] | add), total_validation_positive_events: ([.domain_market_coverage[].validation_positive_events] | add), domain_market_coverage}' artifacts/crisis_warning/global_h5/training_metadata.json`
- `jq '.validation_metrics' artifacts/crisis_warning/global_h1/training_metadata.json`
- `jq '.validation_metrics' artifacts/crisis_warning/global_h5/training_metadata.json`
- `shasum -a 256 artifacts/crisis_warning/global_h1/training_metadata.json`
- `shasum -a 256 artifacts/crisis_warning/global_h5/training_metadata.json`
- `mkdir -p paper`
- `mkdir -p experiments/results`
- `mkdir -p experiments/tables`
- `mkdir -p experiments/figures`
- `python scripts/validate_crisis_warning_contract.py artifacts/crisis_warning/global_h1 artifacts/crisis_warning/global_h5`
- `python -m pytest tests/test_experiments_framework.py -q`
- `python -m pytest tests/test_crisis_warning_engine.py tests/test_oos_allocation_integrity.py tests/test_oos_guard_thresholds.py tests/test_data_provenance_and_oos.py -q`
- Holdout-vs-training duplicate check using Python structured parsing of `experiments/portfolios/holdout_portfolios.yaml` and `artifacts/crisis_warning/global_h1/training_metadata.json`.
- `python experiments/run_crisis_external_eval.py --config experiments/paper_eval_config.yaml --output-dir experiments/results --allow-sandbox-data false` inside sandbox.
- `python experiments/run_crisis_external_eval.py --config experiments/paper_eval_config.yaml --output-dir experiments/results --allow-sandbox-data false` with network-enabled execution.
- `wc -l experiments/results/crisis_predictions_h1.csv experiments/results/crisis_predictions_h5.csv experiments/results/crisis_metrics_by_portfolio.csv experiments/results/crisis_metrics_by_market.csv experiments/results/crisis_eval_skipped.csv`
- `jq '.' experiments/results/artifact_audit_summary.json`
- Horizon-level metric aggregation from generated crisis prediction CSVs using `experiments.metrics.crisis_classification_metrics`.
- Added `experiments/run_crisis_baseline_eval.py` as an experiment-only baseline script.
- `python experiments/run_crisis_baseline_eval.py --config experiments/paper_eval_config.yaml --output-dir experiments/results --allow-sandbox-data false`
- `wc -l experiments/results/baseline_metrics.csv experiments/results/baseline_predictions_h1.csv experiments/results/baseline_predictions_h5.csv experiments/results/baseline_training_summary.csv experiments/results/baseline_eval_skipped.csv`
- Global baseline metric inspection from `experiments/results/baseline_metrics.csv`.
- `python experiments/run_allocation_oos_eval.py --config experiments/paper_eval_config.yaml --output-dir experiments/results --allow-sandbox-data false`
- `wc -l experiments/results/allocation_oos_returns.csv experiments/results/allocation_oos_metrics.csv experiments/results/ablation_metrics.csv experiments/results/allocation_oos_skipped.csv`
- Allocation metric aggregation by strategy from `experiments/results/allocation_oos_metrics.csv`.
- OOS policy-as-of check comparing `policy_asof` in allocation metrics to first test date in allocation return rows.

### Generated Files

- `paper/paper_worklog.md`
- `paper/experiment_manifest.md`
- `paper/outline.md`
- `paper/experiment_protocol.md`
- `paper/data_availability_log.md`
- `experiments/results/crisis_predictions_h1.csv`
- `experiments/results/crisis_predictions_h5.csv`
- `experiments/results/crisis_metrics_by_portfolio.csv`
- `experiments/results/crisis_metrics_by_market.csv`
- `experiments/results/artifact_audit_summary.json`
- `experiments/results/crisis_shap_drivers.csv`
- `experiments/results/crisis_eval_skipped.csv`
- `experiments/run_crisis_baseline_eval.py`
- `experiments/results/baseline_metrics.csv`
- `experiments/results/baseline_predictions_h1.csv`
- `experiments/results/baseline_predictions_h5.csv`
- `experiments/results/baseline_training_summary.csv`
- `experiments/results/baseline_eval_skipped.csv`
- `experiments/results/baseline_audit_summary.json`
- `experiments/results/allocation_oos_returns.csv`
- `experiments/results/allocation_oos_metrics.csv`
- `experiments/results/ablation_metrics.csv`
- `experiments/results/allocation_oos_skipped.csv`

### Key Metrics and Facts

- Project version: no Git repository detected in current directory, so no commit SHA is available.
- H1 artifact hash: `b807acefbc0c5774844331b7514791fd892f33a59846250728a64ca55506d6cd`
- H5 artifact hash: `625482ed714b903cd94ebdfd47fc8d9b0b0e7e5282ccc6a3b9af290b537053d0`
- H1 metadata SHA-256: `50fa9b2e926b82be74f9e6c35e49d40bff64a519a57aa280b5cb198f0d1dafa3`
- H5 metadata SHA-256: `d557cf36493cbe820f7d55d6a9662ca3ca6d416f3001adf5f221b87d9473eafc`
- Covered markets: US, HK, CN, JP, TW for both horizons.
- H1 training rows: 36,849; positive events: 1,941; validation positive events: 383.
- H5 training rows: 36,689; positive events: 2,102; validation positive events: 379.
- H1 validation: ROC-AUC 0.6112, PR-AUC 0.0963, calibrated Brier 0.0482, calibrated log-loss 0.1976, precision@0.60 0.1048, recall@0.60 0.2010.
- H5 validation: ROC-AUC 0.5698, PR-AUC 0.0712, calibrated Brier 0.0485, calibrated log-loss 0.1987, precision@0.60 0.0708, recall@0.60 0.1478.
- Validation status for both artifacts: `degraded_validation`.
- Holdout portfolio count: 20 total, 4 per market.
- Artifact contract validation: passed.
- Experiment framework tests: 4 passed.
- Crisis warning/OOS/provenance integrity tests: 48 passed.
- Holdout portfolios: 20.
- Training-domain portfolios: 20.
- Exact same-market duplicate ticker-set count: 0.
- Maximum within-market individual ticker overlap: 3 out of 5 tickers for several HK/CN/JP/TW sleeves.
- Crisis external evaluation, network-enabled: 68,324 prediction rows; 2 skipped rows; sandbox data disabled.
- Crisis H1 external aggregate: 34,238 rows, 1,840 positives, positive rate 5.37%, ROC-AUC 0.6325, PR-AUC 0.1020, Brier 0.0498, log-loss 0.2047, calibration error 0.0018, precision@0.60 0.5455, recall@0.60 0.0033, top-decile lift 2.2988.
- Crisis H5 external aggregate: 34,086 rows, 1,930 positives, positive rate 5.66%, ROC-AUC 0.6325, PR-AUC 0.0904, Brier 0.0527, log-loss 0.2181, calibration error 0.0035, precision@0.60 0.0000, recall@0.60 0.0000, top-decile lift 1.9013.
- Artifact audit summary confirms both artifact hashes match metadata.
- Crisis baseline evaluation refreshed: 82,086 prediction rows; 300 metric rows; 2 skipped rows; test ratio 0.20; sandbox data disabled.
- Baselines: frozen calibrated XGBoost, frozen raw XGBoost without calibration, gradient boosting, historical tail threshold, logistic regression, random forest.
- Global H1 baseline ROC-AUC: calibrated XGBoost 0.6055, raw XGBoost 0.6095, random forest 0.5759, logistic regression 0.5558, gradient boosting 0.5414, historical threshold 0.5245.
- Global H1 calibrated XGBoost Brier/log-loss: 0.0513 / 0.2081; raw XGBoost Brier/log-loss: 0.2083 / 0.6078.
- Global H5 baseline ROC-AUC: calibrated XGBoost 0.6014, raw XGBoost 0.6122, gradient boosting 0.5717, random forest 0.5706, logistic regression 0.5501, historical threshold 0.5055.
- Global H5 calibrated XGBoost Brier/log-loss: 0.0460 / 0.1911; raw XGBoost Brier/log-loss: 0.2075 / 0.6031.
- Allocation OOS: 19 evaluated portfolios, 114 strategy rows, 42,420 return rows, 1 skipped portfolio, sandbox data disabled.
- Mean allocation cumulative return by strategy: equal weight 0.3763, inverse volatility 0.3355, mean-variance 0.4061, raw Black-Litterman 0.3738, Smart policy 0.3732, Smart policy + OOS guard 0.3926.
- Mean allocation Sharpe by strategy: equal weight 1.1203, inverse volatility 1.1255, mean-variance 1.1799, raw Black-Litterman 1.1581, Smart policy 1.1531, Smart policy + OOS guard 1.1914.
- Mean model score by strategy: equal weight 58.28, inverse volatility 58.95, mean-variance 59.46, raw Black-Litterman 59.53, Smart policy 59.27, Smart policy + OOS guard 59.92.
- Mean benchmark excess return is negative for all allocation strategies in this holdout run; Smart policy + OOS guard is least negative among listed strategies at -0.1363 mean excess return.
- OOS as-of check: 0 violations; every Smart policy `policy_asof` precedes the first test date and `oos_leakage_guard` is true.

### Failures / Limitations

- `git rev-parse HEAD` and `git status --short` failed because the current directory is not a Git repository.
- `.venv` directory is absent; Stage 0 commands ran under system `python` 3.13.9.
- Initial sandbox-limited crisis eval produced zero prediction rows due DNS failures for Yahoo Finance domains. This run is not used for paper metrics.
- Real-data crisis eval skipped `cn_broad_factor_etf` for both horizons because ticker `159915` could not be fetched via AKShare/Yahoo fallback. Logged in `paper/data_availability_log.md`.
- Refreshed crisis baseline eval skipped only `cn_broad_factor_etf` for both horizons because `159915` remained unavailable; `cn_new_energy_healthcare` now runs from the available real-data cache.
- Allocation OOS skipped `cn_broad_factor_etf` because `159915` remained unavailable.

### Next Step

- Generate paper tables and figures, then verify non-empty/non-placeholder outputs.

### Paper Readiness

- Artifact facts are sufficient for an audit-summary subsection.
- Crisis external evaluation results are sufficient for cautious Results text.
- Precision/recall at 0.60 are weak, especially H5 recall of zero; paper must not overclaim threshold-warning performance.
- Crisis baseline results are sufficient for a cautious baseline-comparison subsection. The calibration ablation supports a nuanced claim: calibration improves probability quality while raw scores may retain slightly higher ranking AUC.
- Allocation OOS results are sufficient for cautious Results text: Smart policy + OOS guard has the best mean score/Sharpe in this run, but all strategies underperform their benchmarks on mean excess return.

## 2026-05-18 15:37 HKT - Stage 5-9 Integration Pass

### Current Stage

Stages 5-9 - table/figure generation, citation verification, paper draft, reviewer-risk handoff, and final validation.

### Commands Run

- Modified `experiments/make_paper_tables.py` to generate artifact/baseline CSVs plus Markdown paper tables in `paper/`.
- Modified `experiments/make_paper_figures.py` to generate `framework_architecture.png`.
- `python experiments/make_paper_tables.py --config experiments/paper_eval_config.yaml --results-dir experiments/results --output-dir experiments/tables`
- `python experiments/make_paper_figures.py --config experiments/paper_eval_config.yaml --results-dir experiments/results --output-dir experiments/figures`
- Figure verification using image dimensions, byte size, sampled unique colors, and pixel standard deviation.
- Citation verification spot-check over references, citation log, and related-work notes.
- Reference count check: `rg -n "^@" paper/references.bib`
- `python -m pytest tests/test_experiments_framework.py -q`
- `python -m pytest tests/test_crisis_warning_engine.py tests/test_oos_allocation_integrity.py tests/test_oos_guard_thresholds.py tests/test_data_provenance_and_oos.py -q`
- `python scripts/validate_crisis_warning_contract.py artifacts/crisis_warning/global_h1 artifacts/crisis_warning/global_h5`
- `find backend frontend -type f -mmin -60`
- `find artifacts/crisis_warning/global_h1 artifacts/crisis_warning/global_h5 -type f -mmin -60`

### Generated Files

- `experiments/tables/table_artifact_summary.csv`
- `experiments/tables/table_crisis_metrics.csv`
- `experiments/tables/table_baseline_comparison.csv`
- `experiments/tables/table_allocation_metrics.csv`
- `experiments/tables/table_ablation.csv`
- `paper/table_1_artifact_summary.md`
- `paper/table_2_crisis_metrics.md`
- `paper/table_3_baseline_comparison.md`
- `paper/table_4_allocation_oos.md`
- `paper/table_5_ablation.md`
- `experiments/figures/framework_architecture.png`
- `experiments/figures/roc_pr_by_horizon.png`
- `experiments/figures/calibration_by_horizon.png`
- `experiments/figures/shap_top_drivers.png`
- `experiments/figures/allocation_oos_curves.png`
- `experiments/figures/ablation_summary.png`
- `paper/related_work_notes.md`
- `paper/references.bib`
- `paper/citation_verification_log.md`
- `paper/main_draft.md`
- `paper/reviewer_risk_report.md`
- `paper/next_actions.md`
- `paper/final_status_report.md`

### Key Metrics and Facts

- Paper tables generated: artifact summary 2 rows, crisis metrics 10 rows, baseline comparison 12 rows, allocation metrics 6 rows, ablation 6 rows.
- Paper figures generated and verified non-empty: architecture 212 KB, ROC/PR 111 KB, calibration 68 KB, SHAP drivers 103 KB, allocation curves 177 KB, ablation 64 KB.
- Image verification found non-trivial dimensions and color variance for all six figures; no empty or placeholder-only figure was detected.
- References: 28 verified BibTeX entries.
- Citation scan found no unverified BibTeX entries.
- Post-change experiment framework tests: 4 passed.
- Post-change crisis/OOS/provenance tests: 48 passed.
- Final artifact contract validation: passed.
- Artifact audit JSON still reports H1/H5 hashes matching metadata.
- Final 60-minute file modification scan showed no files under `backend/`, `frontend/`, `artifacts/crisis_warning/global_h1/`, or `artifacts/crisis_warning/global_h5/`.

### Failures / Limitations

- Figure generation emitted pandas mixed-type dtype warnings while reading crisis prediction CSV warning columns. Figures were still generated and validated.
- The current draft is Markdown, not IEEE LaTeX. It is suitable as a first technical manuscript draft but still needs IEEE formatting.
- Reviewer-risk report is delegated to a worker and pending at this timestamp.
- Reviewer worker timed out and was shut down; central window completed `paper/reviewer_risk_report.md` and `paper/next_actions.md`.

### Next Step

- Convert Markdown draft to IEEE Access LaTeX and add threshold-sensitivity analysis.

### Paper Readiness

- Initial IEEE Access style draft exists with verified citations and result numbers.
- Reviewer risk triage is complete.
- Submission readiness is not claimed; first-draft readiness is achieved.

## 2026-05-18 16:18 HKT - Pre-Submission Hardening Pass

### Current Stage

P0-P2 pre-submission hardening: threshold sensitivity, audit-contract framing, captions/callouts, result hashes, zero-security-overlap supplement, reviewer-risk refresh, and LaTeX migration scaffold.

### Commands Run

- `sed -n '1,220p' /Users/zhouhongyi/.codex/skills/ml-paper-writing/SKILL.md`
- `sed -n '1,220p' /Users/zhouhongyi/.codex/skills/academic-plotting/SKILL.md`
- Repository/file survey using `rg --files`, `sed`, `wc -l`, and targeted CSV inspection.
- `python experiments/run_threshold_sensitivity.py --config experiments/paper_eval_config.yaml --results-dir experiments/results --tables-dir experiments/tables --figures-dir experiments/figures`
- `python experiments/make_paper_tables.py --config experiments/paper_eval_config.yaml --results-dir experiments/results --output-dir experiments/tables`
- `python experiments/make_paper_figures.py --config experiments/paper_eval_config.yaml --results-dir experiments/results --output-dir experiments/figures`
- `python -m pytest tests/test_experiments_framework.py -q`
- Training-vs-holdout ticker overlap checks from frozen artifact metadata and YAML portfolio files.
- `python experiments/run_crisis_external_eval.py --config experiments/zero_overlap_supplement_config.yaml --output-dir experiments/results_zero_overlap --allow-sandbox-data false`
- `python experiments/run_threshold_sensitivity.py --config experiments/zero_overlap_supplement_config.yaml --results-dir experiments/results_zero_overlap --tables-dir experiments/tables_zero_overlap --figures-dir experiments/figures_zero_overlap --paper-dir paper/zero_overlap_supplement`
- `python experiments/make_paper_tables.py --config experiments/zero_overlap_supplement_config.yaml --results-dir experiments/results_zero_overlap --output-dir experiments/tables_zero_overlap --paper-dir paper/zero_overlap_supplement`
- `python experiments/make_paper_figures.py --config experiments/zero_overlap_supplement_config.yaml --results-dir experiments/results_zero_overlap --output-dir experiments/figures_zero_overlap`
- Zero-overlap aggregate metric inspection using `experiments.metrics.crisis_classification_metrics`.
- `python experiments/generate_result_hash_manifest.py --output paper/result_hash_manifest.md`
- Final verification: `python -m pytest tests/test_experiments_framework.py -q`
- Final verification: `python experiments/make_paper_tables.py --config experiments/paper_eval_config.yaml --results-dir experiments/results --output-dir experiments/tables`
- Final verification: `python experiments/make_paper_figures.py --config experiments/paper_eval_config.yaml --results-dir experiments/results --output-dir experiments/figures`
- Final verification: `python scripts/validate_crisis_warning_contract.py artifacts/crisis_warning/global_h1 artifacts/crisis_warning/global_h5`
- Final verification: `find artifacts/crisis_warning/global_h1 artifacts/crisis_warning/global_h5 -type f -mmin -90`
- Final verification: `find backend frontend -type f -mmin -90`

### Generated or Updated Files

- `experiments/run_threshold_sensitivity.py`
- `experiments/generate_result_hash_manifest.py`
- `tests/test_experiments_framework.py`
- `experiments/results/threshold_sensitivity_metrics.csv`
- `experiments/tables/table_threshold_sensitivity.csv`
- `paper/table_threshold_sensitivity.md`
- `experiments/figures/threshold_sensitivity.png`
- `paper/figure_captions.md`
- `paper/result_hash_manifest.md`
- `experiments/portfolios/zero_overlap_supplement_portfolios.yaml`
- `experiments/zero_overlap_supplement_config.yaml`
- `experiments/results_zero_overlap/`
- `experiments/tables_zero_overlap/`
- `experiments/figures_zero_overlap/`
- `paper/zero_overlap_supplement/`
- `paper/zero_overlap_supplement_plan.md`
- `paper/latex_conversion_plan.md`
- `paper/latex/main.tex`
- `paper/main_draft.md`
- `paper/experiment_manifest.md`
- `paper/reviewer_risk_report.md`
- `paper/next_actions.md`

### Key Metrics and Facts

- Main threshold sensitivity generated 162 metric rows and 27 paper-table rows from 68,324 real-data crisis prediction rows; sandbox data disabled.
- Main global threshold 0.10: flag rate 4.23%, precision 0.1681, recall 0.1289, F1 0.1459.
- Main global threshold 0.60: 11 flags, precision 0.5455, recall 0.0016, F1 0.0032.
- Main ranking surveillance: top 1% precision 0.2602 and lift 4.7162; top 5% precision 0.1554 and lift 2.8163; top 10% precision 0.1209, recall 0.2191, lift 2.1908.
- H5 remains the critical threshold weakness: 0.60 produces 0 flags in both main and zero-overlap runs.
- Zero-overlap supplement: 10 portfolios, 36,114 predictions, 0 skipped rows, sandbox data disabled.
- Zero-overlap H1: ROC-AUC 0.6290, PR-AUC 0.0971, Brier 0.0480, recall@0.60 0.0043, top-decile lift 2.3551.
- Zero-overlap H5: ROC-AUC 0.6139, PR-AUC 0.0895, Brier 0.0534, recall@0.60 0.0000, top-decile lift 1.8100.
- Zero-overlap global threshold 0.10: precision 0.1703, recall 0.1179, F1 0.1394.
- Zero-overlap global threshold 0.60: 8 flags out of 36,114 rows, recall 0.0020.
- Experiment framework tests after threshold code changes: 6 passed.
- Final experiment framework tests: 6 passed.
- Final main table generation: artifact 2 rows, crisis 10 rows, baseline 12 rows, allocation 6 rows, ablation 6 rows, threshold sensitivity 27 rows.
- Final main figure generation: 7 figures generated, including `threshold_sensitivity.png`.
- Final crisis-warning artifact contract validation: passed.
- Final result hash manifest: 75 rows.
- Final modification scan: no files under frozen artifact directories were modified. No backend/frontend source files were edited; pytest/imports generated backend `__pycache__` files.

### Failures / Limitations

- `head -5` is not usable in this shell because `head` resolves to a different utility; CSV inspection used `sed`.
- Initial zero-overlap threshold run exposed an empty skipped-CSV edge case; `experiments/run_threshold_sensitivity.py` now treats empty CSV files as empty frames and the rerun passed.
- Superseded in the later IEEE Access package pass: the official template is now present, but local PDF compilation is blocked by missing LaTeX tools.

### Paper Readiness

- The paper is now framed as an auditable financial ML framework, not a new model or investment strategy.
- Threshold sensitivity and zero-overlap results reduce the largest reviewer attack surfaces.
- Remaining blocker is compiling the official IEEE Access LaTeX package in a TeX-enabled environment.

## 2026-05-18 HKT - IEEE Access Package Completion Pass

### Current Stage

P0/P1/P2 package hardening: dynamic table notes, uncertainty summaries, full IEEE Access LaTeX migration, status-document refresh, and final validation.

### Commands Run

- `python experiments/run_threshold_sensitivity.py --config experiments/paper_eval_config.yaml --results-dir experiments/results --tables-dir experiments/tables --figures-dir experiments/figures --paper-dir paper`
- `python experiments/run_threshold_sensitivity.py --config experiments/zero_overlap_supplement_config.yaml --results-dir experiments/results_zero_overlap --tables-dir experiments/tables_zero_overlap --figures-dir experiments/figures_zero_overlap --paper-dir paper/zero_overlap_supplement`
- `python experiments/make_paper_tables.py --config experiments/paper_eval_config.yaml --results-dir experiments/results --output-dir experiments/tables --paper-dir paper`
- `python experiments/make_paper_tables.py --config experiments/zero_overlap_supplement_config.yaml --results-dir experiments/results_zero_overlap --output-dir experiments/tables_zero_overlap --paper-dir paper/zero_overlap_supplement`
- `python experiments/run_uncertainty_summary.py --config experiments/paper_eval_config.yaml --results-dir experiments/results --tables-dir experiments/tables --paper-dir paper`
- `python -m pytest tests/test_experiments_framework.py -q`
- `python scripts/validate_crisis_warning_contract.py artifacts/crisis_warning/global_h1 artifacts/crisis_warning/global_h5`
- `pdflatex -interaction=nonstopmode main.tex` from `paper/latex`
- `latexmk -pdf main.tex` from `paper/latex`
- `python experiments/generate_result_hash_manifest.py --output paper/result_hash_manifest.md`

### Generated or Updated Files

- `experiments/make_paper_tables.py`
- `experiments/run_threshold_sensitivity.py`
- `experiments/run_uncertainty_summary.py`
- `experiments/generate_result_hash_manifest.py`
- `experiments/results/uncertainty_summary.csv`
- `experiments/tables/table_uncertainty_summary.csv`
- `paper/table_uncertainty_summary.md`
- `paper/main_draft.md`
- `paper/latex/main.tex`
- `paper/latex/ACCESS_latex_template_20240429.zip`
- `paper/final_status_report.md`
- `paper/reviewer_risk_report.md`
- `paper/latex_conversion_plan.md`
- `paper/next_actions.md`
- `paper/result_hash_manifest.md`

### Key Metrics and Facts

- Main table notes are now generated from the active `results_dir`.
- Zero-overlap crisis notes now report 36,114 prediction rows and 0 skipped rows.
- Zero-overlap baseline/allocation/ablation outputs are marked as not run for that supplement.
- Uncertainty summary generated 28 rows using 500 cross-portfolio bootstrap resamples.
- Official IEEE Access template files were downloaded from IEEE Access and retained under `paper/latex/`.
- Result hash manifest now has 84 rows and states that Git SHA is unavailable because this workspace is not a git repository.

### Validation Results

- Experiment framework tests: 6 passed.
- Crisis-warning artifact contract validation: passed.
- Main threshold generation: 68,324 prediction rows, 162 metric rows, 27 paper-table rows.
- Zero-overlap threshold generation: 36,114 prediction rows, 162 metric rows, 27 paper-table rows.
- Main table generation: artifact 2, crisis 10, baseline 12, allocation 6, ablation 6, threshold 27 rows.
- Zero-overlap table generation: artifact 2, crisis 10, baseline 0, allocation 0, ablation 0, threshold 27 rows.
- LaTeX compile attempt blocked: `pdflatex` and `latexmk` are not installed in this environment.

### Paper Readiness

- The package is ready for a TeX-enabled compile-and-polish pass.
- Author metadata, funding, conflict-of-interest, AI-use disclosure, and biography text have been provided and inserted into the LaTeX manuscript.
- The true remaining submission work is source/PDF synchronization, optional TeX Live compatibility compilation, and publication of the planned GitHub repository or another release archive with a URL plus Git SHA or DOI.
