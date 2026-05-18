# Final Status Report

Updated: 2026-05-18 HKT

## Readiness

The DeepFirm Quant paper package has moved from a technical Markdown package to an IEEE Access pre-submission package with an official-template LaTeX manuscript, regenerated tables, uncertainty summaries, updated reviewer-defense notes, and a dedicated reproducibility README. Author-provided metadata, funding, conflict-of-interest, AI-use disclosure, and biography text have now been inserted into the LaTeX manuscript.

Current final-readiness status: `paper/latex/main.tex` and `paper/latex/main.pdf` are synchronized after a current-pass Tectonic recompile. The source and PDF no longer contain the IEEE template `xxxx` history placeholder or the old `10.1109/ACCESS.2026.DOI` placeholder. The remaining blocker is the human-provided archival metadata in Data and Code Availability: repository URL, Git commit SHA, and archive DOI.

## Current Final Readiness Pass

- Checked `paper/latex/main.tex` for the requested placeholder strings. Only the IEEE history `xxxx` placeholder was present initially; it has been replaced with a submitted-for-review history line. The requested `10.1109/ACCESS.2026.DOI` placeholder is no longer present in source.
- Verified all LaTeX `\ref` targets resolve to labels, all seven `\includegraphics` files resolve under `experiments/figures/`, and all 29 unique citation keys used in `main.tex` exist in `paper/references.bib`.
- Extended `experiments/generate_result_hash_manifest.py` to include root/reproducibility metadata files, dependency lockfiles, and experiment YAML configs in addition to result/table/figure/LaTeX artifacts.
- Re-ran the full test suite: `python -m pytest -q` passed with 209 tests.
- Re-ran frozen crisis-warning artifact contract validation: passed for `global_h1` and `global_h5`.
- Confirmed no system `pdflatex`, `latexmk`, `xelatex`, or `tectonic` executable was found on PATH. After explicit user approval, ran the previous temporary `/private/tmp/tectonic-0.16.9-aarch64-apple-darwin/tectonic` binary outside the sandbox and regenerated `paper/latex/main.pdf` successfully.
- Checked the regenerated PDF text layer with bundled `pypdf`: 13 pages, contains `Hongyi Zhou`, contains the new submitted-for-review history and "To be assigned by IEEE Access" DOI text, no `First Author` or `Second Author`, no requested placeholder strings, no `??` references, and no `[?]` citations.

## Previously Completed

- Fixed `experiments/make_paper_tables.py` so Markdown table notes are computed from the active result directory rather than hardcoded main-run constants.
- Regenerated main tables and zero-overlap supplement tables.
- Marked zero-overlap baseline, allocation, and ablation tables as not run for that supplement, preventing empty tables from entering the manuscript evidence.
- Documented the implemented crisis baseline comparison path and current `baseline_metrics.csv`, `baseline_predictions_h1.csv`, `baseline_predictions_h5.csv`, `baseline_training_summary.csv`, and `baseline_audit_summary.json` outputs.
- Updated `experiments/run_threshold_sensitivity.py` so its paper note is also result-driven.
- Added `experiments/run_uncertainty_summary.py`.
- Generated `experiments/results/uncertainty_summary.csv`, `experiments/tables/table_uncertainty_summary.csv`, and `paper/table_uncertainty_summary.md`.
- Added a statistical-uncertainty paragraph to `paper/main_draft.md`.
- Downloaded the official IEEE Access LaTeX template zip from IEEE Access and retained it under `paper/latex/`.
- Replaced `paper/latex/main.tex` with a full IEEE Access manuscript using the official `ieeeaccess` class, main figures, generated-result tables, metadata fields, and a crisis-warning-only zero-overlap appendix.
- Added the missing official-template `bullet.png` asset to the active LaTeX source directory.
- Added a small `ieeeaccess.cls` compatibility guard so Tectonic/XeTeX falls back to CMYK colors when pdfTeX spot-color primitives are unavailable; pdfTeX keeps the original spot-color path.
- Compiled `paper/latex/main.tex` with Tectonic 0.16.9 and generated `paper/latex/main.pdf`.
- Tightened reviewer-defense wording in the Markdown and LaTeX manuscripts, including explicit ranking-surveillance framing and a clearer crisis-warning-only statement for the zero-security-overlap supplement.
- Inserted the single-author metadata for Hongyi Zhou, PolyU SPEED affiliation, corresponding-author email, no external funding/self-funded statement, no-conflict statement, Codex AI-use disclosure, and author biography into `paper/latex/main.tex`.
- Updated `paper/next_actions.md`, `paper/reviewer_risk_report.md`, `paper/latex_conversion_plan.md`, and this status report.
- Added `paper/reproducibility_README.md` with artifact identification, dependency/version differences, local hardware/software facts, installation steps, experiment commands, expected outputs, runtime notes, reproducibility limits, and archival recommendations.
- Updated `paper/data_availability_log.md` with live-provider redistribution notes and the zero-security-overlap crisis supplement data availability result.
- Replaced the LaTeX Data and Code Availability wording with a formal statement that uses TODO placeholders for repository URL, Git commit SHA, and archive DOI.
- Updated `paper/next_actions.md` to make the remaining author/archive metadata explicit.

## Key Results

