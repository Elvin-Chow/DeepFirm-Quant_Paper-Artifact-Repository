# Next Actions

## Shortest Path To IEEE Access Submission

1. Review the inserted author metadata and disclosures in `paper/latex/main.tex` for final wording.
2. Create the final public repository, Zenodo release, Code Ocean capsule, or equivalent immutable archive.
3. Replace the Data and Code Availability TODO placeholders with the repository URL, Git commit SHA, and archive DOI. Do not invent any of these values.
4. Recompile `paper/latex/main.tex` only after the archive metadata or source text changes again; the current PDF has been regenerated from the current source.
5. Regenerate `paper/result_hash_manifest.md` after the final archive/source package is fixed, so the manifest covers the final Data Availability, reproducibility README, README/dependency/config files, and LaTeX/PDF state.
6. Optionally run a final full TeX Live `pdflatex`/BibTeX compatibility pass on `paper/latex/main.tex` if the submission machine has TeX Live; the current workspace generated `paper/latex/main.pdf` with Tectonic 0.16.9 because no system `pdflatex` or `tectonic` executable is currently on PATH.
7. Submit the IEEE Access source package, generated PDF, figures, bibliography, and supplementary material only after the archive metadata is filled and the source/PDF/manifest are regenerated one final time.

## Already Addressed

1. The paper-table generator now writes notes from the active `results_dir`, including row counts, horizons, skipped rows/portfolios, allocation row counts, and threshold-sensitivity row counts.
2. Main and zero-overlap tables were regenerated; the zero-overlap supplement now reports 36,114 prediction rows and 0 skipped rows.
3. Empty zero-overlap baseline/allocation/ablation tables are explicitly marked as not run for that supplement and are not used as manuscript evidence.
4. Cross-portfolio uncertainty outputs were generated and added to the Markdown and LaTeX manuscripts.
5. `paper/latex/main.tex` now uses the official IEEE Access template package and includes the full manuscript, main figures, main tables, metadata fields, and a crisis-warning-only zero-overlap appendix.
6. `paper/latex/main.pdf` was generated locally with Tectonic 0.16.9 after adding the missing official-template `bullet.png` asset and a small compatibility guard for non-pdfTeX compilation.
7. The zero-overlap supplement wording now explicitly states that it is crisis-warning-only; baseline comparison, allocation OOS, and allocation ablation were not run for that supplement.
8. Single-author metadata, affiliation, corresponding-author email, no external funding/self-funded statement, no-conflict statement, Codex AI-use disclosure, and biography text have been inserted into the LaTeX manuscript.
9. `paper/reproducibility_README.md` now records artifact scope, dependency/version differences, hardware/software facts read from the local machine, install steps, experiment commands, expected outputs, runtime notes, limits, and archival recommendations.
10. `paper/data_availability_log.md` now includes live-provider redistribution notes and the zero-security-overlap crisis supplement data availability result.
11. The LaTeX Data and Code Availability section now uses formal TODO placeholders for repository URL, Git commit SHA, and archive DOI rather than implying a completed final release.
12. The IEEE template `xxxx` history placeholder and DOI placeholder text were removed from `paper/latex/main.tex` during the final readiness pass.
13. The result-hash manifest generator now includes README, reproducibility README, requirements, frontend lockfiles, and experiment YAML configs.
14. `paper/latex/main.pdf` has been regenerated from the current `paper/latex/main.tex`; PDF text-layer checks found no unresolved references/citations or requested placeholders.

## Optional Reviewer Defense

1. Run zero-overlap baseline comparison only if reviewers specifically ask for a strict security-disjoint baseline supplement.
2. Run zero-overlap allocation OOS only if reviewers ask whether allocation behavior changes under strict security disjointness.
3. Add component-level Smart-policy ablations only if the manuscript begins making component-level causal claims.
4. Re-run CN provider fetches only to reduce skipped main-run rows; do not substitute sandbox data.
