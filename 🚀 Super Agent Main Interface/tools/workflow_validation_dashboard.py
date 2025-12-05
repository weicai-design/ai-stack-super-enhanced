#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流验证仪表板

功能：
1. 实时展示工作流验证状态
2. 显示性能指标和趋势
3. 提供告警通知
4. 生成验证报告
5. 支持交互式查询
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
import sys

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.workflow_validation_monitor import (
    WorkflowValidationMonitor,
    get_workflow_validation_monitor,
    ValidationStatus,
)

logger = logging.getLogger(__name__)


class WorkflowValidationDashboard:
    """工作流验证仪表板"""
    
    def __init__(self, monitor: Optional[WorkflowValidationMonitor] = None):
        self.monitor = monitor or get_workflow_validation_monitor()
        self.dashboard_data: Dict[str, Any] = {}
        self.last_update = datetime.now()
        self.update_interval = 5  # 秒
    
    async def start_dashboard(self, port: int = 8080):
        """启动仪表板服务"""
        logger.info(f"启动工作流验证仪表板服务，端口: {port}")
        
        # 这里可以集成Web框架（如FastAPI、Flask）
        # 目前先实现控制台版本
        await self._start_console_dashboard()
    
    async def _start_console_dashboard(self):
        """启动控制台仪表板"""
        logger.info("启动控制台工作流验证仪表板...")
        
        try:
            while True:
                await self._update_dashboard_data()
                self._display_dashboard()
                
                # 等待下一次更新
                await asyncio.sleep(self.update_interval)
                
        except KeyboardInterrupt:
            logger.info("仪表板服务已停止")
        except Exception as e:
            logger.error(f"仪表板服务异常: {e}")
    
    async def _update_dashboard_data(self):
        """更新仪表板数据"""
        self.dashboard_data = {
            "summary": self.monitor.get_validation_summary(),
            "recent_results": self._get_recent_results(10),
            "alerts": self._get_recent_alerts(5),
            "metrics_trend": self._get_metrics_trend(),
            "last_update": datetime.now().isoformat(),
        }
        self.last_update = datetime.now()
    
    def _get_recent_results(self, count: int) -> List[Dict[str, Any]]:
        """获取最近验证结果"""
        recent = self.monitor.validation_results[-count:]
        return [
            {
                "workflow_id": r.workflow_id[:8] + "...",
                "status": r.status.value,
                "duration": f"{r.duration_seconds:.3f}s",
                "steps": f"{r.successful_steps}/{r.steps_count}",
                "rag_calls": r.rag_calls,
                "timestamp": r.timestamp.strftime("%H:%M:%S"),
            }
            for r in recent
        ]
    
    def _get_recent_alerts(self, count: int) -> List[Dict[str, Any]]:
        """获取最近告警"""
        recent = self.monitor.alerts[-count:]
        return [
            {
                "severity": a.severity,
                "type": a.alert_type,
                "message": a.message,
                "timestamp": a.timestamp.strftime("%H:%M:%S"),
            }
            for a in recent
        ]
    
    def _get_metrics_trend(self) -> Dict[str, Any]:
        """获取指标趋势"""
        metrics = {}
        
        # 响应时间趋势
        if "response_time" in self.monitor.metrics_history:
            response_times = self.monitor.metrics_history["response_time"][-20:]
            metrics["response_time"] = {
                "current": response_times[-1] if response_times else 0,
                "average": sum(response_times) / len(response_times) if response_times else 0,
                "trend": "up" if len(response_times) > 1 and response_times[-1] > response_times[-2] else "down",
            }
        
        # 通过率趋势
        if len(self.monitor.validation_results) >= 2:
            recent_results = self.monitor.validation_results[-20:]
            pass_rates = []
            for i in range(0, len(recent_results), 5):
                batch = recent_results[i:i+5]
                if batch:
                    passed = sum(1 for r in batch if r.status == ValidationStatus.PASSED)
                    pass_rates.append(passed / len(batch))
            
            if pass_rates:
                metrics["pass_rate"] = {
                    "current": pass_rates[-1],
                    "average": sum(pass_rates) / len(pass_rates),
                    "trend": "up" if len(pass_rates) > 1 and pass_rates[-1] > pass_rates[-2] else "down",
                }
        
        return metrics
    
    def _display_dashboard(self):
        """显示仪表板"""
        # 清屏（在支持ANSI转义的控制台中）
        print("\033c", end="")
        
        # 显示标题
        print("=" * 80)
        print("🚀 AI-STACK 双线闭环工作流验证仪表板")
        print("=" * 80)
        print(f"最后更新: {self.last_update.strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # 显示摘要信息
        summary = self.dashboard_data.get("summary", {})
        print("📊 验证摘要:")
        print(f"   总验证次数: {summary.get('total_validations', 0)}")
        print(f"   通过率: {summary.get('pass_rate', 0):.1%}")
        print(f"   平均响应时间: {summary.get('average_response_time', 0):.3f}秒")
        print(f"   告警数量: {summary.get('alerts_count', 0)} (严重: {summary.get('critical_alerts', 0)}, 警告: {summary.get('warning_alerts', 0)})")
        print()
        
        # 显示指标趋势
        metrics = self.dashboard_data.get("metrics_trend", {})
        if metrics:
            print("📈 指标趋势:")
            if "response_time" in metrics:
                rt = metrics["response_time"]
                trend_icon = "📈" if rt["trend"] == "up" else "📉"
                print(f"   响应时间: {rt['current']:.3f}s (平均: {rt['average']:.3f}s) {trend_icon}")
            
            if "pass_rate" in metrics:
                pr = metrics["pass_rate"]
                trend_icon = "📈" if pr["trend"] == "up" else "📉"
                print(f"   通过率: {pr['current']:.1%} (平均: {pr['average']:.1%}) {trend_icon}")
            print()
        
        # 显示最近验证结果
        recent_results = self.dashboard_data.get("recent_results", [])
        if recent_results:
            print("🔍 最近验证结果:")
            print("   ID        状态    响应时间   步骤完成  RAG调用  时间")
            print("   " + "-" * 50)
            for result in recent_results:
                status_icon = "✅" if result["status"] == "passed" else "❌"
                print(f"   {result['workflow_id']} {status_icon} {result['duration']:>8} {result['steps']:>10} {result['rag_calls']:>8} {result['timestamp']}")
            print()
        
        # 显示最近告警
        alerts = self.dashboard_data.get("alerts", [])
        if alerts:
            print("⚠️  最近告警:")
            for alert in alerts:
                severity_icon = "🔴" if alert["severity"] == "critical" else "🟡"
                print(f"   {severity_icon} {alert['type']}: {alert['message']} ({alert['timestamp']})")
            print()
        
        # 显示操作提示
        print("💡 操作提示:")
        print("   • 按 Ctrl+C 退出仪表板")
        print("   • 验证报告保存在: validation_reports/")
        print()
    
    def generate_detailed_report(self) -> str:
        """生成详细验证报告"""
        summary = self.monitor.get_validation_summary()
        
        report = f"""
# AI-STACK 双线闭环工作流验证报告

## 报告摘要
- 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- 验证周期: 最近24小时
- 总验证次数: {summary.get('total_validations', 0)}
- 总体通过率: {summary.get('pass_rate', 0):.1%}
- 平均响应时间: {summary.get('average_response_time', 0):.3f}秒
- 告警数量: {summary.get('alerts_count', 0)}

## 详细统计
"""
        
        # 添加验证结果统计
        if self.monitor.validation_results:
            recent_results = [r for r in self.monitor.validation_results 
                            if r.timestamp >= datetime.now() - timedelta(hours=24)]
            
            if recent_results:
                status_counts = {}
                for status in ValidationStatus:
                    status_counts[status.value] = sum(1 for r in recent_results if r.status == status)
                
                report += "### 验证状态分布\n"
                for status, count in status_counts.items():
                    percentage = count / len(recent_results) * 100
                    report += f"- {status}: {count}次 ({percentage:.1f}%)\n"
                
                # 响应时间分布
                response_times = [r.duration_seconds for r in recent_results]
                if response_times:
                    avg_time = sum(response_times) / len(response_times)
                    max_time = max(response_times)
                    min_time = min(response_times)
                    
                    report += f"\n### 响应时间统计\n"
                    report += f"- 平均响应时间: {avg_time:.3f}秒\n"
                    report += f"- 最快响应时间: {min_time:.3f}秒\n"
                    report += f"- 最慢响应时间: {max_time:.3f}秒\n"
        
        # 添加告警详情
        if self.monitor.alerts:
            recent_alerts = [a for a in self.monitor.alerts 
                           if a.timestamp >= datetime.now() - timedelta(hours=24)]
            
            if recent_alerts:
                report += "\n## 告警详情\n"
                
                critical_alerts = [a for a in recent_alerts if a.severity == "critical"]
                warning_alerts = [a for a in recent_alerts if a.severity == "warning"]
                
                if critical_alerts:
                    report += "### 严重告警\n"
                    for alert in critical_alerts[-5:]:  # 最近5个严重告警
                        report += f"- **{alert.timestamp.strftime('%H:%M:%S')}** {alert.message}\n"
                
                if warning_alerts:
                    report += "\n### 警告告警\n"
                    for alert in warning_alerts[-5:]:  # 最近5个警告告警
                        report += f"- {alert.timestamp.strftime('%H:%M:%S')} {alert.message}\n"
        
        report += "\n## 建议和改进\n"
        
        # 根据统计数据提供建议
        if summary.get("pass_rate", 0) < 0.8:
            report += "- ❗ 通过率较低，建议检查工作流执行链路\n"
        
        if summary.get("average_response_time", 0) > 1.5:
            report += "- ⏱️  响应时间较长，建议优化性能瓶颈\n"
        
        if summary.get("critical_alerts", 0) > 0:
            report += "- 🚨 存在严重告警，建议立即处理\n"
        
        report += "- 📊 建议持续监控指标趋势\n"
        report += "- 🔧 定期运行完整验证测试\n"
        
        return report
    
    def save_report(self, report_dir: Path = Path("validation_reports")):
        """保存验证报告"""
        report_dir.mkdir(exist_ok=True)
        
        # 生成报告
        report_content = self.generate_detailed_report()
        
        # 保存报告文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = report_dir / f"workflow_validation_report_{timestamp}.md"
        
        report_file.write_text(report_content, encoding="utf-8")
        logger.info(f"验证报告已保存: {report_file}")
        
        return report_file


async def main():
    """主函数"""
    # 创建仪表板
    dashboard = WorkflowValidationDashboard()
    
    # 启动仪表板
    try:
        print("🚀 启动工作流验证仪表板...")
        print("按 Ctrl+C 退出")
        print()
        
        # 等待用户准备
        await asyncio.sleep(2)
        
        # 启动仪表板
        await dashboard.start_dashboard()
        
    except KeyboardInterrupt:
        print("\n\n正在保存验证报告...")
        
        # 保存最终报告
        report_file = dashboard.save_report()
        print(f"验证报告已保存: {report_file}")
        
        print("仪表板服务已停止")


if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 运行主函数
    asyncio.run(main())