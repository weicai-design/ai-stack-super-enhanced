"""
Test Visualization Performance
测试流程可视化性能

验证BPMN可视化界面的性能指标、压力测试和性能优化
"""

import pytest
import time
import json
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pathlib import Path
import sys
import threading

# 添加ERP模块路径
erp_dir = Path(__file__).parent.parent
sys.path.insert(0, str(erp_dir))

from core.database_models import Base, BusinessProcess, ProcessInstance, ProcessTracking
from core.database import get_db
from api.process_api import router
from fastapi import FastAPI

# 创建测试应用
app = FastAPI()
app.include_router(router)

# 创建测试数据库
test_engine = create_engine("sqlite:///:memory:", echo=False)
Base.metadata.create_all(test_engine)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    """覆盖get_db依赖"""
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    """每个测试前设置数据库"""
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


class TestVisualizationPerformance:
    """流程可视化性能测试类"""

    def test_large_scale_process_loading(self):
        """测试大规模流程加载性能"""
        # 创建大量流程定义
        db = next(override_get_db())
        
        start_time = time.time()
        
        # 批量创建100个流程定义
        for i in range(100):
            process = BusinessProcess(
                name=f"性能测试流程{i}",
                description=f"第{i}个性能测试流程",
                stages=[{"name": "阶段1", "order": 1}, {"name": "阶段2", "order": 2}]
            )
            db.add(process)
        
        db.commit()
        
        # 测试流程列表加载性能
        response = client.get("/process/list")
        end_time = time.time()
        
        assert response.status_code == 200
        processes = response.json()
        
        # 性能要求：100个流程的列表加载时间应小于1秒
        load_time = end_time - start_time
        assert load_time < 1.0, f"流程列表加载时间过长: {load_time:.2f}秒"
        assert len(processes) >= 100
        
        db.close()

    def test_high_concurrency_instance_tracking(self):
        """测试高并发实例追踪性能"""
        # 创建基础流程
        db = next(override_get_db())
        process = BusinessProcess(
            name="高并发测试流程",
            stages=[{"name": "并发阶段", "order": 1}]
        )
        db.add(process)
        db.commit()
        process_id = process.id
        
        # 创建100个实例用于并发测试
        instances = []
        for i in range(100):
            instance = ProcessInstance(
                process_id=process_id,
                instance_name=f"并发实例{i}",
                current_stage="并发阶段"
            )
            db.add(instance)
            instances.append(instance)
        
        db.commit()
        
        # 模拟并发追踪请求
        def track_instance(instance_id):
            tracking_data = {
                "instance_id": instance_id,
                "stage": "并发阶段",
                "status": "completed",
                "action": "并发完成",
                "operator": "并发测试"
            }
            response = client.post(f"/process/instance/{instance_id}/track", json=tracking_data)
            return response.status_code == 200
        
        # 并发执行追踪
        start_time = time.time()
        
        # 使用线程模拟并发
        threads = []
        for instance in instances:
            thread = threading.Thread(target=track_instance, args=(instance.id,))
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        
        # 性能要求：100个并发追踪请求应在3秒内完成
        concurrent_time = end_time - start_time
        assert concurrent_time < 3.0, f"并发追踪时间过长: {concurrent_time:.2f}秒"
        
        db.close()

    def test_real_time_visualization_refresh(self):
        """测试实时可视化刷新性能"""
        # 创建带有时序数据的流程实例
        db = next(override_get_db())
        
        process = BusinessProcess(
            name="实时刷新测试流程",
            stages=[{"name": "实时阶段", "order": 1}]
        )
        db.add(process)
        db.commit()
        
        # 创建实例并添加追踪记录
        instance = ProcessInstance(
            process_id=process.id,
            instance_name="实时刷新实例"
        )
        db.add(instance)
        db.commit()
        instance_id = instance.id
        
        # 测试实时状态接口的响应时间
        refresh_times = []
        
        for i in range(10):  # 测试10次刷新
            start_time = time.time()
            response = client.get(f"/process/instance/{instance_id}/status")
            end_time = time.time()
            
            assert response.status_code == 200
            refresh_times.append(end_time - start_time)
            
            # 添加新的追踪记录模拟实时更新
            tracking = ProcessTracking(
                instance_id=instance_id,
                stage="实时阶段",
                status="in_progress",
                action=f"第{i}次刷新"
            )
            db.add(tracking)
            db.commit()
        
        # 计算平均刷新时间
        avg_refresh_time = sum(refresh_times) / len(refresh_times)
        
        # 性能要求：实时刷新平均时间应小于200毫秒
        assert avg_refresh_time < 0.2, f"实时刷新时间过长: {avg_refresh_time:.3f}秒"
        
        db.close()

    def test_bpmn_xml_generation_performance(self):
        """测试BPMN XML生成性能"""
        # 创建复杂流程定义
        complex_process = {
            "name": "复杂BPMN流程",
            "description": "包含多个节点和连接的复杂流程",
            "process_type": "复杂流程",
            "stages": [
                {"name": "开始", "order": 1, "type": "start"},
                {"name": "任务1", "order": 2, "type": "task"},
                {"name": "决策点", "order": 3, "type": "gateway"},
                {"name": "分支A", "order": 4, "type": "task"},
                {"name": "分支B", "order": 4, "type": "task"},
                {"name": "合并点", "order": 5, "type": "gateway"},
                {"name": "结束", "order": 6, "type": "end"}
            ],
            "connections": [
                {"from": "开始", "to": "任务1"},
                {"from": "任务1", "to": "决策点"},
                {"from": "决策点", "to": "分支A", "condition": "条件A"},
                {"from": "决策点", "to": "分支B", "condition": "条件B"},
                {"from": "分支A", "to": "合并点"},
                {"from": "分支B", "to": "合并点"},
                {"from": "合并点", "to": "结束"}
            ]
        }
        
        response = client.post("/process/define", json=complex_process)
        assert response.status_code == 200
        process_id = response.json()["process_id"]
        
        # 测试BPMN XML生成性能
        start_time = time.time()
        response = client.get(f"/process/{process_id}/bpmn")
        end_time = time.time()
        
        assert response.status_code == 200
        bpmn_xml = response.text
        
        # 性能要求：复杂BPMN XML生成时间应小于500毫秒
        generation_time = end_time - start_time
        assert generation_time < 0.5, f"BPMN XML生成时间过长: {generation_time:.3f}秒"
        
        # 验证XML内容
        assert "bpmn:definitions" in bpmn_xml
        assert "复杂BPMN流程" in bpmn_xml
        assert "开始" in bpmn_xml
        assert "结束" in bpmn_xml

    def test_dashboard_data_aggregation_performance(self):
        """测试仪表板数据聚合性能"""
        # 创建大量实例数据用于聚合测试
        db = next(override_get_db())
        
        # 创建多个流程
        processes = []
        for i in range(5):
            process = BusinessProcess(
                name=f"聚合测试流程{i}",
                stages=[{"name": "阶段1", "order": 1}, {"name": "阶段2", "order": 2}]
            )
            db.add(process)
            processes.append(process)
        
        db.commit()
        
        # 为每个流程创建50个实例
        for process in processes:
            for j in range(50):
                instance = ProcessInstance(
                    process_id=process.id,
                    instance_name=f"{process.name}实例{j}",
                    current_stage="阶段1" if j < 25 else "阶段2",
                    status="pending" if j < 10 else "in_progress" if j < 40 else "completed"
                )
                db.add(instance)
        
        db.commit()
        
        # 测试仪表板数据聚合性能
        start_time = time.time()
        response = client.get("/process/dashboard/overview")
        end_time = time.time()
        
        assert response.status_code == 200
        dashboard_data = response.json()
        
        # 性能要求：250个实例的仪表板聚合时间应小于1秒
        aggregation_time = end_time - start_time
        assert aggregation_time < 1.0, f"仪表板数据聚合时间过长: {aggregation_time:.2f}秒"
        
        # 验证聚合数据
        assert dashboard_data["total_processes"] >= 5
        assert dashboard_data["total_instances"] >= 250
        assert "active_instances" in dashboard_data
        assert "completion_rate" in dashboard_data
        
        db.close()

    def test_memory_usage_under_load(self):
        """测试负载下的内存使用情况"""
        import psutil
        import os
        
        # 获取初始内存使用
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 创建大量数据模拟高负载
        db = next(override_get_db())
        
        # 创建100个流程定义
        for i in range(100):
            process = BusinessProcess(
                name=f"内存测试流程{i}",
                stages=[{"name": "内存阶段", "order": 1}]
            )
            db.add(process)
        
        db.commit()
        
        # 执行多次查询模拟负载
        for i in range(100):
            response = client.get("/process/list")
            assert response.status_code == 200
        
        # 获取负载后的内存使用
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # 内存使用增长应小于50MB
        assert memory_increase < 50, f"内存使用增长过多: {memory_increase:.2f}MB"
        
        db.close()

    def test_response_time_consistency(self):
        """测试响应时间一致性"""
        # 测试关键接口的响应时间一致性
        endpoints_to_test = [
            "/process/list",
            "/process/instances/active", 
            "/process/dashboard/overview"
        ]
        
        for endpoint in endpoints_to_test:
            response_times = []
            
            # 测试10次获取响应时间分布
            for i in range(10):
                start_time = time.time()
                response = client.get(endpoint)
                end_time = time.time()
                
                assert response.status_code == 200
                response_times.append(end_time - start_time)
            
            # 计算标准差，评估响应时间稳定性
            avg_time = sum(response_times) / len(response_times)
            variance = sum((t - avg_time) ** 2 for t in response_times) / len(response_times)
            std_dev = variance ** 0.5
            
            # 响应时间标准差应小于平均时间的20%
            assert std_dev < avg_time * 0.2, f"{endpoint}响应时间不稳定: 标准差={std_dev:.3f}, 平均值={avg_time:.3f}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])