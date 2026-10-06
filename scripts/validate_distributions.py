#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import zipfile
from pathlib import Path

try:
    import yaml
except Exception as exc:
    raise SystemExit("PyYAML is required") from exc


FORBIDDEN_PARTS = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    "research",
    "evals",
    "tests",
}


def load_cfg(root: Path) -> dict:
    return yaml.safe_load((root / "gpt-project.yaml").read_text(encoding="utf-8"))


def validate_custom(root: Path, cfg: dict) -> list[str]:
    errors = []
    build = root / "build" / "custom-gpt"
    if not build.exists():
        return ["Custom GPT build directory missing"]

    instr = build / "builder" / "instructions.md"
    if not instr.exists():
        errors.append("Missing builder/instructions.md")
    else:
        actual = len(instr.read_text(encoding="utf-8"))
        limit = int(cfg["runtime"]["custom_gpt"]["instruction"]["max_characters"])
        if actual > limit:
            errors.append(f"Instruction too long: {actual} > {limit}")

    kp = build / "builder" / "knowledge-package"
    files = [p for p in kp.rglob("*") if p.is_file()] if kp.exists() else []
    limit = int(cfg["runtime"]["custom_gpt"]["knowledge"]["max_files"])
    if len(files) > limit:
        errors.append(f"Too many Knowledge files: {len(files)} > {limit}")

    required = [
        build / "builder" / "instructions.md",
        build / "builder" / "conversation-starters.md",
        build / "builder" / "capabilities.md",
        build / "builder" / "runtime-contract.json",
        build / "builder" / "research-state.yaml",
        build / "README.md",
        build / "COMPATIBILITY.md",
        build / "VERSION",
        build / "MANIFEST.json",
    ]
    for p in required:
        if not p.exists():
            errors.append(f"Missing required file: {p.relative_to(build)}")
    return errors


def validate_chat(root: Path, cfg: dict) -> list[str]:
    errors = []
    build = root / "build" / "chat"
    if not build.exists():
        return ["Chat build directory missing"]

    required = [
        build / "START-HERE.md",
        build / "VERSION",
        build / "MANIFEST.json",
        build / "assistant" / "instructions.md",
        build / "assistant" / "runtime-contract.json",
        build / "research-state.yaml",
    ]
    for p in required:
        if not p.exists():
            errors.append(f"Missing required file: {p.relative_to(build)}")

    for p in build.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(build)
        if any(part in FORBIDDEN_PARTS for part in rel.parts):
            errors.append(f"Forbidden runtime path: {rel}")
    return errors


def validate_plugin(root: Path, cfg: dict) -> list[str]:
    errors = []
    build = root / "build" / "plugin"
    if not build.exists():
        return ["OpenAI Plugin build directory missing"]

    required = [
        build / "plugin.json",
        build / "runtime-contract.json",
        build / "README.md",
        build / "VERSION",
        build / "MANIFEST.json",
        build / "skills" / "marknadskartlaggaren" / "SKILL.md",
        build / "skills" / "marknadskartlaggaren" / "assets" / "research-state.yaml",
        build / "skills" / "marknadskartlaggaren" / "assets" / "market-map-report.md",
    ]
    for p in required:
        if not p.exists():
            errors.append(f"Missing required Plugin file: {p.relative_to(build)}")

    for p in build.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(build)
        if any(part in FORBIDDEN_PARTS or part in {".github", "docs", "scripts", "evals", "tests"} for part in rel.parts):
            errors.append(f"Forbidden plugin path: {rel}")

    contract = build / "runtime-contract.json"
    if contract.exists():
        payload = json.loads(contract.read_text(encoding="utf-8"))
        if payload.get("runtime_id") != "openai_plugin":
            errors.append("Plugin runtime contract has wrong runtime_id")
        adapter = payload.get("adapter", {})
        expected = {
            "mode": "skills_first",
            "compatibility": "ready_runtime_dependent",
            "web_research": "required_host_runtime",
            "filesystem_read": "required_host_runtime",
            "filesystem_write": "required_host_runtime",
            "code_execution": "required_host_runtime",
            "persistent_state": "required_host_runtime",
            "state_authority": "workspace_file_when_present",
            "conversation_fallback": True,
            "mcp_generated": False,
        }
        for key, value in expected.items():
            if adapter.get(key) != value:
                errors.append(f"Plugin adapter mismatch: {key}")
        if adapter.get("script_resources") != []:
            errors.append("Plugin must not package runtime scripts")
        fallback = adapter.get("fallback_policy", {})
        for key in ("without_web", "without_persistent_state", "without_file_write_or_code_execution"):
            if key not in fallback:
                errors.append(f"Plugin fallback missing: {key}")

    skill = build / "skills" / "marknadskartlaggaren" / "SKILL.md"
    if skill.exists():
        text = skill.read_text(encoding="utf-8")
        canonical = (root / cfg["instructions"]["canonical"]).read_text(encoding="utf-8").strip()
        if canonical not in text:
            errors.append("Plugin SKILL does not contain canonical behavior")
        for marker in [
            "Utan webbförmåga ska researchuppdraget blockeras",
            "är den auktoritativ framför chattminne",
            "Påstå inte robust cross-session resume",
            "får arbetet inte markeras färdigt",
            "genererar ingen MCP-wrapper",
        ]:
            if marker not in text:
                errors.append(f"Plugin SKILL missing runtime marker: {marker}")

    policy_root = root / cfg["structure"]["runtime_policy"]["path"]
    refs = build / "skills" / "marknadskartlaggaren" / "references" / "policies"
    for p in sorted(policy_root.rglob("*.md")):
        target = refs / p.relative_to(policy_root)
        if not target.exists() or target.read_bytes() != p.read_bytes():
            errors.append(f"Plugin policy drift: {p.relative_to(policy_root)}")

    assets = build / "skills" / "marknadskartlaggaren" / "assets"
    state_src = root / cfg["workspace_state"]["state"]["path"]
    if (assets / "research-state.yaml").exists() and (assets / "research-state.yaml").read_bytes() != state_src.read_bytes():
        errors.append("Plugin research-state template drift")
    report_src = root / cfg["structure"]["templates"]["path"] / "market-map-report.md"
    if (assets / "market-map-report.md").exists() and (assets / "market-map-report.md").read_bytes() != report_src.read_bytes():
        errors.append("Plugin report template drift")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    cfg = load_cfg(root)

    errors = []
    errors.extend(validate_chat(root, cfg))
    if cfg["runtime"]["custom_gpt"]["enabled"]:
        errors.extend(validate_custom(root, cfg))
    if cfg.get("runtime", {}).get("openai_plugin", {}).get("enabled"):
        errors.extend(validate_plugin(root, cfg))

    if errors:
        print("VALIDATION: FAIL")
        for e in errors:
            print(f"- {e}")
        return 1

    print("VALIDATION: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
