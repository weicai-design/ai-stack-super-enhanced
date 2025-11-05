#!/usr/bin/env python3
"""
快速测试脚本 - 验证RAG集成模块功能

用法: python quick_test.py
"""

import asyncio
import sys
from pathlib import Path

# 添加模块路径
module_path = Path(__file__).parent
sys.path.insert(0, str(module_path))

# 直接导入模块（不使用相对导入）
import rag_integration
import chat_handler
import knowledge_enhancer

async def quick_test():
    """快速功能测试"""
    print("🧪 开始快速测试...\n")
    
    # 测试1: 服务健康检查
    print("1️⃣  测试RAG服务连接...")
    service = rag_integration.get_rag_service()
    health = await service.health_check()
    if health.get("model_ok"):
        print("   ✅ RAG服务正常\n")
    else:
        print("   ❌ RAG服务异常，请检查服务是否运行")
        print(f"   错误: {health.get('error', '未知')}\n")
        return False
    
    # 测试2: 聊天消息保存
    print("2️⃣  测试聊天消息保存...")
    handler = chat_handler.ChatMessageHandler(auto_save=True, min_length=5)
    result = await handler.process_user_message(
        message="这是一个测试消息：OpenWebUI集成测试",
        user_id="test_user",
        session_id="test_session",
    )
    if result.get("saved"):
        print(f"   ✅ 消息已保存，文档ID: {result['doc_id'][:20]}...\n")
    else:
        print(f"   ⚠️  保存失败: {result.get('reason', result.get('error'))}\n")
    
    # 测试3: 知识搜索
    print("3️⃣  测试知识搜索...")
    search_result = await service.search("OpenWebUI集成", top_k=3)
    items = search_result.get("items", [])
    if items:
        print(f"   ✅ 找到 {len(items)} 个相关结果\n")
    else:
        print("   ⚠️  未找到相关结果（这是正常的，如果RAG库为空）\n")
    
    # 测试4: 知识增强
    print("4️⃣  测试知识增强...")
    enhancer = knowledge_enhancer.KnowledgeEnhancer(enable_enhancement=True, top_k=3)
    enhance_result = await enhancer.enhance_response(
        user_query="什么是RAG？",
        original_response="RAG是检索增强生成技术",
    )
    if enhance_result.get("has_knowledge"):
        print(f"   ✅ 找到 {enhance_result.get('knowledge_count', 0)} 条相关知识\n")
    else:
        print("   ℹ️  未找到相关知识（RAG库可能为空）\n")
    
    # 清理
    await service.close()
    
    print("✅ 快速测试完成！")
    return True

if __name__ == "__main__":
    success = asyncio.run(quick_test())
    sys.exit(0 if success else 1)

