"""
添加流程测试数据
"""

import sys
sys.path.insert(0, '/Users/ywc/ai-stack-super-enhanced/💼 Intelligent ERP & Business Management')

from datetime import datetime, timedelta
from core.database import SessionLocal
from core.database_models import (
    BusinessProcess, 
    ProcessInstance, 
    ProcessTracking,
    ProcessException,
    ImprovementPlan
)
import random

def add_process_data():
    """添加流程测试数据"""
    db = SessionLocal()
    
    try:
        print("📝 开始添加流程测试数据...")
        
        # 1. 创建标准业务流程定义（16个阶段）
        standard_stages = [
            {"order": 1, "name": "市场调研", "duration_days": 3},
            {"order": 2, "name": "客户开发", "duration_days": 5},
            {"order": 3, "name": "项目开发", "duration_days": 7},
            {"order": 4, "name": "投产管理", "duration_days": 3},
            {"order": 5, "name": "订单管理", "duration_days": 2},
            {"order": 6, "name": "生产计划", "duration_days": 3},
            {"order": 7, "name": "物料需求计划", "duration_days": 2},
            {"order": 8, "name": "采购计划", "duration_days": 3},
            {"order": 9, "name": "到料", "duration_days": 7},
            {"order": 10, "name": "生产执行", "duration_days": 10},
            {"order": 11, "name": "检验", "duration_days": 2},
            {"order": 12, "name": "入库", "duration_days": 1},
            {"order": 13, "name": "储存", "duration_days": 3},
            {"order": 14, "name": "交付", "duration_days": 2},
            {"order": 15, "name": "发运", "duration_days": 3},
            {"order": 16, "name": "客户账款回款", "duration_days": 30},
        ]
        
        process = BusinessProcess(
            name="标准订单处理流程",
            description="从市场调研到客户回款的完整业务流程",
            process_type="order_fulfillment",
            stages=standard_stages,
            kpi_metrics={
                "total_duration": 82,
                "key_metrics": ["订单准时率", "客户满意度", "回款率"]
            },
            is_active=True
        )
        db.add(process)
        db.commit()
        db.refresh(process)
        print(f"✅ 创建标准流程: {process.name}")
        
        # 2. 创建流程实例
        instances_data = [
            {
                "name": "订单 #SO-20251101-001",
                "status": "in_progress",
                "current_stage": "生产执行",
                "progress": 10
            },
            {
                "name": "订单 #SO-20251025-003",
                "status": "in_progress",
                "current_stage": "检验",
                "progress": 11
            },
            {
                "name": "订单 #SO-20251020-002",
                "status": "in_progress",
                "current_stage": "交付",
                "progress": 14
            },
            {
                "name": "订单 #SO-20251015-001",
                "status": "completed",
                "current_stage": "客户账款回款",
                "progress": 16
            },
            {
                "name": "订单 #SO-20251102-005",
                "status": "pending",
                "current_stage": "市场调研",
                "progress": 1
            },
        ]
        
        instances = []
        for inst_data in instances_data:
            instance = ProcessInstance(
                process_id=process.id,
                instance_name=inst_data["name"],
                status=inst_data["status"],
                current_stage=inst_data["current_stage"],
                started_at=datetime.now() - timedelta(days=random.randint(5, 30)),
                completed_at=datetime.now() if inst_data["status"] == "completed" else None,
                extra_metadata={"order_number": inst_data["name"].split("#")[1]}
            )
            db.add(instance)
            instances.append((instance, inst_data["progress"]))
        
        db.commit()
        print(f"✅ 创建了 {len(instances)} 个流程实例")
        
        # 3. 为每个实例添加跟踪记录
        for instance, progress_index in instances:
            db.refresh(instance)
            
            # 添加已完成的阶段
            for i in range(progress_index):
                stage_info = standard_stages[i]
                tracking = ProcessTracking(
                    instance_id=instance.id,
                    stage=stage_info["name"],
                    status="completed",
                    action=f"完成{stage_info['name']}",
                    operator=random.choice(["张三", "李四", "王五"]),
                    duration=random.randint(1, 10) * 3600,  # 秒
                    notes=f"{stage_info['name']}已完成",
                    created_at=datetime.now() - timedelta(days=30-i*2)
                )
                db.add(tracking)
        
        db.commit()
        print(f"✅ 添加了流程跟踪记录")
        
        # 4. 添加流程异常
        exceptions_data = [
            {
                "instance_id": instances[0][0].id,
                "type": "delay",
                "level": "warning",
                "description": "物料到料延迟3天，影响生产计划",
                "status": "investigating"
            },
            {
                "instance_id": instances[1][0].id,
                "type": "quality",
                "level": "error",
                "description": "质量检验发现不合格品，需要返工",
                "status": "resolved",
                "resolved": True
            },
            {
                "instance_id": instances[2][0].id,
                "type": "resource",
                "level": "info",
                "description": "仓储空间紧张，需要协调",
                "status": "open"
            },
        ]
        
        for exc_data in exceptions_data:
            exception = ProcessException(
                instance_id=exc_data["instance_id"],
                exception_type=exc_data["type"],
                exception_level=exc_data["level"],
                description=exc_data["description"],
                detected_at=datetime.now() - timedelta(days=random.randint(1, 5)),
                status=exc_data["status"],
                resolved_at=datetime.now() - timedelta(days=1) if exc_data.get("resolved") else None,
                resolution="问题已解决" if exc_data.get("resolved") else None
            )
            db.add(exception)
        
        db.commit()
        print(f"✅ 添加了 {len(exceptions_data)} 个流程异常")
        
        # 5. 添加改进计划
        improvement = ImprovementPlan(
            title="优化物料采购流程",
            description="缩短物料采购周期，提高到料准时率",
            related_exception_id=1,
            priority="high",
            status="in_progress",
            planned_start=datetime.now().date() - timedelta(days=3),
            planned_end=datetime.now().date() + timedelta(days=7),
            actual_start=datetime.now().date() - timedelta(days=3),
            responsible="采购部-李四",
            progress=45.0,
            notes="已完成供应商评估，正在优化采购流程"
        )
        db.add(improvement)
        db.commit()
        print(f"✅ 添加了改进计划")
        
        print("=" * 50)
        print("🎉 流程测试数据添加完成！")
        print(f"   - 流程定义: 1个（16个阶段）")
        print(f"   - 流程实例: {len(instances)} 个")
        print(f"   - 流程异常: {len(exceptions_data)} 个")
        print(f"   - 改进计划: 1个")
        
    except Exception as e:
        print(f"❌ 添加数据失败: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    add_process_data()

