#!/usr/bin/env python3
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import shutil
import sys
import zipfile
from pathlib import Path

try:
    import yaml
except Exception as exc:
    raise SystemExit("PyYAML is required to run build_distributions.py") from exc


FIXED_ZIP_DATE = (2020, 1, 1, 0, 0, 0)


def load_config(root: Path) -> dict:
    path = root / "gpt-project.yaml"
    if not path.exists():
        raise SystemExit(f"Missing config: {path}")
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def stable_write_zip(zip_path: Path, root: Path, files: list[Path]) -> None:
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(files, key=lambda p: p.as_posix()):
            rel = path.relative_to(root).as_posix()
            info = zipfile.ZipInfo(rel, FIXED_ZIP_DATE)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            zf.writestr(info, path.read_bytes())


def copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def copy_tree_filtered(src: Path, dst: Path, ignore_names: set[str] | None = None) -> None:
    # Runtime distributions must never contain local Python/cache artifacts.
    ignore_names = set(ignore_names or set()) | {
        "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"
    }
    if not src.exists():
        return
    for p in src.rglob("*"):
        if p.is_dir():
            continue
        rel = p.relative_to(src)
        if any(part in ignore_names for part in rel.parts):
            continue
        if p.suffix in {".pyc", ".pyo"}:
            continue
        copy_file(p, dst / rel)


def render_template(text: str, replacements: dict[str, str]) -> str:
    for k, v in replacements.items():
        text = text.replace("{{" + k + "}}", v)
    return text


def ensure_clean_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)


def build_manifest(root: Path, runtime_id: str, version: str, entrypoint: str | None = None) -> dict:
    files = []
    for p in sorted(root.rglob("*")):
        if p.is_file() and p.name != "MANIFEST.json":
            files.append({
                "path": p.relative_to(root).as_posix(),
                "sha256": sha256(p),
                "size": p.stat().st_size,
            })
    result = {
        "runtime_id": runtime_id,
        "version": version,
        "files": files,
    }
    if entrypoint:
        result["entrypoint"] = entrypoint
    return result


