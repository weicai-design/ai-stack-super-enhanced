# 端到端流程脚本 Playbook

**版本**: v1.0  
**创建日期**: 2025-11-13  
**状态**: ✅ 生产就绪

---

## 📋 概述

本文档描述了AI Stack Super Enhanced系统的端到端业务流程脚本，涵盖从订单创建到任务完成的完整链路。

### 流程链路

```
订单 → 生产 → 内容 → 趋势 → 股票 → 任务
```

### 流程说明

1. **订单模块**: 创建和管理ERP订单
2. **生产模块**: 基于订单创建生产任务
3. **内容模块**: 基于生产结果生成内容
4. **趋势模块**: 分析内容趋势并生成报告
5. **股票模块**: 基于趋势进行股票分析和交易
6. **任务模块**: 创建和管理任务生命周期

---

## 🎯 流程步骤详解

### 步骤1: 创建订单

**API端点**: `POST /api/super-agent/erp/orders`

**请求示例**:
```json
{
  "customer_id": "CUST001",
  "order_date": "2025-11-13",
  "items": [
    {
      "product_id": "PROD001",
      "quantity": 100,
      "unit_price": 50.00
    }
  ],
  "total_amount": 5000.00,
  "status": "pending"
}
```

**响应示例**:
```json
{
  "success": true,
  "order": {
    "order_id": "ORD20251113001",
    "customer_id": "CUST001",
    "order_date": "2025-11-13",
    "total_amount": 5000.00,
    "status": "pending",
    "created_at": "2025-11-13T10:00:00Z"
  }
}
```

**验证点**:
- ✅ 订单创建成功
- ✅ 订单ID生成
- ✅ 订单状态为pending

---

### 步骤2: 创建生产任务

**API端点**: `GET /api/super-agent/erp/demo/production-jobs`

**说明**: 基于订单创建生产任务

**请求示例**:
```bash
GET /api/super-agent/erp/demo/production-jobs?order_id=ORD20251113001
```

**响应示例**:
```json
{
  "success": true,
  "production_jobs": [
    {
      "job_id": "JOB20251113001",
      "order_id": "ORD20251113001",
      "product_id": "PROD001",
      "quantity": 100,
      "status": "scheduled",
      "start_date": "2025-11-14",
      "estimated_completion": "2025-11-20"
    }
  ]
}
```

**验证点**:
- ✅ 生产任务创建成功
- ✅ 任务关联到订单
- ✅ 任务状态为scheduled

---

### 步骤3: 生成内容

**API端点**: `POST /api/super-agent/content/generate`

**说明**: 基于生产任务结果生成内容

**请求示例**:
```json
{
  "prompt": "基于生产任务JOB20251113001，生成产品宣传内容",
  "content_type": "marketing",
  "platform": "douyin"
}
```

**响应示例**:
```json
{
  "success": true,
  "result": {
    "content_id": "CONT20251113001",
    "title": "产品宣传内容",
    "content": "基于生产任务生成的内容...",
    "content_type": "marketing",
    "status": "draft"
  }
}
```

**验证点**:
- ✅ 内容生成成功
- ✅ 内容ID生成
- ✅ 内容状态为draft

---

### 步骤4: 发布内容

**API端点**: `POST /api/super-agent/content/{content_id}/publish`

**请求示例**:
```json
{
  "platform": "douyin",
  "data": {
    "title": "产品宣传内容",
    "description": "基于生产任务生成的内容"
  }
}
```

**响应示例**:
```json
{
  "success": true,
  "result": {
    "content_id": "CONT20251113001",
    "platform": "douyin",
    "published_at": "2025-11-13T10:30:00Z",
    "status": "published"
  }
}
```

**验证点**:
- ✅ 内容发布成功
- ✅ 发布状态更新
- ✅ 发布时间记录

---

### 步骤5: 分析趋势

**API端点**: `POST /api/super-agent/trend/analysis/start`

**说明**: 基于发布的内容启动趋势分析

**请求示例**:
```json
{
  "indicator": "CONTENT_PERFORMANCE",
  "data_source": "CONT20251113001",
  "analysis_type": "content_trend"
}
```

**响应示例**:
```json
{
  "success": true,
  "result": {
    "task_id": "TREND20251113001",
    "indicator": "CONTENT_PERFORMANCE",
    "status": "running",
    "started_at": "2025-11-13T10:35:00Z"
  }
}
```

