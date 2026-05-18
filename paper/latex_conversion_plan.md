# IEEE Access LaTeX Conversion Plan

Status: full local manuscript migration completed; `paper/latex/main.pdf` was generated locally with Tectonic 0.16.9. The environment still lacks system `pdflatex`, `latexmk`, `xelatex`, and `lualatex`, so a full TeX Live pdfTeX pass remains an optional compatibility check on a submission machine.

## Template Source

- Official IEEE Access template page: `https://ieeeaccess.ieee.org/authors/submission-guidelines/`
- Official zip downloaded to: `paper/latex/ACCESS_latex_template_20240429.zip`
- Extracted template directory: `paper/latex/ACCESS_latex_template_20240429/`
- Compile-root support files copied into `paper/latex/`, including `ieeeaccess.cls`, `IEEEtran.bst`, `IEEEtran.cls`, `spotcolor.sty`, logos, `bullet.png`, and template font files.

## Migrated Inputs

- Main Markdown draft: `paper/main_draft.md`
- Verified bibliography: `paper/references.bib`
- Main generated paper tables: `paper/table_1_artifact_summary.md`, `paper/table_2_crisis_metrics.md`, `paper/table_3_baseline_comparison.md`, `paper/table_4_allocation_oos.md`, `paper/table_5_ablation.md`, `paper/table_threshold_sensitivity.md`, `paper/table_uncertainty_summary.md`
- Zero-overlap supplement tables: `paper/zero_overlap_supplement/table_1_artifact_summary.md`, `paper/zero_overlap_supplement/table_2_crisis_metrics.md`, `paper/zero_overlap_supplement/table_threshold_sensitivity.md`
- Figure captions: `paper/figure_captions.md`
- Figure files: `experiments/figures/*.png`
- Result hashes: `paper/result_hash_manifest.md`

## Current LaTeX Package

- Main source: `paper/latex/main.tex`
- Generated PDF: `paper/latex/main.pdf`
- Class: official `ieeeaccess`
- Bibliography: `paper/references.bib`, referenced from `paper/latex/main.tex` as `../references`
- Figures included:
  - `framework_architecture.png`
  - `roc_pr_by_horizon.png`
  - `calibration_by_horizon.png`
  - `threshold_sensitivity.png`
  - `shap_top_drivers.png`
  - `allocation_oos_curves.png`
  - `ablation_summary.png`
- Main tables included:
  - Frozen artifact audit summary
  - Audit-contract controls
  - Crisis warning metrics
  - Threshold sensitivity
  - Baseline comparison
  - Allocation OOS
  - Allocation ablation
  - Cross-portfolio uncertainty summary
- Appendix:
  - Zero-security-overlap crisis-warning supplement only
  - Baseline/allocation/ablation supplement outputs are not reported because they were not run for that supplement

## Compile Status

1. System `pdflatex`, `latexmk`, `xelatex`, `lualatex`, and `tectonic` were not found on `PATH`.
2. A temporary Tectonic 0.16.9 macOS arm64 binary was downloaded to `/private/tmp/` after approval.
3. Running Tectonic from `paper/latex/` generated `main.pdf`, `main.log`, `main.bbl`, `main.blg`, and `main.aux`.
4. References and citations resolved: the PDF text layer has no `??` references and no `[?]` citations.
5. QuickLook-rendered page thumbnails showed readable figures and tables with no obvious missing figures or table clipping.
6. Re-run `python experiments/generate_result_hash_manifest.py --output paper/result_hash_manifest.md` after any final source or PDF change.

## Claim-Control Notes

- Do not use sandbox or synthetic data in any paper number.
- Keep the zero-security-overlap supplement as a crisis-warning-only appendix unless new real supplement experiments are actually run.
- State that the 0.60 threshold is a conservative operating point and that the more defensible operational reading is ranking/top-decile surveillance.
- Keep allocation claims conservative because benchmark excess return is negative for every listed strategy.
- Do not add new references unless they are verified and recorded in `paper/citation_verification_log.md`.
