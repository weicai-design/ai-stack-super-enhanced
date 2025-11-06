#!/usr/bin/env python3
"""
系统日志查看器
实时查看和分析系统日志
"""
import os
import sys
from pathlib import Path
from datetime import datetime
import re
from collections import defaultdict


class LogViewer:
    """日志查看器"""
    
    def __init__(self):
        self.log_dir = Path('/Users/ywc/ai-stack-super-enhanced/logs')
        self.log_dir.mkdir(exist_ok=True)
    
    def list_logs(self):
        """列出所有日志文件"""
        print("\n📋 可用日志文件:\n")
        
        log_files = sorted(self.log_dir.glob('*.log'))
        
        if not log_files:
            print("  暂无日志文件")
            return []
        
        for i, log_file in enumerate(log_files, 1):
            size = log_file.stat().st_size / 1024  # KB
            mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
            print(f"{i}. {log_file.name:<30} ({size:.1f} KB) - {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
        
        return log_files
    
    def tail_log(self, log_file: Path, lines: int = 50):
        """查看日志末尾"""
        print(f"\n📄 查看日志: {log_file.name} (最后{lines}行)\n")
        print("=" * 80)
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
                last_lines = all_lines[-lines:]
                
                for line in last_lines:
                    # 高亮显示不同级别的日志
                    line = line.rstrip()
                    if 'ERROR' in line or '❌' in line:
                        print(f"\033[91m{line}\033[0m")  # 红色
                    elif 'WARNING' in line or '⚠️' in line:
                        print(f"\033[93m{line}\033[0m")  # 黄色
                    elif 'INFO' in line or '✅' in line:
                        print(f"\033[92m{line}\033[0m")  # 绿色
                    else:
                        print(line)
        
        except Exception as e:
            print(f"❌ 读取日志失败: {str(e)}")
    
    def search_logs(self, keyword: str, log_file: Path = None):
        """搜索日志"""
        print(f"\n🔍 搜索关键词: {keyword}\n")
        print("=" * 80)
        
        # 确定搜索范围
        if log_file:
            files_to_search = [log_file]
        else:
            files_to_search = list(self.log_dir.glob('*.log'))
        
        total_matches = 0
        
        for file in files_to_search:
            matches = []
            
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f, 1):
                        if keyword.lower() in line.lower():
                            matches.append((line_num, line.rstrip()))
            except:
                continue
            
            if matches:
                print(f"\n📁 {file.name} - 找到 {len(matches)} 处匹配:\n")
                for line_num, line in matches[-10:]:  # 只显示最后10条
                    print(f"  {line_num:4d} | {line}")
                total_matches += len(matches)
        
        print(f"\n总计找到 {total_matches} 处匹配")
    
    def analyze_errors(self):
        """分析错误日志"""
        print("\n🔍 错误日志分析\n")
        print("=" * 80)
        
        error_patterns = {
            'HTTP错误': r'HTTP/\d\.\d" (\d{3})',
            'Python异常': r'(Exception|Error):',
            '连接失败': r'Connection|连接',
            '超时': r'timeout|超时',
            '权限问题': r'Permission|权限'
        }
        
        all_errors = defaultdict(list)
        
        for log_file in self.log_dir.glob('*.log'):
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    for error_type, pattern in error_patterns.items():
                        matches = re.findall(pattern, content, re.IGNORECASE)
                        if matches:
                            all_errors[error_type].extend(matches[:5])  # 最多5个示例
            except:
                continue
        
        if not all_errors:
            print("✅ 未发现明显错误")
            return
        
        for error_type, examples in all_errors.items():
            print(f"\n⚠️  {error_type}: {len(examples)} 个")
            for example in examples[:3]:
                print(f"     - {example}")
    
    def get_statistics(self):
        """统计日志信息"""
        print("\n📊 日志统计信息\n")
        print("=" * 80)
        
        stats = {
            'total_files': 0,
            'total_size': 0,
            'total_lines': 0,
            'error_count': 0,
            'warning_count': 0
        }
        
        for log_file in self.log_dir.glob('*.log'):
            stats['total_files'] += 1
            stats['total_size'] += log_file.stat().st_size
            
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        stats['total_lines'] += 1
                        if 'ERROR' in line or '❌' in line:
                            stats['error_count'] += 1
                        elif 'WARNING' in line or '⚠️' in line:
                            stats['warning_count'] += 1
            except:
                continue
        
        print(f"总文件数: {stats['total_files']}")
        print(f"总大小: {stats['total_size'] / 1024 / 1024:.2f} MB")
        print(f"总行数: {stats['total_lines']:,}")
        print(f"错误数: {stats['error_count']}")
        print(f"警告数: {stats['warning_count']}")
    
    def clear_logs(self, older_than_days: int = 7):
        """清理旧日志"""
        print(f"\n🗑️  清理{older_than_days}天前的日志...\n")
        
        from datetime import timedelta
        threshold = datetime.now() - timedelta(days=older_than_days)
        
        deleted_count = 0
        deleted_size = 0
        
        for log_file in self.log_dir.glob('*.log'):
            mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
            if mtime < threshold:
                size = log_file.stat().st_size
                log_file.unlink()
                deleted_count += 1
                deleted_size += size
                print(f"  ✓ 删除: {log_file.name}")
        
        if deleted_count > 0:
            print(f"\n✅ 清理完成，删除 {deleted_count} 个文件，释放 {deleted_size / 1024:.1f} KB 空间")
        else:
            print("✅ 无需清理")


def main():
    """主函数"""
    viewer = LogViewer()
    
    print("\n" + "=" * 80)
    print("📝 AI Stack 日志查看器")
    print("=" * 80)
    
    while True:
        print("\n请选择操作:")
        print("1. 查看日志列表")
        print("2. 查看日志末尾")
        print("3. 搜索日志")
        print("4. 分析错误")
        print("5. 统计信息")
        print("6. 清理旧日志")
        print("0. 退出")
        
        choice = input("\n请输入选项 (0-6): ").strip()
        
        if choice == '0':
            print("\n👋 再见！")
            break
        elif choice == '1':
            viewer.list_logs()
        elif choice == '2':
            log_files = viewer.list_logs()
            if log_files:
                index = input("\n请选择日志编号: ").strip()
                try:
                    log_file = log_files[int(index) - 1]
                    lines = input("显示行数 (默认50): ").strip() or "50"
                    viewer.tail_log(log_file, int(lines))
                except (ValueError, IndexError):
                    print("❌ 无效选择")
        elif choice == '3':
            keyword = input("请输入搜索关键词: ").strip()
            if keyword:
                viewer.search_logs(keyword)
        elif choice == '4':
            viewer.analyze_errors()
        elif choice == '5':
            viewer.get_statistics()
        elif choice == '6':
            days = input("清理多少天前的日志 (默认7): ").strip() or "7"
            confirm = input(f"确认清理{days}天前的日志? (y/n): ").strip().lower()
            if confirm == 'y':
                viewer.clear_logs(int(days))
        else:
            print("❌ 无效选项")


if __name__ == "__main__":
    main()










