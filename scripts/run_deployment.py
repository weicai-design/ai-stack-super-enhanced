#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
部署自动化 CLI

示例：
    python scripts/run_deployment.py --profile staging --execute
"""

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "🚀 Super Agent Main Interface"))

from core.config_automation import get_deployment_manager  # noqa: E402


async def main():
    parser = argparse.ArgumentParser(description="AI-STACK 部署自动化")
    parser.add_argument("--profile", required=True, help="环境 profile 名称")
    parser.add_argument(
        "--step",
        action="append",
        dest="steps",
        help="仅执行指定步骤，可多次提供",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="实际执行命令（默认 dry-run）",
    )
    args = parser.parse_args()

    deployment = get_deployment_manager()
    result = await deployment.run_pipeline(
        profile=args.profile,
        dry_run=not args.execute,
        selected_steps=args.steps,
    )
    print(f"运行完成，完成状态：{result['completed']}, dry_run={result['dry_run']}")
    for step in result["steps"]:
        print(f"- {step['name']}: {step['status']}")
        if step.get("detail"):
            print(f"  detail: {step['detail'][:160]}")


if __name__ == "__main__":
    asyncio.run(main())