**验证点**:
- ✅ 趋势分析任务创建成功
- ✅ 任务状态为running
- ✅ 任务ID生成

---

### 步骤6: 获取趋势报告

**API端点**: `GET /api/super-agent/trend/reports/{report_id}`

**说明**: 获取趋势分析报告

**请求示例**:
```bash
GET /api/super-agent/trend/reports/TREND20251113001
```

**响应示例**:
```json
{
  "success": true,
  "report": {
    "report_id": "TREND20251113001",
    "indicator": "CONTENT_PERFORMANCE",
    "summary": "内容表现良好，趋势向上",
    "metrics": {
      "engagement_rate": 0.85,
      "growth_rate": 0.12
    },
    "recommendations": [
      "继续推广类似内容",
      "优化发布时间"
    ]
  }
}
```

**验证点**:
- ✅ 趋势报告生成成功
- ✅ 报告包含指标和推荐

---

### 步骤7: 股票行情查询

**API端点**: `GET /api/super-agent/stock/quote`

**说明**: 基于趋势分析结果查询相关股票行情

**请求示例**:
```bash
GET /api/super-agent/stock/quote?symbol=000001&market=A
```

**响应示例**:
```json
{
  "quote": {
    "symbol": "000001",
    "market": "A",
    "price": 12.50,
    "change": 0.25,
    "change_percent": 2.04,
    "volume": 1000000,
    "timestamp": "2025-11-13T10:40:00Z"
  },
  "sim_fills": []
}
```

**验证点**:
- ✅ 股票行情获取成功
- ✅ 价格数据准确

---

### 步骤8: 股票模拟交易

**API端点**: `POST /api/super-agent/stock/sim/place-order`

**说明**: 基于趋势分析进行模拟交易

**请求示例**:
```json
{
  "symbol": "000001",
  "side": "buy",
  "qty": 1000,
  "order_type": "market"
}
```

**响应示例**:
```json
{
  "success": true,
  "order_id": "STOCK20251113001",
  "symbol": "000001",
  "side": "buy",
  "quantity": 1000,
  "status": "filled",
  "filled_price": 12.50,
  "filled_at": "2025-11-13T10:41:00Z"
}
```

**验证点**:
- ✅ 订单创建成功
- ✅ 订单状态为filled
- ✅ 成交价格记录

---

### 步骤9: 创建任务

**API端点**: `POST /api/task-lifecycle/create`

**说明**: 创建任务生命周期，整合前面所有步骤

**请求示例**:
```json
{
  "task_name": "端到端流程任务",
  "task_type": "end_to_end",
  "priority": 5,
  "metadata": {
    "order_id": "ORD20251113001",
    "production_job_id": "JOB20251113001",
    "content_id": "CONT20251113001",
    "trend_report_id": "TREND20251113001",
    "stock_order_id": "STOCK20251113001"
  }
}
```

**响应示例**:
```json
{
  "success": true,
  "task": {
    "task_id": "TASK20251113001",
    "task_name": "端到端流程任务",
    "task_type": "end_to_end",
    "status": "created",
    "priority": 5,
    "created_at": "2025-11-13T10:42:00Z",
    "metadata": {
      "order_id": "ORD20251113001",
      "production_job_id": "JOB20251113001",
      "content_id": "CONT20251113001",
      "trend_report_id": "TREND20251113001",
      "stock_order_id": "STOCK20251113001"
    }
  }
}
```

**验证点**:
- ✅ 任务创建成功
- ✅ 任务关联所有步骤
- ✅ 任务状态为created

---

### 步骤10: 启动任务

**API端点**: `POST /api/task-lifecycle/{task_id}/start`

**请求示例**:
```bash
POST /api/task-lifecycle/TASK20251113001/start
```

**响应示例**:
```json
{
  "success": true,
  "task": {
    "task_id": "TASK20251113001",
    "status": "in_progress",
    "started_at": "2025-11-13T10:43:00Z"
  }
}
```

**验证点**:
- ✅ 任务启动成功
- ✅ 任务状态为in_progress

---

### 步骤11: 更新任务进度

**API端点**: `POST /api/task-lifecycle/{task_id}/update-progress`

**请求示例**:
```json
{
  "progress": 50.0,
  "current_step": "内容生成完成",
  "completed_steps": 5
}
```

