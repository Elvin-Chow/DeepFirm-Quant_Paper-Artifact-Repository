# Reviewer Risk Report

Perspective: IEEE Access applied research reviewer.

Updated: 2026-05-18 HKT after dynamic table-note repair, uncertainty summaries, full IEEE Access LaTeX migration, and local PDF generation with Tectonic.

## Summary Judgment

The submission is now defensible as an applied, system-oriented IEEE Access paper if the authors keep the claims conservative. The novelty is not a new classifier or optimizer; it is an auditable financial ML framework with frozen artifacts, hash/schema validation, provenance logs, no sandbox substitution, SHAP-style explanations, leakage-guarded allocation checks, threshold sensitivity, uncertainty reporting, and data-availability accounting.

## Risk Table

| Severity | Risk | Current assessment | Fix status | Blocks submission |
|---|---|---|---|---|
| Medium | Predictive novelty may look incremental | The manuscript frames novelty as an audit contract rather than XGBoost/SHAP/Black-Litterman novelty. | Addressed; keep this framing in title, abstract, and introduction. | No |
| Medium | Threshold recall is weak | Threshold sensitivity shows 0.60 is over-conservative: 11 global flags in the main run and zero H5 flags. | Addressed as evidence, not fixed as model behavior. | No, if framed as ranking surveillance |
| Medium | Holdout portfolios are not fully security-disjoint | Main holdout remains portfolio-level external validation, but the zero-overlap supplement now has 10 portfolios, 36,114 predictions, 0 skipped rows, and sandbox disabled. | Addressed with supplement. | No |
| Medium | Allocation does not beat benchmarks | The manuscript states all strategies have negative mean benchmark excess return and limits claims to Sharpe/model score/turnover discipline. | Addressed. | No |
| Medium | Statistical uncertainty could weaken claims | New bootstrap intervals are honest: allocation intervals are wide and benchmark-excess intervals remain mostly negative. | Addressed by adding Table 7 and conservative interpretation. | No |
| Medium | Baseline fairness could be questioned | Crisis baselines are now implemented in `experiments/run_crisis_baseline_eval.py`: non-frozen baselines train on the first 80% and evaluate on the final 20%, while frozen artifacts are sliced to the same windows. | Addressed for the stated final-window design; purged/embargoed challenger validation remains optional. | No |
| Low | Data availability limitations | Main text and captions report skipped CN portfolios and no sandbox substitution. Zero-overlap crisis supplement had 0 skipped rows. | Addressed. | No |
| Low | Result traceability without Git SHA | The workspace is not a Git repo, but the result manifest hashes key CSV/JSON/PNG/MD/LaTeX artifacts and states no Git SHA. | Addressed for artifacts; archival version control remains preferable. | No |
| Low | Empty supplement tables | Empty zero-overlap baseline/allocation/ablation tables are marked as not run and excluded from the LaTeX evidence narrative. | Addressed. | No |
| Low | PDF compilation | `paper/latex/main.pdf` now compiles locally with Tectonic 0.16.9 after adding the missing template bullet asset and a small pdfTeX spot-color compatibility guard. | Addressed for local PDF generation; a full TeX Live pdfTeX pass is still useful if available. | No |

## Specific Reviewer Checks

Threshold recall:

- Main run: threshold 0.60 has global recall 0.0016 and H5 recall 0.0000.
- Threshold 0.10 gives global precision 0.1681, recall 0.1289, F1 0.1459 with 4.23% flag rate.
- Top-decile surveillance gives precision 0.1209, recall 0.2191, lift 2.1908.
- Interpretation: acceptable only as ranking surveillance or watchlist triage, not a binary alarm.

Uncertainty:

- H1 ROC-AUC 0.6325 with cross-portfolio interval 0.6093 to 0.6533.
- H5 ROC-AUC 0.6325 with cross-portfolio interval 0.6099 to 0.6511.
- Smart policy plus OOS guard Sharpe 1.1914 with interval 0.7229 to 1.7184.
- Smart policy plus OOS guard benchmark excess return -0.1363 with interval -0.2844 to -0.0191.
- Interpretation: useful applied evidence, not universal superiority.

Novelty:

- Strongest when framed as the audit contract and reproducibility discipline.
- Avoid phrases such as "outperforms benchmarks", "strong warning model", and "investment recommendation".

Baseline fairness:

- Current main output has 82,086 final-window baseline prediction rows, 300 metric rows, and 2 logged skipped rows with sandbox disabled.
- Compared baselines are frozen calibrated XGBoost, frozen raw XGBoost without calibration, historical tail threshold, logistic regression, random forest, and gradient boosting.
- Adequate for an applied paper if the final-window protocol remains explicit and the results are not framed as a production challenger-model validation.
- A purged/embargoed baseline would be stronger but is not a blocker if not overclaimed.

Allocation claim:

- Current claim is appropriately restrained. Smart policy with OOS guard has the highest mean Sharpe/model score in this run, but benchmark excess return is negative for all strategies.

## Submission Items

1. Author-provided metadata, funding, conflict-of-interest, AI-use disclosure, and biography text have been inserted into the LaTeX manuscript; the author should do one final wording review.
2. Publish the planned GitHub repository or release archive and record a repository URL plus Git SHA or DOI before final submission if immutable provenance is required.
3. Optionally run one final full TeX Live `pdflatex`/BibTeX pass if the submission machine has TeX Live, because the local PDF was generated through the lightweight Tectonic path.

## Non-Blocking Risks

- Run zero-overlap baseline/allocation supplements only if reviewers ask for them.
- Add component-level Smart-policy ablations only if the paper claims component causality.
- Archive the final package in a git repository or release archive if the authors want a Git SHA alongside the SHA-256 file manifest.
