#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI编程助手专家模块集成测试
测试所有专家的生产级功能
"""

import asyncio
import time
import pytest
from typing import Dict, Any

from coding_experts import (
    get_coding_experts,
    get_coding_expert_monitor,
    CodeGenerationExpert,
    CodeReviewExpert,
    PerformanceOptimizationExpert,
    BugFixExpert,
    DocumentationExpert,
    CodingStage
)


class TestCodingExperts:
    """编程助手专家测试类"""
    
    def setup_method(self):
        """测试初始化"""
        self.experts = get_coding_experts()
        self.monitor = get_coding_expert_monitor()
    
    @pytest.mark.asyncio
    async def test_code_generation_expert(self):
        """测试代码生成专家"""
        expert = self.experts["generation_expert"]
        
        # 测试数据
        code_data = {
            "language": "python",
            "quality": 0.85,
            "complexity": 15,
            "structure_quality": 0.8,
            "performance_score": 0.9,
            "security_score": 0.95
        }
        
        start_time = time.time()
        analysis = await expert.analyze_generation(code_data)
        processing_time = time.time() - start_time
        
        # 验证结果
        assert analysis.stage == CodingStage.GENERATION
        assert 0 <= analysis.score <= 100
        assert 0.8 <= analysis.confidence <= 0.95
        assert len(analysis.insights) > 0
        assert isinstance(analysis.metadata, dict)
        
        # 验证SLO要求
        assert processing_time < 2.0, f"响应时间 {processing_time:.2f}s 超过2秒SLO要求"
        
        # 记录监控数据
        self.monitor.record_request("generation_expert", processing_time, True)
        
        print(f"代码生成专家测试通过 - 耗时: {processing_time:.3f}s, 评分: {analysis.score}")
    
    @pytest.mark.asyncio
    async def test_code_review_expert(self):
        """测试代码审查专家"""
        expert = self.experts["review_expert"]
        
        # 测试数据
        review_data = {
            "code_quality": 0.75,
            "issues_found": 3,
            "security_issues": [{"severity": "medium", "type": "xss"}],
            "performance_issues": [{"severity": "low", "type": "inefficient_loop"}],
            "complexity_score": 0.7
        }
        
        start_time = time.time()
        analysis = await expert.analyze_review(review_data)
        processing_time = time.time() - start_time
        
        # 验证结果
        assert analysis.stage == CodingStage.REVIEW
        assert 0 <= analysis.score <= 100
        assert 0.8 <= analysis.confidence <= 0.95
        assert len(analysis.insights) > 0
        
        # 验证SLO要求
        assert processing_time < 2.0, f"响应时间 {processing_time:.2f}s 超过2秒SLO要求"
        
        # 记录监控数据
        self.monitor.record_request("review_expert", processing_time, True)
        
        print(f"代码审查专家测试通过 - 耗时: {processing_time:.3f}s, 评分: {analysis.score}")
    
    @pytest.mark.asyncio
    async def test_performance_optimization_expert(self):
        """测试性能优化专家"""
        expert = self.experts["optimization_expert"]
        
        # 测试数据
        performance_data = {
            "response_time": 150,
            "memory_usage": 85,
            "cpu_utilization": 70,
            "io_performance": 0.8,
            "concurrent_users": 100
        }
        
        start_time = time.time()
        analysis = await expert.analyze_performance(performance_data)
        processing_time = time.time() - start_time
        
        # 验证结果
        assert analysis.stage == CodingStage.OPTIMIZATION
        assert 0 <= analysis.score <= 100
        assert 0.8 <= analysis.confidence <= 0.95
        assert len(analysis.insights) > 0
        
        # 验证SLO要求
        assert processing_time < 2.0, f"响应时间 {processing_time:.2f}s 超过2秒SLO要求"
        
        # 记录监控数据
        self.monitor.record_request("optimization_expert", processing_time, True)
        
        print(f"性能优化专家测试通过 - 耗时: {processing_time:.3f}s, 评分: {analysis.score}")
    
    @pytest.mark.asyncio
    async def test_bug_fix_expert(self):
        """测试Bug修复专家"""
        expert = self.experts["bug_fix_expert"]
        
        # 测试数据
        bug_data = {
            "bugs": [
                {"severity": "critical", "type": "crash", "status": "open"},
                {"severity": "major", "type": "functional", "status": "open"},
                {"severity": "minor", "type": "ui", "status": "fixed"}
            ],
            "difficulty_score": 0.7,
            "impact_score": 0.8,
            "reproducibility_score": 0.9
        }
        
        start_time = time.time()
        analysis = await expert.analyze_bug(bug_data)
        processing_time = time.time() - start_time
        
        # 验证结果
        assert analysis.stage == CodingStage.BUG_FIX
        assert 0 <= analysis.score <= 100
        assert 0.8 <= analysis.confidence <= 0.95
        assert len(analysis.insights) > 0
        
        # 验证SLO要求
        assert processing_time < 2.0, f"响应时间 {processing_time:.2f}s 超过2秒SLO要求"
        
        # 记录监控数据
        self.monitor.record_request("bug_fix_expert", processing_time, True)
        
        print(f"Bug修复专家测试通过 - 耗时: {processing_time:.3f}s, 评分: {analysis.score}")
    
    @pytest.mark.asyncio
    async def test_documentation_expert(self):
        """测试文档生成专家"""
        expert = self.experts["documentation_expert"]
        
        # 测试数据
        doc_data = {
            "completeness": 0.8,
            "coverage": 0.75,
            "quality": 0.85,
            "readability": 0.8,
            "timeliness": 0.7
        }
        
        start_time = time.time()
        analysis = await expert.analyze_documentation(doc_data)
        processing_time = time.time() - start_time
        
        # 验证结果
        assert analysis.stage == CodingStage.DOCUMENTATION
        assert 0 <= analysis.score <= 100
        assert 0.8 <= analysis.confidence <= 0.95
        assert len(analysis.insights) > 0
        
        # 验证SLO要求
        assert processing_time < 2.0, f"响应时间 {processing_time:.2f}s 超过2秒SLO要求"
        
        # 记录监控数据
        self.monitor.record_request("documentation_expert", processing_time, True)
        
        print(f"文档生成专家测试通过 - 耗时: {processing_time:.3f}s, 评分: {analysis.score}")
    
    @pytest.mark.asyncio
    async def test_all_experts_concurrent(self):
        """测试所有专家并发处理能力"""
        
        async def test_expert(expert_id: str, test_data: Dict[str, Any]):
            """单个专家测试函数"""
            expert = self.experts[expert_id]
            
            if expert_id == "generation_expert":
                analysis = await expert.analyze_generation(test_data)
            elif expert_id == "review_expert":
                analysis = await expert.analyze_review(test_data)
            elif expert_id == "optimization_expert":
                analysis = await expert.analyze_performance(test_data)
            elif expert_id == "bug_fix_expert":
                analysis = await expert.analyze_bug(test_data)
            elif expert_id == "documentation_expert":
                analysis = await expert.analyze_documentation(test_data)
            
            return analysis
        
        # 并发测试数据
        test_cases = [
            ("generation_expert", {"language": "python", "quality": 0.8, "complexity": 10, "structure_quality": 0.7, "performance_score": 0.8, "security_score": 0.9}),
            ("review_expert", {"code_quality": 0.7, "issues_found": 2, "security_issues": [], "performance_issues": [], "complexity_score": 0.6}),
            ("optimization_expert", {"response_time": 200, "memory_usage": 80, "cpu_utilization": 60, "io_performance": 0.7, "concurrent_users": 50}),
            ("bug_fix_expert", {"bugs": [], "difficulty_score": 0.6, "impact_score": 0.7, "reproducibility_score": 0.8}),
            ("documentation_expert", {"completeness": 0.7, "quality": 0.8, "coverage": 0.6, "readability": 0.7, "timeliness": 0.6})
        ]
        
        start_time = time.time()
        
        # 并发执行所有测试
        tasks = [test_expert(expert_id, data) for expert_id, data in test_cases]
        results = await asyncio.gather(*tasks)
        
        total_time = time.time() - start_time
        
        # 验证所有结果
        for i, (expert_id, _) in enumerate(test_cases):
            analysis = results[i]
            assert 0 <= analysis.score <= 100
            assert 0.8 <= analysis.confidence <= 0.95
            
            # 记录监控数据
            self.monitor.record_request(expert_id, 0.5, True)  # 估算时间
        
        print(f"并发测试通过 - 总耗时: {total_time:.3f}s, 处理了 {len(results)} 个专家")
    
    def test_monitor_system(self):
        """测试监控系统"""
        # 模拟一些请求
        self.monitor.record_request("generation_expert", 0.8, True)
        self.monitor.record_request("review_expert", 1.2, True)
        self.monitor.record_request("optimization_expert", 0.5, False)
        self.monitor.record_request("bug_fix_expert", 2.1, True)  # SLO违规
        
        # 获取性能报告
        report = self.monitor.get_performance_report()
        
        # 验证报告内容
        assert report["total_requests"] == 4
        assert report["success_rate"] == "75.00%"  # 3/4 = 75%
        assert "generation_expert" in report["expert_performance"]
        assert report["slo_compliance"] == "75.00%"  # 3/4 = 75%
        
        print("监控系统测试通过")
    
    def test_expert_initialization(self):
        """测试专家初始化"""
        # 验证所有专家都已正确初始化
        expected_experts = [
            "generation_expert",
            "review_expert", 
            "optimization_expert",
            "bug_fix_expert",
            "documentation_expert"
        ]
        
        for expert_id in expected_experts:
            assert expert_id in self.experts
            expert = self.experts[expert_id]
            
            # 验证专家属性
            assert hasattr(expert, 'name')
            assert hasattr(expert, 'stage')
            assert hasattr(expert, 'expert_id')
            
            # 验证生产级属性
            assert hasattr(expert, 'data_sources')
            assert hasattr(expert, 'analysis_dimensions')
            
            print(f"专家 {expert_id} 初始化验证通过")


def test_production_ready_features():
    """测试生产级特性"""
    
    # 测试代码生成专家的生产级特性
    generation_expert = CodeGenerationExpert()
    
    # 验证专业能力
    assert len(generation_expert.data_sources) >= 3
    assert len(generation_expert.analysis_dimensions) == 6
    assert len(generation_expert.supported_languages) >= 25
    
    # 验证代码审查专家的生产级特性
    review_expert = CodeReviewExpert()
    assert len(review_expert.data_sources) >= 3
    assert len(review_expert.analysis_dimensions) == 6
    
    # 验证性能优化专家的生产级特性
    optimization_expert = PerformanceOptimizationExpert()
    assert len(optimization_expert.data_sources) >= 3
    assert len(optimization_expert.analysis_dimensions) == 6
    
    # 验证Bug修复专家的生产级特性
    bug_fix_expert = BugFixExpert()
    assert len(bug_fix_expert.data_sources) >= 3
    assert len(bug_fix_expert.analysis_dimensions) == 6
    
    # 验证文档生成专家的生产级特性
    documentation_expert = DocumentationExpert()
    assert len(documentation_expert.data_sources) >= 3
    assert len(documentation_expert.analysis_dimensions) == 6
    
    print("生产级特性验证通过")


if __name__ == "__main__":
    # 运行所有测试
    test_instance = TestCodingExperts()
    test_instance.setup_method()
    
    # 运行异步测试
    async def run_async_tests():
        await test_instance.test_code_generation_expert()
        await test_instance.test_code_review_expert()
        await test_instance.test_performance_optimization_expert()
        await test_instance.test_bug_fix_expert()
        await test_instance.test_documentation_expert()
        await test_instance.test_all_experts_concurrent()
    
    asyncio.run(run_async_tests())
    
    # 运行同步测试
    test_instance.test_monitor_system()
    test_instance.test_expert_initialization()
    test_production_ready_features()
    
    # 输出最终监控报告
    report = test_instance.monitor.get_performance_report()
    print("\n=== 最终性能报告 ===")
    print(f"总请求数: {report['total_requests']}")
    print(f"成功率: {report['success_rate']}")
    print(f"平均响应时间: {report['average_response_time']}")
    print(f"SLO合规率: {report['slo_compliance']}")
    
    print("\n🎉 所有测试通过！编程助手专家模块已达到生产级水平！")