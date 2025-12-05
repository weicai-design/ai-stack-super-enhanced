#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试专家协同模块测试
"""

import asyncio
import sys
import traceback

async def test_expert_collaboration():
    """测试专家协同工作"""
    print("🤝 测试专家协同工作...")
    
    try:
        # 模拟多专家协同分析
        from core.expert_collaboration import ExpertCollaborationHub
        
        hub = ExpertCollaborationHub()
        
        # 创建协同会话（使用同步方法避免异步问题）
        print("尝试创建协同会话...")
        session_id = hub.create_collaboration_session_sync(
            "综合业务分析",
            ["rag_expert", "erp_expert", "content_expert"]
        )
        print(f"会话ID: {session_id}")
        assert session_id is not None, "协同会话创建失败"
        
        print("✅ 专家协同工作测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 专家协同工作测试失败: {e}")
        traceback.print_exc()
        return False

async def test_api_endpoints():
    """测试API端点"""
    print("\n🌐 测试API端点...")
    
    try:
        import httpx
        import time
        
        # 检查API服务器是否运行
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                # 测试主API端点，增加超时设置
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get("http://127.0.0.1:8001/")
                    print(f"主API端点状态码: {response.status_code}")
                    assert response.status_code == 200, f"主API端点不可用，状态码: {response.status_code}"
                    
                    # 测试专家API端点
                    response = await client.get("http://127.0.0.1:8001/api/experts")
                    print(f"专家API端点状态码: {response.status_code}")
                    assert response.status_code == 200, f"专家API端点不可用，状态码: {response.status_code}"
                
                print("✅ API端点测试通过")
                return True
                
            except (httpx.ConnectError, httpx.TimeoutException) as e:
                if attempt < max_retries - 1:
                    print(f"⚠️  API连接失败，{retry_delay}秒后重试... (尝试 {attempt + 1}/{max_retries})")
                    time.sleep(retry_delay)
                else:
                    # 如果所有重试都失败，检查服务器状态
                    print("🔍 检查API服务器状态...")
                    import subprocess
                    try:
                        result = subprocess.run(
                            ["lsof", "-i", ":8001"], 
                            capture_output=True, 
                            text=True
                        )
                        if result.returncode == 0:
                            print(f"✅ API服务器正在运行: {result.stdout}")
                        else:
                            print("❌ API服务器未在端口8001运行")
                    except Exception as check_error:
                        print(f"❌ 检查服务器状态失败: {check_error}")
                    
                    raise e
        
    except Exception as e:
        print(f"❌ API端点测试失败: {e}")
        traceback.print_exc()
        return False

async def main():
    """主测试函数"""
    print("🚀 开始调试测试...")
    
    # 测试专家协同模块
    expert_result = await test_expert_collaboration()
    
    # 测试API端点
    api_result = await test_api_endpoints()
    
    # 打印总结
    print("\n" + "="*60)
    print("📊 调试测试总结")
    print("="*60)
    print(f"专家协同模块: {'✅ 通过' if expert_result else '❌ 失败'}")
    print(f"API端点测试: {'✅ 通过' if api_result else '❌ 失败'}")
    
    if expert_result and api_result:
        print("\n🎉 所有测试通过！")
    else:
        print("\n⚠️  部分测试失败，需要进一步调试")

if __name__ == "__main__":
    asyncio.run(main())