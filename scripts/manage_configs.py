#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
环境配置管理 CLI

用法：
    python scripts/manage_configs.py list
    python scripts/manage_configs.py apply --profile dev --override KEY=VALUE
"""

import argparse
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "🚀 Super Agent Main Interface"))

from core.config_automation import get_env_manager  # noqa: E402


def parse_overrides(overrides: list[str]) -> dict:
    data = {}
    for item in overrides:
        if "=" not in item:
            continue
        key, value = item.split("=", 1)
        data[key.strip()] = value.strip()
    return data


def main():
    parser = argparse.ArgumentParser(description="AI-STACK 环境配置管理")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("list", help="列出可用配置 profile")

    apply_parser = sub.add_parser("apply", help="应用并生成 .env.runtime")
    apply_parser.add_argument("--profile", required=True, help="profile 名称")
    apply_parser.add_argument(
        "--override",
        action="append",
        default=[],
        help="覆盖 env 变量，格式 KEY=VALUE，可重复",
    )

    args = parser.parse_args()
    manager = get_env_manager()

    if args.command == "list":
        for profile in manager.list_profiles():
            print(f"- {profile['name']}: {profile['description']}")
        return

    if args.command == "apply":
        overrides = parse_overrides(args.override)
        result = manager.apply_profile(args.profile, overrides=overrides)
        print(f"已生成 {result['output_file']}，Profile: {result['profile']['name']}")
        return

    parser.print_help()


if __name__ == "__main__":
    main()

