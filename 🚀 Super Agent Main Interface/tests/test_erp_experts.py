#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ERP专家模块集成测试
测试ERP专家系统的功能完整性和API接口
"""

import pytest
import asyncio
from datetime import datetime
from typing import Dict, Any

# 导入ERP专家模块
from core.experts import (
    ERPDimension, ERPAnalysis, ERPDataConnector,
    QualityExpert, CostExpert, DeliveryExpert, SafetyExpert,
    ProfitExpert, EfficiencyExpert, ManagementExpert, TechnologyExpert,
    QualityImprovementExpert, CostOptimizationExpert, DeliveryResilienceExpert,
    SafetyComplianceExpert, ProfitGrowthExpert, EfficiencyAutomationExpert,
    TechnologyInnovationExpert, ERPProcessExpert, ERPExpertCollaboration,
    get_erp_experts
)


class TestERPDataConnector:
    """ERP数据连接器测试"""
    
    def setup_method(self):
        self.connector = ERPDataConnector({"timeout": 30, "max_retries": 3})
    
    @pytest.mark.asyncio
    async def test_connect_to_sap_system(self):
        """测试SAP系统连接"""
        result = await self.connector.connect_to_erp_system("sap")
        assert result is True
        assert "sap" in self.connector.connection_pool
    
    @pytest.mark.asyncio
    async def test_fetch_quality_data(self):
        """测试获取质量数据"""
        data = await self.connector.fetch_quality_data("sap", "monthly")
        assert isinstance(data, dict)
        assert "defect_rate" in data
        assert "cpk" in data
        assert data["data_source"] == "sap"
    
    @pytest.mark.asyncio
    async def test_fetch_cost_data(self):
        """测试获取成本数据"""
        data = await self.connector.fetch_cost_data("oracle", "quarterly")
        assert isinstance(data, dict)
        assert "material_cost" in data
        assert "labor_cost" in data
        assert data["data_source"] == "oracle"
    
    def test_get_connection_status(self):
        """测试获取连接状态"""
        status = self.connector.get_connection_status()
        assert isinstance(status, dict)
        assert "connected_systems" in status
        assert "total_connections" in status


class TestQualityExpert:
    """质量专家测试"""
    
    def setup_method(self):
        self.expert = QualityExpert()
    
    @pytest.mark.asyncio
    async def test_analyze_quality_basic(self):
        """测试基础质量分析"""
        quality_data = {
            "defect_rate": 2.5,
            "total_produced": 10000,
            "total_defects": 250,
            "cpk": 1.45
        }
        
        result = await self.expert.analyze_quality(quality_data)
        
        assert isinstance(result, ERPAnalysis)
        assert result.dimension == ERPDimension.QUALITY
        assert 0 <= result.score <= 100
        assert len(result.insights) > 0
        assert isinstance(result.recommendations, list)
    
    @pytest.mark.asyncio
    async def test_analyze_quality_with_trend(self):
        """测试带趋势的质量分析"""
        quality_data = {
            "defect_rate": 3.0,
            "total_produced": 8000,
            "total_defects": 240,
            "cpk": 1.2,
            "historical_defect_rates": [3.5, 3.2, 3.0, 3.1, 2.9, 3.0]
        }
        
        result = await self.expert.analyze_quality(quality_data)
        
        assert "质量趋势" in " ".join(result.insights)
        assert result.score > 0


class TestCostExpert:
    """成本专家测试"""
    
    def setup_method(self):
        self.expert = CostExpert()
    
    @pytest.mark.asyncio
    async def test_analyze_cost_basic(self):
        """测试基础成本分析"""
        cost_data = {
            "material_cost": 500000,
            "labor_cost": 200000,
            "overhead_cost": 100000,
            "cost_efficiency": 7.5
        }
        
        result = await self.expert.analyze_cost(cost_data)
        
        assert isinstance(result, ERPAnalysis)
        assert result.dimension == ERPDimension.COST
        assert 0 <= result.score <= 100
        assert any("成本结构" in insight for insight in result.insights)
    
    @pytest.mark.asyncio
    async def test_get_cost_breakdown(self):
        """测试成本分解分析"""
        # 先执行一次分析以生成历史数据
        cost_data = {
            "material_cost": 500000,
            "labor_cost": 200000,
            "overhead_cost": 100000
        }
        await self.expert.analyze_cost(cost_data)
        
        # 获取分解数据
        breakdown = await self.expert.get_cost_breakdown()
        
        assert isinstance(breakdown, dict)
        assert "total_cost" in breakdown
        assert "material_ratio" in breakdown


class TestDeliveryExpert:
    """交期专家测试"""
    
    def setup_method(self):
        self.expert = DeliveryExpert()
    
    @pytest.mark.asyncio
    async def test_analyze_delivery_basic(self):
        """测试基础交期分析"""
        delivery_data = {
            "on_time_delivery": 920,
            "total_orders": 1000,
            "avg_delivery_days": 15.2,
            "supply_risk_index": 0.3
        }
        
        result = await self.expert.analyze_delivery(delivery_data)
        
        assert isinstance(result, ERPAnalysis)
        assert result.dimension == ERPDimension.DELIVERY
        assert 0 <= result.score <= 100
        assert any("准时交付率" in insight for insight in result.insights)


class TestERPExpertCollaboration:
    """ERP专家协作测试"""
    
    def setup_method(self):
        self.collaboration = ERPExpertCollaboration()
    
    @pytest.mark.asyncio
    async def test_collaborative_analysis_single_dimension(self):
        """测试单维度协作分析"""
        business_data = {
            "quality": {
                "defect_rate": 2.5,
                "total_produced": 10000,
                "total_defects": 250,
                "cpk": 1.45
            }
        }
        
        result = await self.collaboration.collaborative_analysis(
            business_data, [ERPDimension.QUALITY]
        )
        
        assert isinstance(result, dict)
        assert "overall_score" in result
        assert "dimension_analyses" in result
        assert len(result["dimension_analyses"]) == 1
        assert result["dimension_analyses"][0]["dimension"] == "quality"
    
    @pytest.mark.asyncio
    async def test_collaborative_analysis_multiple_dimensions(self):
        """测试多维度协作分析"""
        business_data = {
            "quality": {
                "defect_rate": 2.5,
                "total_produced": 10000,
                "total_defects": 250,
                "cpk": 1.45
            },
            "cost": {
                "material_cost": 500000,
                "labor_cost": 200000,
                "overhead_cost": 100000,
                "cost_efficiency": 7.5
            },
            "delivery": {
                "on_time_delivery": 920,
                "total_orders": 1000,
                "avg_delivery_days": 15.2
            }
        }
        
        result = await self.collaboration.collaborative_analysis(
            business_data, [ERPDimension.QUALITY, ERPDimension.COST, ERPDimension.DELIVERY]
        )
        
        assert isinstance(result, dict)
        assert "overall_score" in result
        assert "dimension_analyses" in result
        assert len(result["dimension_analyses"]) == 3
        assert "comprehensive_insights" in result
        assert "priority_recommendations" in result
    
    @pytest.mark.asyncio
    async def test_get_collaboration_dashboard(self):
        """测试获取协作仪表板"""
        # 先执行一次协作分析以生成数据
        business_data = {
            "quality": {
                "defect_rate": 2.5,
                "total_produced": 10000,
                "total_defects": 250
            }
        }
        await self.collaboration.collaborative_analysis(
            business_data, [ERPDimension.QUALITY]
        )
        
        # 获取仪表板数据
        dashboard = await self.collaboration.get_collaboration_dashboard()
        
        assert isinstance(dashboard, dict)
        assert "total_collaborations" in dashboard
        assert dashboard["total_collaborations"] > 0
    
    def test_get_expert_list(self):
        """测试获取专家列表"""
        experts = self.collaboration.get_expert_list()
        
        assert isinstance(experts, list)
        assert len(experts) > 0
        
        # 检查专家信息结构
        for expert in experts:
            assert "expert_id" in expert
            assert "name" in expert
            assert "dimension" in expert


class TestERPIntegration:
    """ERP集成测试"""
    
    def test_get_erp_experts(self):
        """测试获取所有ERP专家"""
        experts = get_erp_experts()
        
        assert isinstance(experts, dict)
        assert len(experts) == 16  # 16个专家
        
        # 检查关键专家是否存在
        expected_experts = [
            "quality_expert", "cost_expert", "delivery_expert",
            "safety_expert", "profit_expert", "efficiency_expert",
            "management_expert", "technology_expert"
        ]
        
        for expert_key in expected_experts:
            assert expert_key in experts
    
    @pytest.mark.asyncio
    async def test_expert_performance(self):
        """测试专家性能（SLO要求：2秒内完成）"""
        quality_expert = QualityExpert()
        quality_data = {
            "defect_rate": 2.5,
            "total_produced": 10000,
            "total_defects": 250,
            "cpk": 1.45
        }
        
        start_time = asyncio.get_event_loop().time()
        result = await quality_expert.analyze_quality(quality_data)
        end_time = asyncio.get_event_loop().time()
        
        execution_time = end_time - start_time
        
        assert execution_time < 2.0, f"专家分析耗时{execution_time:.2f}秒，超过2秒SLO要求"
        assert isinstance(result, ERPAnalysis)
        assert result.score > 0


class TestERPDimensionEnum:
    """ERP维度枚举测试"""
    
    def test_dimension_values(self):
        """测试维度枚举值"""
        assert ERPDimension.QUALITY.value == "quality"
        assert ERPDimension.COST.value == "cost"
        assert ERPDimension.DELIVERY.value == "delivery"
        assert ERPDimension.SAFETY.value == "safety"
        assert ERPDimension.PROFIT.value == "profit"
        assert ERPDimension.EFFICIENCY.value == "efficiency"
        assert ERPDimension.MANAGEMENT.value == "management"
        assert ERPDimension.TECHNOLOGY.value == "technology"
    
    def test_dimension_count(self):
        """测试维度数量"""
        dimensions = list(ERPDimension)
        assert len(dimensions) == 8


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])