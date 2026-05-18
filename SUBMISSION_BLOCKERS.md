# Submission Blockers

## A-level blockers remaining

1. Public GitHub tag publication is not verified from this environment. The local tag `v0.1-submission` exists and points to `bb5053309084281e8892b0ea730925720ab6e09f`, but `git push origin v0.1-submission` failed because GitHub HTTPS credentials are not configured here. If the public repository must expose the tag before submission, push this tag from an authenticated shell.

## B-level issues remaining

1. The PDF was regenerated with Tectonic, not a full TeX Live `pdflatex`/BibTeX workflow, because `pdflatex`, `latexmk`, and `bibtex` are not on PATH. Tectonic completed and wrote `paper/latex/main.pdf`, but it still reports pre-existing layout warnings and a rerun warning.
2. The cited release commit remains the clean artifact commit requested for Data Availability; this cleanup commit records the final manuscript metadata, manifest, and PDF/source synchronization edits.

## Final repository URL

https://github.com/Elvin-Chow/DeepFirm-Quant_Paper-Artifact-Repository

## Release tag

`v0.1-submission`

## Commit SHA

`bb5053309084281e8892b0ea730925720ab6e09f`

## Data Availability check

Passed. `paper/latex/main.tex` now contains the public repository URL, release tag, commit SHA, and the archival DOI status sentence: "An archival DOI will be provided through a release archive when available."

## Zero-overlap framing check

Passed. The manuscript frames the zero-security-overlap material as a transfer check and states that baseline comparison, allocation OOS, and allocation ablation were not run for that panel; the evidence is limited to crisis-warning transfer behavior.

## PDF/source consistency check

Passed with the Tectonic caveat above. `paper/latex/main.tex`, `paper/references.bib`, `paper/latex/main.bbl`, `README.md`, `paper/result_hash_manifest.md`, and extracted text from `paper/latex/main.pdf` were searched for the requested stale phrases, and no matches remain in those checked submission files.
