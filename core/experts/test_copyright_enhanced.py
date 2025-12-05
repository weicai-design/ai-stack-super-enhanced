#!/usr/bin/env python3
"""
ContentCopyrightExpert生产级功能增强测试脚本
测试智能版权保护、风险评估、趋势分析和策略优化功能
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from content_experts import ContentCopyrightExpert, ContentAnalysis


class TestContentCopyrightEnhanced:
    """ContentCopyrightExpert生产级增强功能测试类"""
    
    def __init__(self):
        self.expert = ContentCopyrightExpert()
    
    async def test_production_copyright_analysis(self):
        """测试生产级版权分析功能"""
        print("\n=== 测试1: 生产级版权分析功能 ===")
        
        # 测试数据
        copyright_data = {
            "originality": 85.5,
            "similarity": {"max": 25.3, "avg": 12.1},
            "risk_level": "medium",
            "copyright_database": {"matches": 2}
        }
        
        result = await self.expert.analyze_copyright(copyright_data)
        
        # 验证结果
        assert isinstance(result, ContentAnalysis), "返回结果应为ContentAnalysis类型"
        assert result.confidence >= 0.9, f"置信度应≥0.9，实际为{result.confidence}"
        assert result.score >= 70, f"分数应≥70，实际为{result.score}"
        assert len(result.insights) > 0, "应包含分析洞察"
        assert len(result.recommendations) > 0, "应包含优化建议"
        assert result.metadata.get("production_ready") == True, "应标记为生产级"
        
        print("✅ 生产级版权分析测试通过")
        print(f"   分数: {result.score}")
        print(f"   置信度: {result.confidence}")
        print(f"   洞察数量: {len(result.insights)}")
        print(f"   建议数量: {len(result.recommendations)}")
    
    async def test_intelligent_trend_analysis(self):
        """测试智能版权趋势分析功能"""
        print("\n=== 测试2: 智能版权趋势分析功能 ===")
        
        # 先添加一些历史数据
        test_data = {
            "originality": 80,
            "similarity": {"max": 20, "avg": 10},
            "risk_level": "low"
        }
        
        # 添加多个历史记录
        for i in range(5):
            await self.expert.analyze_copyright(test_data)
        
        # 测试趋势分析
        result = await self.expert.analyze_copyright_trend("30d")
        
        # 验证结果
        assert isinstance(result, ContentAnalysis), "返回结果应为ContentAnalysis类型"
        assert result.confidence >= 0.85, f"置信度应≥0.85，实际为{result.confidence}"
        assert result.score >= 70, f"分数应≥70，实际为{result.score}"
        assert len(result.insights) > 0, "应包含趋势洞察"
        assert len(result.recommendations) > 0, "应包含趋势优化建议"
        assert result.metadata.get("production_ready") == True, "应标记为生产级"
        
        print("✅ 智能版权趋势分析测试通过")
        print(f"   趋势分数: {result.score}")
        print(f"   置信度: {result.confidence}")
        print(f"   时间周期: {result.metadata.get('time_period', 'N/A')}")
    
    async def test_strategy_optimization(self):
        """测试版权策略优化功能"""
        print("\n=== 测试3: 版权策略优化功能 ===")
        
        result = await self.expert.optimize_copyright_strategy(target_score=90)
        
        # 验证结果
        assert isinstance(result, ContentAnalysis), "返回结果应为ContentAnalysis类型"
        assert result.confidence >= 0.85, f"置信度应≥0.85，实际为{result.confidence}"
        assert result.score >= 75, f"优化潜力分数应≥75，实际为{result.score}"
        assert len(result.insights) > 0, "应包含策略分析洞察"
        assert len(result.recommendations) > 0, "应包含优化实施建议"
        assert result.metadata.get("production_ready") == True, "应标记为生产级"
        assert result.metadata.get("target_score") == 90, "应包含目标分数"
        
        print("✅ 版权策略优化测试通过")
        print(f"   优化潜力分数: {result.score}")
        print(f"   目标分数: {result.metadata.get('target_score', 'N/A')}")
        print(f"   建议数量: {len(result.recommendations)}")
    
    async def test_real_time_monitoring(self):
        """测试实时版权监控预警功能"""
        print("\n=== 测试4: 实时版权监控预警功能 ===")
        
        # 高风险测试数据
        high_risk_data = {
            "originality": 30.5,
            "similarity": {"max": 85.2, "avg": 60.1},
            "risk_level": "high",
            "copyright_database": {"matches": 5}
        }
        
        result = await self.expert.analyze_copyright(high_risk_data)
        
        # 验证高风险检测
        assert isinstance(result, ContentAnalysis), "返回结果应为ContentAnalysis类型"
        
        # 检查是否包含高风险警告
        high_risk_insights = [insight for insight in result.insights if "⚠️" in insight or "风险" in insight]
        assert len(high_risk_insights) > 0, "高风险数据应触发警告"
        
        print("✅ 实时版权监控预警测试通过")
        print(f"   高风险警告数量: {len(high_risk_insights)}")
        print(f"   最终分数: {result.score}")
    
    async def test_intelligent_originality_analysis(self):
        """测试智能原创性分析功能"""
        print("\n=== 测试5: 智能原创性分析功能 ===")
        
        # 不同原创性水平测试
        test_cases = [
            {"originality": 95, "expected_level": "优秀"},
            {"originality": 85, "expected_level": "良好"},
            {"originality": 70, "expected_level": "一般"},
            {"originality": 45, "expected_level": "不足"}
        ]
        
        for i, test_case in enumerate(test_cases):
            test_data = {
                "originality": test_case["originality"],
                "similarity": {"max": 10, "avg": 5},
                "risk_level": "low"
            }
            
            result = await self.expert.analyze_copyright(test_data)
            
            # 验证原创性分析
            originality_insights = [insight for insight in result.insights 
                                   if test_case["expected_level"] in insight]
            assert len(originality_insights) > 0, f"原创性{test_case['originality']}%应识别为{test_case['expected_level']}"
            
            print(f"   案例{i+1}: {test_case['originality']}% -> {test_case['expected_level']} ✓")
        
        print("✅ 智能原创性分析测试通过")
    
    async def test_intelligent_similarity_analysis(self):
        """测试智能相似度分析功能"""
        print("\n=== 测试6: 智能相似度分析功能 ===")
        
        # 不同相似度水平测试
        test_cases = [
            {"max_similarity": 85, "expected_risk": "高", "expected_text": "相似度过高"},
            {"max_similarity": 65, "expected_risk": "中", "expected_text": "相似度较高"},
            {"max_similarity": 30, "expected_risk": "低", "expected_text": "安全范围内"}
        ]
        
        for i, test_case in enumerate(test_cases):
            test_data = {
                "originality": 80,
                "similarity": {"max": test_case["max_similarity"], "avg": test_case["max_similarity"] * 0.6},
                "risk_level": "medium"
            }
            
            result = await self.expert.analyze_copyright(test_data)
            
            # 验证相似度风险评估 - 检查是否包含预期的文本
            similarity_insights = [insight for insight in result.insights 
                                  if test_case["expected_text"] in insight]
            assert len(similarity_insights) > 0, f"相似度{test_case['max_similarity']}%应包含文本'{test_case['expected_text']}'"
            
            print(f"   案例{i+1}: {test_case['max_similarity']}% -> {test_case['expected_risk']}风险 ({test_case['expected_text']}) ✓")
        
        print("✅ 智能相似度分析测试通过")
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始ContentCopyrightExpert生产级增强功能测试")
        print("=" * 60)
        
        try:
            await self.test_production_copyright_analysis()
            await self.test_intelligent_trend_analysis()
            await self.test_strategy_optimization()
            await self.test_real_time_monitoring()
            await self.test_intelligent_originality_analysis()
            await self.test_intelligent_similarity_analysis()
            
            print("\n" + "=" * 60)
            print("🎉 所有测试用例通过！ContentCopyrightExpert生产级增强功能验证成功")
            print("📊 增强功能包括：")
            print("   • 智能原创性分析（优秀/良好/一般/不足分级）")
            print("   • 智能相似度分析（高/中/低风险评估）")
            print("   • 智能版权风险评估（综合评分系统）")
            print("   • 实时版权监控预警（高风险自动检测）")
            print("   • 智能版权趋势分析（历史数据趋势预测）")
            print("   • 智能版权策略优化（目标导向优化方案）")
            print("   • 生产级配置管理（风险阈值、监控配置、优化策略）")
            print("   • 版权历史记录（分析历史追踪管理）")
            
            return True
            
        except Exception as e:
            print(f"\n❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()
            return False


async def main():
    """主测试函数"""
    tester = TestContentCopyrightEnhanced()
    success = await tester.run_all_tests()
    
    if success:
        print("\n✅ ContentCopyrightExpert生产级增强功能测试完成")
        sys.exit(0)
    else:
        print("\n❌ ContentCopyrightExpert生产级增强功能测试失败")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())