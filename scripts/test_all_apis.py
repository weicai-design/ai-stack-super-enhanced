#!/usr/bin/env python3
"""
API测试工具集
快速测试所有API接口的可用性
"""

import requests
import json
from typing import Dict, List
from datetime import datetime
import sys


class APITester:
    """API测试工具"""
    
    def __init__(self):
        self.results = []
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
    
    def test_api(self, name: str, url: str, method: str = "GET", data: Dict = None) -> bool:
        """测试单个API"""
        self.total_tests += 1
        
        try:
            if method == "GET":
                response = requests.get(url, timeout=5)
            elif method == "POST":
                response = requests.post(url, json=data, timeout=5)
            else:
                response = requests.request(method, url, json=data, timeout=5)
            
            success = response.status_code in [200, 201]
            
            if success:
                self.passed_tests += 1
                status = "✅ PASS"
            else:
                self.failed_tests += 1
                status = f"❌ FAIL ({response.status_code})"
            
            self.results.append({
                "name": name,
                "url": url,
                "method": method,
                "status": status,
                "status_code": response.status_code,
                "success": success
            })
            
            return success
            
        except requests.exceptions.RequestException as e:
            self.failed_tests += 1
            self.results.append({
                "name": name,
                "url": url,
                "method": method,
                "status": f"❌ ERROR",
                "error": str(e),
                "success": False
            })
            return False
    
    def print_results(self):
        """打印测试结果"""
        print("\n" + "="*70)
        print("API 测试结果")
        print("="*70)
        
        for result in self.results:
            print(f"\n{result['status']} {result['name']}")
            print(f"   {result['method']} {result['url']}")
            if 'error' in result:
                print(f"   错误: {result['error']}")
            elif 'status_code' in result:
                print(f"   状态码: {result['status_code']}")
        
        print("\n" + "="*70)
        print(f"总计: {self.total_tests} | 通过: {self.passed_tests} | 失败: {self.failed_tests}")
        print(f"成功率: {self.passed_tests/self.total_tests*100:.1f}%")
        print("="*70 + "\n")
    
    def generate_report(self, filename: str = "api_test_report.json"):
        """生成JSON报告"""
        report = {
            "test_time": datetime.now().isoformat(),
            "total_tests": self.total_tests,
            "passed_tests": self.passed_tests,
            "failed_tests": self.failed_tests,
            "success_rate": f"{self.passed_tests/self.total_tests*100:.1f}%",
            "results": self.results
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"📄 报告已生成: {filename}")


def main():
    """主测试函数"""
    
    print("\n🧪 AI Stack API 测试工具")
    print("="*70)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70 + "\n")
    
    tester = APITester()
    
    # ==================== ERP系统测试 ====================
    
    print("📦 测试 ERP 系统...")
    
    # 健康检查
    tester.test_api(
        "ERP 健康检查",
        "http://localhost:8013/health"
    )
    
    # API信息
    tester.test_api(
        "ERP API 信息",
        "http://localhost:8013/api/info"
    )
    
    # 财务管理
    tester.test_api(
        "财务看板 - 月度",
        "http://localhost:8013/api/finance/dashboard?period_type=monthly"
    )
    
    tester.test_api(
        "财务看板 - 周度",
        "http://localhost:8013/api/finance/dashboard?period_type=weekly"
    )
    
    # 经营分析
    tester.test_api(
        "开源分析",
        "http://localhost:8013/api/analytics/revenue-analysis"
    )
    
    tester.test_api(
        "成本分析",
        "http://localhost:8013/api/analytics/cost-analysis"
    )
    
    tester.test_api(
        "效益分析",
        "http://localhost:8013/api/analytics/efficiency-analysis"
    )
    
    # 流程管理
    tester.test_api(
        "业务流程列表",
        "http://localhost:8013/api/process/processes"
    )
    
    # 采购管理
    tester.test_api(
        "供应商列表",
        "http://localhost:8013/api/procurement/suppliers"
    )
    
    tester.test_api(
        "采购订单列表",
        "http://localhost:8013/api/procurement/purchase-orders"
    )
    
    # 仓储管理
    tester.test_api(
        "库存列表",
        "http://localhost:8013/api/warehouse/inventory"
    )
    
    tester.test_api(
        "仓库列表",
        "http://localhost:8013/api/warehouse/warehouses"
    )
    
    # 质量管理
    tester.test_api(
        "质检记录",
        "http://localhost:8013/api/quality/inspections"
    )
    
    tester.test_api(
        "缺陷列表",
        "http://localhost:8013/api/quality/defects"
    )
    
    # 物料管理
    tester.test_api(
        "物料列表",
        "http://localhost:8013/api/material/materials"
    )
    
    tester.test_api(
        "物料分类",
        "http://localhost:8013/api/material/categories"
    )
    
    tester.test_api(
        "ABC分析",
        "http://localhost:8013/api/material/statistics/abc-analysis"
    )
    
    # 生产管理
    tester.test_api(
        "生产订单",
        "http://localhost:8013/api/production/orders"
    )
    
    tester.test_api(
        "产能分析",
        "http://localhost:8013/api/production/capacity"
    )
    
    tester.test_api(
        "生产KPI",
        "http://localhost:8013/api/production/kpi"
    )
    
    # 设备管理
    tester.test_api(
        "设备列表",
        "http://localhost:8013/api/equipment/equipment"
    )
    
    tester.test_api(
        "维护记录",
        "http://localhost:8013/api/equipment/maintenance/records"
    )
    
    tester.test_api(
        "可靠性分析",
        "http://localhost:8013/api/equipment/statistics/reliability"
    )
    
    # 工艺管理
    tester.test_api(
        "工艺路线",
        "http://localhost:8013/api/engineering/routes"
    )
    
    tester.test_api(
        "工艺参数",
        "http://localhost:8013/api/engineering/parameters"
    )
    
    tester.test_api(
        "良率分析",
        "http://localhost:8013/api/engineering/statistics/yield-analysis"
    )
    
    # 业务管理
    tester.test_api(
        "客户列表",
        "http://localhost:8013/api/business/customers"
    )
    
    # ==================== 命令网关测试 ====================
    
    print("\n🌐 测试 命令网关...")
    
    tester.test_api(
        "命令网关根路径",
        "http://localhost:8020/"
    )
    
    # ==================== 打印结果 ====================
    
    tester.print_results()
    tester.generate_report()
    
    # 返回退出码
    sys.exit(0 if tester.failed_tests == 0 else 1)


if __name__ == "__main__":
    main()

