#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path


FORBIDDEN_TOP_LEVEL = {
    ".github",
    "build",
    "build-templates",
    "conversation-starters",
    "docs",
    "evals",
    "knowledge",
    "runtime",
    "schemas",
    "scripts",
    "src",
    "tests",
}

REQUIRED_FILES = {
    "START-HERE.md",
    "VERSION",
    "MANIFEST.json",
    "assistant/instructions.md",
    "assistant/conversation-starters.md",
    "assistant/runtime-contract.json",
    "research-state.yaml",
    "assistant/policies/report-policy.md",
    "assistant/policies/research-policy.md",
    "assistant/policies/workflow-policy.md",
    "templates/market-map-report.md",
}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def validate_build(build: Path) -> list[str]:
    errors: list[str] = []
    if not build.exists():
        return ["Chat build directory missing"]

    actual_files = {
        p.relative_to(build).as_posix()
        for p in build.rglob("*")
        if p.is_file()
    }
    missing = sorted(REQUIRED_FILES - actual_files)
    for rel in missing:
        errors.append(f"Missing required Chat runtime file: {rel}")

    for rel in sorted(actual_files):
        top = rel.split("/", 1)[0]
        if top in FORBIDDEN_TOP_LEVEL:
            errors.append(f"Development-only path leaked into Chat runtime: {rel}")
        if rel.endswith((".py", ".pyc", ".pyo")):
            errors.append(f"Executable/development Python file leaked into Chat runtime: {rel}")

    manifest_path = build / "MANIFEST.json"
    if not manifest_path.exists():
        return errors

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("entrypoint") != "START-HERE.md":
        errors.append("Chat manifest entrypoint must be START-HERE.md")

    manifest_entries = {item["path"]: item for item in manifest.get("files", [])}
    expected_manifest_files = actual_files - {"MANIFEST.json"}
    if set(manifest_entries) != expected_manifest_files:
        missing_manifest = sorted(expected_manifest_files - set(manifest_entries))
        stale_manifest = sorted(set(manifest_entries) - expected_manifest_files)
        for rel in missing_manifest:
            errors.append(f"File missing from Chat manifest: {rel}")
        for rel in stale_manifest:
            errors.append(f"Manifest references absent Chat file: {rel}")

    for rel, item in manifest_entries.items():
        p = build / rel
        if not p.exists():
            continue
        data = p.read_bytes()
        if item.get("sha256") != digest(data):
            errors.append(f"Checksum mismatch in Chat manifest: {rel}")
        if item.get("size") != len(data):
            errors.append(f"Size mismatch in Chat manifest: {rel}")

    start = (build / "START-HERE.md").read_text(encoding="utf-8") if (build / "START-HERE.md").exists() else ""
    for stale in ["`knowledge/`", "`schemas/`", "`scripts/`"]:
        if stale in start:
            errors.append(f"START-HERE advertises absent runtime path: {stale}")

    instructions = (build / "assistant" / "instructions.md").read_text(encoding="utf-8") if (build / "assistant" / "instructions.md").exists() else ""
    required_markers = [
        "Gör aktuell webbresearch för marknadskartläggningar.",
        "Skilj tydligt mellan **verifierade fakta** och **analys/bedömning**.",
        "Skriv ”Gör nästa steg” så fortsätter jag kartläggningen.",
        "Den nedladdningsbara Markdown-filen är obligatorisk slutleverans.",
    ]
    for marker in required_markers:
        if marker not in instructions:
            errors.append(f"Canonical core marker missing from Chat runtime: {marker}")

    contract_path = build / "assistant" / "runtime-contract.json"
    if contract_path.exists():
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
        if contract.get("runtime_id") != "chatgpt_chat":
            errors.append("Chat runtime contract has wrong runtime_id")
        if contract.get("adapter", {}).get("state_template") != "research-state.yaml":
            errors.append("Chat runtime contract has wrong state template")
        if contract.get("workspace_state", {}).get("state", {}).get("authority") != "workspace_file":
            errors.append("Chat runtime contract must preserve workspace-file state authority")

    return errors


def validate_zip(zip_path: Path, build: Path) -> list[str]:
    errors: list[str] = []
    if not zip_path.exists():
        return [f"Chat ZIP missing: {zip_path}"]
    with zipfile.ZipFile(zip_path) as zf:
        zip_files = {n for n in zf.namelist() if not n.endswith("/")}
        build_files = {p.relative_to(build).as_posix() for p in build.rglob("*") if p.is_file()}
        if zip_files != build_files:
            for rel in sorted(build_files - zip_files):
                errors.append(f"Chat ZIP missing build file: {rel}")
            for rel in sorted(zip_files - build_files):
                errors.append(f"Chat ZIP contains unexpected file: {rel}")
        for rel in sorted(zip_files & build_files):
            if zf.read(rel) != (build / rel).read_bytes():
                errors.append(f"Chat ZIP content differs from build output: {rel}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--zip", default=None, help="Optional path to built Chat ZIP")
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    build = root / "build" / "chat"
    errors = validate_build(build)
    if args.zip:
        errors.extend(validate_zip(Path(args.zip).resolve(), build))

    if errors:
        print("CHAT RUNTIME VALIDATION: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("CHAT RUNTIME VALIDATION: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