- Main crisis-warning run: 68,324 prediction rows, 2 skipped crisis-warning rows, sandbox disabled.
- Main crisis baseline run: 82,086 final-window prediction rows, 300 metric rows, 228 training-summary rows, 2 skipped baseline-evaluation rows, sandbox disabled.
- Baseline comparison includes frozen calibrated XGBoost, frozen raw XGBoost without calibration, historical tail threshold, logistic regression, random forest, and gradient boosting.
- Zero-overlap crisis supplement: 36,114 prediction rows, 0 skipped crisis-warning rows, sandbox disabled.
- Main global threshold 0.10: precision 0.1681, recall 0.1289, F1 0.1459, flag rate 4.23%.
- Main global threshold 0.60: 11 flags out of 68,324 rows, recall 0.0016.
- Main top-decile surveillance: precision 0.1209, recall 0.2191, lift 2.1908.
- Uncertainty summary: 28 rows using 500 cross-portfolio bootstrap resamples.
- Allocation remains conservative: Smart policy plus OOS guard has the best mean Sharpe/model score, but all strategies have negative mean benchmark excess return.

## Verification

- `python -m pytest -q`: 209 passed.
- `python scripts/validate_crisis_warning_contract.py artifacts/crisis_warning/global_h1 artifacts/crisis_warning/global_h5`: passed.
- `python experiments/run_threshold_sensitivity.py --config experiments/paper_eval_config.yaml --results-dir experiments/results --tables-dir experiments/tables --figures-dir experiments/figures --paper-dir paper`: passed, 68,324 prediction rows and 162 metric rows.
- `python experiments/run_crisis_baseline_eval.py --config experiments/paper_eval_config.yaml --output-dir experiments/results --allow-sandbox-data false`: passed, 82,086 prediction rows and 300 metric rows.
- `python experiments/run_threshold_sensitivity.py --config experiments/zero_overlap_supplement_config.yaml --results-dir experiments/results_zero_overlap --tables-dir experiments/tables_zero_overlap --figures-dir experiments/figures_zero_overlap --paper-dir paper/zero_overlap_supplement`: passed, 36,114 prediction rows and 162 metric rows.
- `python experiments/make_paper_tables.py --config experiments/paper_eval_config.yaml --results-dir experiments/results --output-dir experiments/tables --paper-dir paper`: passed, 2/10/12/6/6/27 rows across generated table CSVs.
- `python experiments/make_paper_tables.py --config experiments/zero_overlap_supplement_config.yaml --results-dir experiments/results_zero_overlap --output-dir experiments/tables_zero_overlap --paper-dir paper/zero_overlap_supplement`: passed, 2/10/0/0/0/27 rows across generated table CSVs.
- `python experiments/run_uncertainty_summary.py --config experiments/paper_eval_config.yaml --results-dir experiments/results --tables-dir experiments/tables --paper-dir paper`: passed, 28 uncertainty rows.
- `python experiments/generate_result_hash_manifest.py --output paper/result_hash_manifest.md`: passed, 96 manifest rows after extending source-package metadata coverage.
- `which pdflatex`, `which latexmk`, `which xelatex`, `which lualatex`, `which tectonic`: no system LaTeX engine found.
- Temporary Tectonic 0.16.9 macOS arm64 binary was downloaded to `/private/tmp/` after approval and used to compile `paper/latex/main.tex`.
- `/private/tmp/tectonic-0.16.9-aarch64-apple-darwin/tectonic --keep-logs --keep-intermediates main.tex`: passed and generated `paper/latex/main.pdf`.
- Post-metadata Tectonic recompile of `paper/latex/main.tex`: passed and regenerated `paper/latex/main.pdf`.
- Current-pass compile with the same temporary Tectonic binary outside the sandbox after explicit approval: passed and regenerated `paper/latex/main.pdf`.
- Current PDF text-layer check with bundled `pypdf`: 13 pages, contains `Hongyi Zhou`, contains the new submitted-for-review history and "To be assigned by IEEE Access" DOI text, no requested placeholder strings, no `First Author` or `Second Author`, no `??` references, and no `[?]` citations.
- QuickLook page rendering of split PDF pages: main figures and tables were visually readable; no obvious missing figure, blank page, or table clipping was observed.
- `rg -n "final submission should|workspace is not a git repository|TODO|DOI|requirements|numpy|pandas" paper/latex/main.tex paper/reproducibility_README.md`: passed; no stale `final submission should` wording remains, and Git/repository/archive placeholders are explicitly marked TODO.
- `python -m pytest tests/test_experiments_framework.py -q`: 6 passed in 2.18s.

## Remaining Submission Items

- Create or publish the planned GitHub repository and add its URL plus a Git commit SHA or DOI before final release/archive.
- Replace all repository URL, Git commit SHA, and archive DOI TODO placeholders in `paper/latex/main.tex` and the paper package after the release exists.
- Regenerate `paper/result_hash_manifest.md` after final archival/source metadata updates, so hashes correspond to the final submitted package.
- A full TeX Live `pdflatex`/BibTeX pass remains a useful final compatibility check if the authors have that environment, because this workspace used Tectonic/XeTeX as the lightweight compile path.
- The workspace is not a git repository, so the result manifest must continue to report no Git SHA unless the authors archive or initialize version control before submission.