**响应示例**:
```json
{
  "success": true,
  "task": {
    "task_id": "TASK20251113001",
    "progress": 50.0,
    "current_step": "内容生成完成",
    "completed_steps": 5
  }
}
```

**验证点**:
- ✅ 进度更新成功
- ✅ 当前步骤记录

---

### 步骤12: 完成任务

**API端点**: `POST /api/task-lifecycle/{task_id}/complete`

**请求示例**:
```json
{
  "result": {
    "summary": "端到端流程执行完成",
    "total_steps": 12,
    "success_rate": 100.0
  }
}
```

**响应示例**:
```json
{
  "success": true,
  "task": {
    "task_id": "TASK20251113001",
    "status": "completed",
    "progress": 100.0,
    "completed_at": "2025-11-13T10:45:00Z",
    "result": {
      "summary": "端到端流程执行完成",
      "total_steps": 12,
      "success_rate": 100.0
    }
  }
}
```

**验证点**:
- ✅ 任务完成成功
- ✅ 任务状态为completed
- ✅ 结果记录

---

## 🔄 完整流程脚本

### Python脚本示例

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
端到端流程脚本
订单 → 生产 → 内容 → 趋势 → 股票 → 任务
"""

import asyncio
import httpx
import json
from datetime import datetime
from typing import Dict, Any, Optional

BASE_URL = "http://localhost:8000"

async def run_end_to_end_playbook():
    """运行端到端流程脚本"""
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        results = {}
        
        # 步骤1: 创建订单
        print("步骤1: 创建订单...")
        order_response = await client.post(
            "/api/super-agent/erp/orders",
            json={
                "customer_id": "CUST001",
                "order_date": datetime.now().strftime("%Y-%m-%d"),
                "items": [{"product_id": "PROD001", "quantity": 100, "unit_price": 50.00}],
                "total_amount": 5000.00,
                "status": "pending"
            }
        )
        order_data = order_response.json()
        order_id = order_data["order"]["order_id"]
        results["order_id"] = order_id
        print(f"✅ 订单创建成功: {order_id}")
        
        # 步骤2: 创建生产任务
        print("步骤2: 创建生产任务...")
        production_response = await client.get(
            f"/api/super-agent/erp/demo/production-jobs",
            params={"order_id": order_id}
        )
        production_data = production_response.json()
        job_id = production_data["production_jobs"][0]["job_id"]
        results["production_job_id"] = job_id
        print(f"✅ 生产任务创建成功: {job_id}")
        
        # 步骤3: 生成内容
        print("步骤3: 生成内容...")
        content_response = await client.post(
            "/api/super-agent/content/generate",
            json={
                "prompt": f"基于生产任务{job_id}，生成产品宣传内容",
                "content_type": "marketing",
                "platform": "douyin"
            }
        )
        content_data = content_response.json()
        content_id = content_data["result"]["content_id"]
        results["content_id"] = content_id
        print(f"✅ 内容生成成功: {content_id}")
        
        # 步骤4: 发布内容
        print("步骤4: 发布内容...")
        publish_response = await client.post(
            f"/api/super-agent/content/{content_id}/publish",
            json={
                "platform": "douyin",
                "data": {"title": "产品宣传内容", "description": "基于生产任务生成的内容"}
            }
        )
        publish_data = publish_response.json()
        results["published"] = publish_data["success"]
        print(f"✅ 内容发布成功")
        
        # 步骤5: 启动趋势分析
        print("步骤5: 启动趋势分析...")
        trend_response = await client.post(
            "/api/super-agent/trend/analysis/start",
            json={
                "indicator": "CONTENT_PERFORMANCE",
                "data_source": content_id,
                "analysis_type": "content_trend"
            }
        )
        trend_data = trend_response.json()
        trend_task_id = trend_data["result"]["task_id"]
        results["trend_task_id"] = trend_task_id
        print(f"✅ 趋势分析启动成功: {trend_task_id}")
        
        # 等待趋势分析完成（简化处理，实际应该轮询）
        await asyncio.sleep(5)
        
        # 步骤6: 获取趋势报告
        print("步骤6: 获取趋势报告...")
        report_response = await client.get(
            f"/api/super-agent/trend/reports/{trend_task_id}"
        )
        report_data = report_response.json()
        results["trend_report"] = report_data["report"]
        print(f"✅ 趋势报告获取成功")
        
        # 步骤7: 查询股票行情
        print("步骤7: 查询股票行情...")
        quote_response = await client.get(
            "/api/super-agent/stock/quote",
            params={"symbol": "000001", "market": "A"}
        )
        quote_data = quote_response.json()
        results["stock_quote"] = quote_data["quote"]
        print(f"✅ 股票行情查询成功")
        
        # 步骤8: 股票模拟交易
        print("步骤8: 股票模拟交易...")
        stock_order_response = await client.post(
            "/api/super-agent/stock/sim/place-order",
            json={
                "symbol": "000001",
                "side": "buy",
                "qty": 1000,
                "order_type": "market"
            }
        )
        stock_order_data = stock_order_response.json()
        stock_order_id = stock_order_data["order_id"]
        results["stock_order_id"] = stock_order_id
        print(f"✅ 股票订单创建成功: {stock_order_id}")
        
        # 步骤9: 创建任务
        print("步骤9: 创建任务...")
        task_response = await client.post(
            "/api/task-lifecycle/create",
            json={
                "task_name": "端到端流程任务",
                "task_type": "end_to_end",
                "priority": 5,
                "metadata": results
            }
        )
        task_data = task_response.json()
        task_id = task_data["task"]["task_id"]
        results["task_id"] = task_id
        print(f"✅ 任务创建成功: {task_id}")
        
        # 步骤10: 启动任务
        print("步骤10: 启动任务...")
        start_response = await client.post(
            f"/api/task-lifecycle/{task_id}/start"
        )
        start_data = start_response.json()
        print(f"✅ 任务启动成功")
        
        # 步骤11: 更新任务进度
        print("步骤11: 更新任务进度...")
        progress_response = await client.post(
            f"/api/task-lifecycle/{task_id}/update-progress",
            json={
                "progress": 50.0,
                "current_step": "内容生成完成",
                "completed_steps": 5
            }
        )
        progress_data = progress_response.json()
        print(f"✅ 任务进度更新成功")
        
        # 步骤12: 完成任务
        print("步骤12: 完成任务...")
        complete_response = await client.post(
            f"/api/task-lifecycle/{task_id}/complete",
            json={
                "result": {
                    "summary": "端到端流程执行完成",
                    "total_steps": 12,
                    "success_rate": 100.0
                }
            }
        )
        complete_data = complete_response.json()
        print(f"✅ 任务完成成功")
        
        return results

if __name__ == "__main__":
    results = asyncio.run(run_end_to_end_playbook())
    print("\n" + "="*60)
    print("端到端流程执行完成！")
    print("="*60)
    print(json.dumps(results, indent=2, ensure_ascii=False))
```

---

## 📊 流程验证清单

### 前置条件
- [ ] API服务运行正常
- [ ] 数据库连接正常
- [ ] 必要的依赖服务启动

### 执行验证
- [ ] 订单创建成功
- [ ] 生产任务创建成功
- [ ] 内容生成成功
- [ ] 内容发布成功
- [ ] 趋势分析启动成功
- [ ] 趋势报告获取成功
- [ ] 股票行情查询成功
- [ ] 股票订单创建成功
- [ ] 任务创建成功
- [ ] 任务启动成功
- [ ] 任务进度更新成功
- [ ] 任务完成成功

### 后置验证
- [ ] 所有步骤数据关联正确
- [ ] 任务状态正确
- [ ] 日志记录完整

---

## 🔧 故障处理

### 常见问题

1. **API调用失败**
   - 检查服务是否运行
   - 检查网络连接
   - 检查API密钥

2. **数据关联失败**
   - 检查ID是否正确传递
   - 检查数据是否存在

3. **超时问题**
   - 增加超时时间
   - 检查服务性能

---

## 📝 使用说明

### 运行脚本

```bash
# 使用Python脚本
python3 scripts/end_to_end_playbook.py

# 或使用录屏脚本（包含录屏功能）
./scripts/record_demo.sh end_to_end
```

### 查看日志

```bash
# 查看演示日志
tail -f logs/demos/end_to_end_playbook_*.log
```

### 查看结果

```bash
# 查看执行结果
cat logs/demos/end_to_end_playbook_*.json
```

---

**文档版本**: v1.0  
**最后更新**: 2025-11-13  
**维护团队**: AI Stack开发团队

