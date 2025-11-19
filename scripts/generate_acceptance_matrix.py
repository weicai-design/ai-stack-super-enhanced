#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成验收矩阵Excel文件的独立脚本
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "🚀 Super Agent Main Interface"))

from core.acceptance_matrix_generator import acceptance_matrix_generator

if __name__ == "__main__":
    print("正在生成验收矩阵Excel文件...")
    try:
        output_file = acceptance_matrix_generator.generate_excel()
        print(f"✅ 验收矩阵Excel文件已生成: {output_file}")
        
        # 显示摘要
        summary = acceptance_matrix_generator.get_requirements_summary()
        print("\n📊 验收矩阵摘要:")
        print(f"  总需求数: {summary['total']}")
        print(f"  已完成: {summary['by_status']['completed']}")
        print(f"  进行中: {summary['by_status']['in_progress']}")
        print(f"  待处理: {summary['by_status']['pending']}")
        print(f"  完成率: {summary['completion_rate']:.1f}%")
        print(f"  测试通过率: {summary['test_pass_rate']:.1f}%")
    except Exception as e:
        print(f"❌ 生成失败: {e}")
        sys.exit(1)

