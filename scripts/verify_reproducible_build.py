#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot() -> dict[str, str]:
    dist = ROOT / "dist"
    return {
        p.name: sha256(p)
        for p in sorted(dist.iterdir())
        if p.is_file()
    }


def main() -> int:
    manifest = ROOT / "dist" / "DELIVERY-MANIFEST.json"
    if not manifest.is_file():
        print("REPRODUCIBILITY: FAIL")
        print("- DELIVERY-MANIFEST.json missing before reproducibility check")
        return 1

    version = json.loads(manifest.read_text(encoding="utf-8")).get("version")
    if not version:
        print("REPRODUCIBILITY: FAIL")
        print("- delivery manifest has no version")
        return 1

    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "build_distributions.py"),
        "--project-root", str(ROOT),
        "--version", str(version),
        "--targets", "project,chat,custom-gpt,plugin",
    ]
    subprocess.run(cmd, cwd=ROOT, check=True)
    first = snapshot()
    subprocess.run(cmd, cwd=ROOT, check=True)
    second = snapshot()

    if first != second:
        print("REPRODUCIBILITY: FAIL")
        for name in sorted(set(first) | set(second)):
            if first.get(name) != second.get(name):
                print(f"- {name}: {first.get(name)} != {second.get(name)}")
        return 1

    print("REPRODUCIBILITY: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
