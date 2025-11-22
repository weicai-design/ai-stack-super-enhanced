#!/usr/bin/env python3
"""
OpenWebUI RAG集成使用示例

演示如何使用RAG集成模块的各个功能
"""

import asyncio
import logging
import sys
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

try:
    from .rag_integration import RAGIntegrationService, get_rag_service
    from .chat_handler import ChatMessageHandler
    from .file_upload_handler import FileUploadHandler
    from .knowledge_enhancer import KnowledgeEnhancer
except ImportError:
    current_dir = Path(__file__).parent
    if str(current_dir) not in sys.path:
        sys.path.insert(0, str(current_dir))
    from rag_integration import RAGIntegrationService, get_rag_service
    from chat_handler import ChatMessageHandler
    from file_upload_handler import FileUploadHandler
    from knowledge_enhancer import KnowledgeEnhancer


async def example_1_health_check():
    """示例1: 检查RAG服务健康状态"""
    print("\n" + "="*60)
    print("示例1: 检查RAG服务健康状态")
    print("="*60)
    
    service = get_rag_service()
    result = await service.health_check()
    print(f"服务状态: {result}")
    
    return result.get("model_ok", False)


async def example_2_chat_auto_save():
    """示例2: 聊天内容自动保存"""
    print("\n" + "="*60)
    print("示例2: 聊天内容自动保存")
    print("="*60)
    
    handler = ChatMessageHandler(auto_save=True, min_length=5)
    
    # 保存用户消息
    result = await handler.process_user_message(
        message="这是一个重要的技术问题：如何使用RAG系统？",
        user_id="user123",
        session_id="session456",
    )
    
    print(f"保存结果: {result}")
    
    if result.get("saved"):
        print(f"✅ 消息已保存，文档ID: {result['doc_id']}")
        print(f"   当前索引大小: {result.get('size', 0)}")
    else:
        print(f"❌ 保存失败: {result.get('reason', result.get('error'))}")


async def example_3_search_context():
    """示例3: 搜索相关上下文"""
    print("\n" + "="*60)
    print("示例3: 搜索相关上下文")
    print("="*60)
    
    handler = ChatMessageHandler()
    
    # 搜索相关上下文
    contexts = await handler.search_relevant_context(
        query="RAG系统如何使用",
        top_k=3,
    )
    
    print(f"找到 {len(contexts)} 个相关上下文:")
    for i, ctx in enumerate(contexts, 1):
        print(f"\n{i}. 相似度: {ctx.get('score', 0):.3f}")
        print(f"   内容: {ctx.get('snippet', '')[:100]}...")
        print(f"   来源: {ctx.get('path', '未知')}")


async def example_4_knowledge_enhancement():
    """示例4: 知识增强回答"""
    print("\n" + "="*60)
    print("示例4: 知识增强回答")
    print("="*60)
    
    enhancer = KnowledgeEnhancer(
        enable_enhancement=True,
        top_k=3,
        similarity_threshold=0.3,
    )
    
    # 原始回答
    original_response = "RAG是检索增强生成技术..."
    
    # 增强回答
    result = await enhancer.enhance_response(
        user_query="什么是RAG？",
        original_response=original_response,
        use_context=True,
    )
    
    print(f"找到相关知识: {result.get('has_knowledge', False)}")
    print(f"知识片段数: {result.get('knowledge_count', 0)}")
    
    if result.get("knowledge_snippets"):
        print("\n检索到的知识片段:")
        for i, snippet in enumerate(result["knowledge_snippets"], 1):
            print(f"\n{i}. 相似度: {snippet['score']:.3f}")
            print(f"   内容: {snippet['text'][:150]}...")
    
    print(f"\n增强后的回答:")
    print(result.get("enhanced_response", "")[:300] + "...")


async def example_5_file_upload():
    """示例5: 文件上传处理"""
    print("\n" + "="*60)
    print("示例5: 文件上传处理")
    print("="*60)
    
    handler = FileUploadHandler(auto_process=True)
    
    # 创建测试文件
    test_file = Path("/tmp/rag_test_document.txt")
    test_file.write_text(
        "这是一个测试文档。\n\n"
        "内容包含：\n"
        "- 技术说明\n"
        "- 使用示例\n"
        "- 联系方式: test@example.com\n"
        "- 网址: https://example.com"
    )
    
    print(f"测试文件: {test_file}")
    
    # 处理文件
    result = await handler.process_uploaded_file(
        file_path=str(test_file),
        filename="test_document.txt",
        user_id="user123",
        session_id="session456",
    )
    
    print(f"处理结果: {result}")
    
    if result.get("processed"):
        print(f"✅ 文件已处理，文档ID: {result['doc_id']}")
        print(f"   当前索引大小: {result.get('size', 0)}")
    else:
        print(f"❌ 处理失败: {result.get('error')}")


async def example_6_kg_query():
    """示例6: 知识图谱查询"""
    print("\n" + "="*60)
    print("示例6: 知识图谱查询")
    print("="*60)
    
    service = get_rag_service()
    
    # 获取知识图谱快照
    snapshot = await service.get_kg_snapshot()
    
    if snapshot.get("success"):
        print(f"节点数: {snapshot.get('nodes', 0)}")
        print(f"边数: {snapshot.get('edges', 0)}")
        
        entities = snapshot.get("sample", {})
        if entities.get("emails"):
            print(f"\n提取的邮箱: {entities['emails']}")
        if entities.get("urls"):
            print(f"提取的网址: {entities['urls']}")
        
        # 查询特定实体
        if entities.get("emails"):
            email = entities["emails"][0]
            query_result = await service.query_kg("email", email)
            print(f"\n查询邮箱实体 '{email}':")
            print(query_result)
    else:
        print(f"获取知识图谱失败: {snapshot.get('error')}")


async def main():
    """主函数：运行所有示例"""
    print("\n" + "="*60)
    print("OpenWebUI RAG集成模块 - 使用示例")
    print("="*60)
    
    # 检查服务健康状态
    is_healthy = await example_1_health_check()
    
    if not is_healthy:
        print("\n❌ RAG服务不可用，请先启动RAG服务:")
        print("   make dev")
        return
    
    # 运行示例
    await example_2_chat_auto_save()
    await example_3_search_context()
    await example_4_knowledge_enhancement()
    await example_5_file_upload()
    await example_6_kg_query()
    
    print("\n" + "="*60)
    print("✅ 所有示例运行完成！")
    print("="*60)
    
    # 关闭服务
    service = get_rag_service()
    await service.close()


if __name__ == "__main__":
    asyncio.run(main())

