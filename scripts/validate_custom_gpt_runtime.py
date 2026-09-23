#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path

import yaml

REQUIRED_FILES = {
    "README.md",
    "COMPATIBILITY.md",
    "VERSION",
    "MANIFEST.json",
    "builder/instructions.md",
    "builder/conversation-starters.md",
    "builder/capabilities.md",
    "builder/compilation-report.json",
}

FORBIDDEN_TOP_LEVEL = {
    ".github", "build", "build-templates", "docs", "evals", "runtime",
    "schemas", "scripts", "src", "tests"
}

CORE_MARKERS = [
    "Gör aktuell webbresearch för marknadskartläggningar.",
    "Skilj tydligt mellan **verifierade fakta** och **analys/bedömning**.",
    "Skriv ”Gör nästa steg” så fortsätter jag kartläggningen.",
    "Den nedladdningsbara Markdown-filen är obligatorisk slutleverans.",
    "Operativ kärna",
    "Auktoritativ status",
]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def validate_build(root: Path, build: Path) -> list[str]:
    errors: list[str] = []
    if not build.exists():
        return ["Custom GPT build directory missing"]

    cfg = yaml.safe_load((root / "gpt-project.yaml").read_text(encoding="utf-8"))
    custom = cfg["runtime"]["custom_gpt"]
    max_chars = int(custom["instruction"]["max_characters"])
    max_knowledge = int(custom["knowledge"]["max_files"])

    actual = {p.relative_to(build).as_posix() for p in build.rglob("*") if p.is_file()}
    for rel in sorted(REQUIRED_FILES - actual):
        errors.append(f"Missing required Custom GPT file: {rel}")

    for rel in sorted(actual):
        top = rel.split("/", 1)[0]
        if top in FORBIDDEN_TOP_LEVEL:
            errors.append(f"Development-only path leaked into Custom GPT runtime: {rel}")
        if rel.endswith((".py", ".pyc", ".pyo")):
            errors.append(f"Executable/development Python file leaked into Custom GPT runtime: {rel}")

    instr_path = build / "builder" / "instructions.md"
    if instr_path.exists():
        text = instr_path.read_text(encoding="utf-8")
        if len(text) > max_chars:
            errors.append(f"Compiled instruction exceeds configured limit: {len(text)} > {max_chars}")
        for marker in CORE_MARKERS:
            if marker not in text:
                errors.append(f"Canonical core marker missing from Custom GPT instruction: {marker}")

    cap_path = build / "builder" / "capabilities.md"
    if cap_path.exists():
        cap = cap_path.read_text(encoding="utf-8")
        for required in ["Web Search", "Code Interpreter & Data Analysis", "AKTIVERA"]:
            if required not in cap:
                errors.append(f"Required capability guidance missing: {required}")

    kp = build / "builder" / "knowledge-package"
    knowledge_files = [p for p in kp.rglob("*") if p.is_file()] if kp.exists() else []
    if len(knowledge_files) > max_knowledge:
        errors.append(f"Knowledge file count exceeds configured limit: {len(knowledge_files)} > {max_knowledge}")

    report_path = build / "builder" / "compilation-report.json"
    if report_path.exists():
        report = json.loads(report_path.read_text(encoding="utf-8"))
        instruction = report.get("instruction", {})
        if instruction.get("compiled_characters") != len(instr_path.read_text(encoding="utf-8")):
            errors.append("Compilation report character count does not match instructions.md")
        if instruction.get("core_markers_verified") != len(CORE_MARKERS):
            errors.append("Compilation report does not confirm all core markers")
        knowledge = report.get("knowledge", {})
        if knowledge.get("selected_files") != len(knowledge_files):
            errors.append("Compilation report knowledge count does not match package")

    compat_path = build / "COMPATIBILITY.md"
    if compat_path.exists():
        compat = compat_path.read_text(encoding="utf-8")
        for marker in ["Web Search", "Code Interpreter & Data Analysis", "övergångsdistribution", "2026-09-16"]:
            if marker not in compat:
                errors.append(f"Compatibility document missing required marker: {marker}")

    manifest_path = build / "MANIFEST.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        entries = {i["path"]: i for i in manifest.get("files", [])}
        expected = actual - {"MANIFEST.json"}
        if set(entries) != expected:
            for rel in sorted(expected - set(entries)):
                errors.append(f"File missing from Custom GPT manifest: {rel}")
            for rel in sorted(set(entries) - expected):
                errors.append(f"Manifest references absent Custom GPT file: {rel}")
        for rel, item in entries.items():
            p = build / rel
            if p.exists():
                data = p.read_bytes()
                if item.get("sha256") != sha(data):
                    errors.append(f"Checksum mismatch in Custom GPT manifest: {rel}")
                if item.get("size") != len(data):
                    errors.append(f"Size mismatch in Custom GPT manifest: {rel}")

    return errors


def validate_zip(zip_path: Path, build: Path) -> list[str]:
    errors: list[str] = []
    if not zip_path.exists():
        return [f"Custom GPT ZIP missing: {zip_path}"]
    with zipfile.ZipFile(zip_path) as zf:
        zfiles = {n for n in zf.namelist() if not n.endswith("/")}
        bfiles = {p.relative_to(build).as_posix() for p in build.rglob("*") if p.is_file()}
        if zfiles != bfiles:
            for rel in sorted(bfiles - zfiles):
                errors.append(f"Custom GPT ZIP missing build file: {rel}")
            for rel in sorted(zfiles - bfiles):
                errors.append(f"Custom GPT ZIP contains unexpected file: {rel}")
        for rel in sorted(zfiles & bfiles):
            if zf.read(rel) != (build / rel).read_bytes():
                errors.append(f"Custom GPT ZIP content differs from build output: {rel}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--zip", default=None)
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    build = root / "build" / "custom-gpt"
    errors = validate_build(root, build)
    if args.zip:
        errors.extend(validate_zip(Path(args.zip).resolve(), build))
    if errors:
        print("CUSTOM GPT RUNTIME VALIDATION: FAIL")
        for e in errors:
            print(f"- {e}")
        return 1
    print("CUSTOM GPT RUNTIME VALIDATION: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
