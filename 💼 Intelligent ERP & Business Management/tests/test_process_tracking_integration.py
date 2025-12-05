"""
Test Process Tracking Integration
测试流程追踪集成功能

验证流程追踪与BPMN可视化界面的集成测试
"""

import pytest
import json
import time
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pathlib import Path
import sys

# 添加ERP模块路径
erp_dir = Path(__file__).parent.parent
sys.path.insert(0, str(erp_dir))

from core.database_models import (
    Base, BusinessProcess, ProcessInstance, ProcessTracking, 
    ProcessStatus, ProcessException, ProcessImprovement
)
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


class TestProcessTrackingIntegration:
    """流程追踪集成测试类"""

    def test_real_time_process_tracking(self):
        """测试实时流程追踪功能"""
        # 创建复杂业务流程
        complex_process = {
            "name": "复杂业务流程",
            "description": "包含多个并行和串行环节的复杂流程",
            "process_type": "复杂流程",
            "stages": [
                {"name": "需求收集", "order": 1, "parallel": False},
                {"name": "技术评估", "order": 2, "parallel": True},
                {"name": "商务评估", "order": 2, "parallel": True},
                {"name": "风险评估", "order": 2, "parallel": True},
                {"name": "综合决策", "order": 3, "parallel": False},
                {"name": "执行实施", "order": 4, "parallel": False},
                {"name": "验收交付", "order": 5, "parallel": False}
            ]
        }
        
        response = client.post("/process/define", json=complex_process)
        assert response.status_code == 200
        process_id = response.json()["process_id"]
        
        # 创建流程实例
        instance_data = {"process_id": process_id, "instance_name": "复杂流程实例"}
        response = client.post("/process/instance/create", json=instance_data)
        assert response.status_code == 200
        instance_id = response.json()["instance_id"]
        
        # 模拟实时追踪事件
        tracking_events = [
            {"stage": "需求收集", "status": "completed", "action": "完成需求分析"},
            {"stage": "技术评估", "status": "in_progress", "action": "开始技术评估"},
            {"stage": "商务评估", "status": "pending", "action": "等待商务评估"},
            {"stage": "风险评估", "status": "in_progress", "action": "进行风险评估"}
        ]
        
        for event in tracking_events:
            tracking_data = {
                "instance_id": instance_id,
                "stage": event["stage"],
                "status": event["status"],
                "action": event["action"],
                "operator": "系统管理员",
                "notes": f"{event['stage']}环节追踪事件"
            }
            
            response = client.post(f"/process/instance/{instance_id}/track", json=tracking_data)
            assert response.status_code == 200
            
            # 验证实时状态更新
            response = client.get(f"/process/instance/{instance_id}/status")
            assert response.status_code == 200
            status_info = response.json()
            assert status_info["current_stage"] == event["stage"]

    def test_process_exception_handling(self):
        """测试流程异常处理与追踪"""
        # 创建流程定义
        db = next(override_get_db())
        process = BusinessProcess(
            name="异常处理流程",
            stages=[{"name": "执行阶段", "order": 1}]
        )
        db.add(process)
        db.commit()
        process_id = process.id
        
        # 创建流程实例
        instance = ProcessInstance(
            process_id=process_id,
            instance_name="异常测试实例",
            current_stage="执行阶段"
        )
        db.add(instance)
        db.commit()
        instance_id = instance.id
        
        # 创建异常记录
        exception_data = {
            "instance_id": instance_id,
            "exception_type": "系统错误",
            "description": "数据库连接超时",
            "severity": "high",
            "suggested_action": "检查数据库连接配置"
        }
        
        response = client.post("/process/exception/create", json=exception_data)
        assert response.status_code == 200
        exception_result = response.json()
        assert exception_result["success"] is True
        
        # 验证异常追踪
        response = client.get(f"/process/instance/{instance_id}/exceptions")
        assert response.status_code == 200
        exceptions = response.json()
        assert len(exceptions) > 0
        assert exceptions[0]["exception_type"] == "系统错误"
        
        db.close()

    def test_process_improvement_tracking(self):
        """测试流程改进追踪功能"""
        # 创建流程定义和实例
        db = next(override_get_db())
        process = BusinessProcess(
            name="改进追踪流程",
            stages=[{"name": "改进阶段", "order": 1}]
        )
        db.add(process)
        db.commit()
        process_id = process.id
        
        instance = ProcessInstance(
            process_id=process_id,
            instance_name="改进测试实例"
        )
        db.add(instance)
        db.commit()
        instance_id = instance.id
        
        # 创建改进计划
        improvement_data = {
            "instance_id": instance_id,
            "improvement_area": "流程效率",
            "current_state": "处理时间过长",
            "target_state": "缩短处理时间50%",
            "action_items": [
                "优化数据库查询",
                "引入缓存机制",
                "并行处理任务"
            ],
            "expected_benefits": "提高处理效率，减少等待时间"
        }
        
        response = client.post("/process/improvement/create", json=improvement_data)
        assert response.status_code == 200
        improvement_result = response.json()
        assert improvement_result["success"] is True
        
        # 验证改进追踪
        response = client.get(f"/process/instance/{instance_id}/improvements")
        assert response.status_code == 200
        improvements = response.json()
        assert len(improvements) > 0
        assert improvements[0]["improvement_area"] == "流程效率"
        
        db.close()

    def test_multi_instance_tracking_dashboard(self):
        """测试多实例追踪仪表板功能"""
        # 创建多个流程实例
        db = next(override_get_db())
        
        # 创建多个流程定义
        processes = []
        for i in range(3):
            process = BusinessProcess(
                name=f"流程{i+1}",
                stages=[{"name": "阶段1", "order": 1}, {"name": "阶段2", "order": 2}]
            )
            db.add(process)
            processes.append(process)
        
        db.commit()
        
        # 为每个流程创建多个实例
        instances = []
        for process in processes:
            for j in range(5):
                instance = ProcessInstance(
                    process_id=process.id,
                    instance_name=f"{process.name}实例{j+1}",
                    current_stage="阶段1" if j < 3 else "阶段2"
                )
                db.add(instance)
                instances.append(instance)
        
        db.commit()
        db.close()
        
        # 测试仪表板数据接口
        response = client.get("/process/dashboard/overview")
        assert response.status_code == 200
        dashboard_data = response.json()
        
        # 验证仪表板数据结构
        assert "total_processes" in dashboard_data
        assert "total_instances" in dashboard_data
        assert "active_instances" in dashboard_data
        assert "completion_rate" in dashboard_data
        assert "recent_activities" in dashboard_data
        
        # 测试实例状态分布
        response = client.get("/process/dashboard/status-distribution")
        assert response.status_code == 200
        status_distribution = response.json()
        
        assert "pending" in status_distribution
        assert "in_progress" in status_distribution
        assert "completed" in status_distribution
        assert "failed" in status_distribution

    def test_process_timeline_visualization(self):
        """测试流程时间线可视化功能"""
        # 创建带有时序数据的流程实例
        db = next(override_get_db())
        
        process = BusinessProcess(
            name="时间线测试流程",
            stages=[
                {"name": "开始", "order": 1},
                {"name": "处理", "order": 2},
                {"name": "结束", "order": 3}
            ]
        )
        db.add(process)
        db.commit()
        
        instance = ProcessInstance(
            process_id=process.id,
            instance_name="时间线测试实例"
        )
        db.add(instance)
        db.commit()
        instance_id = instance.id
        
        # 创建带时间戳的追踪记录
        base_time = datetime.now()
        tracking_records = [
            {
                "stage": "开始",
                "status": "completed",
                "action": "启动流程",
                "timestamp": base_time
            },
            {
                "stage": "处理",
                "status": "in_progress",
                "action": "处理中",
                "timestamp": base_time + timedelta(minutes=30)
            },
            {
                "stage": "结束",
                "status": "pending",
                "action": "等待完成",
                "timestamp": base_time + timedelta(hours=1)
            }
        ]
        
        for record in tracking_records:
            tracking = ProcessTracking(
                instance_id=instance_id,
                stage=record["stage"],
                status=record["status"],
                action=record["action"],
                created_at=record["timestamp"]
            )
            db.add(tracking)
        
        db.commit()
        db.close()
        
        # 测试时间线接口
        response = client.get(f"/process/instance/{instance_id}/timeline")
        assert response.status_code == 200
        timeline = response.json()
        
        # 验证时间线数据结构
        assert "events" in timeline
        assert "start_time" in timeline
        assert "end_time" in timeline
        assert "duration" in timeline
        assert len(timeline["events"]) == 3
        
        # 验证事件顺序
        events = timeline["events"]
        assert events[0]["stage"] == "开始"
        assert events[1]["stage"] == "处理"
        assert events[2]["stage"] == "结束"

    def test_process_kpi_tracking(self):
        """测试流程KPI追踪功能"""
        # 创建带KPI指标的流程
        kpi_process = {
            "name": "KPI追踪流程",
            "description": "包含KPI指标追踪的流程",
            "process_type": "KPI流程",
            "stages": [
                {"name": "阶段1", "order": 1, "target_duration": 60},
                {"name": "阶段2", "order": 2, "target_duration": 120},
                {"name": "阶段3", "order": 3, "target_duration": 180}
            ],
            "kpi_metrics": {
                "target_completion_rate": 95,
                "target_cycle_time": 360,
                "quality_threshold": 0.95
            }
        }
        
        response = client.post("/process/define", json=kpi_process)
        assert response.status_code == 200
        process_id = response.json()["process_id"]
        
        # 创建流程实例并模拟KPI数据
        instance_data = {"process_id": process_id, "instance_name": "KPI测试实例"}
        response = client.post("/process/instance/create", json=instance_data)
        assert response.status_code == 200
        instance_id = response.json()["instance_id"]
        
        # 测试KPI追踪接口
        response = client.get(f"/process/instance/{instance_id}/kpi")
        assert response.status_code == 200
        kpi_data = response.json()
        
        # 验证KPI数据结构
        assert "completion_rate" in kpi_data
        assert "cycle_time" in kpi_data
        assert "quality_score" in kpi_data
        assert "performance_indicators" in kpi_data
        assert "targets" in kpi_data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])