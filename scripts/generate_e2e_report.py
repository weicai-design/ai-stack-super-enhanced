#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P0-105: 端到端流程验证报告生成器

从测试结果生成Markdown格式的验证报告
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List


def load_test_results(report_path: Path) -> Dict[str, Any]:
    """加载测试结果"""
    with open(report_path, "r", encoding="utf-8") as f:
        return json.load(f)


def format_timestamp(ts: str) -> str:
    """格式化时间戳"""
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return ts


def generate_report(test_results: Dict[str, Any]) -> str:
    """生成Markdown报告"""
    lines = []
    
    # 标题
    lines.append("# P0-105: 端到端流程验证报告")
    lines.append("")
    lines.append(f"**生成时间**: {format_timestamp(test_results.get('test_start_time', ''))}")
    lines.append("")
    
    # 测试概览
    lines.append("## 测试概览")
    lines.append("")
    lines.append(f"- **测试开始时间**: {format_timestamp(test_results.get('test_start_time', ''))}")
    lines.append(f"- **测试结束时间**: {format_timestamp(test_results.get('test_end_time', ''))}")
    lines.append(f"- **总流程数**: {test_results.get('total_flows', 0)}")
    lines.append(f"- **成功流程数**: {test_results.get('successful_flows', 0)}")
    lines.append(f"- **失败流程数**: {test_results.get('failed_flows', 0)}")
    lines.append("")
    
    # 流程详情
    lines.append("## 流程详情")
    lines.append("")
    
    for flow in test_results.get("flows", []):
        flow_name = flow.get("flow_name", "未知流程")
        success = flow.get("success", False)
        status_icon = "✅" if success else "❌"
        status_text = "成功" if success else "失败"
        
        lines.append(f"### {status_icon} {flow_name} - {status_text}")
        lines.append("")
        lines.append(f"- **开始时间**: {format_timestamp(flow.get('start_time', ''))}")
        lines.append(f"- **结束时间**: {format_timestamp(flow.get('end_time', ''))}")
        
        if not success:
            lines.append(f"- **错误信息**: {flow.get('error', '未知错误')}")
        
        lines.append("")
        
        # 步骤详情
        all_steps = test_results.get("all_steps", [])
        flow_steps = [s for s in all_steps if s.get("flow") == flow_name]
        
        if flow_steps:
            lines.append("#### 测试步骤")
            lines.append("")
            for i, step in enumerate(flow_steps, 1):
                step_name = step.get("step", "未知步骤")
                step_success = step.get("success", False)
                step_icon = "✅" if step_success else "❌"
                
                lines.append(f"**步骤 {i}: {step_icon} {step_name}**")
                lines.append("")
                lines.append(f"- **时间**: {format_timestamp(step.get('timestamp', ''))}")
                
                if step.get("request"):
                    lines.append(f"- **请求**: `{json.dumps(step['request'], ensure_ascii=False, indent=2)[:200]}...`")
                
                if step.get("response"):
                    resp_summary = {}
                    resp = step["response"]
                    if "success" in resp:
                        resp_summary["success"] = resp["success"]
                    if "job_id" in resp:
                        resp_summary["job_id"] = resp["job_id"]
                    if "execution_id" in resp:
                        resp_summary["execution_id"] = resp["execution_id"]
                    if "sync_id" in resp:
                        resp_summary["sync_id"] = resp["sync_id"]
                    if resp_summary:
                        lines.append(f"- **响应摘要**: `{json.dumps(resp_summary, ensure_ascii=False)}`")
                
                if step.get("error"):
                    lines.append(f"- **错误**: {step['error']}")
                
                lines.append("")
    
    # 数据流验证
    lines.append("## 数据流验证")
    lines.append("")
    lines.append("### 流程1: 抖音内容生成发布")
    lines.append("")
    lines.append("**数据流路径**:")
    lines.append("")
    lines.append("1. **内容生成**: `POST /content/storyboard/generate`")
    lines.append("   - 输入: 概念、模板、时长、风格")
    lines.append("   - 输出: 故事板（场景列表、脚本）")
    lines.append("   - 数据存储: 通过 `ClosedLoopEngine` 记录执行证据")
    lines.append("")
    lines.append("2. **内容发布**: `POST /douyin/publish`")
    lines.append("   - 输入: 标题、内容、标签、媒体URL")
    lines.append("   - 处理: 合规检测、去AI化、风控评估")
    lines.append("   - 输出: 发布任务ID、合规报告、去AI化评分")
    lines.append("   - 数据存储: `ContentAnalytics.record_publication()`")
    lines.append("")
    lines.append("3. **运营分析**: `GET /content/analytics`")
    lines.append("   - 查询: 最近N天的内容表现数据")
    lines.append("   - 输出: 总内容数、阅读量、互动率等")
    lines.append("   - 数据源: `ContentAnalytics` 内存存储 + 数据库")
    lines.append("")
    
    lines.append("### 流程2: ERP订单→生产→财务")
    lines.append("")
    lines.append("**数据流路径**:")
    lines.append("")
    lines.append("1. **订单创建**: 模拟订单数据")
    lines.append("   - 订单ID、产品代码、数量、单价")
    lines.append("")
    lines.append("2. **运营试算**: `POST /erp/trial/calc`")
    lines.append("   - 输入: 目标周营收或日产量")
    lines.append("   - 输出: 建议日产量、预计周营收")
    lines.append("   - 数据存储: 通过 `ClosedLoopEngine` 记录执行证据")
    lines.append("")
    lines.append("3. **8D分析**: `POST /erp/8d/analyze`")
    lines.append("   - 输入: 8个维度的评分（质量/成本/交期/安全/利润/效率/管理/技术）")
    lines.append("   - 输出: 各维度评分、综合评分")
    lines.append("")
    lines.append("4. **ERP数据同步**: `POST /operations-finance/erp/sync`")
    lines.append("   - 输入: 订单数据、试算结果、8D评分")
    lines.append("   - 输出: 同步ID、同步状态")
    lines.append("   - 数据存储: `ERPDataSync.sync_data()`")
    lines.append("")
    lines.append("5. **同步状态查询**: `GET /operations-finance/erp/sync/status`")
    lines.append("   - 查询: 最新同步状态")
    lines.append("   - 输出: 同步状态、最后同步时间")
    lines.append("")
    lines.append("6. **运营财务KPI**: `GET /operations-finance/kpis`")
    lines.append("   - 查询: 财务关键指标")
    lines.append("   - 输出: 净现金流、烧钱率、跑道等")
    lines.append("   - 数据源: `DataService` 查询 `operations_data` 表")
    lines.append("")
    
    # 验证结论
    lines.append("## 验证结论")
    lines.append("")
    
    total_flows = test_results.get("total_flows", 0)
    successful_flows = test_results.get("successful_flows", 0)
    
    if successful_flows == total_flows:
        lines.append("✅ **所有流程测试通过**")
        lines.append("")
        lines.append("两个代表性流程均成功完成端到端数据流验证：")
        lines.append("")
        lines.append("1. **抖音内容生成发布流程**: 从故事板生成到内容发布，再到运营分析，数据流完整，各环节均有日志记录。")
        lines.append("2. **ERP订单→生产→财务流程**: 从订单创建到运营试算，再到8D分析和财务同步，数据流完整，各环节均有验证。")
    else:
        lines.append("⚠️ **部分流程测试失败**")
        lines.append("")
        lines.append(f"成功: {successful_flows}/{total_flows}")
        lines.append(f"失败: {test_results.get('failed_flows', 0)}/{total_flows}")
        lines.append("")
        for flow in test_results.get("flows", []):
            if not flow.get("success"):
                lines.append(f"- ❌ {flow.get('flow_name')}: {flow.get('error', '未知错误')}")
    
    lines.append("")
    lines.append("## 测试记录")
    lines.append("")
    lines.append("详细的测试步骤记录已保存在 `artifacts/e2e_validation_report.json`")
    lines.append("")
    lines.append("## 日志文件")
    lines.append("")
    lines.append("测试执行日志已保存在 `e2e_validation.log`")
    lines.append("")
    
    return "\n".join(lines)


def main():
    """主函数"""
    report_path = Path("artifacts/e2e_validation_report.json")
    
    if not report_path.exists():
        print(f"错误: 测试报告文件不存在: {report_path}")
        print("请先运行: python scripts/e2e_validation.py")
        sys.exit(1)
    
    test_results = load_test_results(report_path)
    report_md = generate_report(test_results)
    
    output_path = Path("P0-105-端到端流程验证报告.md")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report_md)
    
    print(f"✅ 验证报告已生成: {output_path}")


if __name__ == "__main__":
    main()

