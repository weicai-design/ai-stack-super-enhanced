#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T002任务：RAG双检索完整验证测试脚本

验证RAG双检索验证器的完整功能：
1. 验证第1次RAG检索（理解需求）的完整性和质量
2. 验证第2次RAG检索（整合经验知识）的完整性和质量
3. 测试验证器API接口
4. 生成验证报告
"""

import asyncio
import json
import sys
import os
from datetime import datetime
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.rag_double_retrieval_validator import (
    RAGDoubleRetrievalValidator,
    get_double_retrieval_validator,
    ValidationStatus,
    RetrievalType,
)


class MockRAGService:
    """模拟RAG服务，用于测试"""
    
    def __init__(self):
        self.retrieve_count = 0
        self.retrieve_for_integration_count = 0
    
    async def retrieve(self, query: str, top_k: int = 5, context: dict = None, filter_type: str = "general") -> list:
        """模拟第1次RAG检索"""
        self.retrieve_count += 1
        await asyncio.sleep(0.1)  # 模拟网络延迟
        
        # 模拟检索结果
        results = []
        for i in range(min(top_k, 3)):
            results.append({
                "content": f"第{i+1}个检索结果，查询：{query}",
                "score": 0.7 - (i * 0.1),
                "metadata": {
                    "source": "knowledge_base",
                    "type": "general",
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            })
        
        return results
    
    async def retrieve_for_integration(self, execution_result: dict, top_k: int = 3, context: dict = None, filter_type: str = "experience") -> list:
        """模拟第2次RAG检索"""
        self.retrieve_for_integration_count += 1
        await asyncio.sleep(0.15)  # 模拟网络延迟
        
        # 模拟经验知识检索结果
        results = []
        module = execution_result.get("module", "unknown")
        
        for i in range(min(top_k, 2)):
            results.append({
                "content": f"经验知识{i+1}：基于{module}模块的执行结果",
                "score": 0.8 - (i * 0.1),
                "metadata": {
                    "source": "experience_base",
                    "type": "experience",
                    "module": module,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            })
        
        return results


class T002RAGDoubleRetrievalTest:
    """T002任务测试类"""
    
    def __init__(self):
        self.test_results = []
        self.mock_rag_service = MockRAGService()
        self.validator = None
    
    async def setup(self):
        """测试设置"""
        print("🔧 初始化RAG双检索验证器...")
        
        # 创建验证器实例
        self.validator = RAGDoubleRetrievalValidator(self.mock_rag_service)
        
        print("✅ 验证器初始化完成")
    
    async def test_validator_initialization(self):
        """测试验证器初始化"""
        print("\n🧪 测试验证器初始化...")
        
        try:
            # 检查验证器属性
            assert self.validator is not None, "验证器实例为空"
            assert hasattr(self.validator, 'rag_service'), "验证器缺少rag_service属性"
            assert hasattr(self.validator, 'validation_history'), "验证器缺少validation_history属性"
            assert hasattr(self.validator, 'validation_config'), "验证器缺少validation_config属性"
            
            # 检查配置
            config = self.validator.validation_config
            assert "first_retrieval" in config, "缺少第1次检索配置"
            assert "second_retrieval" in config, "缺少第2次检索配置"
            
            print("✅ 验证器初始化测试通过")
            return True
            
        except AssertionError as e:
            print(f"❌ 验证器初始化测试失败: {e}")
            return False
    
    async def test_singleton_pattern(self):
        """测试单例模式"""
        print("\n🧪 测试单例模式...")
        
        try:
            # 获取第一个实例
            validator1 = get_double_retrieval_validator(self.mock_rag_service)
            
            # 获取第二个实例（应该返回同一个实例）
            validator2 = get_double_retrieval_validator()
            
            assert validator1 is validator2, "单例模式失败：返回了不同的实例"
            
            print("✅ 单例模式测试通过")
            return True
            
        except Exception as e:
            print(f"❌ 单例模式测试失败: {e}")
            return False
    
    async def test_first_retrieval_validation(self):
        """测试第1次RAG检索验证"""
        print("\n🧪 测试第1次RAG检索验证...")
        
        try:
            query = "测试查询：如何实现RAG双检索机制？"
            
            # 执行验证
            report = await self.validator.validate_double_retrieval(query)
            
            # 验证结果
            assert report.first_retrieval_result is not None, "第1次检索结果为空"
            assert report.first_retrieval_result.retrieval_type == RetrievalType.FIRST_RETRIEVAL, "检索类型错误"
            assert len(report.first_retrieval_result.results) > 0, "检索结果为空"
            assert report.first_retrieval_result.duration_seconds > 0, "检索时间无效"
            
            # 检查验证指标
            metrics = report.first_retrieval_result.validation_metrics
            assert "results_count" in metrics, "缺少结果数量指标"
            assert "response_time" in metrics, "缺少响应时间指标"
            
            print(f"✅ 第1次检索验证测试通过 - 结果数量: {len(report.first_retrieval_result.results)}")
            return True
            
        except Exception as e:
            print(f"❌ 第1次检索验证测试失败: {e}")
            return False
    
    async def test_double_retrieval_validation(self):
        """测试完整双检索验证"""
        print("\n🧪 测试完整双检索验证...")
        
        try:
            query = "完整测试：RAG双检索机制验证"
            execution_result = {
                "success": True,
                "module": "ERP",
                "type": "analysis",
                "data": {"result": "模拟执行结果"}
            }
            
            # 执行完整验证
            report = await self.validator.validate_double_retrieval(
                query=query,
                execution_result=execution_result,
                top_k_first=3,
                top_k_second=2
            )
            
            # 验证第1次检索
            assert report.first_retrieval_result is not None, "第1次检索结果为空"
            assert report.first_retrieval_result.validation_status != ValidationStatus.FAILED, "第1次检索验证失败"
            
            # 验证第2次检索
            assert report.second_retrieval_result is not None, "第2次检索结果为空"
            assert report.second_retrieval_result.validation_status != ValidationStatus.FAILED, "第2次检索验证失败"
            
            # 验证整体状态
            assert report.overall_status != ValidationStatus.FAILED, "整体验证失败"
            
            # 验证性能指标
            assert "total_duration" in report.performance_metrics, "缺少总时长指标"
            assert report.performance_metrics["total_duration"] > 0, "总时长无效"
            
            print(f"✅ 完整双检索验证测试通过 - 整体状态: {report.overall_status.value}")
            return True
            
        except Exception as e:
            print(f"❌ 完整双检索验证测试失败: {e}")
            return False
    
    async def test_validation_stats(self):
        """测试验证统计信息"""
        print("\n🧪 测试验证统计信息...")
        
        try:
            # 获取统计信息
            stats = await self.validator.get_validation_stats()
            
            # 验证统计信息
            assert "total_validations" in stats, "缺少总验证次数"
            assert "passed_validations" in stats, "缺少通过验证次数"
            assert "failed_validations" in stats, "缺少失败验证次数"
            assert "pass_rate" in stats, "缺少通过率"
            
            # 验证数据合理性
            assert stats["total_validations"] >= 0, "总验证次数无效"
            assert 0 <= stats["pass_rate"] <= 100, "通过率无效"
            
            print(f"✅ 验证统计信息测试通过 - 总验证次数: {stats['total_validations']}")
            return True
            
        except Exception as e:
            print(f"❌ 验证统计信息测试失败: {e}")
            return False
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始执行T002任务：RAG双检索完整验证测试")
        print("=" * 60)
        
        # 初始化
        await self.setup()
        
        # 执行测试
        tests = [
            ("验证器初始化", self.test_validator_initialization),
            ("单例模式", self.test_singleton_pattern),
            ("第1次检索验证", self.test_first_retrieval_validation),
            ("完整双检索验证", self.test_double_retrieval_validation),
            ("验证统计信息", self.test_validation_stats),
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            try:
                result = await test_func()
                if result:
                    passed_tests += 1
                    self.test_results.append((test_name, "PASSED"))
                else:
                    self.test_results.append((test_name, "FAILED"))
            except Exception as e:
                print(f"❌ {test_name}测试异常: {e}")
                self.test_results.append((test_name, "ERROR"))
        
        # 生成测试报告
        await self.generate_test_report(passed_tests, total_tests)
        
        return passed_tests == total_tests
    
    async def generate_test_report(self, passed: int, total: int):
        """生成测试报告"""
        print("\n" + "=" * 60)
        print("📊 T002任务测试报告")
        print("=" * 60)
        
        pass_rate = (passed / total) * 100 if total > 0 else 0
        
        print(f"总测试数: {total}")
        print(f"通过数: {passed}")
        print(f"通过率: {pass_rate:.1f}%")
        
        print("\n详细测试结果:")
        for test_name, status in self.test_results:
            status_icon = "✅" if status == "PASSED" else "❌"
            print(f"  {status_icon} {test_name}: {status}")
        
        # 保存报告到文件
        report_data = {
            "task": "T002 - RAG双检索完整验证",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "total_tests": total,
            "passed_tests": passed,
            "pass_rate": pass_rate,
            "test_results": self.test_results,
            "mock_service_stats": {
                "retrieve_count": self.mock_rag_service.retrieve_count,
                "retrieve_for_integration_count": self.mock_rag_service.retrieve_for_integration_count,
            }
        }
        
        report_file = project_root / "reports" / "t002_rag_double_retrieval_report.json"
        report_file.parent.mkdir(exist_ok=True)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 详细报告已保存至: {report_file}")
        
        if passed == total:
            print("\n🎉 T002任务测试全部通过！RAG双检索完整验证机制已实现。")
        else:
            print(f"\n⚠️ T002任务测试部分失败，通过率: {pass_rate:.1f}%")


async def main():
    """主函数"""
    tester = T002RAGDoubleRetrievalTest()
    success = await tester.run_all_tests()
    
    # 返回退出码
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())