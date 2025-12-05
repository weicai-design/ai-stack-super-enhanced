"""
趋势分析专家模块集成测试

测试趋势分析模块的6个专家类及其增强功能：
1. 趋势采集专家 (T007-1)
2. 趋势处理专家 (T007-2) 
3. 趋势分析专家 (T007-3)
4. 趋势预测专家 (T007-4)
5. 趋势报告专家 (T007-5)
6. 趋势预警专家 (T007-6)

测试功能包括：
- 数据连接器功能
- 实时数据采集
- 多平台数据集成
- 专家协作
- 性能监控
"""

import pytest
import asyncio
import time
from typing import Dict, Any
import sys
import os

# 添加模块路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.experts.trend_experts import (
    TrendDataConnector,
    TrendCollectionExpert,
    TrendProcessingExpert,
    TrendAnalysisExpert,
    TrendPredictionExpert,
    TrendReportExpert,
    TrendAlertExpert,
    get_trend_experts,
    TrendStage
)


class TestTrendDataConnector:
    """测试趋势数据连接器"""
    
    def setup_method(self):
        """测试前初始化"""
        self.connector = TrendDataConnector()
    
    def test_initialization(self):
        """测试连接器初始化"""
        assert self.connector is not None
        assert hasattr(self.connector, 'platforms')
        assert len(self.connector.platforms) == 5
    
    def test_get_connection_status(self):
        """测试获取连接状态"""
        status = self.connector.get_connection_status()
        assert isinstance(status, dict)
        assert len(status) == 5
        
        for platform in ['financial', 'social_media', 'news', 'market', 'research']:
            assert platform in status
            assert 'status' in status[platform]
            assert 'last_connected' in status[platform]
    
    @pytest.mark.asyncio
    async def test_get_trend_data(self):
        """测试获取趋势数据"""
        for platform in ['financial', 'social_media']:
            data = await self.connector.get_trend_data(platform, '2024-01-01', '2024-01-31')
            assert isinstance(data, dict)
            assert 'data_count' in data
            assert 'trend_count' in data
            assert 'platform' in data
    
    @pytest.mark.asyncio
    async def test_get_real_time_data(self):
        """测试获取实时数据"""
        for platform in ['financial', 'news']:
            data = await self.connector.get_real_time_data(platform)
            assert isinstance(data, dict)
            assert 'data_count' in data
            assert 'volatility' in data
            assert 'anomaly_count' in data
    
    def test_get_connection_history(self):
        """测试获取连接历史"""
        history = self.connector.get_connection_history()
        assert isinstance(history, list)
        assert len(history) <= 100  # 历史记录上限


class TestTrendCollectionExpert:
    """测试趋势采集专家"""
    
    def setup_method(self):
        """测试前初始化"""
        self.connector = TrendDataConnector()
        self.expert = TrendCollectionExpert(self.connector)
    
    @pytest.mark.asyncio
    async def test_analyze_collection(self):
        """测试采集分析"""
        test_data = {
            "start_date": "2024-01-01",
            "end_date": "2024-01-31",
            "data_volume": 1000
        }
        
        result = await self.expert.analyze(test_data)
        
        assert result.stage == TrendStage.COLLECTION
        assert 0 <= result.confidence <= 1
        assert 0 <= result.accuracy <= 100
        assert isinstance(result.insights, list)
        assert isinstance(result.recommendations, list)
        assert isinstance(result.metadata, dict)
    
    @pytest.mark.asyncio
    async def test_get_collection_dashboard(self):
        """测试获取采集仪表板"""
        # 先执行一次分析
        test_data = {"data_volume": 500}
        await self.expert.analyze(test_data)
        
        dashboard = self.expert.get_collection_dashboard()
        
        assert isinstance(dashboard, dict)
        assert dashboard['expert_id'] == self.expert.expert_id
        assert dashboard['expert_name'] == self.expert.expert_name
        assert dashboard['total_analyses'] >= 1
        assert 'avg_data_quality' in dashboard


