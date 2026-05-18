"""Generate SHA-256 manifest for paper result artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

REPOSITORY_URL = "https://github.com/Elvin-Chow/DeepFirm-Quant_Paper-Artifact-Repository"
RELEASE_TAG = "v0.1-submission"


DEFAULT_PATTERNS = [
    ".gitattributes",
    ".github/workflows/ci.yml",
    ".gitignore",
    "CITATION.cff",
    "DATA.md",
    "README.md",
    "RELEASE_CHECKLIST.md",
    "requirements.txt",
    "requirements-dev.txt",
    "frontend/package.json",
    "frontend/package-lock.json",
    "experiments/*.yaml",
    "experiments/portfolios/*.yaml",
    "experiments/results/*.csv",
    "experiments/results/*.json",
    "experiments/results_zero_overlap/*.csv",
    "experiments/results_zero_overlap/*.json",
    "experiments/tables/*.csv",
    "experiments/tables_zero_overlap/*.csv",
    "experiments/figures/*.png",
    "experiments/figures_zero_overlap/*.png",
    "paper/table_*.md",
    "paper/table_threshold_sensitivity.md",
    "paper/table_uncertainty_summary.md",
    "paper/zero_overlap_supplement/*.md",
    "paper/baseline_ablation_gap_report.md",
    "paper/citation_verification_log.md",
    "paper/experiment_protocol.md",
    "paper/zero_overlap_supplement_plan.md",
    "paper/figure_captions.md",
    "paper/data_availability_log.md",
    "paper/experiment_manifest.md",
    "paper/final_status_report.md",
    "paper/latex_conversion_plan.md",
    "paper/next_actions.md",
    "paper/paper_worklog.md",
    "paper/reproducibility_README.md",
    "paper/reviewer_risk_report.md",
    "paper/references.bib",
    "paper/related_work_notes.md",
    "paper/main_draft.md",
    "paper/latex/ACCESS_latex_template_20240429.zip",
    "paper/latex/*.cls",
    "paper/latex/*.bst",
    "paper/latex/*.sty",
    "paper/latex/main.bbl",
    "paper/latex/main.tex",
    "paper/latex/main.pdf",
]


def git_release_sha(root: Path = ROOT) -> str:
    commands = (
        ["git", "rev-list", "-n", "1", RELEASE_TAG],
        ["git", "rev-parse", "HEAD"],
    )
    for command in commands:
        try:
            return subprocess.run(
                command,
                cwd=root,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
        except Exception:
            continue
    return "not recorded in this generation context"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def iter_files(patterns: Iterable[str], root: Path = ROOT) -> list[Path]:
    files: list[Path] = []
    seen: set[Path] = set()
    for pattern in patterns:
        for path in sorted(root.glob(pattern)):
            if not path.is_file():
                continue
            resolved = path.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            files.append(path)
    return sorted(files, key=lambda item: item.as_posix())


def manifest_rows(patterns: Iterable[str], root: Path = ROOT) -> list[dict[str, object]]:
    rows = []
    for path in iter_files(patterns, root=root):
        rows.append(
            {
                "path": path.relative_to(root).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    return rows


def write_markdown(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    generated = datetime.now().astimezone().isoformat(timespec="seconds")
    lines = [
        "# Result Hash Manifest",
        "",
        f"Generated: {generated}",
        "",
        "Scope: key paper result CSV, JSON, PNG, Markdown table, release documentation, dependency/lockfile, experiment-config, CI, and LaTeX artifacts. Hashes are SHA-256 over file bytes.",
        "",
        f"Repository URL: {REPOSITORY_URL}",
        f"Release tag: `{RELEASE_TAG}`",
        f"Commit SHA: `{git_release_sha()}`",
        "",
        "| Path | Bytes | SHA-256 |",
        "|---|---:|---|",
    ]
    for row in rows:
        lines.append(f"| `{row['path']}` | {row['bytes']} | `{row['sha256']}` |")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate paper result SHA-256 manifest.")
    parser.add_argument("--output", default=str(ROOT / "paper" / "result_hash_manifest.md"))
    parser.add_argument("--json-output", default=None)
    parser.add_argument("--patterns", default=None, help="Comma-separated glob patterns. Defaults cover paper outputs.")
    return parser


def main() -> int:
    args = make_parser().parse_args()
    patterns = DEFAULT_PATTERNS if args.patterns is None else [item.strip() for item in args.patterns.split(",")]
    rows = manifest_rows(patterns)
    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = ROOT / output_path
    write_markdown(output_path, rows)
    if args.json_output:
        json_path = Path(args.json_output)
        if not json_path.is_absolute():
            json_path = ROOT / json_path
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(rows, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output_path), "rows": len(rows)}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
