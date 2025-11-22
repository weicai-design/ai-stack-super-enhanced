#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dependency consistency checker for AI-STACK.

Usage:
    python scripts/tools/check_dependency_conflicts.py \
        --requirements requirements-locked.txt \
        --pip-check \
        --json
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from importlib import metadata
from pathlib import Path
from typing import Dict, List


@dataclass
class RequirementEntry:
    raw_name: str
    normalized_name: str
    version: str


def parse_requirements(path: Path) -> Dict[str, RequirementEntry]:
    if not path.exists():
        raise FileNotFoundError(f"requirements file not found: {path}")

    entries: Dict[str, RequirementEntry] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "==" not in line:
            raise ValueError(f"Only pinned requirements allowed (line: {line})")
        raw_name, version = line.split("==", 1)
        normalized = raw_name.split("[", 1)[0].strip().lower()
        entries[normalized] = RequirementEntry(
            raw_name=raw_name.strip(),
            normalized_name=normalized,
            version=version.strip(),
        )
    return entries


def check_installed(requirements: Dict[str, RequirementEntry]) -> Dict[str, List[str]]:
    missing: List[str] = []
    mismatched: List[str] = []

    for key, entry in requirements.items():
        try:
            installed_version = metadata.version(entry.normalized_name)
        except metadata.PackageNotFoundError:
            missing.append(entry.raw_name)
            continue

        if installed_version != entry.version:
            mismatched.append(f"{entry.raw_name} (installed {installed_version})")

    return {"missing": missing, "mismatched": mismatched}


def run_pip_check() -> str:
    """Execute `pip check` and return output (even if non-zero)."""
    try:
        out = subprocess.check_output(
            [sys.executable, "-m", "pip", "check"],
            stderr=subprocess.STDOUT,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        return exc.output.strip()
    return out.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate dependency consistency.")
    parser.add_argument(
        "--requirements",
        default="requirements-locked.txt",
        help="Pinned requirements file path.",
    )
    parser.add_argument("--json", action="store_true", help="Print JSON summary.")
    parser.add_argument("--pip-check", action="store_true", help="Run `pip check`.")
    args = parser.parse_args()

    req_path = Path(args.requirements)
    requirements = parse_requirements(req_path)
    result = check_installed(requirements)

    pip_check_output = ""
    if args.pip_check:
        pip_check_output = run_pip_check()

    success = (
        not result["missing"]
        and not result["mismatched"]
        and (not args.pip_check or pip_check_output == "No broken requirements found.")
    )

    payload = {
        "requirements_file": str(req_path),
        "missing": result["missing"],
        "mismatched": result["mismatched"],
        "pip_check": pip_check_output,
        "success": success,
    }

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"[check-deps] requirements: {req_path}")
        if result["missing"]:
            print("  ✗ Missing:", ", ".join(result["missing"]))
        if result["mismatched"]:
            print("  ✗ Version mismatch:", ", ".join(result["mismatched"]))
        if args.pip_check:
            print("  pip check:")
            print(pip_check_output or "(no output)")
        if success:
            print("  ✓ Dependencies look consistent.")

    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())

