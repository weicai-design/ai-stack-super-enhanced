#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
2秒SLO性能验证运行脚本
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from tests.performance.test_2s_slo_validation import main


def run_slo_validation():
    """运行2秒SLO验证"""
    print("🚀 开始执行2秒SLO性能验证")
    print("=" * 60)
    
    try:
        # 运行SLO验证
        success = asyncio.run(main())
        
        print("\n" + "=" * 60)
        if success:
            print("✅ 2秒SLO性能验证通过！所有API端点满足性能要求")
        else:
            print("❌ 2秒SLO性能验证失败！部分API端点需要优化")
        
        return success
        
    except Exception as e:
        print(f"❌ SLO验证执行失败: {e}")
        return False


if __name__ == "__main__":
    # 检查是否在正确的目录中运行
    current_dir = os.path.dirname(os.path.abspath(__file__))
    expected_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "tests", "performance")
    
    if current_dir != expected_dir:
        print(f"⚠️  警告：建议在项目根目录运行此脚本")
        print(f"   当前目录: {current_dir}")
        print(f"   建议目录: {expected_dir}")
        print()
    
    # 运行验证
    success = run_slo_validation()
    
    # 退出码
    sys.exit(0 if success else 1)