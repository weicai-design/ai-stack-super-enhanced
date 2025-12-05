#!/usr/bin/env python3
"""
系统集成测试脚本
测试所有AI专家模块的集成和协同工作
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.experts import (
    get_rag_experts, get_erp_experts, get_content_experts,
    get_trend_experts, get_stock_experts, get_operations_finance_experts
)

from core.experts.rag_experts import KnowledgeExpert, RetrievalExpert, GraphExpert
from core.experts.erp_experts import QualityExpert, CostExpert, DeliveryExpert
from core.experts.content_experts import ContentPlanningExpert, ContentGenerationExpert
from core.experts.trend_experts import TrendCollectionExpert, TrendAnalysisExpert
from core.experts.stock_experts import StockQuoteExpert, StockStrategyExpert
from core.experts.operations_finance_experts import OperationsAnalysisExpert, UserAnalysisExpert


class SystemIntegrationTest:
    """系统集成测试类"""
    
    def __init__(self):
        self.results = {}
        self.test_count = 0
        self.passed_count = 0
    
    async def test_rag_module(self):
        """测试RAG模块"""
        print("\n🔍 测试RAG模块...")
        
        try:
            # 获取所有RAG专家
            rag_experts = get_rag_experts()
            assert len(rag_experts) >= 3, f"RAG专家数量不足: {len(rag_experts)}"
            
            # 测试知识专家 - 使用更简单的测试方法
            knowledge_expert = KnowledgeExpert()
            
            # 检查专家基本属性
            assert hasattr(knowledge_expert, 'expert_id'), "知识专家缺少expert_id属性"
            assert hasattr(knowledge_expert, 'name'), "知识专家缺少name属性"
            assert hasattr(knowledge_expert, 'stage'), "知识专家缺少stage属性"
            
            # 检查专家方法
            assert hasattr(knowledge_expert, 'analyze_knowledge'), "知识专家缺少analyze_knowledge方法"
            
            self.results["rag_module"] = "✅ 通过"
            self.passed_count += 1
            print("✅ RAG模块测试通过")
            
        except Exception as e:
            self.results["rag_module"] = f"❌ 失败: {str(e)}"
            print(f"❌ RAG模块测试失败: {e}")
    
    async def test_erp_module(self):
        """测试ERP模块"""
        print("\n🏭 测试ERP模块...")
        
        try:
            # 获取所有ERP专家
            erp_experts = get_erp_experts()
            assert len(erp_experts) >= 10, f"ERP专家数量不足: {len(erp_experts)}"
            
            # 测试质量专家
            quality_expert = QualityExpert()
            result = await quality_expert.analyze_quality(
                {"quality_metrics": {"defect_rate": 0.02}}, 
                {"industry": "manufacturing"}
            )
            assert result.score > 0, "质量专家分析失败"
            
            self.results["erp_module"] = "✅ 通过"
            self.passed_count += 1
            print("✅ ERP模块测试通过")
            
        except Exception as e:
            self.results["erp_module"] = f"❌ 失败: {str(e)}"
            print(f"❌ ERP模块测试失败: {e}")
    
    async def test_content_module(self):
        """测试内容创作模块"""
        print("\n✍️ 测试内容创作模块...")
        
        try:
            # 获取所有内容专家
            content_experts = get_content_experts()
            assert len(content_experts) >= 6, f"内容专家数量不足: {len(content_experts)}"
            
            # 测试内容策划专家
            planning_expert = ContentPlanningExpert()
            result = await planning_expert.analyze_planning(
                {"topics": ["AI技术"]}, 
                {"platform": "xiaohongshu"}
            )
            assert result.score > 0, "内容策划专家分析失败"
            
            self.results["content_module"] = "✅ 通过"
            self.passed_count += 1
            print("✅ 内容创作模块测试通过")
            
        except Exception as e:
            self.results["content_module"] = f"❌ 失败: {str(e)}"
            print(f"❌ 内容创作模块测试失败: {e}")
    
    async def test_trend_module(self):
        """测试趋势分析模块"""
        print("\n📈 测试趋势分析模块...")
        
        try:
            # 获取所有趋势专家
            trend_experts = get_trend_experts()
            assert len(trend_experts) >= 6, f"趋势专家数量不足: {len(trend_experts)}"
            
            # 测试趋势收集专家
            collection_expert = TrendCollectionExpert()
            result = await collection_expert.analyze(
                {"trend_data": [{"keyword": "AI", "volume": 1000}]}, 
                {"time_range": "7d"}
            )
            # 使用accuracy属性替代score
            assert result.accuracy > 0, "趋势收集专家分析失败"
            
            self.results["trend_module"] = "✅ 通过"
            self.passed_count += 1
            print("✅ 趋势分析模块测试通过")
            
        except Exception as e:
            self.results["trend_module"] = f"❌ 失败: {str(e)}"
            print(f"❌ 趋势分析模块测试失败: {e}")
    
    async def test_stock_module(self):
        """测试股票分析模块"""
        print("\n📊 测试股票分析模块...")
        
        try:
            # 获取所有股票专家
            stock_experts = get_stock_experts()
            assert len(stock_experts) >= 7, f"股票专家数量不足: {len(stock_experts)}"
            
            # 测试股票报价专家
            quote_expert = StockQuoteExpert()
            result = await quote_expert.analyze_quote(
                {"symbol": "AAPL"}, 
                {"market": "US"}
            )
            assert result.score > 0, "股票报价专家分析失败"
            
            self.results["stock_module"] = "✅ 通过"
            self.passed_count += 1
            print("✅ 股票分析模块测试通过")
            
        except Exception as e:
            self.results["stock_module"] = f"❌ 失败: {str(e)}"
            print(f"❌ 股票分析模块测试失败: {e}")
    
    async def test_operations_finance_module(self):
        """测试运营财务模块"""
        print("\n💰 测试运营财务模块...")
        
        try:
            # 获取所有运营财务专家
            ops_finance_experts = get_operations_finance_experts()
            assert len(ops_finance_experts) >= 10, f"运营财务专家数量不足: {len(ops_finance_experts)}"
            
            # 测试运营分析专家
            operations_expert = OperationsAnalysisExpert()
            result = await operations_expert.analyze_operations(
                {"kpi_data": {"revenue": 1000000}}, 
                {"period": "monthly"}
            )
            assert result.score > 0, "运营分析专家分析失败"
            
            self.results["operations_finance_module"] = "✅ 通过"
            self.passed_count += 1
            print("✅ 运营财务模块测试通过")
            
        except Exception as e:
            self.results["operations_finance_module"] = f"❌ 失败: {str(e)}"
            print(f"❌ 运营财务模块测试失败: {e}")
    
    async def test_expert_collaboration(self):
        """测试专家协同工作"""
        print("\n🤝 测试专家协同工作...")
        
        try:
            # 模拟多专家协同分析
            from core.expert_collaboration import ExpertCollaborationHub
            
            hub = ExpertCollaborationHub()
            
            # 使用异步方法创建协同会话
            session_id = await hub.start_session(
                "综合业务分析",
                ["rag_expert", "erp_expert", "content_expert"]
            )
            assert session_id is not None, "协同会话创建失败"
            
            # 添加一些模拟贡献
            await hub.add_contribution(session_id, "rag_expert", "提供相关文档检索结果")
            await hub.add_contribution(session_id, "erp_expert", "分析业务数据趋势")
            await hub.add_contribution(session_id, "content_expert", "生成内容策略建议")
            
            # 完成会话
            decision = await hub.finalize_session(session_id)
            assert decision is not None, "协同决策生成失败"
            
            self.results["expert_collaboration"] = "✅ 通过"
            self.passed_count += 1
            print("✅ 专家协同工作测试通过")
            
        except Exception as e:
            self.results["expert_collaboration"] = f"❌ 失败: {str(e)}"
            print(f"❌ 专家协同工作测试失败: {e}")
    
    async def test_api_endpoints(self):
        """测试API端点"""
        print("\n🌐 测试API端点...")
        
        try:
            import httpx
            import time
            import asyncio
            
            # 检查API服务器是否运行
            max_retries = 5
            retry_delay = 3
            
            for attempt in range(max_retries):
                try:
                    # 测试主API端点，增加超时设置
                    async with httpx.AsyncClient(timeout=15.0) as client:
                        print(f"尝试连接API服务器... (尝试 {attempt + 1}/{max_retries})")
                        response = await client.get("http://127.0.0.1:8002/")
                        print(f"主API端点状态码: {response.status_code}")
                        assert response.status_code == 200, f"主API端点不可用，状态码: {response.status_code}"
                        
                        # 测试专家API端点
                        response = await client.get("http://127.0.0.1:8002/api/experts")
                        print(f"专家API端点状态码: {response.status_code}")
                        assert response.status_code == 200, f"专家API端点不可用，状态码: {response.status_code}"
                    
                    self.results["api_endpoints"] = "✅ 通过"
                    self.passed_count += 1
                    print("✅ API端点测试通过")
                    return
                    
                except (httpx.ConnectError, httpx.TimeoutException) as e:
                    if attempt < max_retries - 1:
                        print(f"⚠️  API连接失败，{retry_delay}秒后重试...")
                        await asyncio.sleep(retry_delay)
                    else:
                        # 如果所有重试都失败，检查服务器状态
                        print("🔍 检查API服务器状态...")
                        import subprocess
                        try:
                            result = subprocess.run(
                                ["lsof", "-i", ":8002"], 
                                capture_output=True, 
                                text=True
                            )
                            if result.returncode == 0:
                                print(f"✅ API服务器正在运行: {result.stdout}")
                            else:
                                print("❌ API服务器未在端口8002运行")
                        except Exception as check_error:
                            print(f"❌ 检查服务器状态失败: {check_error}")
                        
                        raise e
            
        except Exception as e:
            self.results["api_endpoints"] = f"❌ 失败: {str(e)}"
            print(f"❌ API端点测试失败: {e}")
    
    def print_summary(self):
        """打印测试总结"""
        print("\n" + "="*60)
        print("📊 系统集成测试总结")
        print("="*60)
        
        total_tests = len(self.results)
        success_rate = (self.passed_count / total_tests) * 100 if total_tests > 0 else 0
        
        for module, result in self.results.items():
            print(f"{module}: {result}")
        
        print("-"*60)
        print(f"总计测试: {total_tests}")
        print(f"通过测试: {self.passed_count}")
        print(f"失败测试: {total_tests - self.passed_count}")
        print(f"成功率: {success_rate:.1f}%")
        
        if success_rate >= 80:
            print("\n🎉 系统集成测试总体成功！")
        else:
            print("\n⚠️  系统集成测试需要改进")


async def main():
    """主测试函数"""
    print("🚀 开始系统集成测试...")
    
    tester = SystemIntegrationTest()
    
    # 执行所有测试
    await tester.test_rag_module()
    await tester.test_erp_module()
    await tester.test_content_module()
    await tester.test_trend_module()
    await tester.test_stock_module()
    await tester.test_operations_finance_module()
    await tester.test_expert_collaboration()
    await tester.test_api_endpoints()
    
    # 打印总结
    tester.print_summary()


if __name__ == "__main__":
    asyncio.run(main())