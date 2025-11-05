"""
Test Process API
测试流程管理API

验证流程定义、流程实例、流程跟踪等功能
"""

import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import sys
from pathlib import Path
erp_dir = Path(__file__).parent.parent
sys.path.insert(0, str(erp_dir))

from core.database_models import (
    Base,
    BusinessProcess,
    ProcessInstance,
    ProcessTracking,
    ProcessStatus,
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
    Base.metadata.create_all(test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


def test_define_process():
    """测试定义流程"""
    data = {
        "name": "测试流程",
        "description": "这是一个测试流程",
        "process_type": "生产流程",
        "stages": [
            {"name": "阶段1", "order": 1},
            {"name": "阶段2", "order": 2},
        ],
        "kpi_metrics": {"completion_rate": 95},
    }
    
    response = client.post("/process/define", json=data)
    
    assert response.status_code == 200
    result = response.json()
    assert result["success"] is True
    assert "process_id" in result


def test_create_process_instance():
    """测试创建流程实例"""
    # 先创建流程定义
    db = next(override_get_db())
    process = BusinessProcess(
        name="测试流程",
        stages=[{"name": "初始", "order": 1}, {"name": "完成", "order": 2}],
    )
    db.add(process)
    db.commit()
    process_id = process.id
    db.close()
    
    # 创建流程实例
    data = {
        "process_id": process_id,
        "instance_name": "测试实例1",
    }
    
    response = client.post("/process/instance/create", json=data)
    
    assert response.status_code == 200
    result = response.json()
    assert result["success"] is True
    assert "instance_id" in result
    assert result["status"] == "pending"


def test_track_process():
    """测试流程跟踪"""
    # 创建流程和实例
    db = next(override_get_db())
    process = BusinessProcess(
        name="测试流程",
        stages=[{"name": "阶段1", "order": 1}],
    )
    db.add(process)
    db.flush()
    
    instance = ProcessInstance(
        process_id=process.id,
        instance_name="测试实例",
        status=ProcessStatus.IN_PROGRESS,
        current_stage="阶段1",
    )
    db.add(instance)
    db.commit()
    instance_id = instance.id
    db.close()
    
    # 跟踪流程
    data = {
        "instance_id": instance_id,
        "stage": "阶段1",
        "status": "completed",
        "action": "完成任务",
        "operator": "张三",
        "notes": "测试备注",
    }
    
    response = client.post(f"/process/instance/{instance_id}/track", json=data)
    
    assert response.status_code == 200
    result = response.json()
    assert result["success"] is True
    assert "tracking_id" in result


def test_get_process_progress():
    """测试获取流程进度"""
    # 创建流程和实例
    db = next(override_get_db())
    process = BusinessProcess(
        name="测试流程",
        stages=[
            {"name": "阶段1", "order": 1},
            {"name": "阶段2", "order": 2},
        ],
    )
    db.add(process)
    db.flush()
    
    instance = ProcessInstance(
        process_id=process.id,
        instance_name="测试实例",
        status=ProcessStatus.IN_PROGRESS,
        current_stage="阶段1",
    )
    db.add(instance)
    db.flush()
    
    # 创建跟踪记录
    tracking = ProcessTracking(
        instance_id=instance.id,
        stage="阶段1",
        status="completed",
        action="完成阶段1",
    )
    db.add(tracking)
    db.commit()
    instance_id = instance.id
    db.close()
    
    # 获取进度
    response = client.get(f"/process/instance/{instance_id}/progress")
    
    assert response.status_code == 200
    result = response.json()
    assert result["instance_id"] == instance_id
    assert result["current_stage"] == "阶段1"
    assert result["progress_percentage"] > 0
    assert len(result["completed_stages"]) >= 0


def test_get_full_process_flow():
    """测试获取全流程视图"""
    response = client.get("/process/full-flow")
    
    assert response.status_code == 200
    result = response.json()
    assert "flow_stages" in result
    assert len(result["flow_stages"]) == 16  # 16个标准阶段
    assert "instances" in result
    assert "progress" in result


def test_create_exception():
    """测试创建流程异常"""
    # 创建流程实例
    db = next(override_get_db())
    process = BusinessProcess(name="测试流程", stages=[{"name": "阶段1", "order": 1}])
    db.add(process)
    db.flush()
    
    instance = ProcessInstance(process_id=process.id, status=ProcessStatus.IN_PROGRESS)
    db.add(instance)
    db.commit()
    instance_id = instance.id
    db.close()
    
    # 创建异常
    data = {
        "instance_id": instance_id,
        "exception_type": "延迟",
        "exception_level": "warning",
        "description": "流程延迟警告",
    }
    
    response = client.post("/process/exceptions", json=data)
    
    assert response.status_code == 200
    result = response.json()
    assert result["success"] is True
    assert "exception_id" in result


def test_get_exceptions():
    """测试获取流程异常"""
    response = client.get("/process/exceptions")
    
    assert response.status_code == 200
    result = response.json()
    assert "success" in result
    assert "exceptions" in result
    assert "count" in result


def test_get_improvements():
    """测试获取改进计划"""
    response = client.get("/process/improvements")
    
    assert response.status_code == 200
    result = response.json()
    assert "success" in result
    assert "plans" in result
    assert "count" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

