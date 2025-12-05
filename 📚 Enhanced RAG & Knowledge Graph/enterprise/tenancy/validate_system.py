"""
多租户认证系统综合验证脚本
Multi-tenant Authentication System Comprehensive Validation Script

整合完整性检查和集成测试，提供完整的系统验证报告。

运行方式：
    python "📚 Enhanced RAG & Knowledge Graph/enterprise/tenancy/validate_system.py"
"""

import sys
import os
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List, Tuple

# 添加项目根目录到路径
rag_root = Path(__file__).parent.parent.parent  # "📚 Enhanced RAG & Knowledge Graph"
project_root = rag_root.parent  # 项目根目录
sys.path.insert(0, str(rag_root))
sys.path.insert(0, str(project_root))

# 切换到正确的目录
os.chdir(rag_root)


class Colors:
    """终端颜色"""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_header(title: str):
    """打印标题"""
    print("\n" + "=" * 70)
    print(f"  {Colors.BOLD}{title}{Colors.END}")
    print("=" * 70)


def run_check_script() -> Tuple[bool, str]:
    """运行完整性检查脚本"""
    print_header("阶段 1: 系统完整性检查")
    
    check_script = Path(__file__).parent / "check_system_integrity.py"
    
    if not check_script.exists():
        print(f"{Colors.RED}❌ 完整性检查脚本不存在: {check_script}{Colors.END}")
        return False, "脚本不存在"
    
    try:
        # 运行检查脚本
        result = subprocess.run(
            [sys.executable, str(check_script)],
            capture_output=True,
            text=True,
            cwd=str(rag_root)
        )
        
        # 输出结果
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
        
        return result.returncode == 0, result.stdout + result.stderr
        
    except Exception as e:
        print(f"{Colors.RED}❌ 运行完整性检查失败: {e}{Colors.END}")
        return False, str(e)


def run_integration_tests() -> Tuple[bool, str]:
    """运行集成测试"""
    print_header("阶段 2: 集成测试")
    
    test_script = Path(__file__).parent / "test_integration.py"
    
    if not test_script.exists():
        print(f"{Colors.RED}❌ 集成测试脚本不存在: {test_script}{Colors.END}")
        return False, "脚本不存在"
    
    try:
        # 运行测试脚本
        result = subprocess.run(
            [sys.executable, str(test_script)],
            capture_output=True,
            text=True,
            cwd=str(rag_root)
        )
        
        # 输出结果
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
        
        return result.returncode == 0, result.stdout + result.stderr
        
    except Exception as e:
        print(f"{Colors.RED}❌ 运行集成测试失败: {e}{Colors.END}")
        return False, str(e)


def generate_report(check_passed: bool, test_passed: bool, check_output: str, test_output: str):
    """生成验证报告"""
    print_header("验证报告")
    
    report_file = project_root / "validation_report.txt"
    
    with open(report_file, "w", encoding="utf-8") as f:
        f.write("=" * 70 + "\n")
        f.write("  多租户认证系统验证报告\n")
        f.write("  Multi-tenant Authentication System Validation Report\n")
        f.write("=" * 70 + "\n")
        f.write(f"\n验证时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"项目根目录: {project_root}\n")
        f.write("\n")
        
        f.write("-" * 70 + "\n")
        f.write("阶段 1: 系统完整性检查\n")
        f.write("-" * 70 + "\n")
        f.write(f"结果: {'✅ 通过' if check_passed else '❌ 失败'}\n")
        f.write("\n")
        f.write(check_output)
        f.write("\n")
        
        f.write("-" * 70 + "\n")
        f.write("阶段 2: 集成测试\n")
        f.write("-" * 70 + "\n")
        f.write(f"结果: {'✅ 通过' if test_passed else '❌ 失败'}\n")
        f.write("\n")
        f.write(test_output)
        f.write("\n")
        
        f.write("-" * 70 + "\n")
        f.write("总体结果\n")
        f.write("-" * 70 + "\n")
        if check_passed and test_passed:
            f.write("✅ 所有验证通过！系统运行正常。\n")
        else:
            f.write("❌ 部分验证失败，请检查上述详细信息。\n")
    
    print(f"✅ 验证报告已保存: {report_file}")


def main():
    """主函数"""
    print("\n" + "=" * 70)
    print(f"  {Colors.BOLD}多租户认证系统综合验证{Colors.END}")
    print(f"  Multi-tenant Authentication System Comprehensive Validation")
    print("=" * 70)
    print(f"\n开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"项目根目录: {project_root}")
    print(f"工作目录: {rag_root}")
    
    # 阶段 1: 完整性检查
    check_passed, check_output = run_check_script()
    
    # 如果完整性检查失败，询问是否继续
    if not check_passed:
        print(f"\n{Colors.YELLOW}⚠️  完整性检查失败，建议先修复问题后再运行集成测试。{Colors.END}")
        print(f"{Colors.YELLOW}是否继续运行集成测试？ (y/n): {Colors.END}", end="")
        try:
            response = input().strip().lower()
            if response != 'y':
                print("验证已取消。")
                return 1
        except (EOFError, KeyboardInterrupt):
            print("\n验证已取消。")
            return 1
    
    # 阶段 2: 集成测试
    test_passed, test_output = run_integration_tests()
    
    # 生成报告
    generate_report(check_passed, test_passed, check_output, test_output)
    
    # 输出最终结果
    print_header("验证结果汇总")
    
    print(f"  完整性检查: {'✅ 通过' if check_passed else '❌ 失败'}")
    print(f"  集成测试:   {'✅ 通过' if test_passed else '❌ 失败'}")
    
    if check_passed and test_passed:
        print(f"\n{Colors.GREEN}{'🎉' * 35}{Colors.END}")
        print(f"  {Colors.BOLD}{Colors.GREEN}所有验证通过！系统运行正常。{Colors.END}")
        print(f"{Colors.GREEN}{'🎉' * 35}{Colors.END}\n")
        print(f"验证报告: {project_root / 'validation_report.txt'}")
        return 0
    else:
        print(f"\n{Colors.YELLOW}{'⚠️' * 35}{Colors.END}")
        failed_items = []
        if not check_passed:
            failed_items.append("完整性检查")
        if not test_passed:
            failed_items.append("集成测试")
        print(f"  {Colors.BOLD}{Colors.YELLOW}{', '.join(failed_items)} 失败，请检查验证报告。{Colors.END}")
        print(f"{Colors.YELLOW}{'⚠️' * 35}{Colors.END}\n")
        print(f"验证报告: {project_root / 'validation_report.txt'}")
        return 1


if __name__ == "__main__":
    sys.exit(main())














