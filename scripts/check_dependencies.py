#!/usr/bin/env python3
"""
统一依赖体检脚本
---------------------------------
1. 校验 requirements.lock 是否存在，并与 requirements.txt 差异保持可见
2. 调用 `pip check` 发现 Python 依赖冲突
3. 调用 `npm ls --depth=0` 检查 ERP 前端依赖是否可解析

执行：
    python scripts/check_dependencies.py
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PY_REQ = PROJECT_ROOT / "requirements.txt"
PY_LOCK = PROJECT_ROOT / "requirements.lock"
ERP_FE_DIR = PROJECT_ROOT / "💼 Intelligent ERP & Business Management" / "web" / "frontend"
NPM_LOCK = ERP_FE_DIR / "package-lock.json"


def log(title: str) -> None:
    print(f"\n== {title} ==")


def run_cmd(cmd: list[str], cwd: Path | None = None) -> int:
    """Run a shell command and stream output."""
    result = subprocess.run(cmd, cwd=cwd, text=True)
    if result.returncode != 0:
        print(f"[WARN] Command {' '.join(cmd)} exited with {result.returncode}")
    return result.returncode


def compare_python_requirements() -> None:
    log("Python 依赖比对")
    if not PY_LOCK.exists():
        print(f"[ERROR] 找不到 {PY_LOCK}")
        sys.exit(1)
    req_pkgs = {
        line.strip().split("==")[0]
        for line in PY_REQ.read_text().splitlines()
        if line.strip() and not line.startswith("#")
    }
    lock_pkgs = {
        line.strip().split("==")[0]
        for line in PY_LOCK.read_text().splitlines()
        if line.strip() and not line.startswith("#")
    }
    missing_in_lock = sorted(req_pkgs - lock_pkgs)
    extra_in_lock = sorted(lock_pkgs - req_pkgs)
    if missing_in_lock:
        print("[INFO] 以下包在 requirements.txt 中出现但未被锁定：")
        for pkg in missing_in_lock:
            print(f"  - {pkg}")
    if extra_in_lock:
        print("[INFO] 以下包仅存在于锁文件：")
        for pkg in extra_in_lock:
            print(f"  - {pkg}")
    if not missing_in_lock and not extra_in_lock:
        print("✅ requirements.txt 与 requirements.lock 保持一致。")


def pip_check() -> None:
    log("pip check")
    exit_code = run_cmd([sys.executable, "-m", "pip", "check"])
    if exit_code == 0:
        print("✅ 当前 Python 依赖无冲突。")
    else:
        print("ℹ️ 如因权限受限导致 pip check 失败，请在虚拟环境或具有读取 site-packages 权限的 shell 中重试。")


def npm_check() -> None:
    log("npm 依赖检查（ERP 前端）")
    if not NPM_LOCK.exists():
        print(f"[WARN] 找不到 {NPM_LOCK}，请在 {ERP_FE_DIR} 执行 `npm install --package-lock-only`")
        return
    try:
        package_name = json.loads((ERP_FE_DIR / "package.json").read_text())["name"]
        print(f"[INFO] 目标前端项目：{package_name}")
    except Exception:  # pylint: disable=broad-except
        pass
    exit_code = run_cmd(["npm", "ls", "--depth=0"], cwd=ERP_FE_DIR)
    if exit_code == 0:
        print("✅ npm 依赖解析成功。")
    else:
        print("ℹ️ 若提示无权限访问全局 npm，请使用 nvm/本地 npm 或在具备访问权限的环境执行。")


def main() -> None:
    compare_python_requirements()
    pip_check()
    npm_check()
    log("完成")


if __name__ == "__main__":
    main()

