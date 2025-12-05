#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
运营财务专家测试套件

测试覆盖以下10个专家类：
1. OperationsAnalysisExpert (T009-1) - 运营分析专家
2. UserAnalysisExpert (T009-2) - 用户分析专家  
3. ActivityExpert (T009-3) - 活动专家
4. ChannelExpert (T009-4) - 渠道专家
5. FinanceAccountingExpert (T009-5) - 财务核算专家
6. CostManagementExpert (T009-6) - 成本管理专家
7. BudgetExpert (T009-7) - 预算管理专家
8. ReportExpert (T009-8) - 报表专家
9. TaxExpert (T009-9) - 税务专家
10. RiskControlExpert (T009-10) - 风控专家
"""

import pytest
import asyncio
from typing import Dict, Any
from operations_finance_experts import (
    OperationsAnalysisExpert,
    UserAnalysisExpert,
    ActivityExpert,
    ChannelExpert,
    FinanceAccountingExpert,
    CostManagementExpert,
    BudgetExpert,
    ReportExpert,
    TaxExpert,
    RiskControlExpert,
    OperationsFinanceStage,
    OperationsFinanceAnalysis
)


class TestOperationsAnalysisExpert:
    """运营分析专家测试"""
    
    def setup_method(self):
        """测试前准备"""
        self.expert = OperationsAnalysisExpert()
        
    @pytest.mark.asyncio
    async def test_analyze_operations_basic(self):
        """测试基本运营分析"""
        operations_data = {
            "active_users": 15000,
            "total_users": 50000,
            "revenue": 1200000,
            "conversion_rate": 4.5,
            "efficiency": 0.85,
            "cost_per_acquisition": 75,
            "user_satisfaction": 88,
            "service_quality": 0.92,
            "complaint_rate": 0.8,
            "growth_rate": 18,
            "new_users": 2000,
            "revenue_growth": 22,
            "uptime": 99.95,
            "churn_rate": 4.5,
            "stability_index": 0.94,
            "innovation_index": 0.78,
            "new_features": 6,
            "improvement_rate": 12
        }
        
        result = await self.expert.analyze_operations(operations_data)
        
        # 验证结果结构
        assert isinstance(result, OperationsFinanceAnalysis)
        assert result.stage == OperationsFinanceStage.OPERATIONS
        assert 0 <= result.confidence <= 1
        assert 0 <= result.score <= 100
        assert isinstance(result.insights, list)
        assert isinstance(result.recommendations, list)
        assert isinstance(result.metadata, dict)
        
        # 验证具体分析结果
        assert len(result.insights) > 0
        assert "活跃用户数" in " ".join(result.insights)
        assert "营收规模" in " ".join(result.insights)
        
    @pytest.mark.asyncio
    async def test_analyze_operations_empty_data(self):
        """测试空数据运营分析"""
        operations_data = {}
        
        result = await self.expert.analyze_operations(operations_data)
        
        assert isinstance(result, OperationsFinanceAnalysis)
        assert result.score >= 0
        assert result.confidence >= 0
        
    @pytest.mark.asyncio
    async def test_forecast_operations_trend(self):
        """测试运营趋势预测"""
        historical_data = {
            "active_users": [10000, 12000, 15000],
            "revenue": [800000, 1000000, 1200000],
            "growth_rate": [15, 20, 18]
        }
        
        result = await self.expert.forecast_operations_trend(historical_data)
        
        assert isinstance(result, dict)
        assert "trend" in result
        assert "confidence" in result
        assert "forecast_period" in result
        
    @pytest.mark.asyncio
    async def test_optimize_operations_strategy(self):
        """测试运营策略优化"""
        current_data = {
            "active_users": 15000,
            "conversion_rate": 4.5,
            "cost_per_acquisition": 75
        }
        
        result = await self.expert.optimize_operations_strategy(current_data)
        
        assert isinstance(result, dict)
        assert "optimization_areas" in result
        assert "expected_improvement" in result


class TestUserAnalysisExpert:
    """用户分析专家测试"""
    
    def setup_method(self):
        """测试前准备"""
        self.expert = UserAnalysisExpert()
        
    @pytest.mark.asyncio
    async def test_analyze_users_basic(self):
        """测试基本用户分析"""
        user_data = {
            "total_users": 50000,
            "new_users": 2000,
            "active_users": 15000,
            "retention_rate": 65,
            "churn_rate": 8,
            "user_satisfaction": 85,
            "arpu": 120,
            "ltv": 1500,
            "conversion_rate": 3.5,
            "loyalty_score": 0.82,
            "engagement_rate": 0.45,
            "growth_potential": 0.75
        }
        
        result = await self.expert.analyze_users(user_data)
        
        # 验证结果结构
        assert isinstance(result, OperationsFinanceAnalysis)
        assert result.stage == OperationsFinanceStage.USER
        assert 0 <= result.confidence <= 1
        assert 0 <= result.score <= 100
        
        # 验证具体分析结果
        assert len(result.insights) > 0
        assert "总用户数" in " ".join(result.insights)
        assert "ARPU" in " ".join(result.insights)
        
    @pytest.mark.asyncio
    async def test_analyze_users_empty_data(self):
        """测试空数据用户分析"""
        user_data = {}
        
        result = await self.expert.analyze_users(user_data)
        
        assert isinstance(result, OperationsFinanceAnalysis)
        assert result.score >= 0
        assert result.confidence >= 0


class TestActivityExpert:
    """活动专家测试"""
    
    def setup_method(self):
        """测试前准备"""
        self.expert = ActivityExpert()
        
    @pytest.mark.asyncio
    async def test_analyze_activity_basic(self):
        """测试基本活动分析"""
        activity_data = {
            "total_participants": 5000,
            "new_users": 800,
            "engagement_rate": 0.75,
            "conversion_rate": 5.2,
            "roi": 3.5,
            "cost_per_participant": 25,
            "satisfaction_score": 4.2,
            "effectiveness_score": 0.88
        }
        
        result = await self.expert.analyze_activity(activity_data)
        
        # 验证结果结构
        assert isinstance(result, OperationsFinanceAnalysis)
        assert result.stage == OperationsFinanceStage.ACTIVITY
        assert 0 <= result.confidence <= 1
        assert 0 <= result.score <= 100
        
    @pytest.mark.asyncio
    async def test_analyze_activity_performance(self):
        """测试活动性能分析功能"""
        activity_data = {
            "participation_rate": 0.65,
            "roi": 1.8,
            "impact_score": 0.75,
            "engagement_level": 0.7,
            "cost_efficiency": 1.2
        }
        result = await self.expert.analyze_activity(activity_data)
        
        assert isinstance(result, OperationsFinanceAnalysis)
        assert result.score >= 0
        assert result.score <= 100
        assert isinstance(result.insights, list)
        assert isinstance(result.recommendations, list)


class TestChannelExpert:
    """渠道专家测试"""
    
    def setup_method(self):
        """测试前准备"""
        self.expert = ChannelExpert()
        
    @pytest.mark.asyncio
    async def test_analyze_channel_basic(self):
        """测试基本渠道分析"""
        channel_data = {
            "wechat": {"users": 20000, "conversion": 4.5, "cost": 60},
            "weibo": {"users": 8000, "conversion": 3.2, "cost": 45},
            "douyin": {"users": 12000, "conversion": 5.8, "cost": 75},
            "total_users": 40000,
            "total_conversion": 4.3,
            "total_cost": 180000
        }
        
        result = await self.expert.analyze_channel(channel_data)
        
        # 验证结果结构
        assert isinstance(result, OperationsFinanceAnalysis)
        assert result.stage == OperationsFinanceStage.CHANNEL
        assert 0 <= result.confidence <= 1
        assert 0 <= result.score <= 100
        
    @pytest.mark.asyncio
    async def test_analyze_channel_performance(self):
        """测试渠道性能分析功能"""
        channel_data = {
            "channel_name": "电商渠道",
            "budget": 500000,
            "conversion_rate": 0.12,
            "customer_acquisition_cost": 150,
            "roi": 2.5
        }
        result = await self.expert.analyze_channel(channel_data)
        
        assert isinstance(result, OperationsFinanceAnalysis)
        assert result.score >= 0
        assert result.score <= 100
        assert isinstance(result.insights, list)
        assert isinstance(result.recommendations, list)


class TestFinanceAccountingExpert:
    """财务核算专家测试"""
    
    def setup_method(self):
        """测试前准备"""
        self.expert = FinanceAccountingExpert()
        
    @pytest.mark.asyncio
    async def test_analyze_accounting_basic(self):
        """测试基本财务核算分析"""
        accounting_data = {
            "revenue": 1500000,
            "expenses": 1200000,
            "profit": 300000,
            "assets": 5000000,
            "liabilities": 2000000,
            "equity": 3000000,
            "cash_flow": 250000,
            "debt_ratio": 0.4
        }
        
        result = await self.expert.analyze_accounting(accounting_data)
        
        # 验证结果结构
        assert isinstance(result, OperationsFinanceAnalysis)
        assert result.stage == OperationsFinanceStage.ACCOUNTING
        assert 0 <= result.confidence <= 1
        assert 0 <= result.score <= 100
        
    @pytest.mark.asyncio
    async def test_analyze_accounting_quality(self):
        """测试会计核算质量分析功能"""
        accounting_data = {
            "accuracy": 95.5,
            "timeliness": 98.0,
            "completeness": 92.0,
            "consistency": 96.0,
            "automation_rate": 85.0,
            "processing_time": 18.0
        }
        
        result = await self.expert.analyze_accounting(accounting_data)
        
        assert isinstance(result, OperationsFinanceAnalysis)
        assert result.score >= 0
        assert result.score <= 100
        assert isinstance(result.insights, list)
        assert isinstance(result.recommendations, list)


class TestCostManagementExpert:
    """成本管理专家测试"""
    
    def setup_method(self):
        """测试前准备"""
        self.expert = CostManagementExpert()
        
    @pytest.mark.asyncio
    async def test_analyze_cost_basic(self):
        """测试基本成本分析"""
        cost_data = {
            "material_costs": 400000,
            "labor_costs": 300000,
            "overhead_costs": 200000,
            "marketing_costs": 150000,
            "total_costs": 1050000,
            "cost_efficiency": 0.85,
            "cost_reduction_potential": 0.15
        }
        
        result = await self.expert.analyze_cost(cost_data)
        
        # 验证结果结构
        assert isinstance(result, OperationsFinanceAnalysis)
        assert result.stage == OperationsFinanceStage.COST
        assert 0 <= result.confidence <= 1
        assert 0 <= result.score <= 100
        
    @pytest.mark.asyncio
    async def test_analyze_cost_efficiency(self):
        """测试成本效率分析功能"""
        cost_data = {
            "cost_structure": {
                "原材料": 0.35,
                "人工": 0.25,
                "制造费用": 0.20,
                "管理费用": 0.15,
                "销售费用": 0.05
            },
            "cost_control": 88.5,
            "budget_variance": -2.3,
            "cost_efficiency": 1.35,
            "cost_trend": "stable"
        }
        result = await self.expert.analyze_cost(cost_data)
        
        assert isinstance(result, OperationsFinanceAnalysis)
        assert result.score >= 0
        assert result.score <= 100
        assert isinstance(result.insights, list)
        assert isinstance(result.recommendations, list)


class TestBudgetExpert:
    """预算专家测试"""
    
    def setup_method(self):
        """测试前准备"""
        self.expert = BudgetExpert()
        
    @pytest.mark.asyncio
    async def test_analyze_budget_basic(self):
        """测试基本预算分析"""
        budget_data = {
            "planned_budget": 1000000,
            "actual_spending": 950000,
            "variance": -50000,
            "variance_percentage": -5.0
        }
        
        result = await self.expert.analyze_budget(budget_data)
        
        # 验证结果结构
        assert isinstance(result, OperationsFinanceAnalysis)
        assert result.stage == OperationsFinanceStage.BUDGET
        assert 0 <= result.confidence <= 1
        assert 0 <= result.score <= 100
        
    @pytest.mark.asyncio
    async def test_analyze_budget_performance(self):
        """测试预算执行情况分析功能"""
        budget_data = {
            "planned_budget": 5000000,
            "actual_spending": 4800000,
            "variance": -200000,
            "variance_percentage": -4.0,
            "budget_categories": {
                "研发": 1500000,
                "营销": 1200000,
                "运营": 1000000,
                "行政": 800000,
                "其他": 500000
            }
        }
        result = await self.expert.analyze_budget(budget_data)
        
        assert isinstance(result, OperationsFinanceAnalysis)
        assert result.score >= 0
        assert result.score <= 100
        assert isinstance(result.insights, list)
        assert isinstance(result.recommendations, list)


class TestReportExpert:
    """报表专家测试"""
    
    def setup_method(self):
        """测试前准备"""
        self.expert = ReportExpert()
        
    @pytest.mark.asyncio
    async def test_analyze_report_basic(self):
        """测试基本报表分析"""
        report_data = {
            "completeness": 0.95,
            "accuracy": 0.92,
            "timeliness": 0.88,
            "consistency": 0.90,
            "relevance": 0.85,
            "report_quality_score": 0.90
        }
        
        result = await self.expert.analyze_report(report_data)
        
        # 验证结果结构
        assert isinstance(result, OperationsFinanceAnalysis)
        assert result.stage == OperationsFinanceStage.REPORT
        assert 0 <= result.confidence <= 1
        assert 0 <= result.score <= 100
        
    @pytest.mark.asyncio
    async def test_analyze_report_quality(self):
        """测试报表质量分析功能"""
        report_data = {
            "completeness": 92.0,
            "accuracy": 95.5,
            "timeliness": 88.0,
            "consistency": 90.0,
            "clarity": 85.0,
            "actionability": 80.0
        }
        result = await self.expert.analyze_report(report_data)
        
        assert isinstance(result, OperationsFinanceAnalysis)
        assert result.score >= 0
        assert result.score <= 100
        assert isinstance(result.insights, list)
        assert isinstance(result.recommendations, list)


class TestTaxExpert:
    """税务专家测试"""
    
    def setup_method(self):
        """测试前准备"""
        self.expert = TaxExpert()
        
    @pytest.mark.asyncio
    async def test_analyze_tax_basic(self):
        """测试基本税务分析"""
        tax_data = {
            "income_tax": 150000,
            "vat": 80000,
            "business_tax": 20000,
            "total_tax_liability": 250000,
            "tax_efficiency": 0.75,
            "compliance_score": 0.92
        }
        
        result = await self.expert.analyze_tax(tax_data)
        
        # 验证结果结构
        assert isinstance(result, OperationsFinanceAnalysis)
        assert result.stage == OperationsFinanceStage.TAX
        assert 0 <= result.confidence <= 1
        assert 0 <= result.score <= 100
        
    @pytest.mark.asyncio
    async def test_analyze_tax_compliance(self):
        """测试税务合规性分析功能"""
        tax_data = {
            "compliance_score": 88.0,
            "risk_level": "medium",
            "optimization_potential": 75.0,
            "efficiency_score": 82.0,
            "strategic_alignment": 85.0,
            "sustainability": 80.0
        }
        result = await self.expert.analyze_tax(tax_data)
        
        assert isinstance(result, OperationsFinanceAnalysis)
        assert result.score >= 0
        assert result.score <= 100
        assert isinstance(result.insights, list)
        assert isinstance(result.recommendations, list)


class TestRiskControlExpert:
    """风控专家测试"""
    
    def setup_method(self):
        """测试前准备"""
        self.expert = RiskControlExpert()
        
    @pytest.mark.asyncio
    async def test_analyze_risk_basic(self):
        """测试基本风险分析"""
        risk_data = {
            "market_risk": 0.25,
            "credit_risk": 0.15,
            "operational_risk": 0.20,
            "liquidity_risk": 0.10,
            "overall_risk_score": 0.18,
            "risk_exposure": 500000
        }
        
        result = await self.expert.analyze_risk(risk_data)
        
        # 验证结果结构
        assert isinstance(result, OperationsFinanceAnalysis)
        assert result.stage == OperationsFinanceStage.RISK
        assert 0 <= result.confidence <= 1
        assert 0 <= result.score <= 100
        
    @pytest.mark.asyncio
    async def test_analyze_risk_level(self):
        """测试风险水平分析功能"""
        risk_data = {
            "liquidity_ratio": 2.1,
            "debt_ratio": 45.0,
            "internal_control_score": 85,
            "market_volatility": "medium",
            "credit_risk": "low",
            "operational_risk": "medium"
        }
        result = await self.expert.analyze_risk(risk_data)
        
        assert isinstance(result, OperationsFinanceAnalysis)
        assert result.score >= 0
        assert result.score <= 100
        assert isinstance(result.insights, list)
        assert isinstance(result.recommendations, list)


class TestOperationsFinanceIntegration:
    """运营财务专家集成测试"""
    
    def setup_method(self):
        """测试前准备"""
        self.experts = {
            "operations": OperationsAnalysisExpert(),
            "user": UserAnalysisExpert(),
            "activity": ActivityExpert(),
            "channel": ChannelExpert(),
            "accounting": FinanceAccountingExpert(),
            "cost": CostManagementExpert(),
            "budget": BudgetExpert(),
            "report": ReportExpert(),
            "tax": TaxExpert(),
            "risk": RiskControlExpert()
        }
        
    @pytest.mark.asyncio
    async def test_all_experts_integration(self):
        """测试所有专家集成分析"""
        # 模拟综合业务数据
        business_data = {
            "operations": {
                "active_users": 15000,
                "revenue": 1200000,
                "conversion_rate": 4.5
            },
            "users": {
                "total_users": 50000,
                "retention_rate": 65,
                "arpu": 120
            },
            "finance": {
                "profit": 300000,
                "assets": 5000000,
                "tax_liability": 250000
            }
        }
        
        # 根据专家类型调用对应的分析方法
        tasks = []
        for expert_name, expert in self.experts.items():
            if expert_name in business_data:
                if expert_name == "operations":
                    tasks.append(expert.analyze_operations(business_data[expert_name]))
                elif expert_name == "users":
                    tasks.append(expert.analyze_users(business_data[expert_name]))
                elif expert_name == "activity":
                    tasks.append(expert.analyze_activity(business_data[expert_name]))
                elif expert_name == "channel":
                    tasks.append(expert.analyze_channel(business_data[expert_name]))
                elif expert_name == "accounting":
                    tasks.append(expert.analyze_accounting(business_data[expert_name]))
                elif expert_name == "cost":
                    tasks.append(expert.analyze_cost(business_data[expert_name]))
                elif expert_name == "budget":
                    tasks.append(expert.analyze_budget(business_data[expert_name]))
                elif expert_name == "report":
                    tasks.append(expert.analyze_report(business_data[expert_name]))
                elif expert_name == "tax":
                    tasks.append(expert.analyze_tax(business_data[expert_name]))
                elif expert_name == "risk":
                    tasks.append(expert.analyze_risk(business_data[expert_name]))
        
        results = await asyncio.gather(*tasks)
        
        # 验证所有专家都返回了有效结果
        assert len(results) > 0
        for result in results:
            assert isinstance(result, OperationsFinanceAnalysis)
            assert result.score >= 0
            assert result.confidence >= 0


if __name__ == "__main__":
    # 运行所有测试
    pytest.main([__file__, "-v", "--tb=short"])