class TestTrendProcessingExpert:
    """测试趋势处理专家"""
    
    def setup_method(self):
        """测试前初始化"""
        self.connector = TrendDataConnector()
        self.expert = TrendProcessingExpert(self.connector)
    
    @pytest.mark.asyncio
    async def test_analyze_processing(self):
        """测试处理分析"""
        test_data = {
            "data_diversity": 0.8,
            "data_quality": 0.9,
            "processing_efficiency": 0.7
        }
        
        result = await self.expert.analyze(test_data)
        
        assert result.stage == TrendStage.PROCESSING
        assert 0 <= result.confidence <= 1
        assert 0 <= result.accuracy <= 100
        assert isinstance(result.insights, list)
        assert isinstance(result.recommendations, list)
    
    @pytest.mark.asyncio
    async def test_process_trend_data(self):
        """测试数据处理"""
        raw_data = {
            "trends": [
                {"id": 1, "value": 100, "timestamp": "2024-01-01"},
                {"id": 2, "value": 150, "timestamp": "2024-01-02"}
            ]
        }
        
        processed_data = await self.expert.process_trend_data(raw_data)
        
        assert isinstance(processed_data, dict)
        assert 'cleaned_data' in processed_data
        assert 'standardized_data' in processed_data
        assert 'features' in processed_data
    
    @pytest.mark.asyncio
    async def test_get_processing_dashboard(self):
        """测试获取处理仪表板"""
        # 先执行一次分析
        test_data = {"data_diversity": 0.7}
        await self.expert.analyze(test_data)
        
        dashboard = self.expert.get_processing_dashboard()
        
        assert isinstance(dashboard, dict)
        assert dashboard['expert_id'] == self.expert.expert_id
        assert dashboard['expert_name'] == self.expert.expert_name
        assert dashboard['total_analyses'] >= 1


class TestTrendAnalysisExpert:
    """测试趋势分析专家"""
    
    def setup_method(self):
        """测试前初始化"""
        self.connector = TrendDataConnector()
        self.expert = TrendAnalysisExpert(self.connector)
    
    @pytest.mark.asyncio
    async def test_analyze_trends(self):
        """测试趋势分析"""
        test_data = {
            "trends": [
                {"id": 1, "strength": 0.8, "direction": "up"},
                {"id": 2, "strength": 0.6, "direction": "down"}
            ],
            "patterns": [
                {"id": 1, "confidence": 0.9, "type": "seasonal"}
            ]
        }
        
        result = await self.expert.analyze(test_data)
        
        assert result.stage == TrendStage.ANALYSIS
        assert 0 <= result.confidence <= 1
        assert 0 <= result.accuracy <= 100
        assert isinstance(result.insights, list)
    
    @pytest.mark.asyncio
    async def test_analyze_trend_patterns(self):
        """测试趋势模式分析"""
        analysis_data = {
            "trends": [
                {"id": 1, "values": [1, 2, 3, 4, 5]},
                {"id": 2, "values": [5, 4, 3, 2, 1]}
            ]
        }
        
        patterns = await self.expert.analyze_trend_patterns(analysis_data)
        
        assert isinstance(patterns, dict)
        assert 'identified_trends' in patterns
        assert 'discovered_patterns' in patterns
        assert 'correlation_analysis' in patterns
    
    @pytest.mark.asyncio
    async def test_get_analysis_dashboard(self):
        """测试获取分析仪表板"""
        # 先执行一次分析
        test_data = {"trends": [{"id": 1, "strength": 0.7}]}
        await self.expert.analyze(test_data)
        
        dashboard = self.expert.get_analysis_dashboard()
        
        assert isinstance(dashboard, dict)
        assert dashboard['expert_id'] == self.expert.expert_id
        assert dashboard['expert_name'] == self.expert.expert_name
        assert dashboard['total_analyses'] >= 1


class TestTrendPredictionExpert:
    """测试趋势预测专家"""
    
    def setup_method(self):
        """测试前初始化"""
        self.connector = TrendDataConnector()
        self.expert = TrendPredictionExpert(self.connector)
    
    @pytest.mark.asyncio
    async def test_analyze_prediction(self):
        """测试预测分析"""
        test_data = {
            "prediction_accuracy": 0.85,
            "prediction_horizon": 30,
            "model_count": 3
        }
        
        result = await self.expert.analyze(test_data)
        
        assert result.stage == TrendStage.PREDICTION
        assert 0 <= result.confidence <= 1
        assert 0 <= result.accuracy <= 100
        assert isinstance(result.insights, list)
    
    @pytest.mark.asyncio
    async def test_predict_trends(self):
        """测试趋势预测"""
        historical_data = {
            "trends": [
                {"id": 1, "values": [10, 20, 30, 40, 50], "timestamps": [1, 2, 3, 4, 5]}
            ]
        }
        
        predictions = await self.expert.predict_trends(historical_data, periods=3)
        
        assert isinstance(predictions, dict)
        assert 'time_series_predictions' in predictions
        assert 'pattern_predictions' in predictions
        assert 'risk_assessment' in predictions
    
    @pytest.mark.asyncio
    async def test_get_prediction_dashboard(self):
        """测试获取预测仪表板"""
        # 先执行一次分析
        test_data = {"prediction_accuracy": 0.8}
        await self.expert.analyze(test_data)
        
        dashboard = self.expert.get_prediction_dashboard()
        
        assert isinstance(dashboard, dict)
        assert dashboard['expert_id'] == self.expert.expert_id
        assert dashboard['expert_name'] == self.expert.expert_name
        assert dashboard['total_analyses'] >= 1


