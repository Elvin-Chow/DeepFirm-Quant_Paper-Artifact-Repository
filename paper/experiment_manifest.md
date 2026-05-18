# Experiment Manifest

This manifest records the frozen inputs, commands, and outputs for the IEEE Access paper evaluation. It is intentionally conservative: results enter the paper only if they are traceable to project scripts, generated files, or explicitly marked as not ready for paper use.

## Project State

- Workspace: `/Users/zhouhongyi/Documents/VS_Code/DeepFirm-Quant-Paper-2026`
- Project version: unavailable, current directory is not a Git repository.
- README project name: DeepFirm Quant
- Main experiment config: `experiments/paper_eval_config.yaml`
- Holdout portfolio config: `experiments/portfolios/holdout_portfolios.yaml`
- Sandbox data policy: disabled for paper experiments unless explicitly noted as a non-paper smoke test.

## Frozen Crisis-Warning Artifacts

| Horizon | Artifact path | Artifact hash | Metadata SHA-256 | Validation status | Global complete | Covered markets |
|---|---|---:|---:|---|---|---|
| 1D | `artifacts/crisis_warning/global_h1/` | `b807acefbc0c5774844331b7514791fd892f33a59846250728a64ca55506d6cd` | `50fa9b2e926b82be74f9e6c35e49d40bff64a519a57aa280b5cb198f0d1dafa3` | `degraded_validation` | true | US, HK, CN, JP, TW |
| 5D | `artifacts/crisis_warning/global_h5/` | `625482ed714b903cd94ebdfd47fc8d9b0b0e7e5282ccc6a3b9af290b537053d0` | `d557cf36493cbe820f7d55d6a9662ca3ca6d416f3001adf5f221b87d9473eafc` | `degraded_validation` | true | US, HK, CN, JP, TW |

## Training Coverage by Horizon

| Horizon | Training rows | Positive events | Validation positive events | Target definition |
|---|---:|---:|---:|---|
| 1D | 36,849 | 1,941 | 383 | Future 1D portfolio log return below trailing 5% historical 1D return threshold. |
| 5D | 36,689 | 2,102 | 379 | Future 5D portfolio log return below trailing 5% historical 5D return threshold. |

## Validation Metrics from Frozen Metadata

| Horizon | ROC-AUC | PR-AUC | Brier | Calibrated Brier | Log-loss | Calibrated log-loss | Calibration error | Precision@0.60 | Recall@0.60 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1D | 0.6112 | 0.0963 | 0.2112 | 0.0482 | 0.6141 | 0.1976 | 0.3928 | 0.1048 | 0.2010 |
| 5D | 0.5698 | 0.0712 | 0.2094 | 0.0485 | 0.6076 | 0.1987 | 0.3832 | 0.0708 | 0.1478 |

## Holdout Portfolio Coverage

- Total holdout portfolios: 20
- Markets: US, HK, CN, JP, TW
- Portfolios per market: 4
- Protocol note: Stage 1 will explicitly check ticker-set overlap against the training-domain portfolios recorded in frozen metadata.

## Planned Output Locations

### Experiment Outputs

- `experiments/results/crisis_predictions_h1.csv`
- `experiments/results/crisis_predictions_h5.csv`
- `experiments/results/crisis_metrics_by_portfolio.csv`
- `experiments/results/crisis_metrics_by_market.csv`
- `experiments/results/artifact_audit_summary.json`
- `experiments/results/baseline_metrics.csv`
- `experiments/results/ablation_metrics.csv`
- `experiments/results/allocation_oos_returns.csv`
- `experiments/results/allocation_oos_metrics.csv`
- `experiments/results/uncertainty_summary.csv`

### Paper Outputs

- `paper/experiment_protocol.md`
- `paper/data_availability_log.md`
- `paper/table_1_artifact_summary.md`
- `paper/table_2_crisis_metrics.md`
- `paper/table_3_baseline_comparison.md`
- `paper/table_4_allocation_oos.md`
- `paper/table_5_ablation.md`
- `paper/table_threshold_sensitivity.md`
- `paper/table_uncertainty_summary.md`
- `paper/related_work_notes.md`
- `paper/references.bib`
- `paper/citation_verification_log.md`
- `paper/main_draft.md`
- `paper/reviewer_risk_report.md`
- `paper/next_actions.md`
- `paper/final_status_report.md`
- `paper/result_hash_manifest.md`
- `paper/figure_captions.md`
- `paper/zero_overlap_supplement_plan.md`
- `paper/latex_conversion_plan.md`
- `paper/latex/main.tex`
- `paper/latex/ACCESS_latex_template_20240429.zip`

## Reproducibility Guardrails

- Do not retrain or overwrite `artifacts/crisis_warning/global_h1/`.
- Do not retrain or overwrite `artifacts/crisis_warning/global_h5/`.
- Do not modify backend API or frontend default behavior.
- Use experiment scripts under `experiments/` for paper numbers.
- Do not substitute sandbox data for failed real-market data in paper results.
- Do not add a citation to the manuscript unless it has been verified and recorded in the citation verification log.

## Added Pre-Submission Artifacts - 2026-05-18 HKT

### Threshold Sensitivity

- Script: `experiments/run_threshold_sensitivity.py`
- Main metrics: `experiments/results/threshold_sensitivity_metrics.csv`
- Main table: `experiments/tables/table_threshold_sensitivity.csv`
- Paper table: `paper/table_threshold_sensitivity.md`
- Figure: `experiments/figures/threshold_sensitivity.png`
- Threshold grid: 0.05, 0.075, 0.10, 0.15, 0.20, 0.30, 0.40, 0.50, 0.60
- Ranking surveillance: top 1%, top 5%, top 10% precision, recall, and lift

### Result Hashes

- Manifest: `paper/result_hash_manifest.md`
- Scope: key paper CSV, JSON, PNG, Markdown table, and LaTeX artifacts
- Hash algorithm: SHA-256 over file bytes
- Git SHA: unavailable because the workspace is not a git repository

### Zero-Security-Overlap Supplement

- Portfolio file: `experiments/portfolios/zero_overlap_supplement_portfolios.yaml`
- Config: `experiments/zero_overlap_supplement_config.yaml`
- Result directory: `experiments/results_zero_overlap`
- Prediction rows: 36,114
- Skipped rows: 0
- Sandbox data: disabled
- Supplement plan/results: `paper/zero_overlap_supplement_plan.md`

### Cross-Portfolio Uncertainty

- Script: `experiments/run_uncertainty_summary.py`
- Main result: `experiments/results/uncertainty_summary.csv`
- Paper table CSV: `experiments/tables/table_uncertainty_summary.csv`
- Paper Markdown table: `paper/table_uncertainty_summary.md`
- Bootstrap units: portfolios within each horizon for crisis-warning metrics; portfolios within each strategy for allocation metrics
- Bootstrap resamples: 500
- Frozen artifacts: not retrained

### IEEE Access LaTeX Package

- Official template zip: `paper/latex/ACCESS_latex_template_20240429.zip`
- Extracted template directory: `paper/latex/ACCESS_latex_template_20240429/`
- Main source: `paper/latex/main.tex`
- Current blocker: no local LaTeX engine is installed in this workspace, so PDF compilation must be completed in a TeX-enabled environment
