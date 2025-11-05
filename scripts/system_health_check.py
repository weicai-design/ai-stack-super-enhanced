#!/usr/bin/env python3
"""
AI Stack Super Enhanced - 系统健康检查脚本
功能：检查所有服务状态、端口占用、依赖环境
"""

import requests
import subprocess
import sys
import time
from typing import Dict, List, Tuple
from dataclasses import dataclass

# 颜色输出
class Colors:
    GREEN = '\033[0;32m'
    RED = '\033[0;31m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'

@dataclass
class Service:
    name: str
    port: int
    health_url: str
    status: str = "unknown"
    
class HealthChecker:
    def __init__(self):
        self.services = [
            Service("OpenWebUI", 3000, "http://localhost:3000"),
            Service("RAG系统", 8011, "http://localhost:8011/health"),
            Service("ERP前端", 8012, "http://localhost:8012"),
            Service("ERP后端", 8013, "http://localhost:8013/health"),
            Service("股票交易", 8014, "http://localhost:8014/health"),
            Service("趋势分析", 8015, "http://localhost:8015/health"),
            Service("内容创作", 8016, "http://localhost:8016/health"),
            Service("任务代理", 8017, "http://localhost:8017/health"),
            Service("资源管理", 8018, "http://localhost:8018/health"),
            Service("自我学习", 8019, "http://localhost:8019/health"),
        ]
        
    def print_header(self, text: str):
        """打印标题"""
        print(f"\n{Colors.CYAN}{'='*60}{Colors.NC}")
        print(f"{Colors.CYAN}{text:^60}{Colors.NC}")
        print(f"{Colors.CYAN}{'='*60}{Colors.NC}\n")
        
    def check_service(self, service: Service) -> bool:
        """检查单个服务"""
        try:
            response = requests.get(service.health_url, timeout=3)
            if response.status_code == 200:
                service.status = "running"
                return True
        except requests.exceptions.RequestException:
            pass
        
        service.status = "stopped"
        return False
        
    def check_all_services(self):
        """检查所有服务"""
        self.print_header("检查服务状态")
        
        running_count = 0
        stopped_count = 0
        
        for service in self.services:
            print(f"检查 {service.name:15} (端口 {service.port})... ", end="", flush=True)
            
            if self.check_service(service):
                print(f"{Colors.GREEN}✓ 运行中{Colors.NC}")
                running_count += 1
            else:
                print(f"{Colors.RED}✗ 未运行{Colors.NC}")
                stopped_count += 1
        
        return running_count, stopped_count
        
    def check_dependencies(self) -> Dict[str, bool]:
        """检查系统依赖"""
        self.print_header("检查系统依赖")
        
        dependencies = {
            'python3': 'python3 --version',
            'node': 'node --version',
            'npm': 'npm --version',
            'docker': 'docker --version',
            'ollama': 'ollama --version'
        }
        
        results = {}
        
        for name, cmd in dependencies.items():
            try:
                result = subprocess.run(
                    cmd.split(),
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    version = result.stdout.strip().split('\n')[0]
                    print(f"{Colors.GREEN}✓{Colors.NC} {name:15} {version}")
                    results[name] = True
                else:
                    print(f"{Colors.RED}✗{Colors.NC} {name:15} 未安装")
                    results[name] = False
            except Exception as e:
                print(f"{Colors.RED}✗{Colors.NC} {name:15} 未安装")
                results[name] = False
                
        return results
        
    def check_ports(self) -> List[int]:
        """检查端口占用"""
        self.print_header("检查端口占用")
        
        occupied_ports = []
        
        for service in self.services:
            try:
                result = subprocess.run(
                    ['lsof', '-i', f':{service.port}'],
                    capture_output=True,
                    text=True,
                    timeout=3
                )
                
                if result.returncode == 0 and result.stdout:
                    print(f"{Colors.YELLOW}⚠{Colors.NC}  端口 {service.port:5} 被占用 ({service.name})")
                    occupied_ports.append(service.port)
                else:
                    print(f"{Colors.GREEN}✓{Colors.NC}  端口 {service.port:5} 可用")
            except Exception:
                print(f"{Colors.BLUE}?{Colors.NC}  端口 {service.port:5} 状态未知")
                
        return occupied_ports
        
    def generate_report(self, running_count: int, stopped_count: int):
        """生成健康报告"""
        self.print_header("系统健康报告")
        
        total = running_count + stopped_count
        success_rate = (running_count / total * 100) if total > 0 else 0
        
        print(f"总服务数: {total}")
        print(f"{Colors.GREEN}运行中: {running_count}{Colors.NC}")
        print(f"{Colors.RED}已停止: {stopped_count}{Colors.NC}")
        print(f"成功率: {success_rate:.1f}%")
        print()
        
        if success_rate == 100:
            print(f"{Colors.GREEN}✅ 所有服务运行正常！{Colors.NC}")
            return 0
        elif success_rate >= 70:
            print(f"{Colors.YELLOW}⚠️  部分服务需要启动{Colors.NC}")
            return 1
        elif success_rate > 0:
            print(f"{Colors.YELLOW}⚠️  多数服务未运行{Colors.NC}")
            return 2
        else:
            print(f"{Colors.RED}❌ 所有服务未运行{Colors.NC}")
            return 3
            
    def get_startup_suggestions(self, stopped_count: int):
        """提供启动建议"""
        if stopped_count == 0:
            return
            
        self.print_header("启动建议")
        
        print("以下服务未运行：")
        for service in self.services:
            if service.status == "stopped":
                print(f"  • {service.name} (端口 {service.port})")
        
        print()
        print("快速启动命令：")
        print(f"{Colors.BLUE}  ./scripts/start_all_services.sh{Colors.NC}")
        print()
        print("或单独启动ERP系统：")
        print(f"{Colors.BLUE}  cd '💼 Intelligent ERP & Business Management' && ./start_erp.sh{Colors.NC}")
        print()
        
    def run_full_check(self) -> int:
        """运行完整检查"""
        print(f"{Colors.BLUE}")
        print("🏥 AI Stack Super Enhanced - 系统健康检查")
        print(f"   检查时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{Colors.NC}")
        
        # 1. 检查依赖
        deps = self.check_dependencies()
        
        # 2. 检查端口
        occupied = self.check_ports()
        
        # 3. 检查服务
        running, stopped = self.check_all_services()
        
        # 4. 生成报告
        exit_code = self.generate_report(running, stopped)
        
        # 5. 提供建议
        self.get_startup_suggestions(stopped)
        
        return exit_code

def main():
    checker = HealthChecker()
    exit_code = checker.run_full_check()
    sys.exit(exit_code)

if __name__ == "__main__":
    main()