class TestTrendReportExpert:
    """测试趋势报告专家"""
    
    def setup_method(self):
        """测试前初始化"""
        self.connector = TrendDataConnector()
        self.expert = TrendReportExpert(self.connector)
    
    @pytest.mark.asyncio
    async def test_analyze_report(self):
        """测试报告分析"""
        test_data = {
            "report_quality": 0.8,
            "visualization_quality": 0.7,
            "insight_quality": 0.6
        }
        
        result = await self.expert.analyze(test_data)
        
        assert result.stage == TrendStage.REPORT
        assert 0 <= result.confidence <= 1
        assert 0 <= result.accuracy <= 100
        assert isinstance(result.insights, list)
    
    @pytest.mark.asyncio
    async def test_generate_trend_report(self):
        """测试生成趋势报告"""
        analysis_data = {
            "trends": [{"id": 1, "strength": 0.8}],
            "patterns": [{"id": 1, "confidence": 0.9}],
            "predictions": [{"id": 1, "confidence": 0.85}]
        }
        
        report = await self.expert.generate_trend_report(analysis_data)
        
        assert isinstance(report, dict)
        assert 'report_structure' in report
        assert 'visualizations' in report
        assert 'key_insights' in report
    
    @pytest.mark.asyncio
    async def test_get_report_dashboard(self):
        """测试获取报告仪表板"""
        # 先执行一次分析
        test_data = {"report_quality": 0.7}
        await self.expert.analyze(test_data)
        
        dashboard = self.expert.get_report_dashboard()
        
        assert isinstance(dashboard, dict)
        assert dashboard['expert_id'] == self.expert.expert_id
        assert dashboard['expert_name'] == self.expert.expert_name
        assert dashboard['total_reports'] >= 1


class TestTrendAlertExpert:
    """测试趋势预警专家"""
    
    def setup_method(self):
        """测试前初始化"""
        self.connector = TrendDataConnector()
        self.expert = TrendAlertExpert(self.connector)
    
    @pytest.mark.asyncio
    async def test_analyze_alert(self):
        """测试预警分析"""
        test_data = {
            "alerts": [
                {"id": 1, "level": "high", "message": "高风险预警"},
                {"id": 2, "level": "medium", "message": "中风险预警"}
            ],
            "accuracy": 85,
            "avg_response_time": 10
        }
        
        result = await self.expert.analyze_alert(test_data)
        
        assert result.stage == TrendStage.ALERT
        assert 0 <= result.confidence <= 1
        assert 0 <= result.accuracy <= 100
        assert isinstance(result.insights, list)
    
    @pytest.mark.asyncio
    async def test_detect_anomalies(self):
        """测试异常检测"""
        trend_data = {
            "trends": [
                {"id": 1, "volatility": 0.9},
                {"id": 2, "volatility": 0.4}
            ],
            "patterns": [
                {"id": 1, "anomaly_score": 0.85}
            ]
        }
        
        anomalies = await self.expert.detect_anomalies(trend_data)
        
        assert isinstance(anomalies, dict)
        assert 'anomalies' in anomalies
        assert 'total_count' in anomalies
        assert 'high_severity' in anomalies
    
    @pytest.mark.asyncio
    async def test_evaluate_response_time(self):
        """测试响应时间评估"""
        alert_data = {
            "detection_time": time.time() - 600,  # 10分钟前
            "response_time": 300  # 5分钟
        }
        
        evaluation = await self.expert.evaluate_response_time(alert_data)
        
        assert isinstance(evaluation, dict)
        assert 'time_elapsed' in evaluation
        assert 'response_efficiency' in evaluation
        assert 'recommendation' in evaluation
    
    def test_set_alert_thresholds(self):
        """测试设置预警阈值"""
        new_thresholds = {
            "high": 0.9,
            "medium": 0.6,
            "low": 0.4
        }
        
        result = self.expert.set_alert_thresholds(new_thresholds)
        
        assert result is True
        assert self.expert.alert_thresholds["high"] == 0.9
        assert self.expert.alert_thresholds["medium"] == 0.6
        assert self.expert.alert_thresholds["low"] == 0.4
    
    @pytest.mark.asyncio
    async def test_get_alert_dashboard(self):
        """测试获取预警仪表板"""
        # 先执行一次分析
        test_data = {"alerts": [{"level": "medium"}], "accuracy": 80}
        await self.expert.analyze_alert(test_data)
        
        dashboard = self.expert.get_alert_dashboard()
        
        assert isinstance(dashboard, dict)
        assert dashboard['expert_id'] == self.expert.expert_id
        assert dashboard['name'] == self.expert.name
        assert dashboard['total_alerts'] >= 1


