#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path


REQUIRED_SHARED = [
    "python scripts/lint_gpt_project.py --project-root .",
    "python scripts/project_hygiene.py --project-root . --mode checkpoint",
    "python -m unittest discover -s tests -p 'test_*.py'",
    "python scripts/validate_instruction_adherence.py --project-root .",
    "python scripts/validate_distributions.py --project-root .",
    "python scripts/validate_runtime_parity.py --project-root .",
    "python scripts/validate_release_readiness.py --project-root .",
]


def validate(root: Path) -> list[str]:
    errors: list[str] = []
    ci = (root / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    release = (root / ".github/workflows/release.yml").read_text(encoding="utf-8")

    for command in REQUIRED_SHARED:
        if command not in ci:
            errors.append(f"CI missing shared gate: {command}")
        if command not in release:
            errors.append(f"Release missing shared gate: {command}")

    ci_target = "--targets project,chat,custom-gpt"
    if ci_target not in ci or ci_target not in release:
        errors.append("CI and release must build the same active targets")

    for marker in (
        "validate_chat_runtime.py",
        "validate_custom_gpt_runtime.py",
    ):
        if marker not in ci or marker not in release:
            errors.append(f"CI/release runtime validation drift: {marker}")

    if "github.event.release.tag_name" not in release:
        errors.append("Release version must derive from GitHub Release tag")

    if "validate_workflow_parity.py" not in release:
        errors.append("Release must enforce workflow parity")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    args = parser.parse_args()
    errors = validate(Path(args.project_root).resolve())
    if errors:
        print("WORKFLOW PARITY: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("WORKFLOW PARITY: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
