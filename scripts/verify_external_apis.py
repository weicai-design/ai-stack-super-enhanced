#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证外部 API 配置脚本

检查外部 API（抖音、Tushare、同花顺等）的配置是否正确
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

def check_douyin_config():
    """检查抖音 API 配置"""
    app_key = os.getenv("DOUYIN_APP_KEY") or os.getenv("DOUYIN_APP_KEY")
    app_secret = os.getenv("DOUYIN_APP_SECRET") or os.getenv("DOUYIN_APP_SECRET")
    enabled = os.getenv("DOUYIN_REAL_MODE", "0") == "1"
    
    if enabled:
        if not app_key or not app_secret:
            print("⚠️  抖音 API 已启用但缺少配置（APP_KEY 或 APP_SECRET）")
            return False
        print("✅ 抖音 API 配置完整")
    else:
        print("ℹ️  抖音 API 未启用（使用模拟模式）")
    return True

def check_tushare_config():
    """检查 Tushare API 配置"""
    token = os.getenv("TUSHARE_TOKEN")
    enabled = os.getenv("TUSHARE_ENABLED", "0") == "1"
    
    if enabled:
        if not token:
            print("⚠️  Tushare API 已启用但缺少 TOKEN")
            return False
        print("✅ Tushare API 配置完整")
    else:
        print("ℹ️  Tushare API 未启用")
    return True

def check_ths_config():
    """检查同花顺 API 配置"""
    app_key = os.getenv("THS_APP_KEY")
    app_secret = os.getenv("THS_APP_SECRET")
    enabled = os.getenv("THS_ENABLED", "0") == "1"
    
    if enabled:
        if not app_key or not app_secret:
            print("⚠️  同花顺 API 已启用但缺少配置（APP_KEY 或 APP_SECRET）")
            return False
        print("✅ 同花顺 API 配置完整")
    else:
        print("ℹ️  同花顺 API 未启用")
    return True

def main():
    """主函数"""
    print("=" * 60)
    print("外部 API 配置验证")
    print("=" * 60)
    
    results = []
    results.append(check_douyin_config())
    results.append(check_tushare_config())
    results.append(check_ths_config())
    
    print("=" * 60)
    if all(results):
        print("✅ 所有外部 API 配置验证通过")
        sys.exit(0)
    else:
        print("⚠️  部分外部 API 配置不完整，但可以继续部署（将使用模拟模式）")
        sys.exit(0)  # 不阻止部署，只是警告

if __name__ == "__main__":
    main()

