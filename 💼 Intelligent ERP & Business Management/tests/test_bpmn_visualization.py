"""
Test BPMN Visualization End-to-End
测试BPMN可视化端到端功能

验证BPMN设计器、运行时追踪、可视化界面的完整功能
"""

import pytest
import json
import time
from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pathlib import Path
import sys

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


class TestBPMNVisualization:
    """BPMN可视化端到端测试类"""

    def test_bpmn_designer_interface(self):
        """测试BPMN设计器界面功能"""
        # 测试流程定义API
        process_data = {
            "name": "采购订单流程",
            "description": "完整的采购订单处理流程",
            "process_type": "采购流程",
            "stages": [
                {"name": "需求申请", "order": 1, "type": "start"},
                {"name": "审批", "order": 2, "type": "approval"},
                {"name": "采购执行", "order": 3, "type": "execution"},
                {"name": "收货验收", "order": 4, "type": "verification"},
                {"name": "财务结算", "order": 5, "type": "finance"},
                {"name": "完成归档", "order": 6, "type": "end"}
            ],
            "kpi_metrics": {"completion_rate": 95, "cycle_time": 24}
        }
        
        response = client.post("/process/define", json=process_data)
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        process_id = result["process_id"]
        
        # 测试获取流程定义
        response = client.get(f"/process/{process_id}")
        assert response.status_code == 200
        process_info = response.json()
        assert process_info["name"] == "采购订单流程"
        assert len(process_info["stages"]) == 6
        
        # 测试BPMN XML生成
        response = client.get(f"/process/{process_id}/bpmn")
        assert response.status_code == 200
        bpmn_xml = response.text
        assert "bpmn:definitions" in bpmn_xml
        assert "采购订单流程" in bpmn_xml

    def test_bpmn_runtime_tracking(self):
        """测试BPMN运行时追踪功能"""
        # 创建流程定义
        db = next(override_get_db())
        process = BusinessProcess(
            name="销售订单流程",
            stages=[
                {"name": "订单接收", "order": 1},
                {"name": "库存检查", "order": 2},
                {"name": "生产安排", "order": 3},
                {"name": "发货", "order": 4},
                {"name": "客户确认", "order": 5}
            ]
        )
        db.add(process)
        db.commit()
        process_id = process.id
        db.close()
        
        # 创建多个流程实例
        instances_data = []
        for i in range(3):
            instance_data = {
                "process_id": process_id,
                "instance_name": f"销售订单实例{i+1}"
            }
            response = client.post("/process/instance/create", json=instance_data)
            assert response.status_code == 200
            instance_result = response.json()
            instances_data.append(instance_result)
        
        # 测试获取活跃实例
        response = client.get("/process/instances/active")
        assert response.status_code == 200
        active_instances = response.json()
        assert len(active_instances) >= 3
        
        # 测试流程追踪时间线
        for instance in instances_data:
            instance_id = instance["instance_id"]
            response = client.get(f"/process/instance/{instance_id}/timeline")
            assert response.status_code == 200
            timeline = response.json()
            assert "events" in timeline
            assert "current_stage" in timeline

    def test_visualization_performance(self):
        """测试可视化性能"""
        # 创建大量流程实例进行性能测试
        db = next(override_get_db())
        process = BusinessProcess(
            name="性能测试流程",
            stages=[{"name": "测试阶段", "order": 1}]
        )
        db.add(process)
        db.commit()
        process_id = process.id
        
        # 批量创建实例
        start_time = time.time()
        for i in range(50):  # 创建50个实例
            instance = ProcessInstance(
                process_id=process_id,
                instance_name=f"性能测试实例{i}",
                current_stage="测试阶段"
            )
            db.add(instance)
        db.commit()
        
        # 测试获取所有实例的性能
        response = client.get("/process/instances")
        end_time = time.time()
        
        assert response.status_code == 200
        instances = response.json()
        
        # 性能要求：50个实例的查询时间应小于2秒
        assert (end_time - start_time) < 2.0
        assert len(instances) >= 50
        
        db.close()

    def test_11_stage_complete_process_tracking(self):
        """测试11个环节的完整流程追踪能力"""
        # 定义11个环节的完整流程
        eleven_stages = [
            {"name": "需求分析", "order": 1},
            {"name": "方案设计", "order": 2},
            {"name": "预算审批", "order": 3},
            {"name": "采购申请", "order": 4},
            {"name": "供应商选择", "order": 5},
            {"name": "合同签订", "order": 6},
            {"name": "生产制造", "order": 7},
            {"name": "质量检验", "order": 8},
            {"name": "物流配送", "order": 9},
            {"name": "客户验收", "order": 10},
            {"name": "售后服务", "order": 11}
        ]
        
        # 创建流程定义
        process_data = {
            "name": "11环节完整业务流程",
            "description": "包含11个环节的端到端业务流程",
            "process_type": "完整业务流",
            "stages": eleven_stages,
            "kpi_metrics": {"total_stages": 11, "target_completion": 100}
        }
        
        response = client.post("/process/define", json=process_data)
        assert response.status_code == 200
        process_result = response.json()
        process_id = process_result["process_id"]
        
        # 创建流程实例
        instance_data = {
            "process_id": process_id,
            "instance_name": "11环节测试实例"
        }
        response = client.post("/process/instance/create", json=instance_data)
        assert response.status_code == 200
        instance_result = response.json()
        instance_id = instance_result["instance_id"]
        
        # 模拟11个环节的完整追踪
        for i, stage in enumerate(eleven_stages):
            tracking_data = {
                "instance_id": instance_id,
                "stage": stage["name"],
                "status": "completed" if i < 10 else "in_progress",
                "action": f"完成{stage['name']}环节",
                "operator": f"操作员{i+1}",
                "notes": f"第{i+1}个环节执行完成"
            }
            
            response = client.post(f"/process/instance/{instance_id}/track", json=tracking_data)
            assert response.status_code == 200
            
            # 验证进度
            response = client.get(f"/process/instance/{instance_id}/progress")
            assert response.status_code == 200
            progress = response.json()
            
            expected_percentage = min(100, (i + 1) * 100 / 11)
            assert abs(progress["progress_percentage"] - expected_percentage) < 1
            assert progress["current_stage"] == stage["name"]
            assert len(progress["completed_stages"]) == i + 1

    def test_bpmn_visualization_integration(self):
        """测试BPMN可视化集成功能"""
        # 测试流程可视化数据接口
        response = client.get("/process/visualization/data")
        assert response.status_code == 200
        visualization_data = response.json()
        
        # 验证返回的数据结构
        assert "processes" in visualization_data
        assert "instances" in visualization_data
        assert "statistics" in visualization_data
        
        # 测试BPMN运行时状态
        response = client.get("/process/runtime/status")
        assert response.status_code == 200
        runtime_status = response.json()
        
        assert "active_instances" in runtime_status
        assert "completed_instances" in runtime_status
        assert "average_cycle_time" in runtime_status


if __name__ == "__main__":
    pytest.main([__file__, "-v"])