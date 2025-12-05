#!/usr/bin/env python3
"""
智能任务管理系统集成测试
覆盖所有核心功能的端到端测试
"""

import asyncio
import pytest
import sys
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any

# 添加路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from fastapi import FastAPI
from task_management_v5_api import router

# 创建测试应用
app = FastAPI()
app.include_router(router)


class TestTaskManagementIntegration:
    """智能任务管理系统集成测试类"""
    
    def setup_method(self):
        """测试设置"""
        self.client = TestClient(app)
        self.created_tasks = []
    
    def teardown_method(self):
        """测试清理"""
        # 清理测试数据
        for task_id in self.created_tasks:
            try:
                self.client.delete(f"/{task_id}")
            except:
                pass
    
    def test_create_task_from_user(self):
        """测试用户创建任务"""
        response = self.client.post("/api/v5/task/create", json={
            "title": "集成测试任务",
            "description": "这是集成测试创建的任务",
            "source": "user_defined",
            "priority": "high",
            "required_modules": ["api", "testing"],
            "estimated_duration": 60
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] is not None
        assert data["title"] == "集成测试任务"
        assert data["status"] == "pending"
        assert data["source"] == "user_defined"
        
        self.created_tasks.append(data["id"])
        print(f"✅ 用户创建任务成功: {data['id']}")
    
    def test_create_task_from_agent(self):
        """测试从超级Agent创建任务"""
        response = self.client.post("/api/v5/task/create/from-agent", params={
            "title": "Agent识别任务",
            "description": "超级Agent自动识别的优化任务",
            "identified_from": "chat",
            "required_modules": ["optimization", "analysis"]
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        assert data["task"]["source"] == "agent_identified"
        assert "等待用户确认" in data["message"]
        
        self.created_tasks.append(data["task"]["id"])
        print(f"✅ Agent创建任务成功: {data['task']['id']}")
    
    def test_task_confirmation_workflow(self):
        """测试任务确认流程"""
        # 1. 创建任务
        create_response = self.client.post("/api/v5/task/create", json={
            "title": "待确认任务",
            "description": "需要用户确认的任务",
            "source": "agent_identified",
            "priority": "medium"
        })
        
        assert create_response.status_code == 200
        task_id = create_response.json()["id"]
        self.created_tasks.append(task_id)
        
        # 2. 确认任务
        confirm_response = self.client.post("/api/v5/task/confirm", json={
            "task_id": task_id,
            "notes": "确认执行此任务"
        })
        
        assert confirm_response.status_code == 200
        confirm_data = confirm_response.json()
        
        assert confirm_data["success"] == True
        assert confirm_data["task"]["status"] == "confirmed"
        assert confirm_data["task"]["confirmed_at"] is not None
        
        print(f"✅ 任务确认流程成功: {task_id}")
    
    def test_task_rejection_workflow(self):
        """测试任务拒绝流程"""
        # 1. 创建任务
        create_response = self.client.post("/api/v5/task/create", json={
            "title": "待拒绝任务",
            "description": "用户选择拒绝的任务",
            "source": "agent_identified",
            "priority": "low"
        })
        
        assert create_response.status_code == 200
        task_id = create_response.json()["id"]
        self.created_tasks.append(task_id)
        
        # 2. 拒绝任务
        reject_response = self.client.post("/api/v5/task/reject", json={
            "task_id": task_id,
            "reason": "任务优先级过低，暂不执行"
        })
        
        assert reject_response.status_code == 200
        reject_data = reject_response.json()
        
        assert reject_data["success"] == True
        assert reject_data["task"]["status"] == "rejected"
        
        print(f"✅ 任务拒绝流程成功: {task_id}")
    
    def test_task_listing_with_filters(self):
        """测试带过滤条件的任务列表"""
        # 创建多个不同状态的任务
        tasks_data = [
            {"title": "待处理任务1", "status": "pending", "source": "user_defined"},
            {"title": "待处理任务2", "status": "pending", "source": "agent_identified"},
            {"title": "执行中任务", "status": "executing", "source": "user_defined"},
            {"title": "已完成任务", "status": "completed", "source": "memo_extracted"}
        ]
        
        for task_data in tasks_data:
            response = self.client.post("/api/v5/task/create", json={
                "title": task_data["title"],
                "description": f"测试任务: {task_data['title']}",
                "source": task_data["source"],
                "priority": "medium"
            })
            
            task_id = response.json()["id"]
            self.created_tasks.append(task_id)
            
            # 更新任务状态
            if task_data["status"] != "pending":
                self.client.put(f"/api/v5/task/{task_id}", json={
                    "status": task_data["status"]
                })
        
        # 测试按状态过滤
        pending_response = self.client.get("/api/v5/task/list?status=pending")
        assert pending_response.status_code == 200
        pending_data = pending_response.json()
        assert len(pending_data["tasks"]) >= 2
        
        # 测试按来源过滤
        agent_response = self.client.get("/api/v5/task/list?source=agent_identified")
        assert agent_response.status_code == 200
        agent_data = agent_response.json()
        assert len(agent_data["tasks"]) >= 1
        
        print(f"✅ 任务列表过滤功能正常")
    
    def test_task_statistics(self):
        """测试任务统计功能"""
        response = self.client.get("/api/v5/task/stats/overview")
        
        assert response.status_code == 200
        stats_data = response.json()
        
        # 验证统计数据结构
        assert "total" in stats_data
        assert "by_status" in stats_data
        assert "by_source" in stats_data
        assert "completion_rate" in stats_data
        assert "rejection_rate" in stats_data
        
        # 验证状态统计
        status_stats = stats_data["by_status"]
        assert "pending" in status_stats
        assert "confirmed" in status_stats
        assert "executing" in status_stats
        assert "completed" in status_stats
        
        print(f"✅ 任务统计功能正常")
    
    def test_task_analysis(self):
        """测试任务分析功能"""
        response = self.client.get("/api/v5/task/analyze")
        
        assert response.status_code == 200
        analysis_data = response.json()
        
        # 验证分析数据结构
        assert "completion_rate" in analysis_data
        assert "avg_execution_time" in analysis_data
        assert "most_common_modules" in analysis_data
        assert "bottlenecks" in analysis_data
        assert "recommendations" in analysis_data
        
        # 验证分析结果类型
        assert isinstance(analysis_data["completion_rate"], (int, float))
        assert isinstance(analysis_data["avg_execution_time"], (int, float))
        assert isinstance(analysis_data["most_common_modules"], list)
        assert isinstance(analysis_data["bottlenecks"], list)
        assert isinstance(analysis_data["recommendations"], list)
        
        print(f"✅ 任务分析功能正常")
    
    def test_task_monitoring(self):
        """测试任务监控功能"""
        response = self.client.get("/api/v5/task/monitor")
        
        assert response.status_code == 200
        monitor_data = response.json()
        
        # 验证监控数据结构
        assert "executing_tasks" in monitor_data
        assert "monitoring_data" in monitor_data
        assert "alerts" in monitor_data
        
        # 验证数据类型
        assert isinstance(monitor_data["executing_tasks"], int)
        assert isinstance(monitor_data["monitoring_data"], list)
        assert isinstance(monitor_data["alerts"], list)
        
        print(f"✅ 任务监控功能正常")
    
    def test_task_planning(self):
        """测试智能任务规划"""
        response = self.client.post("/api/v5/task/plan", params={
            "goal": "完成本月财务分析报告",
            "time_limit": 180
        })
        
        assert response.status_code == 200
        plan_data = response.json()
        
        # 验证规划结果
        assert "goal" in plan_data
        assert "sub_tasks" in plan_data
        assert "total_estimated_duration" in plan_data
        assert "suggested_start" in plan_data
        assert "suggested_end" in plan_data
        
        # 验证子任务结构
        sub_tasks = plan_data["sub_tasks"]
        assert len(sub_tasks) > 0
        
        for task in sub_tasks:
            assert "title" in task
            assert "description" in task
            assert "estimated_duration" in task
        
        print(f"✅ 智能任务规划功能正常")
    
    def test_sync_with_agent(self):
        """测试与超级Agent同步"""
        response = self.client.post("/api/v5/task/sync-with-agent")
        
        assert response.status_code == 200
        sync_data = response.json()
        
        # 验证同步结果
        assert "success" in sync_data
        assert "new_tasks_created" in sync_data
        assert "tasks_reported" in sync_data
        assert "sync_time" in sync_data
        
        print(f"✅ 与超级Agent同步功能正常")
    
    def test_rate_limiting(self):
        """测试限流功能"""
        # 快速发送多个请求测试限流
        responses = []
        
        for i in range(15):  # 超过限流配置的10个请求
            response = self.client.post("/api/v5/task/create", json={
                "title": f"限流测试任务 {i}",
                "description": "限流功能测试",
                "source": "user_defined"
            })
            responses.append(response)
        
        # 统计成功和限流响应
        success_count = sum(1 for r in responses if r.status_code == 200)
        rate_limit_count = sum(1 for r in responses if r.status_code == 429)
        
        # 验证限流生效
        assert rate_limit_count > 0, "限流功能未生效"
        assert success_count <= 10, "限流配置不正确"
        
        print(f"✅ 限流功能正常: {success_count}成功, {rate_limit_count}限流")
    
    def test_error_handling(self):
        """测试错误处理"""
        # 测试无效任务ID
        response = self.client.get("/api/v5/task/invalid-task-id")
        assert response.status_code == 404
        
        # 测试无效确认请求
        response = self.client.post("/api/v5/task/confirm", json={
            "task_id": "nonexistent-task"
        })
        assert response.status_code == 404
        
        # 测试无效数据
        response = self.client.post("/api/v5/task/create", json={
            "invalid": "data"
        })
        assert response.status_code == 422  # 数据验证错误
        
        print(f"✅ 错误处理功能正常")


class TestTaskManagementPerformance:
    """性能测试类"""
    
    def setup_method(self):
        """性能测试设置"""
        self.client = TestClient(app)
        self.performance_results = []
    
    def test_create_task_performance(self):
        """测试任务创建性能"""
        import time
        
        start_time = time.time()
        
        # 批量创建任务
        for i in range(10):
            response = self.client.post("/api/v5/task/create", json={
                "title": f"性能测试任务 {i}",
                "description": "性能测试",
                "source": "user_defined"
            })
            assert response.status_code == 200
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # 记录性能结果
        self.performance_results.append({
            "test": "create_task_performance",
            "execution_time": execution_time,
            "tasks_per_second": 10 / execution_time
        })
        
        assert execution_time < 5.0, "任务创建性能不达标"
        print(f"✅ 任务创建性能: {execution_time:.3f}s ({10/execution_time:.1f} tasks/s)")
    
    def test_list_tasks_performance(self):
        """测试任务列表查询性能"""
        import time
        
        start_time = time.time()
        
        # 多次查询测试性能
        for i in range(20):
            response = self.client.get("/api/v5/task/list")
            assert response.status_code == 200
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # 记录性能结果
        self.performance_results.append({
            "test": "list_tasks_performance",
            "execution_time": execution_time,
            "queries_per_second": 20 / execution_time
        })
        
        assert execution_time < 3.0, "任务列表查询性能不达标"
        print(f"✅ 任务列表查询性能: {execution_time:.3f}s ({20/execution_time:.1f} queries/s)")


class TestTaskManagementConcurrency:
    """并发测试类"""
    
    def setup_method(self):
        """并发测试设置"""
        self.client = TestClient(app)
    
    async def test_concurrent_task_creation(self):
        """测试并发任务创建"""
        import asyncio
        
        async def create_task(i):
            response = self.client.post("/api/v5/task/create", json={
                "title": f"并发测试任务 {i}",
                "description": "并发测试",
                "source": "user_defined"
            })
            return response.status_code
        
        # 并发创建任务
        tasks = [create_task(i) for i in range(5)]
        results = await asyncio.gather(*tasks)
        
        # 验证所有请求都成功
        success_count = sum(1 for code in results if code == 200)
        assert success_count == 5, "并发任务创建失败"
        
        print(f"✅ 并发任务创建测试通过: {success_count}/5 成功")


def run_all_tests():
    """运行所有测试"""
    print("🚀 开始智能任务管理系统集成测试")
    print("=" * 60)
    
    # 创建测试实例
    integration_tester = TestTaskManagementIntegration()
    performance_tester = TestTaskManagementPerformance()
    
    # 运行集成测试
    integration_tests = [
        "test_create_task_from_user",
        "test_create_task_from_agent", 
        "test_task_confirmation_workflow",
        "test_task_rejection_workflow",
        "test_task_listing_with_filters",
        "test_task_statistics",
        "test_task_analysis",
        "test_task_monitoring",
        "test_task_planning",
        "test_sync_with_agent",
        "test_rate_limiting",
        "test_error_handling"
    ]
    
    integration_passed = 0
    for test_name in integration_tests:
        try:
            integration_tester.setup_method()
            getattr(integration_tester, test_name)()
            integration_tester.teardown_method()
            integration_passed += 1
            print(f"✅ {test_name}: 通过")
        except Exception as e:
            print(f"❌ {test_name}: 失败 - {e}")
    
    # 运行性能测试
    performance_tests = [
        "test_create_task_performance",
        "test_list_tasks_performance"
    ]
    
    performance_passed = 0
    for test_name in performance_tests:
        try:
            performance_tester.setup_method()
            getattr(performance_tester, test_name)()
            performance_passed += 1
            print(f"✅ {test_name}: 通过")
        except Exception as e:
            print(f"❌ {test_name}: 失败 - {e}")
    
    # 输出测试报告
    print("\n" + "=" * 60)
    print("📊 测试报告")
    print("=" * 60)
    print(f"集成测试: {integration_passed}/{len(integration_tests)} 通过")
    print(f"性能测试: {performance_passed}/{len(performance_tests)} 通过")
    print(f"总体通过率: {(integration_passed + performance_passed) / (len(integration_tests) + len(performance_tests)) * 100:.1f}%")
    
    if integration_passed == len(integration_tests) and performance_passed == len(performance_tests):
        print("🎉 所有测试通过！智能任务管理系统功能完整")
        return True
    else:
        print("⚠️ 部分测试失败，需要进一步优化")
        return False


if __name__ == "__main__":
    # 运行所有测试
    success = run_all_tests()
    
    # 退出码
    sys.exit(0 if success else 1)