class TestTrendExpertsIntegration:
    """测试趋势专家集成功能"""
    
    def setup_method(self):
        """测试前初始化"""
        self.connector = TrendDataConnector()
        self.experts = get_trend_experts(self.connector)
    
    def test_get_all_experts(self):
        """测试获取所有专家"""
        assert len(self.experts) == 6
        
        expected_keys = [
            'collection_expert',
            'processing_expert', 
            'analysis_expert',
            'prediction_expert',
            'report_expert',
            'alert_expert'
        ]
        
        for key in expected_keys:
            assert key in self.experts
            assert self.experts[key] is not None
    
    @pytest.mark.asyncio
    async def test_expert_workflow_integration(self):
        """测试专家工作流集成"""
        # 模拟完整的工作流程
        collection_data = {"data_volume": 1000}
        processing_data = {"data_diversity": 0.8}
        analysis_data = {"trends": [{"strength": 0.7}]}
        prediction_data = {"prediction_accuracy": 0.85}
        report_data = {"report_quality": 0.8}
        alert_data = {"alerts": [], "accuracy": 90}
        
        # 执行各专家分析
        collection_result = await self.experts['collection_expert'].analyze(collection_data)
        processing_result = await self.experts['processing_expert'].analyze(processing_data)
        analysis_result = await self.experts['analysis_expert'].analyze(analysis_data)
        prediction_result = await self.experts['prediction_expert'].analyze(prediction_data)
        report_result = await self.experts['report_expert'].analyze(report_data)
        alert_result = await self.experts['alert_expert'].analyze_alert(alert_data)
        
        # 验证结果
        assert collection_result.stage == TrendStage.COLLECTION
        assert processing_result.stage == TrendStage.PROCESSING
        assert analysis_result.stage == TrendStage.ANALYSIS
        assert prediction_result.stage == TrendStage.PREDICTION
        assert report_result.stage == TrendStage.REPORT
        assert alert_result.stage == TrendStage.ALERT
    
    @pytest.mark.asyncio
    async def test_performance_benchmark(self):
        """测试性能基准"""
        # 测试单个专家响应时间
        start_time = time.time()
        
        test_data = {"data_volume": 500}
        result = await self.experts['collection_expert'].analyze(test_data)
        
        end_time = time.time()
        response_time = end_time - start_time
        
        # 验证响应时间在合理范围内（2秒SLO要求）
        assert response_time < 2.0, f"响应时间 {response_time:.2f} 秒超过2秒SLO要求"
        assert result is not None
    
    def test_dashboard_integration(self):
        """测试仪表板集成"""
        # 获取所有专家的仪表板数据
        dashboards = {}
        
        for expert_name, expert in self.experts.items():
            if hasattr(expert, 'get_collection_dashboard'):
                dashboards[expert_name] = expert.get_collection_dashboard()
            elif hasattr(expert, 'get_processing_dashboard'):
                dashboards[expert_name] = expert.get_processing_dashboard()
            elif hasattr(expert, 'get_analysis_dashboard'):
                dashboards[expert_name] = expert.get_analysis_dashboard()
            elif hasattr(expert, 'get_prediction_dashboard'):
                dashboards[expert_name] = expert.get_prediction_dashboard()
            elif hasattr(expert, 'get_report_dashboard'):
                dashboards[expert_name] = expert.get_report_dashboard()
            elif hasattr(expert, 'get_alert_dashboard'):
                dashboards[expert_name] = expert.get_alert_dashboard()
        
        # 验证仪表板数据
        assert len(dashboards) == 6
        for expert_name, dashboard in dashboards.items():
            assert isinstance(dashboard, dict)
            assert 'expert_id' in dashboard
            assert 'name' in dashboard


if __name__ == "__main__":
    # 运行性能测试
    import time
    
    connector = TrendDataConnector()
    experts = get_trend_experts(connector)
    
    print("趋势分析专家模块性能测试...")
    
    # 测试单个专家性能
    test_start = time.time()
    
    async def test_single_expert():
        test_data = {"data_volume": 1000}
        result = await experts['collection_expert'].analyze(test_data)
        return result
    
    result = asyncio.run(test_single_expert())
    test_end = time.time()
    
    print(f"单个专家分析时间: {test_end - test_start:.3f} 秒")
    print(f"分析结果置信度: {result.confidence:.2f}")
    print(f"分析结果准确率: {result.accuracy:.2f}%")
    
    # 测试完整工作流性能
    workflow_start = time.time()
    
    async def test_workflow():
        tasks = []
        for expert_name in ['collection_expert', 'processing_expert', 'analysis_expert']:
            test_data = {"data_volume": 500} if expert_name == 'collection_expert' else {}
            tasks.append(experts[expert_name].analyze(test_data))
        
        results = await asyncio.gather(*tasks)
        return results
    
    results = asyncio.run(test_workflow())
    workflow_end = time.time()
    
    print(f"完整工作流时间: {workflow_end - workflow_start:.3f} 秒")
    print(f"处理专家数量: {len(results)}")
    
    print("性能测试完成！")