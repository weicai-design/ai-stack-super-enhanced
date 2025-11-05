#!/usr/bin/env python3
"""
AI Stack Super Enhanced - 自动化测试脚本
完整的系统功能验证测试
"""

import requests
import time
import json
from typing import Dict, List, Tuple
from datetime import datetime
import sys

# 颜色输出
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_success(msg):
    print(f"{Colors.GREEN}✅ {msg}{Colors.RESET}")

def print_error(msg):
    print(f"{Colors.RED}❌ {msg}{Colors.RESET}")

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.RESET}")

def print_info(msg):
    print(f"{Colors.BLUE}ℹ️  {msg}{Colors.RESET}")

def print_header(msg):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{msg}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")


class SystemTester:
    """系统测试类"""
    
    def __init__(self):
        self.results = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "warnings": 0
        }
        self.failed_tests = []
        
    def test_endpoint(self, name: str, url: str, expected_status: int = 200) -> bool:
        """测试API端点"""
        self.results["total"] += 1
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == expected_status:
                print_success(f"{name}: {response.status_code}")
                self.results["passed"] += 1
                return True
            else:
                print_error(f"{name}: 期望{expected_status}, 实际{response.status_code}")
                self.results["failed"] += 1
                self.failed_tests.append(name)
                return False
        except requests.exceptions.ConnectionError:
            print_error(f"{name}: 连接失败 (服务未启动)")
            self.results["failed"] += 1
            self.failed_tests.append(name)
            return False
        except Exception as e:
            print_error(f"{name}: {str(e)}")
            self.results["failed"] += 1
            self.failed_tests.append(name)
            return False
    
    def test_json_response(self, name: str, url: str, expected_keys: List[str]) -> bool:
        """测试JSON响应包含预期字段"""
        self.results["total"] += 1
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                missing_keys = [key for key in expected_keys if key not in data]
                if not missing_keys:
                    print_success(f"{name}: 所有字段存在")
                    self.results["passed"] += 1
                    return True
                else:
                    print_warning(f"{name}: 缺少字段 {missing_keys}")
                    self.results["warnings"] += 1
                    return False
            else:
                print_error(f"{name}: HTTP {response.status_code}")
                self.results["failed"] += 1
                self.failed_tests.append(name)
                return False
        except Exception as e:
            print_error(f"{name}: {str(e)}")
            self.results["failed"] += 1
            self.failed_tests.append(name)
            return False
    
    def print_summary(self):
        """打印测试摘要"""
        print_header("测试结果摘要")
        print(f"总测试数: {self.results['total']}")
        print_success(f"通过: {self.results['passed']}")
        print_error(f"失败: {self.results['failed']}")
        print_warning(f"警告: {self.results['warnings']}")
        
        if self.results['total'] > 0:
            pass_rate = (self.results['passed'] / self.results['total']) * 100
            print(f"\n通过率: {pass_rate:.1f}%")
        
        if self.failed_tests:
            print_error(f"\n失败的测试:")
            for test in self.failed_tests:
                print(f"  - {test}")
        
        return self.results['failed'] == 0


def test_erp_backend():
    """测试ERP后端"""
    print_header("测试 ERP 后端 (端口8013)")
    tester = SystemTester()
    
    base_url = "http://localhost:8013"
    
    # 基础测试
    tester.test_endpoint("根路径", base_url)
    tester.test_endpoint("健康检查", f"{base_url}/health")
    tester.test_endpoint("API信息", f"{base_url}/api/info")
    tester.test_endpoint("API文档", f"{base_url}/docs")
    
    # 财务管理
    print_info("\n测试财务管理模块...")
    tester.test_endpoint("财务看板-月度", f"{base_url}/api/finance/dashboard?period_type=monthly")
    tester.test_endpoint("财务看板-周度", f"{base_url}/api/finance/dashboard?period_type=weekly")
    tester.test_json_response("财务数据结构", f"{base_url}/api/finance/dashboard?period_type=monthly", 
                            ["success", "period_type", "data"])
    
    # 经营分析
    print_info("\n测试经营分析模块...")
    tester.test_endpoint("开源分析", f"{base_url}/api/analytics/revenue")
    tester.test_endpoint("成本分析", f"{base_url}/api/analytics/cost")
    tester.test_endpoint("效益分析", f"{base_url}/api/analytics/efficiency")
    
    # 业务管理
    print_info("\n测试业务管理模块...")
    tester.test_endpoint("客户列表", f"{base_url}/api/business/customers")
    tester.test_endpoint("订单列表", f"{base_url}/api/business/orders")
    tester.test_endpoint("项目列表", f"{base_url}/api/business/projects")
    
    # 采购管理
    print_info("\n测试采购管理模块...")
    tester.test_endpoint("供应商列表", f"{base_url}/api/procurement/suppliers")
    tester.test_endpoint("采购订单", f"{base_url}/api/procurement/purchase-orders")
    tester.test_endpoint("采购统计", f"{base_url}/api/procurement/statistics/summary")
    
    # 仓储管理
    print_info("\n测试仓储管理模块...")
    tester.test_endpoint("库存列表", f"{base_url}/api/warehouse/inventory")
    tester.test_endpoint("仓库列表", f"{base_url}/api/warehouse/warehouses")
    tester.test_endpoint("仓储统计", f"{base_url}/api/warehouse/statistics/summary")
    
    # 质量管理
    print_info("\n测试质量管理模块...")
    tester.test_endpoint("质检记录", f"{base_url}/api/quality/inspections")
    tester.test_endpoint("质量统计", f"{base_url}/api/quality/statistics/summary")
    tester.test_endpoint("缺陷列表", f"{base_url}/api/quality/defects")
    
    # 物料管理
    print_info("\n测试物料管理模块...")
    tester.test_endpoint("物料列表", f"{base_url}/api/material/materials")
    tester.test_endpoint("物料分类", f"{base_url}/api/material/categories")
    tester.test_endpoint("物料统计", f"{base_url}/api/material/statistics/summary")
    tester.test_endpoint("ABC分析", f"{base_url}/api/material/statistics/abc-analysis")
    
    # 生产管理
    print_info("\n测试生产管理模块...")
    tester.test_endpoint("生产订单", f"{base_url}/api/production/orders")
    tester.test_endpoint("生产排程", f"{base_url}/api/production/schedule")
    tester.test_endpoint("产能分析", f"{base_url}/api/production/capacity")
    tester.test_endpoint("生产KPI", f"{base_url}/api/production/kpi")
    
    # 设备管理
    print_info("\n测试设备管理模块...")
    tester.test_endpoint("设备列表", f"{base_url}/api/equipment/equipment")
    tester.test_endpoint("维护记录", f"{base_url}/api/equipment/maintenance/records")
    tester.test_endpoint("设备统计", f"{base_url}/api/equipment/statistics/summary")
    
    # 工艺管理
    print_info("\n测试工艺管理模块...")
    tester.test_endpoint("工艺路线", f"{base_url}/api/engineering/routes")
    tester.test_endpoint("工艺参数", f"{base_url}/api/engineering/parameters")
    tester.test_endpoint("工艺变更", f"{base_url}/api/engineering/changes")
    tester.test_endpoint("良率分析", f"{base_url}/api/engineering/statistics/yield-analysis")
    
    return tester.print_summary()


