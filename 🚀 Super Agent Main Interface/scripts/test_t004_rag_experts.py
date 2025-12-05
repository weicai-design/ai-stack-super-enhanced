#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T004 RAG专家系统测试脚本
测试RAG模块3个专家的功能实现和API接口
"""

import asyncio
import json
import sys
import time
from datetime import datetime
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.rag_expert_system import RAGExpertSystem, QueryAnalysis
from core.experts.rag_experts import ExpertDomain, KnowledgeExpert, RetrievalExpert, GraphExpert


class T004RAGExpertsTester:
    """T004 RAG专家系统测试器"""
    
    def __init__(self):
        self.test_results = []
        self.start_time = None
        self.end_time = None
        
    def log_test(self, test_name: str, status: str, details: str = ""):
        """记录测试结果"""
        result = {
            "test_name": test_name,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        print(f"[{status.upper()}] {test_name}: {details}")
        
    def run_tests(self):
        """运行所有测试"""
        self.start_time = time.time()
        print("🚀 开始T004 RAG专家系统测试...")
        print("=" * 60)
        
        # 测试专家系统初始化
        self.test_expert_system_initialization()
        
        # 测试查询分析功能
        asyncio.run(self.test_query_analysis())
        
        # 测试知识专家功能
        asyncio.run(self.test_knowledge_expert())
        
        # 测试检索专家功能
        asyncio.run(self.test_retrieval_expert())
        
        # 测试图谱专家功能
        asyncio.run(self.test_graph_expert())
        
        # 测试综合专家回答
        asyncio.run(self.test_comprehensive_expert_answer())
        
        # 测试API接口兼容性
        self.test_api_compatibility()
        
        self.end_time = time.time()
        self.generate_report()
        
    def test_expert_system_initialization(self):
        """测试专家系统初始化"""
        try:
            # 测试专家系统创建
            expert_system = RAGExpertSystem()
            assert len(expert_system.experts) == 3, "专家数量应为3个"
            
            # 验证专家类型
            assert ExpertDomain.KNOWLEDGE in expert_system.experts
            assert ExpertDomain.RETRIEVAL in expert_system.experts
            assert ExpertDomain.GRAPH in expert_system.experts
            
            # 验证能力描述
            capabilities = expert_system.describe_capabilities()
            assert isinstance(capabilities, dict), "能力描述应为字典"
            assert len(capabilities) == 3, "能力描述应包含3个专家领域"
            
            self.log_test(
                "专家系统初始化", 
                "PASS", 
                f"成功创建包含{len(expert_system.experts)}个专家的系统"
            )
            
        except Exception as e:
            self.log_test("专家系统初始化", "FAIL", str(e))
            
    async def test_query_analysis(self):
        """测试查询分析功能"""
        try:
            expert_system = RAGExpertSystem()
            
            # 测试知识类查询
            knowledge_query = "如何组织企业知识库？"
            analysis = expert_system.analyze_query(knowledge_query)
            assert analysis.domain == ExpertDomain.KNOWLEDGE
            assert 0.2 <= analysis.complexity <= 1.0
            assert len(analysis.focus_keywords) > 0
            
            # 测试检索类查询
            retrieval_query = "如何优化RAG检索性能？"
            analysis = expert_system.analyze_query(retrieval_query)
            assert analysis.domain == ExpertDomain.RETRIEVAL
            
            # 测试图谱类查询
            graph_query = "如何构建知识图谱实体关系？"
            analysis = expert_system.analyze_query(graph_query)
            assert analysis.domain == ExpertDomain.GRAPH
            
            self.log_test("查询分析功能", "PASS", "成功分析不同类型查询意图")
            
        except Exception as e:
            self.log_test("查询分析功能", "FAIL", str(e))
            
    async def test_knowledge_expert(self):
        """测试知识专家功能"""
        try:
            knowledge_expert = KnowledgeExpert()
            
            # 测试知识分析
            knowledge_items = [
                {"title": "机器学习基础", "category": "AI", "score": 0.9},
                {"title": "深度学习原理", "category": "AI", "score": 0.8},
                {"title": "自然语言处理", "category": "NLP", "score": 0.7}
            ]
            
            analysis = await knowledge_expert.analyze_knowledge(knowledge_items)
            assert analysis.domain == ExpertDomain.KNOWLEDGE
            assert len(analysis.insights) > 0
            assert len(analysis.recommendations) > 0
            assert analysis.confidence > 0
            
            # 测试知识组织建议
            organization_suggestion = await knowledge_expert.suggest_knowledge_organization(knowledge_items)
            assert "suggested_topics" in organization_suggestion
            
            self.log_test("知识专家功能", "PASS", "知识专家分析功能正常")
            
        except Exception as e:
            self.log_test("知识专家功能", "FAIL", str(e))
            
    async def test_retrieval_expert(self):
        """测试检索专家功能"""
        try:
            retrieval_expert = RetrievalExpert()
            
            # 测试检索优化
            query = "如何提升RAG系统性能？"
            retrieval_results = [
                {"title": "RAG优化技巧", "relevance": 0.9, "content": "..."},
                {"title": "检索算法选择", "relevance": 0.7, "content": "..."},
                {"title": "向量数据库配置", "relevance": 0.6, "content": "..."}
            ]
            
            analysis = await retrieval_expert.optimize_retrieval(query, retrieval_results)
            assert analysis.domain == ExpertDomain.RETRIEVAL
            assert len(analysis.insights) > 0
            assert len(analysis.recommendations) > 0
            
            self.log_test("检索专家功能", "PASS", "检索专家优化功能正常")
            
        except Exception as e:
            self.log_test("检索专家功能", "FAIL", str(e))
            
    async def test_graph_expert(self):
        """测试图谱专家功能"""
        try:
            graph_expert = GraphExpert()
            
            # 测试图谱结构分析
            entities = [
                {"id": "e1", "name": "机器学习", "type": "概念"},
                {"id": "e2", "name": "深度学习", "type": "概念"}
            ]
            relations = [
                {"from": "e1", "to": "e2", "type": "包含", "weight": 0.8}
            ]
            
            analysis = await graph_expert.analyze_graph_structure(entities, relations)
            assert analysis.domain == ExpertDomain.GRAPH, f"期望domain为GRAPH，实际为{analysis.domain}"
            assert len(analysis.insights) > 0, "insights列表为空"
            assert len(analysis.recommendations) > 0, f"recommendations列表为空，内容为{analysis.recommendations}"
            
            # 测试图谱增强建议
            enhancement_suggestion = await graph_expert.suggest_graph_enhancement(entities, relations)
            assert "suggestions" in enhancement_suggestion, f"增强建议缺少suggestions字段，实际字段为{list(enhancement_suggestion.keys())}"
            
            self.log_test("图谱专家功能", "PASS", "图谱专家分析功能正常")
            
        except AssertionError as e:
            self.log_test("图谱专家功能", "FAIL", f"断言失败: {str(e)}")
        except Exception as e:
            import traceback
            error_details = f"异常: {str(e)}\n{traceback.format_exc()}"
            self.log_test("图谱专家功能", "FAIL", error_details)
            
    async def test_comprehensive_expert_answer(self):
        """测试综合专家回答功能"""
        try:
            expert_system = RAGExpertSystem()
            
            # 测试查询分析
            query = "如何优化企业知识管理系统？"
            analysis = expert_system.analyze_query(query)
            
            # 测试综合回答生成
            context = [
                {
                    "knowledge_items": [
                        {"title": "知识管理最佳实践", "category": "KM", "score": 0.8}
                    ]
                }
            ]
            
            answer = await expert_system.generate_expert_answer(query, analysis, context)
            
            assert len(answer.answer) > 0
            assert answer.confidence > 0
            assert isinstance(answer.recommendations, list)
            assert isinstance(answer.related_concepts, list)
            
            self.log_test("综合专家回答功能", "PASS", "专家综合回答生成正常")
            
        except Exception as e:
            self.log_test("综合专家回答功能", "FAIL", str(e))
            
    def test_api_compatibility(self):
        """测试API接口兼容性"""
        try:
            # 检查API文件是否存在
            api_file = project_root / "api" / "rag_expert_system_api.py"
            assert api_file.exists(), "RAG专家系统API文件不存在"
            
            # 检查API导入路径
            import importlib.util
            spec = importlib.util.spec_from_file_location("rag_expert_system_api", api_file)
            api_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(api_module)
            
            # 验证API组件
            assert hasattr(api_module, 'router'), "API缺少router组件"
            assert hasattr(api_module, 'setup_rag_expert_system_api'), "API缺少setup函数"
            
            self.log_test("API接口兼容性", "PASS", "RAG专家系统API接口完整")
            
        except Exception as e:
            self.log_test("API接口兼容性", "FAIL", str(e))
            
    def generate_report(self):
        """生成测试报告"""
        print("\n" + "=" * 60)
        print("📊 T004 RAG专家系统测试报告")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r["status"] == "PASS")
        failed_tests = total_tests - passed_tests
        
        # 计算测试时长
        duration = self.end_time - self.start_time
        
        print(f"\n📈 测试统计:")
        print(f"   总测试数: {total_tests}")
        print(f"   通过测试: {passed_tests}")
        print(f"   失败测试: {failed_tests}")
        print(f"   通过率: {(passed_tests/total_tests)*100:.1f}%")
        print(f"   测试时长: {duration:.2f}秒")
        
        # 详细测试结果
        print(f"\n🔍 详细结果:")
        for result in self.test_results:
            status_icon = "✅" if result["status"] == "PASS" else "❌"
            print(f"   {status_icon} {result['test_name']}: {result['details']}")
        
        # 生成测试报告文件
        report_data = {
            "task_id": "T004",
            "task_name": "实现RAG模块3个专家",
            "test_timestamp": datetime.now().isoformat(),
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "pass_rate": (passed_tests/total_tests)*100,
            "test_duration": duration,
            "test_results": self.test_results
        }
        
        # 保存测试报告
        report_filename = f"t004_rag_experts_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_path = project_root / "reports" / report_filename
        
        # 确保reports目录存在
        report_path.parent.mkdir(exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 测试报告已保存: {report_path}")
        
        # 最终结论
        if failed_tests == 0:
            print("\n🎉 T004 RAG专家系统测试全部通过！")
            print("✅ 3个RAG专家功能实现完整")
            print("✅ 专家系统集成正常")
            print("✅ API接口兼容性良好")
            print("✅ 达到生产水平要求")
            return True
        else:
            print(f"\n⚠️  T004测试存在{failed_tests}个失败项，需要修复")
            return False


def main():
    """主函数"""
    tester = T004RAGExpertsTester()
    success = tester.run_tests()
    
    # 返回退出码
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()