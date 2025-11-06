#!/usr/bin/env python3
"""
AI Stack 集成测试套件
测试所有模块的API接口和集成功能
"""
import asyncio
import httpx
from typing import Dict, Any, List
from datetime import datetime
import json


class IntegrationTester:
    """集成测试器"""
    
    def __init__(self, base_url: str = "http://localhost"):
        """
        初始化测试器
        
        Args:
            base_url: 基础URL
        """
        self.base_url = base_url
        self.results = []
        
        # 服务端口映射
        self.services = {
            "AI交互中心": 8020,
            "RAG系统": 8011,
            "ERP系统": 8013,
            "股票交易": 8014,
            "趋势分析": 8015,
            "内容创作": 8016,
            "任务代理": 8017,
            "资源管理": 8018,
            "自我学习": 8019
        }
    
    async def test_service_health(self, name: str, port: int) -> Dict[str, Any]:
        """
        测试服务健康状态
        
        Args:
            name: 服务名称
            port: 端口号
        
        Returns:
            测试结果
        """
        url = f"{self.base_url}:{port}/health"
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url)
                
                success = response.status_code == 200
                
                return {
                    "service": name,
                    "test": "健康检查",
                    "success": success,
                    "status_code": response.status_code,
                    "response_time": response.elapsed.total_seconds() if hasattr(response, 'elapsed') else 0,
                    "message": "服务正常" if success else f"状态码: {response.status_code}"
                }
        
        except Exception as e:
            return {
                "service": name,
                "test": "健康检查",
                "success": False,
                "error": str(e),
                "message": f"连接失败: {str(e)}"
            }
    
    async def test_chat_api(self) -> Dict[str, Any]:
        """测试AI交互中心API"""
        url = f"{self.base_url}:8020/api/chat"
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    url,
                    json={
                        "message": "你好，这是集成测试",
                        "user_id": "test_user"
                    }
                )
                
                success = response.status_code == 200
                
                return {
                    "service": "AI交互中心",
                    "test": "聊天API",
                    "success": success,
                    "status_code": response.status_code,
                    "message": "聊天功能正常" if success else "聊天API测试失败"
                }
        
        except Exception as e:
            return {
                "service": "AI交互中心",
                "test": "聊天API",
                "success": False,
                "error": str(e)
            }
    
    async def test_rag_search(self) -> Dict[str, Any]:
        """测试RAG检索API"""
        url = f"{self.base_url}:8011/api/search"
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    url,
                    json={
                        "query": "测试查询",
                        "top_k": 5
                    }
                )
                
                success = response.status_code == 200
                
                return {
                    "service": "RAG系统",
                    "test": "知识检索",
                    "success": success,
                    "status_code": response.status_code,
                    "message": "检索功能正常" if success else "检索API测试失败"
                }
        
        except Exception as e:
            return {
                "service": "RAG系统",
                "test": "知识检索",
                "success": False,
                "error": str(e)
            }
    
    async def test_erp_customer_list(self) -> Dict[str, Any]:
        """测试ERP客户列表API"""
        url = f"{self.base_url}:8013/api/customers"
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                
                success = response.status_code == 200
                
                return {
                    "service": "ERP系统",
                    "test": "客户列表",
                    "success": success,
                    "status_code": response.status_code,
                    "message": "ERP API正常" if success else "ERP API测试失败"
                }
        
        except Exception as e:
            return {
                "service": "ERP系统",
                "test": "客户列表",
                "success": False,
                "error": str(e)
            }
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("=" * 60)
        print("🧪 AI Stack 集成测试开始")
        print("=" * 60)
        print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"基础URL: {self.base_url}")
        print()
        
        # 1. 健康检查测试
        print("📋 第一阶段: 服务健康检查")
        print("-" * 60)
        
        health_tasks = [
            self.test_service_health(name, port)
            for name, port in self.services.items()
        ]
        
        health_results = await asyncio.gather(*health_tasks)
        self.results.extend(health_results)
        
        for result in health_results:
            icon = "✅" if result["success"] else "❌"
            print(f"{icon} {result['service']}: {result.get('message', 'N/A')}")
        
        print()
        
        # 2. API功能测试
        print("📋 第二阶段: API功能测试")
        print("-" * 60)
        
        api_tests = [
            self.test_chat_api(),
            self.test_rag_search(),
            self.test_erp_customer_list()
        ]
        
        api_results = await asyncio.gather(*api_tests, return_exceptions=True)
        
        for result in api_results:
            if isinstance(result, dict):
                self.results.append(result)
                icon = "✅" if result["success"] else "❌"
                print(f"{icon} {result['service']} - {result['test']}: {result.get('message', 'N/A')}")
        
        print()
        
        # 3. 生成测试报告
        self.generate_report()
    
    def generate_report(self):
        """生成测试报告"""
        print("=" * 60)
        print("📊 测试报告")
        print("=" * 60)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.get("success", False))
        failed_tests = total_tests - passed_tests
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"总测试数: {total_tests}")
        print(f"通过: {passed_tests} ✅")
        print(f"失败: {failed_tests} ❌")
        print(f"成功率: {success_rate:.1f}%")
        print()
        
        if failed_tests > 0:
            print("❌ 失败的测试:")
            for result in self.results:
                if not result.get("success", False):
                    print(f"  • {result['service']} - {result['test']}")
                    if "error" in result:
                        print(f"    错误: {result['error']}")
        
        print()
        print("=" * 60)
        
        # 保存到文件
        report_file = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "success_rate": success_rate,
                "results": self.results
            }, f, ensure_ascii=False, indent=2)
        
        print(f"📝 详细报告已保存到: {report_file}")


async def main():
    """主函数"""
    tester = IntegrationTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())

