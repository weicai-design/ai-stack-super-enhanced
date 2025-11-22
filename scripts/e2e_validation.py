#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P0-105: 端到端真实性验证脚本

测试两个代表性流程：
1. 抖音内容生成发布流程
2. ERP 订单→生产→财务流程
"""

import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import httpx

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('e2e_validation.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# API 基础URL
BASE_URL = "http://localhost:8000/api"


class E2EValidator:
    """端到端验证器"""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
        self.results: List[Dict[str, Any]] = []
        self.screenshots_dir = Path("artifacts/e2e_screenshots")
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Dict[str, Any]:
        """发送HTTP请求"""
        url = f"{self.base_url}{endpoint}"
        try:
            response = await self.client.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP错误 {e.response.status_code}: {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"请求失败: {str(e)}")
            raise
    
    def _record_step(
        self,
        flow_name: str,
        step_name: str,
        request: Dict[str, Any],
        response: Dict[str, Any],
        success: bool,
        error: Optional[str] = None
    ):
        """记录测试步骤"""
        step = {
            "flow": flow_name,
            "step": step_name,
            "timestamp": datetime.now().isoformat(),
            "request": request,
            "response": response,
            "success": success,
            "error": error
        }
        self.results.append(step)
        logger.info(f"[{flow_name}] {step_name}: {'✅' if success else '❌'}")
        if error:
            logger.error(f"  错误: {error}")
    
    async def test_douyin_content_flow(self) -> Dict[str, Any]:
        """测试抖音内容生成发布流程"""
        flow_name = "抖音内容生成发布"
        logger.info(f"\n{'='*60}")
        logger.info(f"开始测试: {flow_name}")
        logger.info(f"{'='*60}\n")
        
        flow_results = {
            "flow_name": flow_name,
            "start_time": datetime.now().isoformat(),
            "steps": []
        }
        
        try:
            # 步骤1: 生成故事板/脚本
            logger.info("步骤1: 生成故事板/脚本")
            storyboard_req = {
                "concept": "AI技术如何改变我们的生活",
                "template_name": "fast_promo",
                "duration": 60,
                "style": "modern"
            }
            storyboard_resp = await self._request(
                "POST",
                "/content/storyboard/generate",
                json=storyboard_req
            )
            self._record_step(
                flow_name,
                "生成故事板",
                storyboard_req,
                storyboard_resp,
                storyboard_resp.get("success", False),
                None if storyboard_resp.get("success") else "故事板生成失败"
            )
            
            if not storyboard_resp.get("success"):
                raise Exception("故事板生成失败")
            
            storyboard = storyboard_resp.get("storyboard", {})
            scenes = storyboard.get("scenes", [])
            logger.info(f"  生成场景数: {len(scenes)}")
            
            # 步骤2: 构建发布内容
            logger.info("步骤2: 构建发布内容")
            content_title = storyboard.get("title", "AI技术改变生活")
            content_text = "\n".join([
                f"场景{i+1}: {scene.get('description', '')}"
                for i, scene in enumerate(scenes[:3])  # 取前3个场景
            ])
            
            # 步骤3: 发布到抖音
            logger.info("步骤3: 发布到抖音")
            publish_req = {
                "title": content_title,
                "content": content_text,
                "tags": ["AI", "科技", "生活"],
                "media_url": None,
                "min_originality": 0.6,
                "block_sensitive": True,
                "deai_enabled": True,
                "deai_style": "casual",
                "deai_intensity": 0.5
            }
            publish_resp = await self._request(
                "POST",
                "/douyin/publish",
                json=publish_req
            )
            self._record_step(
                flow_name,
                "发布到抖音",
                publish_req,
                publish_resp,
                publish_resp.get("success", False),
                None if publish_resp.get("success") else publish_resp.get("message", "发布失败")
            )
            
            if not publish_resp.get("success"):
                raise Exception(f"发布失败: {publish_resp.get('message', '未知错误')}")
            
            job = publish_resp.get("job", {})
            job_id = job.get("job_id")
            logger.info(f"  发布任务ID: {job_id}")
            logger.info(f"  合规检测: {publish_resp.get('compliance', {}).get('originality_percent', 0):.1%}")
            logger.info(f"  去AI化: {publish_resp.get('deai', {}).get('human_score', 0):.1%}")
            
            # 步骤4: 查询运营分析
            logger.info("步骤4: 查询运营分析")
            await asyncio.sleep(1)  # 等待数据写入
            analytics_resp = await self._request(
                "GET",
                "/content/analytics",
                params={"days": 1}
            )
            self._record_step(
                flow_name,
                "查询运营分析",
                {},
                analytics_resp,
                analytics_resp.get("success", False),
                None if analytics_resp.get("success") else "查询失败"
            )
            
            if analytics_resp.get("success"):
                analytics = analytics_resp.get("analytics", {})
                total = analytics.get("total", 0)
                logger.info(f"  总内容数: {total}")
            
            flow_results["end_time"] = datetime.now().isoformat()
            flow_results["success"] = True
            logger.info(f"\n✅ {flow_name} 流程测试完成\n")
            
        except Exception as e:
            flow_results["end_time"] = datetime.now().isoformat()
            flow_results["success"] = False
            flow_results["error"] = str(e)
            logger.error(f"\n❌ {flow_name} 流程测试失败: {str(e)}\n")
        
        return flow_results
    
    async def test_erp_order_production_finance_flow(self) -> Dict[str, Any]:
        """测试ERP订单→生产→财务流程"""
        flow_name = "ERP订单→生产→财务"
        logger.info(f"\n{'='*60}")
        logger.info(f"开始测试: {flow_name}")
        logger.info(f"{'='*60}\n")
        
        flow_results = {
            "flow_name": flow_name,
            "start_time": datetime.now().isoformat(),
            "steps": []
        }
        
        try:
            # 步骤1: 创建订单（模拟）
            logger.info("步骤1: 创建订单（模拟）")
            order_id = f"ORDER_{int(datetime.now().timestamp())}"
            product_code = "PROD_001"
            order_data = {
                "order_id": order_id,
                "product_code": product_code,
                "quantity": 100,
                "unit_price": 50.0,
                "target_delivery_date": (datetime.now().timestamp() + 7 * 24 * 3600)
            }
            logger.info(f"  订单ID: {order_id}")
            logger.info(f"  产品代码: {product_code}")
            logger.info(f"  数量: {order_data['quantity']}")
            
            # 步骤2: 运营试算（根据目标周营收）
            logger.info("步骤2: 运营试算（根据目标周营收）")
            target_weekly_revenue = 50000.0
            trial_req = {
                "target_weekly_revenue": target_weekly_revenue,
                "product_code": product_code,
                "order_id": order_id
            }
            trial_resp = await self._request(
                "POST",
                "/erp/trial/calc",
                json=trial_req
            )
            self._record_step(
                flow_name,
                "运营试算",
                trial_req,
                trial_resp,
                trial_resp.get("success", False),
                None if trial_resp.get("success") else "试算失败"
            )
            
            if not trial_resp.get("success"):
                raise Exception("运营试算失败")
            
            trial_result = trial_resp.get("trial", {})
            logger.info(f"  目标周营收: ¥{target_weekly_revenue:,.2f}")
            if "suggested_daily_units" in trial_result:
                logger.info(f"  建议日产量: {trial_result['suggested_daily_units']} 件")
            if "estimated_weekly_revenue" in trial_result:
                logger.info(f"  预计周营收: ¥{trial_result['estimated_weekly_revenue']:,.2f}")
            
            # 步骤3: 8D分析（质量/成本/交期等）
            logger.info("步骤3: 8D分析（质量/成本/交期等）")
            eight_d_req = {
                "quality_score": 0.85,
                "cost_efficiency": 0.80,
                "delivery_performance": 0.90,
                "safety_score": 0.95,
                "profit_margin": 0.25,
                "efficiency_score": 0.88,
                "management_score": 0.82,
                "tech_score": 0.90
            }
            eight_d_resp = await self._request(
                "POST",
                "/erp/8d/analyze",
                json=eight_d_req
            )
            self._record_step(
                flow_name,
                "8D分析",
                eight_d_req,
                eight_d_resp,
                eight_d_resp.get("success", False),
                None if eight_d_resp.get("success") else "8D分析失败"
            )
            
            if eight_d_resp.get("success"):
                scores = eight_d_resp.get("scores", {})
                overall = eight_d_resp.get("overall_score", 0)
                logger.info(f"  综合评分: {overall:.2f}")
                logger.info(f"  质量: {scores.get('quality', 0):.2f}")
                logger.info(f"  成本: {scores.get('cost', 0):.2f}")
                logger.info(f"  交期: {scores.get('delivery', 0):.2f}")
            
            # 步骤4: ERP数据同步到运营财务
            logger.info("步骤4: ERP数据同步到运营财务")
            sync_data = {
                "order_id": order_id,
                "product_code": product_code,
                "quantity": order_data["quantity"],
                "unit_price": order_data["unit_price"],
                "total_amount": order_data["quantity"] * order_data["unit_price"],
                "trial_result": trial_result,
                "eight_d_score": eight_d_resp.get("overall_score", 0) if eight_d_resp.get("success") else None
            }
            sync_req = {
                "data_type": "order_to_finance",
                "data": sync_data,
                "direction": "erp_to_finance"
            }
            sync_resp = await self._request(
                "POST",
                "/operations-finance/erp/sync",
                json=sync_req
            )
            self._record_step(
                flow_name,
                "ERP数据同步",
                sync_req,
                sync_resp,
                sync_resp.get("success", False),
                None if sync_resp.get("success") else "同步失败"
            )
            
            if sync_resp.get("success"):
                sync_id = sync_resp.get("sync_id")
                logger.info(f"  同步ID: {sync_id}")
            
            # 步骤5: 查询同步状态
            logger.info("步骤5: 查询同步状态")
            await asyncio.sleep(1)  # 等待数据写入
            sync_status_resp = await self._request(
                "GET",
                "/operations-finance/erp/sync/status"
            )
            self._record_step(
                flow_name,
                "查询同步状态",
                {},
                sync_status_resp,
                sync_status_resp.get("success", False),
                None if sync_status_resp.get("success") else "查询失败"
            )
            
            if sync_status_resp.get("success"):
                status = sync_status_resp.get("status", {})
                logger.info(f"  同步状态: {status.get('status', 'unknown')}")
                logger.info(f"  最后同步时间: {status.get('last_sync_time', 'N/A')}")
            
            # 步骤6: 查询运营财务KPI
            logger.info("步骤6: 查询运营财务KPI")
            kpi_resp = await self._request(
                "GET",
                "/operations-finance/kpis"
            )
            self._record_step(
                flow_name,
                "查询运营财务KPI",
                {},
                kpi_resp,
                kpi_resp.get("success", False),
                None if kpi_resp.get("success") else "查询失败"
            )
            
            if kpi_resp.get("success"):
                kpis = kpi_resp.get("kpis", {})
                logger.info(f"  净现金流: ¥{kpis.get('net_cash', 0):,.2f}")
                logger.info(f"  烧钱率: ¥{kpis.get('burn_rate', 0):,.2f}/月")
                logger.info(f"  跑道: {kpis.get('runway', 0):.1f} 月")
            
            flow_results["end_time"] = datetime.now().isoformat()
            flow_results["success"] = True
            logger.info(f"\n✅ {flow_name} 流程测试完成\n")
            
        except Exception as e:
            flow_results["end_time"] = datetime.now().isoformat()
            flow_results["success"] = False
            flow_results["error"] = str(e)
            logger.error(f"\n❌ {flow_name} 流程测试失败: {str(e)}\n")
        
        return flow_results
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """运行所有测试"""
        logger.info("="*60)
        logger.info("开始端到端真实性验证")
        logger.info("="*60)
        
        report = {
            "test_start_time": datetime.now().isoformat(),
            "flows": []
        }
        
        # 测试流程1: 抖音内容生成发布
        flow1_result = await self.test_douyin_content_flow()
        report["flows"].append(flow1_result)
        
        # 测试流程2: ERP订单→生产→财务
        flow2_result = await self.test_erp_order_production_finance_flow()
        report["flows"].append(flow2_result)
        
        # 汇总结果
        report["test_end_time"] = datetime.now().isoformat()
        report["total_flows"] = len(report["flows"])
        report["successful_flows"] = sum(1 for f in report["flows"] if f.get("success"))
        report["failed_flows"] = report["total_flows"] - report["successful_flows"]
        report["all_steps"] = self.results
        
        # 保存报告
        report_path = Path("artifacts/e2e_validation_report.json")
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info("="*60)
        logger.info("端到端真实性验证完成")
        logger.info(f"成功流程: {report['successful_flows']}/{report['total_flows']}")
        logger.info(f"失败流程: {report['failed_flows']}/{report['total_flows']}")
        logger.info(f"报告已保存: {report_path}")
        logger.info("="*60)
        
        return report


async def main():
    """主函数"""
    async with E2EValidator() as validator:
        report = await validator.run_all_tests()
        return report


if __name__ == "__main__":
    asyncio.run(main())

