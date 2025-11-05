#!/usr/bin/env python3
"""
系统诊断工具
System Diagnostic Tool

全面检查AI Stack系统健康状况，发现潜在问题
"""

import os
import sys
import psutil
import requests
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import json

# 颜色输出
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


class SystemDiagnostic:
    """系统诊断类"""
    
    def __init__(self):
        self.project_root = Path("/Users/ywc/ai-stack-super-enhanced")
        self.issues = []
        self.warnings = []
        self.info = []
        
    def print_section(self, title):
        """打印章节标题"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}{title}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}\n")
    
    def print_ok(self, msg):
        print(f"{Colors.GREEN}✅ {msg}{Colors.RESET}")
    
    def print_error(self, msg):
        print(f"{Colors.RED}❌ {msg}{Colors.RESET}")
        self.issues.append(msg)
    
    def print_warning(self, msg):
        print(f"{Colors.YELLOW}⚠️  {msg}{Colors.RESET}")
        self.warnings.append(msg)
    
    def print_info(self, msg):
        print(f"{Colors.CYAN}ℹ️  {msg}{Colors.RESET}")
        self.info.append(msg)
    
    def check_system_resources(self):
        """检查系统资源"""
        self.print_section("1. 系统资源检查")
        
        # CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        print(f"CPU使用率: {cpu_percent}% (核心数: {cpu_count})")
        if cpu_percent > 80:
            self.print_warning(f"CPU使用率过高: {cpu_percent}%")
        else:
            self.print_ok(f"CPU使用率正常: {cpu_percent}%")
        
        # 内存
        memory = psutil.virtual_memory()
        memory_gb = memory.total / (1024**3)
        memory_used_gb = memory.used / (1024**3)
        memory_percent = memory.percent
        
        print(f"内存: {memory_used_gb:.2f}GB / {memory_gb:.2f}GB ({memory_percent}%)")
        if memory_percent > 85:
            self.print_warning(f"内存使用率过高: {memory_percent}%")
        else:
            self.print_ok(f"内存使用率正常: {memory_percent}%")
        
        # 磁盘
        disk = psutil.disk_usage('/')
        disk_gb = disk.total / (1024**3)
        disk_used_gb = disk.used / (1024**3)
        disk_free_gb = disk.free / (1024**3)
        disk_percent = disk.percent
        
        print(f"磁盘: {disk_used_gb:.2f}GB / {disk_gb:.2f}GB (剩余: {disk_free_gb:.2f}GB)")
        if disk_percent > 90:
            self.print_error(f"磁盘空间严重不足: {disk_percent}%")
        elif disk_percent > 80:
            self.print_warning(f"磁盘空间偏少: {disk_percent}%")
        else:
            self.print_ok(f"磁盘空间充足: {disk_free_gb:.2f}GB")
    
    def check_dependencies(self):
        """检查依赖项"""
        self.print_section("2. 依赖项检查")
        
        # Python版本
        python_version = sys.version.split()[0]
        print(f"Python版本: {python_version}")
        if python_version >= "3.8":
            self.print_ok(f"Python版本符合要求: {python_version}")
        else:
            self.print_error(f"Python版本过低: {python_version} (需要3.8+)")
        
        # 检查关键Python包
        required_packages = [
            'fastapi', 'uvicorn', 'sqlalchemy', 'pydantic', 
            'requests', 'psutil', 'numpy', 'pandas'
        ]
        
        for package in required_packages:
            try:
                __import__(package)
                self.print_ok(f"Python包已安装: {package}")
            except ImportError:
                self.print_warning(f"Python包未安装: {package}")
        
        # 检查Node.js
        import subprocess
        try:
            result = subprocess.run(['node', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                self.print_ok(f"Node.js已安装: {result.stdout.strip()}")
            else:
                self.print_warning("Node.js未安装（前端功能可能受限）")
        except:
            self.print_warning("Node.js未安装（前端功能可能受限）")
        
        # 检查Docker
        try:
            result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                self.print_ok(f"Docker已安装: {result.stdout.strip()}")
            else:
                self.print_warning("Docker未安装（容器部署受限）")
        except:
            self.print_warning("Docker未安装（容器部署受限）")
    
    def check_file_structure(self):
        """检查文件结构"""
        self.print_section("3. 文件结构检查")
        
        critical_paths = [
            "💼 Intelligent ERP & Business Management",
            "📚 Enhanced RAG & Knowledge Graph",
            "💬 Intelligent OpenWebUI Interaction Center",
            "scripts",
            "common",
            "monitoring"
        ]
        
        for path in critical_paths:
            full_path = self.project_root / path
            if full_path.exists():
                self.print_ok(f"目录存在: {path}")
            else:
                self.print_error(f"目录缺失: {path}")
        
        # 检查关键文件
        critical_files = [
            "README.md",
            "requirements.txt",
            "docker-compose.yml",
            "💼 Intelligent ERP & Business Management/api/main.py",
            "scripts/quick_deploy.sh",
            "scripts/automated_test.py"
        ]
        
        for file in critical_files:
            full_path = self.project_root / file
            if full_path.exists():
                self.print_ok(f"文件存在: {file}")
            else:
                self.print_error(f"文件缺失: {file}")
    
    def check_services(self):
        """检查服务状态"""
        self.print_section("4. 服务状态检查")
        
        services = {
            "ERP后端": "http://localhost:8013/health",
            "命令网关": "http://localhost:8020/health",
            "RAG系统": "http://localhost:8011/health",
            "OpenWebUI": "http://localhost:3000"
        }
        
        for service_name, url in services.items():
            try:
                response = requests.get(url, timeout=2)
                if response.status_code == 200:
                    self.print_ok(f"{service_name}: 运行中")
                else:
                    self.print_warning(f"{service_name}: 响应异常 ({response.status_code})")
            except requests.exceptions.ConnectionError:
                self.print_warning(f"{service_name}: 未运行")
            except Exception as e:
                self.print_warning(f"{service_name}: 检查失败 ({str(e)})")
    
    def check_database(self):
        """检查数据库"""
        self.print_section("5. 数据库检查")
        
        db_path = self.project_root / "💼 Intelligent ERP & Business Management" / "ai_stack.db"
        
        if db_path.exists():
            self.print_ok(f"数据库文件存在: {db_path.name}")
            
            # 检查数据库大小
            db_size_mb = db_path.stat().st_size / (1024**2)
            print(f"数据库大小: {db_size_mb:.2f}MB")
            
            # 检查数据库内容
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # 获取表列表
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                
                print(f"数据库表数量: {len(tables)}")
                
                # 检查关键表的数据
                key_tables = ['financial_data', 'customers', 'business_orders']
                for table in key_tables:
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        count = cursor.fetchone()[0]
                        self.print_ok(f"表 {table}: {count} 条数据")
                    except:
                        self.print_warning(f"表 {table}: 不存在或无法访问")
                
                conn.close()
            except Exception as e:
                self.print_error(f"数据库访问失败: {e}")
        else:
            self.print_warning("数据库文件不存在（首次运行需初始化）")
    
    def check_ports(self):
        """检查端口占用"""
        self.print_section("6. 端口占用检查")
        
        required_ports = {
            8011: "RAG系统",
            8012: "ERP前端",
            8013: "ERP后端",
            8014: "股票系统",
            8015: "趋势分析",
            8016: "内容创作",
            8017: "任务代理",
            8018: "资源管理",
            8019: "自我学习",
            8020: "命令网关",
            3000: "OpenWebUI"
        }
        
        for port, service in required_ports.items():
            connections = [conn for conn in psutil.net_connections() if conn.laddr.port == port]
            if connections:
                self.print_info(f"端口 {port} ({service}): 已占用")
            else:
                self.print_warning(f"端口 {port} ({service}): 未使用")
    
    def check_configuration(self):
        """检查配置文件"""
        self.print_section("7. 配置文件检查")
        
        config_files = [
            "docker-compose.yml",
            "docker-compose.full.yml",
            ".env"
        ]
        
        for config in config_files:
            config_path = self.project_root / config
            if config_path.exists():
                self.print_ok(f"配置文件存在: {config}")
            else:
                self.print_warning(f"配置文件不存在: {config}")
    
    def generate_report(self):
        """生成诊断报告"""
        self.print_section("诊断摘要")
        
        print(f"\n{Colors.BOLD}问题总数: {len(self.issues)}{Colors.RESET}")
        print(f"{Colors.BOLD}警告总数: {len(self.warnings)}{Colors.RESET}")
        print(f"{Colors.BOLD}信息总数: {len(self.info)}{Colors.RESET}\n")
        
        if self.issues:
            print(f"{Colors.RED}{Colors.BOLD}❌ 发现的问题:{Colors.RESET}")
            for issue in self.issues:
                print(f"  • {issue}")
            print()
        
        if self.warnings:
            print(f"{Colors.YELLOW}{Colors.BOLD}⚠️  警告信息:{Colors.RESET}")
            for warning in self.warnings:
                print(f"  • {warning}")
            print()
        
        # 生成JSON报告
        report = {
            "timestamp": datetime.now().isoformat(),
            "version": "v2.0.1",
            "issues": self.issues,
            "warnings": self.warnings,
            "info": self.info,
            "health_score": self._calculate_health_score()
        }
        
        report_path = self.project_root / "diagnostic_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"{Colors.GREEN}✅ 诊断报告已保存: diagnostic_report.json{Colors.RESET}\n")
        
        return report
    
    def _calculate_health_score(self):
        """计算健康分数"""
        base_score = 100
        score = base_score - (len(self.issues) * 10) - (len(self.warnings) * 3)
        return max(0, min(100, score))
    
    def run_full_diagnostic(self):
        """运行完整诊断"""
        print(f"{Colors.BOLD}{Colors.CYAN}")
        print("="*70)
        print("  AI Stack Super Enhanced - 系统诊断工具 v1.0")
        print("="*70)
        print(f"{Colors.RESET}\n")
        print(f"诊断时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        self.check_system_resources()
        self.check_dependencies()
        self.check_file_structure()
        self.check_services()
        self.check_database()
        self.check_ports()
        self.check_configuration()
        
        report = self.generate_report()
        
        # 打印健康分数
        health_score = report['health_score']
        print(f"{Colors.BOLD}系统健康分数: {health_score}/100{Colors.RESET}")
        
        if health_score >= 90:
            print(f"{Colors.GREEN}系统状态：优秀 ⭐⭐⭐⭐⭐{Colors.RESET}")
        elif health_score >= 70:
            print(f"{Colors.YELLOW}系统状态：良好 ⭐⭐⭐⭐{Colors.RESET}")
        elif health_score >= 50:
            print(f"{Colors.YELLOW}系统状态：需要优化 ⭐⭐⭐{Colors.RESET}")
        else:
            print(f"{Colors.RED}系统状态：需要修复 ⭐⭐{Colors.RESET}")
        
        print(f"\n{Colors.CYAN}建议：{Colors.RESET}")
        if len(self.issues) > 0:
            print("  1. 优先修复发现的问题")
        if len(self.warnings) > 0:
            print("  2. 关注警告信息")
        if health_score >= 90:
            print("  ✅ 系统运行良好，可以正常使用！")
        
        return health_score


def main():
    """主函数"""
    diagnostic = SystemDiagnostic()
    health_score = diagnostic.run_full_diagnostic()
    
    return 0 if health_score >= 70 else 1


if __name__ == "__main__":
    sys.exit(main())

