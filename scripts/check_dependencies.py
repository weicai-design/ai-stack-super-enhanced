#!/usr/bin/env python3
"""
统一依赖体检脚本
---------------------------------
1. 校验 requirements-locked.txt 是否存在，并与 requirements.txt 做缺包/版本差异检测
2. 调用 `pip check` 发现 Python 依赖冲突
3. 调用 `npm ls --depth=0` 检查 ERP 前端依赖是否可解析

执行：
    python scripts/check_dependencies.py
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

try:
    from packaging import version as packaging_version
except ImportError:
    packaging_version = None  # pragma: no cover

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PY_REQ = PROJECT_ROOT / "requirements.txt"
PY_LOCK = PROJECT_ROOT / "requirements-locked.txt"
ERP_FE_DIR = PROJECT_ROOT / "💼 Intelligent ERP & Business Management" / "web" / "frontend"
NPM_LOCK = ERP_FE_DIR / "package-lock.json"
REPORT_DIR = PROJECT_ROOT / "artifacts" / "dependency_reports"
REPORT_FILE = REPORT_DIR / "dependency_report.json"

REPORT: list[dict[str, str]] = []
REQ_LINE_PATTERN = re.compile(
    r"^\s*([A-Za-z0-9_.-]+)(?:\[[^\]]+\])?\s*(==|>=|<=|~=|>|<)?\s*([A-Za-z0-9*_.+-]+)?"
)
IGNORED_EXTRA_PACKAGES = {"pip", "setuptools", "wheel"}


@dataclass
class RequirementSpec:
    raw: str
    name: str
    operator: Optional[str]
    version: Optional[str]


def log(title: str) -> None:
    print(f"\n== {title} ==")


def record(section: str, status: str, message: str) -> None:
    REPORT.append(
        {
            "section": section,
            "status": status,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )


def run_cmd(cmd: list[str], cwd: Path | None = None) -> tuple[int, str]:
    """Run a shell command, stream output, and capture combined logs."""
    result = subprocess.run(
        cmd,
        cwd=cwd,
        text=True,
        capture_output=True,
    )
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)
    if result.returncode != 0:
        print(f"[WARN] Command {' '.join(cmd)} exited with {result.returncode}")
    combined = (result.stdout or "") + (result.stderr or "")
    return result.returncode, combined


def parse_requirements_file(path: Path) -> List[RequirementSpec]:
    specs: List[RequirementSpec] = []
    if not path.exists():
        return specs
    for line in path.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        match = REQ_LINE_PATTERN.match(stripped)
        if not match:
            continue
        name, operator, version = match.groups()
        specs.append(
            RequirementSpec(
                raw=stripped,
                name=normalize_name(name),
                operator=operator,
                version=version,
            )
        )
    return specs


def parse_lock_file(path: Path) -> Dict[str, str]:
    locked: Dict[str, str] = {}
    if not path.exists():
        return locked
    for line in path.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "==" not in stripped:
            continue
        pkg, version = stripped.split("==", 1)
        locked[normalize_name(pkg)] = version
    return locked


def normalize_name(name: str) -> str:
    return name.lower().replace("_", "-")


def version_satisfied(spec: RequirementSpec, locked_version: str) -> Tuple[bool, str]:
    if not spec.operator or not spec.version or not locked_version:
        return True, ""
    if packaging_version is None:
        return True, ""
    try:
        locked = packaging_version.parse(locked_version)
        expected = packaging_version.parse(spec.version)
    except Exception:  # pragma: no cover
        return True, ""
    
    operator = spec.operator
    if operator == "==":
        return locked == expected, f"{spec.raw} (锁定为 {locked_version})"
    if operator == ">=":
        return locked >= expected, f"{spec.raw} (锁定为 {locked_version})"
    if operator == "<=":
        return locked <= expected, f"{spec.raw} (锁定为 {locked_version})"
    if operator == ">":
        return locked > expected, f"{spec.raw} (锁定为 {locked_version})"
    if operator == "<":
        return locked < expected, f"{spec.raw} (锁定为 {locked_version})"
    if operator == "~=":
        return locked >= expected, f"{spec.raw} (锁定为 {locked_version})"
    return True, ""


def compare_python_requirements() -> None:
    log("Python 依赖比对（requirements.txt vs requirements-locked.txt）")
    if not PY_LOCK.exists():
        print(f"[ERROR] 找不到 {PY_LOCK}")
        sys.exit(1)
    req_specs = parse_requirements_file(PY_REQ)
    lock_pkgs = parse_lock_file(PY_LOCK)
    req_names: Set[str] = {spec.name for spec in req_specs}

    missing_in_lock = []
    version_conflicts = []

    for spec in req_specs:
        locked_version = lock_pkgs.get(spec.name)
        if not locked_version:
            missing_in_lock.append(spec.raw)
            continue
        ok, message = version_satisfied(spec, locked_version)
        if not ok and message:
            version_conflicts.append(message)

    extra_in_lock = sorted(
        pkg for pkg in lock_pkgs.keys()
        if pkg not in req_names and pkg not in IGNORED_EXTRA_PACKAGES
    )

    if missing_in_lock:
        print("[WARN] 以下依赖在 requirements.txt 中存在，但未出现在 requirements-locked.txt，可能尚未安装：")
        for pkg in missing_in_lock:
            print(f"  - {pkg}")
    if version_conflicts:
        print("[WARN] 以下依赖版本与锁文件不一致：")
        for conflict in version_conflicts:
            print(f"  - {conflict}")
    if extra_in_lock:
        print("[INFO] 以下依赖仅存在于锁文件（可能是运行期临时或 transitive 依赖）：")
        for pkg in extra_in_lock:
            print(f"  - {pkg}=={lock_pkgs[pkg]}")

    if not missing_in_lock and not version_conflicts:
        print("✅ requirements.txt 与 requirements-locked.txt 无缺包或版本冲突。")
        record("python_requirements", "ok", "缺包/版本检查通过")
    else:
        record(
            "python_requirements",
            "warn",
            f"缺包: {', '.join(missing_in_lock) or '无'}; 版本冲突: {', '.join(version_conflicts) or '无'}",
        )


def pip_check() -> None:
    log("pip check")
    exit_code, output = run_cmd([sys.executable, "-m", "pip", "check"])
    if exit_code == 0:
        print("✅ 当前 Python 依赖无冲突。")
        record("pip_check", "ok", "pip check 通过")
    else:
        print("ℹ️ 如因权限受限导致 pip check 失败，请在虚拟环境或具有读取 site-packages 权限的 shell 中重试。")
        record("pip_check", "error", output.strip() or "pip check 失败")


def npm_check() -> None:
    log("npm 依赖检查（ERP 前端）")
    if not NPM_LOCK.exists():
        print(f"[WARN] 找不到 {NPM_LOCK}，请在 {ERP_FE_DIR} 执行 `npm install --package-lock-only`")
        record("npm_check", "warn", "缺少 package-lock.json")
        return
    try:
        package_name = json.loads((ERP_FE_DIR / "package.json").read_text())["name"]
        print(f"[INFO] 目标前端项目：{package_name}")
    except Exception:  # pylint: disable=broad-except
        pass
    exit_code, output = run_cmd(["npm", "ls", "--depth=0"], cwd=ERP_FE_DIR)
    if exit_code == 0:
        print("✅ npm 依赖解析成功。")
        record("npm_check", "ok", "npm ls --depth=0 成功")
    else:
        print("ℹ️ 若提示无权限访问全局 npm，请使用 nvm/本地 npm 或在具备访问权限的环境执行。")
        record("npm_check", "warn", output.strip() or "npm ls 失败")


def system_dependency_check() -> None:
    log("系统依赖检查")
    tools = {
        "python3": ["python3", "--version"],
        "node": ["node", "--version"],
        "npm": ["npm", "--version"],
        "git": ["git", "--version"],
    }
    missing = []
    for tool, cmd in tools.items():
        if shutil.which(tool) is None:
            print(f"[WARN] 未找到 {tool} 可执行文件")
            missing.append(tool)
            continue
        exit_code, output = run_cmd(cmd)
        status = "ok" if exit_code == 0 else "warn"
        record(f"system_{tool}", status, output.strip() or f"{tool} 检查完成")
    if missing:
        record("system_tools", "warn", f"缺少工具: {', '.join(missing)}")
    else:
        record("system_tools", "ok", "核心系统工具已安装")


def write_report() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "project_root": str(PROJECT_ROOT),
        "results": REPORT,
    }
    REPORT_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    print(f"\n[INFO] 依赖报告已写入 {REPORT_FILE}")


def main() -> None:
    compare_python_requirements()
    pip_check()
    npm_check()
    system_dependency_check()
    log("完成")
    write_report()


if __name__ == "__main__":
    main()