def write_manifest(root: Path, runtime_id: str, version: str, entrypoint: str | None = None) -> None:
    manifest = build_manifest(root, runtime_id, version, entrypoint)
    (root / "MANIFEST.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def runtime_contract(cfg: dict, runtime_id: str, adapter: dict) -> dict:
    return {
        "schema_version": 1,
        "runtime_id": runtime_id,
        "capabilities": cfg.get("capabilities", {}),
        "artifacts": cfg.get("artifacts", {}),
        "workspace_state": cfg.get("workspace_state", {}),
        "tools": cfg.get("tools", {}),
        "adapter": adapter,
    }


def write_runtime_contract(path: Path, cfg: dict, runtime_id: str, adapter: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(runtime_contract(cfg, runtime_id, adapter), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def build_chat(root: Path, cfg: dict, build_root: Path, version: str) -> Path:
    out = build_root / "chat"
    ensure_clean_dir(out)

    assistant = out / "assistant"
    policies = assistant / "policies"
    policies.mkdir(parents=True)

    instr_src = root / cfg["instructions"]["canonical"]
    copy_file(instr_src, assistant / "instructions.md")

    state_src = root / cfg["workspace_state"]["state"]["path"]
    copy_file(state_src, out / "research-state.yaml")
    write_runtime_contract(
        assistant / "runtime-contract.json",
        cfg,
        "chatgpt_chat",
        {
            "mode": "chat_zip",
            "instructions": "assistant/instructions.md",
            "state_template": "research-state.yaml",
            "web_research_required": True,
            "file_delivery_required": True,
        },
    )

    starters_root = root / cfg["structure"]["conversation_starters"]["path"]
    if starters_root.exists():
        starters = [p for p in starters_root.rglob("*") if p.is_file() and p.name != "README.md"]
        if starters:
            combined = "\n\n".join(p.read_text(encoding="utf-8") for p in sorted(starters))
            (assistant / "conversation-starters.md").write_text(combined, encoding="utf-8")

    policy_root = root / cfg["structure"]["runtime_policy"]["path"]
    if policy_root.exists():
        for p in sorted(policy_root.rglob("*.md")):
            copy_file(p, policies / p.name)

    knowledge_root = root / cfg["knowledge_architecture"]["canonical_root"]
    if knowledge_root.exists():
        for p in sorted(knowledge_root.rglob("*")):
            if p.is_file() and p.name != "KNOWLEDGE.md":
                copy_file(p, out / "knowledge" / p.relative_to(knowledge_root))

    # Runtime-relevant schemas/scripts/templates are included for now.
    # Later steps may refine this with explicit per-file role metadata.
    for key in ["schemas", "scripts", "templates"]:
        path = root / cfg["structure"][key]["path"]
        if path.exists():
            copy_tree_filtered(path, out / key, ignore_names={"README.md"})

    template_path = root / cfg["runtime"]["chat_zip"]["start_here_template"]
    template = template_path.read_text(encoding="utf-8")
    start_here = render_template(template, {
        "GPT_NAME": cfg["project"]["name"],
        "VERSION": version,
    })
    (out / "START-HERE.md").write_text(start_here, encoding="utf-8")
    (out / "VERSION").write_text(version + "\n", encoding="utf-8")
    write_manifest(out, cfg["project"]["id"] + "-chat", version, "START-HERE.md")
    return out


def _knowledge_priority_patterns(cfg: dict) -> list[str]:
    return list(cfg.get("knowledge_architecture", {}).get("custom_gpt", {}).get("priority", []) or [])


def _rank_knowledge(files: list[Path], root: Path, cfg: dict) -> list[Path]:
    patterns = _knowledge_priority_patterns(cfg)
    ranked = []
    for p in files:
        rel_from_project = p.relative_to(root).as_posix()
        rank = len(patterns) + 1
        for idx, pattern in enumerate(patterns):
            if fnmatch.fnmatch(rel_from_project, pattern):
                rank = idx
                break
        ranked.append((rank, rel_from_project, p))
    return [p for _, _, p in sorted(ranked)]


def collect_custom_knowledge(root: Path, cfg: dict, target: Path) -> list[Path]:
    knowledge_root = root / cfg["knowledge_architecture"]["canonical_root"]
    files = [p for p in sorted(knowledge_root.rglob("*")) if p.is_file() and p.name != "KNOWLEDGE.md"] if knowledge_root.exists() else []
    max_files = int(cfg["runtime"]["custom_gpt"]["knowledge"]["max_files"])
    strategy = cfg["runtime"]["custom_gpt"]["knowledge"]["strategy"]

    if len(files) <= max_files:
        selected = files
    elif strategy in {"prioritize", "hybrid"}:
        selected = _rank_knowledge(files, root, cfg)[:max_files]
    else:
        raise SystemExit(
            f"Custom GPT Knowledge has {len(files)} files but max is {max_files}; "
            f"strategy {strategy!r} requires explicit consolidation support for overflow."
        )

    copied = []
    for p in selected:
        dst = target / p.relative_to(knowledge_root)
        copy_file(p, dst)
        copied.append(dst)
    return copied


def compile_custom_instruction(text: str, mode: str, max_chars: int, core_markers: list[str]) -> str:
    if mode == "identical":
        compiled = text
    elif mode in {"compressed", "compiled"}:
        # Conservative deterministic compression: preserve wording and headings,
        # remove trailing whitespace and collapse repeated blank lines.
        lines = [line.rstrip() for line in text.splitlines()]
        out = []
        blank = False
        for line in lines:
            if not line.strip():
                if blank:
                    continue
                blank = True
                out.append("")
            else:
                blank = False
                out.append(line)
        compiled = "\n".join(out).strip() + "\n"
    else:
        raise SystemExit(f"Unknown Custom GPT instruction mode: {mode!r}")

    missing = [marker for marker in core_markers if marker not in compiled]
    if missing:
        raise SystemExit(f"Custom GPT instruction compilation removed core behavior markers: {missing}")
    if len(compiled) > max_chars:
        raise SystemExit(
            f"Custom GPT instruction is {len(compiled)} characters after {mode!r} compilation; max is {max_chars}. "
            "Reduce or explicitly mark distribution-specific source material; do not move core behavior to Knowledge."
        )
    return compiled


def build_custom(root: Path, cfg: dict, build_root: Path, version: str) -> Path:
    out = build_root / "custom-gpt"
    ensure_clean_dir(out)
    builder = out / "builder"
    kp = builder / "knowledge-package"
    kp.mkdir(parents=True)

    instr = (root / cfg["instructions"]["canonical"]).read_text(encoding="utf-8")
    max_chars = int(cfg["runtime"]["custom_gpt"]["instruction"]["max_characters"])
    mode = cfg["runtime"]["custom_gpt"]["instruction"]["mode"]
    core_markers = list(cfg.get("instructions", {}).get("core_contract", {}).get("required_markers", []) or [])
    compiled_instr = compile_custom_instruction(instr, mode, max_chars, core_markers)
    (builder / "instructions.md").write_text(compiled_instr, encoding="utf-8")

    state_src = root / cfg["workspace_state"]["state"]["path"]
    copy_file(state_src, builder / "research-state.yaml")
    write_runtime_contract(
        builder / "runtime-contract.json",
        cfg,
        "chatgpt_custom",
        {
            "mode": "custom_gpt",
            "instructions": "builder/instructions.md",
            "state_template": "builder/research-state.yaml",
            "web_research_required": True,
            "file_delivery_required": True,
            "state_persistence": "conversation_or_file",
        },
    )

    starters_root = root / cfg["structure"]["conversation_starters"]["path"]
    starters = [p for p in starters_root.rglob("*") if p.is_file() and p.name != "README.md"] if starters_root.exists() else []
    combined = "\n\n".join(p.read_text(encoding="utf-8") for p in sorted(starters))
    (builder / "conversation-starters.md").write_text(combined, encoding="utf-8")

    cap_tpl = (root / cfg["runtime"]["custom_gpt"]["templates"]["capabilities"]).read_text(encoding="utf-8")
    capabilities = cfg["runtime"]["custom_gpt"].get("capabilities", {})
    cap_labels = [
        ("web_search", "Web Search"),
        ("code_interpreter_data_analysis", "Code Interpreter & Data Analysis"),
        ("image_generation", "Image generation"),
        ("canvas", "Canvas"),
        ("apps", "Apps"),
        ("actions", "Actions"),
    ]
    state_labels = {
        "required": "AKTIVERA – krävs för kärnflödet",
        "disabled": "AV – behövs inte",
        "not_required": "inte krav",
    }
    capability_lines = []
    for key, label in cap_labels:
        state = capabilities.get(key, "not_required")
        capability_lines.append(f"- {label}: **{state_labels.get(state, state)}**")
    cap_text = render_template(cap_tpl, {
        "CAPABILITY_RECOMMENDATIONS": "\n".join(capability_lines)
    })
    (builder / "capabilities.md").write_text(cap_text, encoding="utf-8")

    copied_knowledge = collect_custom_knowledge(root, cfg, kp)

    knowledge_root = root / cfg["knowledge_architecture"]["canonical_root"]
    canonical_knowledge = [p for p in sorted(knowledge_root.rglob("*")) if p.is_file() and p.name != "KNOWLEDGE.md"] if knowledge_root.exists() else []
    selected_rel = [p.relative_to(kp).as_posix() for p in copied_knowledge]
    selected_set = set(selected_rel)
    excluded_rel = [p.relative_to(knowledge_root).as_posix() for p in canonical_knowledge if p.relative_to(knowledge_root).as_posix() not in selected_set]
    compilation_report = {
        "instruction": {
            "mode": mode,
            "canonical_characters": len(instr),
            "compiled_characters": len(compiled_instr),
            "max_characters": max_chars,
            "core_markers_verified": len(core_markers),
        },
        "knowledge": {
            "strategy": cfg["runtime"]["custom_gpt"]["knowledge"]["strategy"],
            "canonical_files": len(canonical_knowledge),
            "selected_files": len(copied_knowledge),
            "max_files": int(cfg["runtime"]["custom_gpt"]["knowledge"]["max_files"]),
            "priority_patterns": _knowledge_priority_patterns(cfg),
            "selected": selected_rel,
            "excluded": excluded_rel,
        },
    }
    (builder / "compilation-report.json").write_text(json.dumps(compilation_report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    readme_tpl = (root / cfg["runtime"]["custom_gpt"]["templates"]["readme"]).read_text(encoding="utf-8")
    (out / "README.md").write_text(
        render_template(readme_tpl, {"GPT_NAME": cfg["project"]["name"], "VERSION": version}),
        encoding="utf-8",
    )

    compat_tpl = (root / cfg["runtime"]["custom_gpt"]["templates"]["compatibility"]).read_text(encoding="utf-8")
    platform = cfg["runtime"]["custom_gpt"].get("platform_status", {})
    sources = platform.get("sources", [])
    source_lines = "\n".join(f"- {url}" for url in sources) if sources else "- Ingen extern plattformskälla registrerad."
    platform_status = (
        f"Verifierat: **{platform.get('verified_date', 'ej angivet')}**. "
        f"{platform.get('note', '')}\n\nKällor för plattformsläget:\n{source_lines}"
    )
    parity_table = (
        "| Förmåga | Chat ZIP | Custom GPT |\n"
        "|---|---|---|\n"
        "| Canonical instruktion | Full | Full, kompilerad inom instruktionsgränsen |\n"
        "| Aktuell webbresearch | Kräver att värdchatten har webbsökning | Web Search måste aktiveras |\n"
        "| Nedladdningsbar Markdown | Kräver filskapande i värdchatten | Code Interpreter & Data Analysis måste aktiveras |\n"
        "| Knowledge | Ej krav för kärnbeteende | Ej krav; paketet kan vara tomt |\n"
        "| Flerstegsflöde | Stöds av canonical kontrakt | Stöds av canonical kontrakt |"
    )
    compat = render_template(compat_tpl, {
        "GPT_NAME": cfg["project"]["name"],
        "RUNTIME_RECOMMENDATION": "Chat ZIP och Custom GPT har samma kärnkontrakt. Custom GPT bör ses som en övergångsdistribution på grund av aktuellt plattformsläge.",
        "PARITY_TABLE": parity_table,
        "REDUCED_FEATURES": "Ingen avsiktlig reducering i research-, analys- eller rapportkontraktet. Custom GPT är däremot beroende av att Web Search och Code Interpreter & Data Analysis är tillgängliga och aktiverade.",
        "MISSING_FEATURES": "Inga kända kärnfunktioner saknas när de två obligatoriska capabilities är tillgängliga. Apps, Actions, Canvas och Image generation krävs inte.",
        "PLATFORM_STATUS": platform_status,
    })
    (out / "COMPATIBILITY.md").write_text(compat, encoding="utf-8")
    (out / "VERSION").write_text(version + "\n", encoding="utf-8")

    write_manifest(out, cfg["project"]["id"] + "-custom-gpt", version)
    return out


def build_plugin(root: Path, cfg: dict, build_root: Path, version: str) -> Path:
    out = build_root / "plugin"
    ensure_clean_dir(out)
    skill = out / "skills" / "marknadskartlaggaren"
    refs = skill / "references" / "policies"
    assets = skill / "assets"
    refs.mkdir(parents=True)
    assets.mkdir(parents=True)

    canonical = (root / cfg["instructions"]["canonical"]).read_text(encoding="utf-8").strip()
    policy_root = root / cfg["structure"]["runtime_policy"]["path"]
    policy_lines = []
    for p in sorted(policy_root.rglob("*.md")):
        rel = p.relative_to(policy_root)
        copy_file(p, refs / rel)
        policy_lines.append(f"- references/policies/{rel.as_posix()}")

    state_src = root / cfg["workspace_state"]["state"]["path"]
    copy_file(state_src, assets / "research-state.yaml")
    report_src = root / cfg["structure"]["templates"]["path"] / "market-map-report.md"
    copy_file(report_src, assets / "market-map-report.md")

    skill_text = (
        "---\n"
        "name: marknadskartlaggaren\n"
        "description: Aktuell, källbaserad marknadskartläggning av kommersiella och open source-produkter med resumable research och nedladdningsbar Markdown-rapport.\n"
        "metadata:\n"
        "  source: generated-from-canonical-project\n"
        "---\n\n"
        "# Marknadskartläggaren\n\n"
        "## Runtime adapter\n\n"
        "- Aktuell marknadskartläggning kräver faktisk webbresearch från hosten. Utan webbförmåga ska researchuppdraget blockeras; ersätt inte med modellminne.\n"
        "- Skapa en arbetskopia av assets/research-state.yaml i hostens skrivbara workspace för flerstegsarbete. När arbetskopian finns är den auktoritativ framför chattminne.\n"
        "- Uppdatera persistent research-state efter varje genomfört större researchsteg. Konversationsjournalen är fallback endast när persistent filstatus saknas.\n"
        "- Påstå inte robust cross-session resume om hosten inte bevarar workspace/state mellan sessioner.\n"
        "- Skrivbar filyta och code execution krävs för obligatorisk slutleverans. Utan dem får arbetet inte markeras färdigt och ingen Markdown-fil får påstås vara skapad.\n"
        "- Använd assets/market-map-report.md som strukturstöd för slutrapporten när lämpligt.\n"
        "- Pluginen innehåller inga runtime-skript eller custom tools och genererar ingen MCP-wrapper.\n\n"
        "## Canonical behavior\n\n"
        + canonical
        + "\n\n## References\n\n"
        + "\n".join(policy_lines)
        + "\n\n## Assets\n\n- assets/research-state.yaml\n- assets/market-map-report.md\n"
    )
    (skill / "SKILL.md").write_text(skill_text, encoding="utf-8")

    (out / "plugin.json").write_text(
        json.dumps({
            "$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
            "name": "marknadskartlaggaren",
            "version": version,
            "description": "Aktuell källbaserad marknadskartläggning med resumable state och Markdown-slutrapport.",
        }, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_runtime_contract(
        out / "runtime-contract.json",
        cfg,
        "openai_plugin",
        {
            "mode": "skills_first",
            "compatibility": "ready_runtime_dependent",
            "entrypoint": "skills/marknadskartlaggaren/SKILL.md",
            "web_research": "required_host_runtime",
            "filesystem_read": "required_host_runtime",
            "filesystem_write": "required_host_runtime",
            "code_execution": "required_host_runtime",
            "persistent_state": "required_host_runtime",
            "state_template": "skills/marknadskartlaggaren/assets/research-state.yaml",
            "state_authority": "workspace_file_when_present",
            "conversation_fallback": True,
            "mcp_generated": False,
            "script_resources": [],
            "fallback_policy": {
                "without_web": "block_current_market_research_do_not_use_model_memory_as_substitute",
                "without_persistent_state": "allow_session_journal_only_do_not_claim_cross_session_resume",
                "without_file_write_or_code_execution": "do_not_mark_complete_or_claim_markdown_file_created",
            },
        },
    )
    (out / "README.md").write_text(
        f"# {cfg['project']['name']} – OpenAI Plugin {version}\n\n"
        "Skills-first peer-runtime med ready_runtime_dependent parity. Webbresearch, skrivbar filyta, code execution och persistent state är hostberoenden. "
        "Policies paketeras som references; research-state och rapportmall som assets. Inga runtime-skript eller MCP-wrapper ingår.\n",
        encoding="utf-8",
    )
    (out / "VERSION").write_text(version + "\n", encoding="utf-8")
    write_manifest(out, cfg["project"]["id"] + "-plugin", version, "plugin.json")
    return out

def project_files(root: Path) -> list[Path]:
    excluded_top = {"build", "dist", ".git"}
    result = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(root)
        if rel.parts and rel.parts[0] in excluded_top:
            continue
        if "__pycache__" in rel.parts or ".pytest_cache" in rel.parts:
            continue
        result.append(p)
    return result


def write_checksums(dist: Path) -> None:
    lines = []
    for p in sorted(dist.glob("*.zip")):
        lines.append(f"{sha256(p)}  {p.name}")
    (dist / "SHA256SUMS.txt").write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def write_delivery_manifest(dist: Path, cfg: dict, version: str) -> None:
    artifacts = []
    for p in sorted(dist.iterdir()):
        if not p.is_file() or p.name in {"DELIVERY-MANIFEST.json"}:
            continue
        if p.suffix == ".zip":
            if "-project" in p.name:
                artifact_type = "project_zip"
            elif "-chat-" in p.name:
                artifact_type = "chat_zip"
            elif "-custom-gpt-" in p.name:
                artifact_type = "custom_gpt_zip"
            elif "-plugin-" in p.name:
                artifact_type = "plugin_zip"
            else:
                artifact_type = "zip"
        elif p.name == "SHA256SUMS.txt":
            artifact_type = "checksums"
        else:
            artifact_type = "file"
        artifacts.append({
            "type": artifact_type,
            "file": p.name,
            "sha256": sha256(p),
            "size": p.stat().st_size,
        })

    payload = {
        "project": cfg["project"]["id"],
        "project_name": cfg["project"]["name"],
        "version": version,
        "runtime_strategy": "peer_distributions",
        "custom_gpt_enabled": bool(cfg["runtime"]["custom_gpt"]["enabled"]),
        "artifacts": artifacts,
    }
    (dist / "DELIVERY-MANIFEST.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--version", default="0.0.0-dev")
    parser.add_argument("--targets", default="project,chat,custom-gpt,plugin")
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    cfg = load_config(root)
    build_root = root / "build"
    dist = root / "dist"
    build_root.mkdir(exist_ok=True)
    dist.mkdir(exist_ok=True)

    targets = {t.strip() for t in args.targets.split(",") if t.strip()}
    project_id = cfg["project"]["id"]
    version = args.version

    if "chat" in targets:
        chat_root = build_chat(root, cfg, build_root, version)
        chat_zip = dist / f"{project_id}-chat-{version}.zip"
        stable_write_zip(chat_zip, chat_root, [p for p in chat_root.rglob("*") if p.is_file()])

    if "custom-gpt" in targets and cfg["runtime"]["custom_gpt"]["enabled"]:
        custom_root = build_custom(root, cfg, build_root, version)
        custom_zip = dist / f"{project_id}-custom-gpt-{version}.zip"
        stable_write_zip(custom_zip, custom_root, [p for p in custom_root.rglob("*") if p.is_file()])

    if "plugin" in targets and cfg.get("runtime", {}).get("openai_plugin", {}).get("enabled"):
        plugin_root = build_plugin(root, cfg, build_root, version)
        plugin_zip = dist / f"{project_id}-plugin-{version}.zip"
        stable_write_zip(plugin_zip, plugin_root, [p for p in plugin_root.rglob("*") if p.is_file()])

    if "project" in targets:
        project_zip = dist / f"{project_id}-project.zip"
        stable_write_zip(project_zip, root, project_files(root))

    write_checksums(dist)
    write_delivery_manifest(dist, cfg, version)

    print(f"Build complete: {dist}")
    for p in sorted(dist.iterdir()):
        if p.is_file():
            print(p.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
