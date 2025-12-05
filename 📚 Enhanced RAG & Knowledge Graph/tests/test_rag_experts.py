"""
RAG专家系统测试脚本
测试知识专家、检索专家、知识图谱专家的功能
"""

import asyncio
import sys
import os

# 添加路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.rag_experts import knowledge_expert, search_expert, graph_expert


async def test_knowledge_expert():
    """测试知识管理专家"""
    print("=== 测试知识管理专家 ===")
    
    # 测试对话功能
    response = await knowledge_expert.chat_response("帮我评估一下文档质量", {})
    print(f"对话响应: {response}")
    
    # 测试文档分析
    test_content = """
    人工智能(AI)是计算机科学的一个分支，旨在创造能够执行通常需要人类智能的任务的机器。
    机器学习是AI的一个子集，它使计算机能够在没有明确编程的情况下学习。
    深度学习是机器学习的一个子集，使用神经网络模拟人脑的工作方式。
    """
    
    analysis = await knowledge_expert.analyze_document(test_content, {"title": "AI技术介绍"})
    print(f"文档分析结果: {analysis}")
    
    # 测试专家状态
    status = knowledge_expert.get_status()
    print(f"专家状态: {status}")
    
    print("知识专家测试完成✅\n")


async def test_search_expert():
    """测试检索优化专家"""
    print("=== 测试检索优化专家 ===")
    
    # 测试对话功能
    response = await search_expert.chat_response("如何优化AI相关的查询", {})
    print(f"对话响应: {response}")
    
    # 测试查询优化
    test_query = "AI技术发展趋势"
    optimization = await search_expert.optimize_query(test_query)
    print(f"查询优化结果: {optimization}")
    
    # 测试专家状态
    status = search_expert.get_status()
    print(f"专家状态: {status}")
    
    print("检索专家测试完成✅\n")


async def test_graph_expert():
    """测试知识图谱专家"""
    print("=== 测试知识图谱专家 ===")
    
    # 测试对话功能
    response = await graph_expert.chat_response("从文本中提取实体", {})
    print(f"对话响应: {response}")
    
    # 测试实体提取
    test_text = """
    Python是一种高级编程语言，由Guido van Rossum创建。
    FastAPI是基于Python的现代Web框架，用于构建API。
    Docker是容器化平台，Kubernetes是容器编排系统。
    """
    
    entities = await graph_expert.extract_entities(test_text)
    print(f"实体提取结果: {entities}")
    
    # 测试知识图谱构建
    test_documents = [
        {"content": "AI技术包括机器学习和深度学习", "source": "doc1"},
        {"content": "Python是AI开发的主要语言", "source": "doc2"},
        {"content": "Docker用于AI应用的容器化部署", "source": "doc3"}
    ]
    
    graph = await graph_expert.build_graph(test_documents)
    print(f"知识图谱构建结果: {graph}")
    
    # 测试专家状态
    status = graph_expert.get_status()
    print(f"专家状态: {status}")
    
    print("图谱专家测试完成✅\n")


async def test_all_experts():
    """测试所有专家"""
    print("🚀 开始测试RAG专家系统...\n")
    
    await test_knowledge_expert()
    await test_search_expert()
    await test_graph_expert()
    
    print("🎉 所有RAG专家测试完成！")
    
    # 汇总专家信息
    experts_info = {
        "knowledge_expert": knowledge_expert.get_status(),
        "search_expert": search_expert.get_status(),
        "graph_expert": graph_expert.get_status()
    }
    
    print(f"\n📊 专家系统汇总:")
    for name, info in experts_info.items():
        print(f"  {name}: {info['name']} - {len(info['capabilities'])}项能力")


if __name__ == "__main__":
    asyncio.run(test_all_experts())