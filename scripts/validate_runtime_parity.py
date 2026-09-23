#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml


EXPECTED_RUNTIMES = {
    "chatgpt_chat",
    "chatgpt_custom",
    "claude_project",
    "opencode",
    "openai_plugin",
}
EXPECTED_CATEGORIES = {
    "behavior",
    "capability",
    "artifact",
    "workspace_state",
    "tool",
}


def validate(root: Path) -> dict:
    cfg = yaml.safe_load((root / "gpt-project.yaml").read_text(encoding="utf-8"))
    errors: list[str] = []

    parity = cfg.get("runtime_parity", {})
    registered = set(parity.get("registered_runtimes", []))
    categories = set(parity.get("compared_categories", []))
    if registered != EXPECTED_RUNTIMES:
        errors.append(f"registered runtimes differ: {sorted(registered)}")
    if categories != EXPECTED_CATEGORIES:
        errors.append(f"parity categories differ: {sorted(categories)}")

    candidates = {
        item.get("runtime_id"): item
        for item in cfg.get("analysis", {}).get("runtime", {}).get("candidates", [])
        if isinstance(item, dict) and item.get("runtime_id")
    }
    if set(candidates) != EXPECTED_RUNTIMES:
        errors.append("all five runtimes must have explicit suitability assessment")

    for runtime_id in EXPECTED_RUNTIMES:
        item = candidates.get(runtime_id, {})
        if not item.get("reason"):
            errors.append(f"{runtime_id} missing assessment reason")
        if item.get("suitability") not in {"ready", "reduced", "not_viable"}:
            errors.append(f"{runtime_id} invalid suitability")

    for runtime_id in ("chatgpt_chat", "chatgpt_custom"):
        if candidates.get(runtime_id, {}).get("activate_by_default") is not True:
            errors.append(f"{runtime_id} must be active by default")
    for runtime_id in ("claude_project", "opencode", "openai_plugin"):
        item = candidates.get(runtime_id, {})
        if item.get("activate_by_default") is not False:
            errors.append(f"{runtime_id} must remain inactive")
        if item.get("suitability") != "reduced":
            errors.append(f"{runtime_id} must be assessed as reduced")

    if cfg.get("runtime", {}).get("chat_zip", {}).get("enabled") is not True:
        errors.append("Chat ZIP must be enabled")
    if cfg.get("runtime", {}).get("custom_gpt", {}).get("enabled") is not True:
        errors.append("Custom GPT must be enabled")

    chat_build = root / "build" / "chat"
    custom_build = root / "build" / "custom-gpt"
    canonical = (root / cfg["instructions"]["canonical"]).read_text(encoding="utf-8")
    core_markers = list(cfg.get("instructions", {}).get("core_contract", {}).get("required_markers", []))

    chat_instr = chat_build / "assistant" / "instructions.md"
    custom_instr = custom_build / "builder" / "instructions.md"
    if not chat_instr.is_file():
        errors.append("Chat built instruction missing")
    elif chat_instr.read_text(encoding="utf-8") != canonical:
        errors.append("Chat instruction is not byte-identical with canonical")

    if not custom_instr.is_file():
        errors.append("Custom GPT built instruction missing")
    else:
        custom_text = custom_instr.read_text(encoding="utf-8")
        limit = int(cfg["runtime"]["custom_gpt"]["instruction"]["max_characters"])
        if len(custom_text) > limit:
            errors.append(f"Custom GPT instruction too long: {len(custom_text)} > {limit}")
        missing = [marker for marker in core_markers if marker not in custom_text]
        if missing:
            errors.append(f"Custom GPT missing core markers: {missing}")

    contracts = [
        (chat_build / "assistant" / "runtime-contract.json", "chatgpt_chat"),
        (custom_build / "builder" / "runtime-contract.json", "chatgpt_custom"),
    ]
    for path, runtime_id in contracts:
        if not path.is_file():
            errors.append(f"missing runtime contract: {path.relative_to(root)}")
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("runtime_id") != runtime_id:
            errors.append(f"wrong runtime_id in {path.relative_to(root)}")
        for key in ("capabilities", "artifacts", "workspace_state", "tools"):
            if payload.get(key) != cfg.get(key):
                errors.append(f"{runtime_id} {key} contract drift")
        adapter = payload.get("adapter", {})
        if adapter.get("web_research_required") is not True:
            errors.append(f"{runtime_id} must require web research")
        if adapter.get("file_delivery_required") is not True:
            errors.append(f"{runtime_id} must require file delivery")

    chat_state = chat_build / "research-state.yaml"
    custom_state = custom_build / "builder" / "research-state.yaml"
    source_state = root / cfg["workspace_state"]["state"]["path"]
    for path in (chat_state, custom_state):
        if not path.is_file():
            errors.append(f"missing research state template: {path.relative_to(root)}")
        elif path.read_bytes() != source_state.read_bytes():
            errors.append(f"research state template drift: {path.relative_to(root)}")

    return {
        "result": "PASS" if not errors else "FAIL",
        "registered_runtimes": sorted(registered),
        "compared_categories": sorted(categories),
        "active_runtimes": ["chatgpt_chat", "chatgpt_custom"],
        "assessed_inactive_runtimes": ["claude_project", "opencode", "openai_plugin"],
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    args = parser.parse_args()
    report = validate(Path(args.project_root).resolve())
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
