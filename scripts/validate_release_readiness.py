#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import zipfile
from pathlib import Path

import yaml


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def validate(root: Path) -> dict:
    errors: list[str] = []
    cfg = yaml.safe_load((root / "gpt-project.yaml").read_text(encoding="utf-8"))
    status = yaml.safe_load((root / "project-status.yaml").read_text(encoding="utf-8"))

    proc = subprocess.run(
        [sys.executable, str(root / "scripts" / "validate_runtime_parity.py"), "--project-root", str(root)],
        cwd=root,
        text=True,
        capture_output=True,
    )
    if proc.returncode != 0:
        errors.append("runtime parity gate failed")

    progress = status.get("progress", {})
    if progress.get("current_step") not in {11, 12}:
        errors.append("migration status must be on step 11 or 12")
    if int(progress.get("last_completed_step", 0)) < 10:
        errors.append("step 10 must be completed")
    if status.get("state", {}).get("blocking_issues"):
        errors.append("blocking issues must be empty")

    dist = root / "dist"
    version = None
    manifests = list(dist.glob("DELIVERY-MANIFEST.json"))
    if not manifests:
        errors.append("DELIVERY-MANIFEST.json missing")
    else:
        delivery = json.loads(manifests[0].read_text(encoding="utf-8"))
        version = delivery.get("version")
        artifact_types = {item.get("type") for item in delivery.get("artifacts", [])}
        for required in {"project_zip", "chat_zip", "custom_gpt_zip", "checksums"}:
            if required not in artifact_types:
                errors.append(f"delivery manifest missing artifact type: {required}")

    sums_path = dist / "SHA256SUMS.txt"
    if not sums_path.is_file():
        errors.append("SHA256SUMS.txt missing")
    else:
        sums: dict[str, str] = {}
        for line in sums_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            digest, name = line.split(None, 1)
            sums[name.strip()] = digest
        for zip_path in sorted(dist.glob("*.zip")):
            if sums.get(zip_path.name) != sha256(zip_path):
                errors.append(f"checksum mismatch or missing: {zip_path.name}")
            try:
                with zipfile.ZipFile(zip_path) as zf:
                    bad = zf.testzip()
                    if bad:
                        errors.append(f"ZIP CRC error in {zip_path.name}: {bad}")
            except zipfile.BadZipFile:
                errors.append(f"invalid ZIP: {zip_path.name}")

    candidates = {
        item.get("runtime_id"): item
        for item in cfg.get("analysis", {}).get("runtime", {}).get("candidates", [])
        if isinstance(item, dict) and item.get("runtime_id")
    }
    for runtime_id in ("claude_project", "opencode", "openai_plugin"):
        if candidates.get(runtime_id, {}).get("activate_by_default") is not False:
            errors.append(f"{runtime_id} unexpectedly active in release readiness")

    return {
        "result": "PASS" if not errors else "FAIL",
        "version": version,
        "runtime_parity_exit_code": proc.returncode,
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
