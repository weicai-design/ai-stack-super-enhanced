#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
端到端流程脚本（生产级实现）
8.1: 订单 → 生产 → 内容 → 趋势 → 股票 → 任务
"""

from __future__ import annotations

import asyncio
import httpx
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import sys

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

logger = logging.getLogger(__name__)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 配置
BASE_URL = "http://localhost:8000"
LOG_DIR = PROJECT_ROOT / "logs" / "demos"
LOG_DIR.mkdir(parents=True, exist_ok=True)


class EndToEndPlaybook:
    """
    端到端流程脚本执行器（生产级实现 - 8.1）
    
    流程: 订单 → 生产 → 内容 → 趋势 → 股票 → 任务
    """
    
    def __init__(self, base_url: str = BASE_URL, log_dir: Path = LOG_DIR):
        self.base_url = base_url
        self.log_dir = log_dir
        self.client: Optional[httpx.AsyncClient] = None
        self.results: Dict[str, Any] = {}
        self.logs: list[str] = []
        
        # 创建日志文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = self.log_dir / f"end_to_end_playbook_{timestamp}.log"
        self.result_file = self.log_dir / f"end_to_end_playbook_{timestamp}.json"
        
        logger.info(f"端到端流程脚本初始化完成（日志目录: {self.log_dir}）")
    
    def _log(self, message: str, level: str = "INFO"):
        """记录日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] [{level}] {message}"
        self.logs.append(log_message)
        print(log_message)
        
        # 写入日志文件
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(log_message + "\n")
    
    async def _get_client(self) -> httpx.AsyncClient:
        """获取HTTP客户端"""
        if self.client is None:
            self.client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=30.0,
            )
        return self.client
    
    async def close(self):
        """关闭HTTP客户端"""
        if self.client:
            await self.client.aclose()
            self.client = None
    
    # ============ 步骤实现 ============
    
    async def step1_create_order(self) -> str:
        """步骤1: 创建订单"""
        self._log("步骤1: 创建订单...")
        
        try:
            client = await self._get_client()
            response = await client.post(
                "/api/super-agent/erp/orders",
                json={
                    "customer_id": "CUST001",
                    "order_date": datetime.now().strftime("%Y-%m-%d"),
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
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get("success") and "order" in data:
                order_id = data["order"]["order_id"]
                self.results["order_id"] = order_id
                self._log(f"✅ 订单创建成功: {order_id}")
                return order_id
            else:
                raise ValueError(f"订单创建失败: {data}")
        
        except Exception as e:
            self._log(f"❌ 订单创建失败: {e}", "ERROR")
            raise
    
    async def step2_create_production_job(self, order_id: str) -> str:
        """步骤2: 创建生产任务"""
        self._log("步骤2: 创建生产任务...")
        
        try:
            client = await self._get_client()
            response = await client.get(
                "/api/super-agent/erp/demo/production-jobs",
                params={"order_id": order_id}
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get("success") and "production_jobs" in data and len(data["production_jobs"]) > 0:
                job_id = data["production_jobs"][0]["job_id"]
                self.results["production_job_id"] = job_id
                self._log(f"✅ 生产任务创建成功: {job_id}")
                return job_id
            else:
                raise ValueError(f"生产任务创建失败: {data}")
        
        except Exception as e:
            self._log(f"❌ 生产任务创建失败: {e}", "ERROR")
            raise
    
    async def step3_generate_content(self, job_id: str) -> str:
        """步骤3: 生成内容"""
        self._log("步骤3: 生成内容...")
        
        try:
            client = await self._get_client()
            response = await client.post(
                "/api/super-agent/content/generate",
                json={
                    "prompt": f"基于生产任务{job_id}，生成产品宣传内容",
                    "content_type": "marketing",
                    "platform": "douyin"
                }
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get("success") and "result" in data:
                content_id = data["result"]["content_id"]
                self.results["content_id"] = content_id
                self._log(f"✅ 内容生成成功: {content_id}")
                return content_id
            else:
                raise ValueError(f"内容生成失败: {data}")
        
        except Exception as e:
            self._log(f"❌ 内容生成失败: {e}", "ERROR")
            raise
    
    async def step4_publish_content(self, content_id: str) -> bool:
        """步骤4: 发布内容"""
        self._log("步骤4: 发布内容...")
        
        try:
            client = await self._get_client()
            response = await client.post(
                f"/api/super-agent/content/{content_id}/publish",
                json={
                    "platform": "douyin",
                    "data": {
                        "title": "产品宣传内容",
                        "description": "基于生产任务生成的内容"
                    }
                }
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get("success"):
                self.results["published"] = True
                self._log("✅ 内容发布成功")
                return True
            else:
                raise ValueError(f"内容发布失败: {data}")
        
        except Exception as e:
            self._log(f"❌ 内容发布失败: {e}", "ERROR")
            raise
    
    async def step5_start_trend_analysis(self, content_id: str) -> str:
        """步骤5: 启动趋势分析"""
        self._log("步骤5: 启动趋势分析...")
        
        try:
            client = await self._get_client()
            response = await client.post(
                "/api/super-agent/trend/analysis/start",
                json={
                    "indicator": "CONTENT_PERFORMANCE",
                    "data_source": content_id,
                    "analysis_type": "content_trend"
                }
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get("success") and "result" in data:
                trend_task_id = data["result"]["task_id"]
                self.results["trend_task_id"] = trend_task_id
                self._log(f"✅ 趋势分析启动成功: {trend_task_id}")
                return trend_task_id
            else:
                raise ValueError(f"趋势分析启动失败: {data}")
        
        except Exception as e:
            self._log(f"❌ 趋势分析启动失败: {e}", "ERROR")
            raise
    
    async def step6_get_trend_report(self, trend_task_id: str) -> Dict[str, Any]:
        """步骤6: 获取趋势报告"""
        self._log("步骤6: 获取趋势报告...")
        
        # 等待趋势分析完成（简化处理，实际应该轮询）
        await asyncio.sleep(5)
        
        try:
            client = await self._get_client()
            response = await client.get(
                f"/api/super-agent/trend/reports/{trend_task_id}"
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get("success") and "report" in data:
                report = data["report"]
                self.results["trend_report"] = report
                self._log("✅ 趋势报告获取成功")
                return report
            else:
                raise ValueError(f"趋势报告获取失败: {data}")
        
        except Exception as e:
            self._log(f"❌ 趋势报告获取失败: {e}", "ERROR")
            raise
    
    async def step7_get_stock_quote(self, symbol: str = "000001", market: str = "A") -> Dict[str, Any]:
        """步骤7: 查询股票行情"""
        self._log("步骤7: 查询股票行情...")
        
        try:
            client = await self._get_client()
            response = await client.get(
                "/api/super-agent/stock/quote",
                params={"symbol": symbol, "market": market}
            )
            response.raise_for_status()
            data = response.json()
            
            if "quote" in data:
                quote = data["quote"]
                self.results["stock_quote"] = quote
                self._log("✅ 股票行情查询成功")
                return quote
            else:
                raise ValueError(f"股票行情查询失败: {data}")
        
        except Exception as e:
            self._log(f"❌ 股票行情查询失败: {e}", "ERROR")
            raise
    
    async def step8_place_stock_order(self, symbol: str = "000001", qty: int = 1000) -> str:
        """步骤8: 股票模拟交易"""
        self._log("步骤8: 股票模拟交易...")
        
        try:
            client = await self._get_client()
            response = await client.post(
                "/api/super-agent/stock/sim/place-order",
                json={
                    "symbol": symbol,
                    "side": "buy",
                    "qty": qty,
                    "order_type": "market"
                }
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get("success") and "order_id" in data:
                stock_order_id = data["order_id"]
                self.results["stock_order_id"] = stock_order_id
                self._log(f"✅ 股票订单创建成功: {stock_order_id}")
                return stock_order_id
            else:
                raise ValueError(f"股票订单创建失败: {data}")
        
        except Exception as e:
            self._log(f"❌ 股票订单创建失败: {e}", "ERROR")
            raise
    
    async def step9_create_task(self) -> str:
        """步骤9: 创建任务"""
        self._log("步骤9: 创建任务...")
        
        try:
            client = await self._get_client()
            response = await client.post(
                "/api/task-lifecycle/create",
                json={
                    "task_name": "端到端流程任务",
                    "task_type": "end_to_end",
                    "priority": 5,
                    "metadata": self.results
                }
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get("success") and "task" in data:
                task_id = data["task"]["task_id"]
                self.results["task_id"] = task_id
                self._log(f"✅ 任务创建成功: {task_id}")
                return task_id
            else:
                raise ValueError(f"任务创建失败: {data}")
        
        except Exception as e:
            self._log(f"❌ 任务创建失败: {e}", "ERROR")
            raise
    
    async def step10_start_task(self, task_id: str) -> bool:
        """步骤10: 启动任务"""
        self._log("步骤10: 启动任务...")
        
        try:
            client = await self._get_client()
            response = await client.post(
                f"/api/task-lifecycle/{task_id}/start"
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get("success"):
                self._log("✅ 任务启动成功")
                return True
            else:
                raise ValueError(f"任务启动失败: {data}")
        
        except Exception as e:
            self._log(f"❌ 任务启动失败: {e}", "ERROR")
            raise
    
    async def step11_update_progress(self, task_id: str, progress: float = 50.0) -> bool:
        """步骤11: 更新任务进度"""
        self._log("步骤11: 更新任务进度...")
        
        try:
            client = await self._get_client()
            response = await client.post(
                f"/api/task-lifecycle/{task_id}/update-progress",
                json={
                    "progress": progress,
                    "current_step": "内容生成完成",
                    "completed_steps": 5
                }
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get("success"):
                self._log("✅ 任务进度更新成功")
                return True
            else:
                raise ValueError(f"任务进度更新失败: {data}")
        
        except Exception as e:
            self._log(f"❌ 任务进度更新失败: {e}", "ERROR")
            raise
    
    async def step12_complete_task(self, task_id: str) -> bool:
        """步骤12: 完成任务"""
        self._log("步骤12: 完成任务...")
        
        try:
            client = await self._get_client()
            response = await client.post(
                f"/api/task-lifecycle/{task_id}/complete",
                json={
                    "result": {
                        "summary": "端到端流程执行完成",
                        "total_steps": 12,
                        "success_rate": 100.0
                    }
                }
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get("success"):
                self._log("✅ 任务完成成功")
                return True
            else:
                raise ValueError(f"任务完成失败: {data}")
        
        except Exception as e:
            self._log(f"❌ 任务完成失败: {e}", "ERROR")
            raise
    
    # ============ 主流程 ============
    
    async def run(self) -> Dict[str, Any]:
        """运行完整流程"""
        start_time = datetime.now()
        self._log("="*60)
        self._log("开始执行端到端流程脚本")
        self._log("="*60)
        
        try:
            # 步骤1: 创建订单
            order_id = await self.step1_create_order()
            
            # 步骤2: 创建生产任务
            job_id = await self.step2_create_production_job(order_id)
            
            # 步骤3: 生成内容
            content_id = await self.step3_generate_content(job_id)
            
            # 步骤4: 发布内容
            await self.step4_publish_content(content_id)
            
            # 步骤5: 启动趋势分析
            trend_task_id = await self.step5_start_trend_analysis(content_id)
            
            # 步骤6: 获取趋势报告
            await self.step6_get_trend_report(trend_task_id)
            
            # 步骤7: 查询股票行情
            await self.step7_get_stock_quote()
            
            # 步骤8: 股票模拟交易
            await self.step8_place_stock_order()
            
            # 步骤9: 创建任务
            task_id = await self.step9_create_task()
            
            # 步骤10: 启动任务
            await self.step10_start_task(task_id)
            
            # 步骤11: 更新任务进度
            await self.step11_update_progress(task_id)
            
            # 步骤12: 完成任务
            await self.step12_complete_task(task_id)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # 保存结果
            self.results["execution_summary"] = {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration_seconds": duration,
                "total_steps": 12,
                "success": True
            }
            
            # 保存结果到文件
            with open(self.result_file, "w", encoding="utf-8") as f:
                json.dump(self.results, f, ensure_ascii=False, indent=2)
            
            self._log("="*60)
            self._log(f"端到端流程执行完成！耗时: {duration:.2f}秒")
            self._log("="*60)
            self._log(f"结果已保存: {self.result_file}")
            
            return self.results
        
        except Exception as e:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            self.results["execution_summary"] = {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration_seconds": duration,
                "success": False,
                "error": str(e)
            }
            
            # 保存结果到文件
            with open(self.result_file, "w", encoding="utf-8") as f:
                json.dump(self.results, f, ensure_ascii=False, indent=2)
            
            self._log(f"❌ 端到端流程执行失败: {e}", "ERROR")
            raise


async def main():
    """主函数"""
    playbook = EndToEndPlaybook()
    
    try:
        results = await playbook.run()
        print("\n" + "="*60)
        print("执行结果:")
        print("="*60)
        print(json.dumps(results, indent=2, ensure_ascii=False))
        return 0
    except Exception as e:
        logger.error(f"执行失败: {e}", exc_info=True)
        return 1
    finally:
        await playbook.close()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

