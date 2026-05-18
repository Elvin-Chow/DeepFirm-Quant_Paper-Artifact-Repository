# Public Repository Release Checklist

Use this checklist before pushing the experiment package to a new public GitHub repository.

## Repository Boundary

- [ ] Keep this as a paper experiment/reproducibility repository, separate from the main DeepFirm Quant product repository.
- [ ] Track source code, frozen artifacts, experiment configs, generated paper outputs, figures, tables, and paper documentation.
- [ ] Do not track local runtime caches, virtual environments, pycache files, Node build outputs, editor files, or raw provider cache files.
- [ ] Keep the Hugging Face/Vercel deployment workflow in the main product repository unless a new deployment target is intentionally configured.

## Data and Secrets

- [ ] Confirm `cache/` is ignored.
- [ ] Confirm `data/` is ignored unless a future explicitly licensed dataset is added with a separate license note.
- [ ] Confirm no `.env`, `.env.*`, token, password, API key, or credential file is present.
- [ ] Confirm paper experiments use `allow_sandbox_data: false`.
- [ ] Confirm provider failures are documented in skip files and `paper/data_availability_log.md`.

## Verification

- [ ] Run `python scripts/validate_crisis_warning_contract.py`.
- [ ] Run the paper guardrail tests from the README.
- [ ] Regenerate `paper/result_hash_manifest.md`.
- [ ] Check `git status --short --ignored` before the first commit.
- [ ] Check for large files with `find . -type f -size +50M -print`.

## Archive Metadata

- [ ] Create the GitHub repository.
- [ ] Push the cleaned `main` branch.
- [ ] Record the final commit SHA.
- [ ] Create a release tag such as `paper-submission-v1`.
- [ ] Create an archive DOI if needed, for example through Zenodo, Code Ocean, or an institutional archive.
- [ ] Replace repository URL, Git SHA, and DOI TODO placeholders in the paper package after the values exist.

## Suggested First Commit

```bash
git init -b main
git add .
git status --short
git commit -m "Prepare paper reproducibility package"
```

After creating the remote repository:

```bash
git remote add origin <new-repository-url>
git push -u origin main
git tag paper-submission-v1
git push origin paper-submission-v1
```