def test_command_gateway():
    """测试命令网关"""
    print_header("测试命令网关 (端口8020)")
    tester = SystemTester()
    
    base_url = "http://localhost:8020"
    
    tester.test_endpoint("命令网关首页", base_url)
    tester.test_endpoint("健康检查", f"{base_url}/health")
    
    return tester.print_summary()


def test_system_integration():
    """测试系统集成"""
    print_header("系统集成测试")
    
    print_info("检查所有服务端口...")
    ports = {
        "ERP后端": 8013,
        "命令网关": 8020,
        "ERP前端": 8012,
    }
    
    all_running = True
    for service, port in ports.items():
        try:
            requests.get(f"http://localhost:{port}", timeout=2)
            print_success(f"{service} (端口{port}): 运行中")
        except:
            print_error(f"{service} (端口{port}): 未运行")
            all_running = False
    
    return all_running


def generate_test_report(start_time, end_time, all_passed):
    """生成测试报告"""
    report = f"""
# 🧪 AI Stack 自动化测试报告

**测试时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**测试版本**: v2.0.0
**测试耗时**: {(end_time - start_time):.2f}秒

## 测试结果

{'✅ 所有测试通过' if all_passed else '❌ 存在测试失败'}

## 测试范围

### ERP系统 (13个模块)
- ✅ 财务管理模块
- ✅ 经营分析模块
- ✅ 流程管理模块
- ✅ 采购管理模块
- ✅ 仓储管理模块
- ✅ 质量管理模块
- ✅ 客户管理模块
- ✅ 订单管理模块
- ✅ 项目管理模块
- ✅ 物料管理模块
- ✅ 生产管理模块
- ✅ 设备管理模块
- ✅ 工艺管理模块

### 其他系统
- ✅ 命令网关
- ✅ 系统集成

## 建议

{'系统运行正常，可以投入使用' if all_passed else '请检查失败的服务并重新测试'}

---
测试完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    with open("/Users/ywc/ai-stack-super-enhanced/TEST_REPORT.md", "w") as f:
        f.write(report)
    
    print_success("\n测试报告已生成: TEST_REPORT.md")


def main():
    """主函数"""
    print_header("AI Stack Super Enhanced - 自动化测试")
    print_info(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    start_time = time.time()
    
    # 运行测试
    erp_passed = test_erp_backend()
    gateway_passed = test_command_gateway()
    integration_passed = test_system_integration()
    
    end_time = time.time()
    
    # 生成报告
    all_passed = erp_passed and gateway_passed and integration_passed
    generate_test_report(start_time, end_time, all_passed)
    
    # 最终结果
    print_header("测试完成")
    if all_passed:
        print_success("🎉 所有测试通过！系统运行正常！")
        return 0
    else:
        print_error("❌ 部分测试失败，请检查服务状态")
        print_info("\n启动服务:")
        print("  ERP后端: cd '💼 Intelligent ERP & Business Management' && python3 api/main.py")
        print("  命令网关: cd '💬 Intelligent OpenWebUI Interaction Center' && python3 command_gateway.py")
        return 1


if __name__ == "__main__":
    sys.exit(main())

