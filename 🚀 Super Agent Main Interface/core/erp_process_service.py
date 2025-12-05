#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ERP 11环节全流程服务
负责：
1. 维护11个环节（市场→客户→项目→投产→订单→采购→到料→生产→检验→入库→交付/回款）的运行状态
2. 管理每个环节的业务数据（订单、项目、采购、库存、生产等）
3. 构建时间线、八维度分析、风险/下一步动作等信息，供前端和API使用
4. 为ERP 11环节管理器（ERP11StagesManager）提供统一封装，确保在缺少后端服务时仍可用
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from datetime import datetime, timezone
import logging
from statistics import mean
from typing import Any, Dict, List, Optional, Tuple
import uuid

# 使用绝对路径导入避免模块冲突
import sys
import os

# 获取当前文件所在目录的父目录（Super Agent Main Interface）
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)

# 确保core目录在sys.path中
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# 使用绝对路径导入erp_8d_analysis模块
from erp_8d_analysis import analyze_8d, DIMENSION_LIBRARY

logger = logging.getLogger(__name__)

DIMENSIONS = [
    "quality",
    "cost",
    "delivery",
    "safety",
    "profit",
    "efficiency",
    "management",
    "technology",
]

STAGE_LABELS = {
    "order_management": "订单管理",
    "project_development": "项目管理",
    "procurement": "采购管理",
    "material_receipt": "到料与入库",
    "warehousing": "库存运营",
    "production": "生产执行",
    "quality_check": "质量管理",
    "delivery": "物流交付",
    "after_sales": "售后服务",
    "finance_settlement": "财务结算",
}

CAPABILITY_TARGETS = {
    "order_management": 25,
    "project_development": 30,
    "procurement": 25,
    "material_receipt": 30,
    "warehousing": 30,
    "production": 40,
    "quality_check": 20,
    "delivery": 20,
    "after_sales": 15,
    "finance_settlement": 15,
}

BASE_STAGE_CAPABILITIES: Dict[str, List[Tuple[str, str]]] = {
    "order_management": [
        ("多渠道订单接收", "整合 CRM/EDI/表单/邮件输入，实现零漏单接收"),
        ("合同与信用校验", "实时核验合同条款与信用评级，阻断高风险订单"),
        ("需求归一化处理", "自动将自定义字段映射到标准 BOM/工艺"),
        ("交期承诺引擎", "结合排程能力给出最优交期与备选方案"),
        ("库存占用联动", "订单确认即触发自动占用与可用量回写"),
        ("订单风险雷达", "监控金额、毛利、交付复杂度等 12 项风险指标"),
        ("利润敏感度分析", "测算成本波动对项目利润的影响区间"),
        ("变更审批编排", "多角色审批流，支持平行/串行/条件节点"),
        ("电子签章驱动", "自动生成签章包并回写状态"),
        ("排程反馈闭环", "排程与订单保持秒级同步，异常自动推送"),
        ("客户沟通纪要", "沉淀客户关键沟通摘要与承诺"),
        ("计费条款引擎", "支持里程碑/进度/混合计费方式"),
        ("可视化订单旅程", "展示从接收到回款的全生命周期"),
        ("服务级别监控", "SLA 告警、超期记录与补偿策略"),
        ("自动关单策略", "完成交付与回款后自动归档"),
    ],
    "project_development": [
        ("项目立项模板库", "按行业提供立项模板与文档清单"),
        ("WBS 自动拆解", "基于订单/解决方案生成 WBS"),
        ("跨部门资源对齐", "协调研发/制造/供应链资源占用"),
        ("技术评审流程", "集成 DFMEA/PFMEA 审批闭环"),
        ("BOM 成熟度跟踪", "BOM 状态与变更基线管理"),
        ("工程变更管理", "ECN 生命周期管理"),
        ("里程碑燃尽图", "一键输出甘特与燃尽视图"),
        ("成本基线监控", "记录并对比项目成本目标与实际"),
        ("风险矩阵", "维度包含影响/概率/缓解措施"),
        ("知识沉淀", "项目结束自动沉淀经验与复盘"),
    ],
    "procurement": [
        ("供应商准入评分", "支持多维度供应商打分与黑名单"),
        ("框架合同引擎", "合同模板、条款与审批自动化"),
        ("需求合并下单", "自动合并同物料需求减少下单次数"),
        ("价格波动监控", "关联行情与历史采购成本"),
        ("交期承诺追踪", "可视化供应商承诺与履约情况"),
        ("供应风险预警", "识别单一来源、产能瓶颈等风险"),
        ("发票与对账", "自动匹配发票、到货与付款计划"),
        ("绿色供应链指标", "跟踪 ESG 相关指标"),
        ("招投标工作流", "支持多轮询价、评分与中标记录"),
        ("动态安全库存联动", "结合库存与消费预测触发补货"),
    ],
    "material_receipt": [
        ("ASN 对齐", "提前获取到货通知与卸货计划"),
        ("码头排队优化", "按优先级安排月台/叉车资源"),
        ("IQC 抽样策略", "依据物料等级动态调整抽样比例"),
        ("不合格品隔离", "自动生成隔离与处置任务"),
        ("批次追溯", "扫描入库即绑定批次、供应商、订单"),
        ("电子看板", "实时显示到货状态与异常预警"),
        ("温湿度监控", "易损物料存储环境记录"),
        ("自动上架策略", "依 ABC 类别推荐库位与路径"),
        ("供应商绩效回写", "入库表现自动回写供应商 KPI"),
        ("入库时效 KPI", "统计从到货到入库的分钟级耗时"),
    ],
    "warehousing": [
        ("库存可视化", "在hand/available/reserved多视角展示"),
        ("批次/序列号管理", "整合 SN、Lot、托盘等粒度"),
        ("循环盘点", "支持 ABC/动态盘点计划"),
        ("再订货计算", "自动计算 ROP 与补货建议"),
        ("呆滞库存分析", "识别滞销物料与处置策略"),
        ("库位优化", "推荐调整库位、通道与容积"),
        ("多组织共享", "支持跨工厂的库存调拨与共享"),
        ("成本层级分析", "材料/制成/在制品多层成本透视"),
        ("安全库存模拟", "基于需求波动进行蒙特卡洛模拟"),
        ("库存金融化", "输出可质押库存列表"),
    ],
    "production": [
        ("APS 排程", "按约束理论进行有限能力排程"),
        ("产能模拟", "模拟不同班次/产能组合结果"),
        ("工单分解", "自动拆分主工单与子工单"),
        ("物料齐套校验", "MRP 结果与现场库存双重校验"),
        ("产线 IoT 对接", "采集 OEE/停机等实时数据"),
        ("换线优化", "SMED 数据沉淀与节拍优化"),
        ("工序看板", "显示每条产线当前工序与节拍"),
        ("异常闭环", "停线/质量/物料异常自动升级"),
        ("成本回写", "实时回写工时/能耗/报废成本"),
        ("能源监控", "按产线监控能耗 KPI"),
        ("多产线协同", "跨工厂产能协同与订单转移"),
        ("生产仿真", "数字孪生模型评估变更影响"),
        ("维保联动", "结合维护计划自动避开停机"),
        ("安全工况监控", "对危险工位进行互锁监控"),
    ],
    "quality_check": [
        ("SPC 实时图", "自动绘制 Cp/Cpk 与趋势线"),
        ("抽样计划引擎", "依据 AQL/多级抽检策略执行"),
        ("不良品管理", "自动生成 8D/5W2H 纠正措施"),
        ("客诉闭环", "对接售后系统，跟踪整改"),
        ("试验室排程", "实验室资源与样品排程"),
        ("多模型检测", "融合 AI 视觉/传感器/人工判定"),
        ("质量追溯", "向前向后追溯受影响批次"),
        ("知识库", "沉淀失效模式与经验库"),
    ],
    "delivery": [
        ("运输商协同", "多承运商 API 对接，获取实时轨迹"),
        ("关务与单证", "生成报关、原产地证等文档"),
        ("多段运输编排", "支持海陆空组合运输计划"),
        ("到岸成本估算", "计算物流+关税+保险成本"),
        ("SLA 仪表盘", "可视化交付 SLA 与异常"),
        ("客户通知中心", "自动推送节点短信/邮件/IM"),
        ("签收证据回传", "收集 POD、照片、坐标信息"),
        ("碳排放核算", "监控运输过程中碳排放"),
        ("物流风险雷达", "监控天气、港口、政策风险"),
        ("仓储联动", "自动预约入仓/出仓时间"),
    ],
    "after_sales": [
        ("工单路由", "按技能/区域/优先级路由服务工单"),
        ("远程诊断", "结合 IoT 数据推送诊断报告"),
        ("备件管理", "自动核对备件可用量与替代件"),
        ("SLA 执行", "服务响应/到场/解决 KPI 在线监控"),
        ("知识建议", "推送相似案例与修复方案"),
        ("费用结算", "自动生成备件与工时费用"),
        ("客户满意度闭环", "收集 NPS/CSAT 并生成改善建议"),
        ("现场安全合规", "校验服务工程师资质与安全清单"),
        ("多渠道接入", "接入电话/小程序/邮件/IM"),
        ("升级路径", "触发二线/三线支持并保留证据"),
    ],
    "finance_settlement": [
        ("里程碑收款计划", "自动生成收款计划与提醒"),
        ("多币种对账", "支持多币种、多实体对账"),
        ("票据管理", "发票申请、开票、作废闭环"),
        ("应收账龄分析", "分行业/客户维度监控账龄"),
        ("坏账准备建模", "依据风险评分生成坏账准备建议"),
        ("跨系统核销", "对接 ERP/财务系统进行核销"),
        ("现金流预测", "结合订单与费用预测现金流"),
        ("AI 异常侦测", "识别异常付款/重复发票"),
        ("自动函证", "生成与发送函证邮件/文档"),
        ("财务合规检查", "校验税率、票据合规性"),
    ],
}

BASE_STAGE_LIFECYCLES = {
    "order_management": ["接收", "校验", "评估", "承诺", "执行", "回款"],
    "project_development": ["立项", "方案", "验证", "试产", "量产准备"],
    "procurement": ["需求", "寻源", "下单", "跟催", "到货"],
    "material_receipt": ["预约", "到港/到厂", "卸货", "IQC", "上架"],
    "warehousing": ["补货", "拣选", "盘点", "调拨", "优化"],
    "production": ["计划", "排程", "执行", "反馈", "结案"],
    "quality_check": ["计划", "采样", "检测", "判定", "纠正"],
    "delivery": ["装运准备", "干线运输", "清关/交接", "签收"],
    "after_sales": ["受理", "诊断", "调度", "现场/远程处理", "复盘"],
    "finance_settlement": ["开票", "对账", "收款", "核销", "结案"],
}

BASE_STAGE_AUTOMATIONS = {
    "order_management": ["自动占用库存", "交付承诺回写", "变更审批流", "电子签章触发"],
    "project_development": ["WBS 生成器", "风险升级通知", "工程变更同步"],
    "procurement": ["自动合并下单", "异常催单机器人", "供应商绩效回写"],
    "material_receipt": ["IQC 自动抽样", "到车提醒", "不合格品隔离任务"],
    "warehousing": ["补货建议推送", "动态再订货", "库存金融化报表"],
    "production": ["APS 排程作业", "工单异常升级", "实时报工回写"],
    "quality_check": ["SPC 趋势告警", "自动生成 8D 报告", "不良品隔离单"],
    "delivery": ["节点推送", "关务文档生成", "承运商 API 调度"],
    "after_sales": ["SLA 超时提醒", "备件需求联动", "远程诊断脚本"],
    "finance_settlement": ["账龄告警", "自动对账", "收款提醒"],
}

BASE_STAGE_KPIS = {
    "order_management": ["订单满足率", "订单毛利率", "交付承诺准确率"],
    "project_development": ["里程碑准时率", "工程变更次数", "资源负荷偏差"],
    "procurement": ["平均交期", "价格节省率", "供应商绩效得分"],
    "material_receipt": ["入库时效", "IQC 通过率", "到货偏差率"],
    "warehousing": ["库存周转天数", "安全库存命中率", "库存准确率"],
    "production": ["OEE", "良品率", "计划达成率", "换线时间"],
    "quality_check": ["一次通过率", "客诉关闭周期", "不良率"],
    "delivery": ["准时交付率", "运输损耗率", "物流成本率"],
    "after_sales": ["SLA 达成率", "一次修复率", "客户满意度"],
    "finance_settlement": ["账龄结构", "收款及时率", "现金流覆盖率"],
}


def _now() -> str:
    try:
        return datetime.now(timezone.utc).isoformat()
    except Exception:  # pragma: no cover - 容错
        return datetime.now(timezone.utc).isoformat()


def _status_from_score(score: float) -> str:
    if score >= 0.85:
        return "good"
    if score >= 0.7:
        return "watch"
    return "risk"


def _stage_label(stage_id: str) -> str:
    return STAGE_LABELS.get(stage_id, stage_id.replace("_", " ").title())


def _build_stage_capabilities(stage_id: str) -> List[Dict[str, str]]:
    entries: List[Dict[str, str]] = [
        {"name": name, "description": desc}
        for name, desc in BASE_STAGE_CAPABILITIES.get(stage_id, [])
    ]
    target = CAPABILITY_TARGETS.get(stage_id)
    label = _stage_label(stage_id)
    idx = 1
    while target and len(entries) < target:
        entries.append(
            {
                "name": f"{label}扩展能力#{idx}",
                "description": f"{label}扩展自动化场景 #{idx}",
            }
        )
        idx += 1
    return entries


def _get_stage_lifecycle(stage_id: str) -> List[str]:
    return BASE_STAGE_LIFECYCLES.get(stage_id, [])


def _get_stage_automations(stage_id: str) -> List[str]:
    return BASE_STAGE_AUTOMATIONS.get(stage_id, [])


def _get_stage_kpis(stage_id: str) -> List[str]:
    return BASE_STAGE_KPIS.get(stage_id, [])


@dataclass
class StageState:
    """单个环节的基础信息"""

    id: str
    name: str
    owner: str
    duration_days: int
    status: str
    progress: int
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    risks: List[str] = field(default_factory=list)
    next_actions: List[str] = field(default_factory=list)
    documents: List[str] = field(default_factory=list)
    dimension_scores: Dict[str, float] = field(default_factory=dict)
    touchpoints: List[str] = field(default_factory=list)

    def as_dict(self) -> Dict[str, Any]:
        payload = copy.deepcopy(self.__dict__)
        payload["dimension_summary"] = [
            {
                "dimension": dim,
                "score": round(score, 3),
                "status": _status_from_score(score),
            }
            for dim, score in self.dimension_scores.items()
        ]
        return payload


class ERPProcessService:
    """ERP 11环节主服务"""

    def __init__(self, stage_manager: Optional[Any] = None, data_source: Optional[Any] = None):
        self.stage_manager = stage_manager
        self.data_source = data_source
        self._local_instances: Dict[str, Dict[str, Any]] = {}
        self.stage_state = self._bootstrap_stage_state()
        self.stage_blueprints = self._bootstrap_stage_blueprints()
        self.timeline = self._bootstrap_timeline()
        self.orders = self._bootstrap_orders()
        self.projects = self._bootstrap_projects()
        self.procurements = self._bootstrap_procurements()
        self.inventory = self._bootstrap_inventory()
        self.production_jobs = self._bootstrap_production_jobs()
        self.quality_checks = self._bootstrap_quality_checks()
        self.logistics = self._bootstrap_logistics()
        self.after_sales = self._bootstrap_after_sales()
        self.finance = self._bootstrap_finance()

    # --------------------------------------------------------------------- #
    # Bootstrap data
    # --------------------------------------------------------------------- #

    def _safe_datasource_call(self, method: str, *args, **kwargs):
        if not self.data_source or not hasattr(self.data_source, method):
            return None
        try:
            return getattr(self.data_source, method)(*args, **kwargs)
        except Exception as exc:  # pragma: no cover - 数据源容错
            logger.debug("ERP数据源调用失败 %s: %s", method, exc)
            return None

    def _normalize_order_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        quantity = record.get("quantity") or record.get("qty") or 0
        unit_price = record.get("unit_price") or record.get("price") or 0
        value = record.get("value") or (quantity or 0) * (unit_price or 0)
        dimensions = record.get("dimensions") or {dim: 0.78 for dim in DIMENSIONS}
        return {
            "order_id": record.get("order_id") or record.get("id"),
            "customer": record.get("customer") or record.get("client"),
            "industry": record.get("industry") or record.get("segment"),
            "value": value,
            "currency": record.get("currency", "CNY"),
            "status": record.get("status") or "planned",
            "delivery_date": record.get("promise_date") or record.get("delivery_date"),
            "priority": record.get("priority") or "normal",
            "stage": record.get("stage") or record.get("phase") or "processing",
            "risk": record.get("risk") or record.get("alerts"),
            "dimensions": dimensions,
        }

    @staticmethod
    def _normalize_procurement_record(record: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "po_id": record.get("po_id") or record.get("id"),
            "supplier": record.get("supplier"),
            "category": record.get("category") or record.get("material_group"),
            "material_code": record.get("material_code"),
            "material_name": record.get("material_name"),
            "amount": record.get("amount") or record.get("total_cost") or 0,
            "currency": record.get("currency", "CNY"),
            "status": record.get("status") or "sent",
            "eta": record.get("eta"),
            "risk": record.get("alert") or record.get("risk"),
        }

    @staticmethod
    def _normalize_inventory_record(record: Dict[str, Any]) -> Dict[str, Any]:
        on_hand = record.get("on_hand") or record.get("quantity") or 0
        allocated = record.get("reserved") or record.get("allocated") or 0
        available = record.get("available")
        if available is None:
            available = on_hand - allocated
        return {
            "material_id": record.get("material_id") or record.get("material_code"),
            "name": record.get("material_name") or record.get("name"),
            "on_hand": on_hand,
            "allocated": allocated,
            "available": available,
            "safety_stock": record.get("safety_stock") or 0,
            "reorder_point": record.get("reorder_point") or record.get("rop") or 0,
            "status_flag": record.get("status_flag"),
        }

    @staticmethod
    def _normalize_production_job(record: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "job_id": record.get("job_id") or record.get("id"),
            "order_id": record.get("order_id"),
            "line": record.get("line") or record.get("workcenter"),
            "quantity": record.get("quantity") or 0,
            "completed": record.get("completed") or record.get("qty_completed") or 0,
            "start_plan": record.get("plan_start"),
            "end_plan": record.get("plan_end"),
            "status": record.get("status") or "planned",
        }

    def _bootstrap_stage_state(self) -> Dict[str, StageState]:
        """初始化11个环节的默认状态"""
        return {
            "market_research": StageState(
                id="market_research",
                name="市场调研",
                owner="市场洞察组",
                status="completed",
                progress=100,
                duration_days=7,
                started_at="2025-10-01T09:00:00",
                completed_at="2025-10-07T18:00:00",
                metrics={
                    "market_size": "¥1.2B",
                    "segments": 3,
                    "feasibility": "A",
                    "opportunities": 12,
                },
                risks=["竞争对手价格战"],
                next_actions=["移交客户开发团队"],
                documents=["市场洞察报告.pdf"],
                dimension_scores={
                    "quality": 0.88,
                    "cost": 0.82,
                    "delivery": 0.91,
                    "safety": 0.86,
                    "profit": 0.79,
                    "efficiency": 0.9,
                    "management": 0.84,
                    "technology": 0.8,
                },
                touchpoints=["/erp/process/stages/market_research"],
            ),
            "customer_development": StageState(
                id="customer_development",
                name="客户开发",
                owner="销售拓展",
                status="completed",
                progress=100,
                duration_days=10,
                started_at="2025-10-08T09:00:00",
                completed_at="2025-10-18T18:00:00",
                metrics={
                    "leads_contacted": 36,
                    "qualified_leads": 14,
                    "conversion_rate": 38,
                },
                next_actions=["初步技术评估"],
                documents=["客户沟通记录.xlsx"],
                dimension_scores={dim: 0.86 for dim in DIMENSIONS},
                touchpoints=["/erp/process/stages/customer_development"],
            ),
            "project_development": StageState(
                id="project_development",
                name="项目开发",
                owner="解决方案部",
                status="completed",
                progress=100,
                duration_days=12,
                metrics={
                    "bom_ready": True,
                    "custom_features": 4,
                    "engineering_hours": 320,
                },
                risks=["部分功能需二次确认"],
                next_actions=["生成投产计划"],
                documents=["项目规格书.docx"],
                dimension_scores={dim: 0.83 for dim in DIMENSIONS},
                touchpoints=["/erp/projects"],
            ),
            "production_planning": StageState(
                id="production_planning",
                name="投产计划",
                owner="计划调度中心",
                status="completed",
                progress=100,
                duration_days=5,
                metrics={
                    "lines_reserved": 2,
                    "capacity_utilization": 86,
                    "planned_batches": 6,
                },
                next_actions=["创建客户订单"],
                documents=["生产排程表.xlsx"],
                dimension_scores={dim: 0.85 for dim in DIMENSIONS},
                touchpoints=["/erp/production/jobs"],
            ),
            "order_management": StageState(
                id="order_management",
                name="订单管理",
                owner="订单运营",
                status="in_progress",
                progress=72,
                duration_days=9,
                metrics={
                    "orders_confirmed": 4,
                    "orders_pending": 1,
                    "value_confirmed": "¥4.5M",
                },
                risks=["一个关键订单待客户签字"],
                next_actions=["同步采购需求"],
                documents=["订单确认书.pdf"],
                dimension_scores={
                    "quality": 0.91,
                    "cost": 0.78,
                    "delivery": 0.74,
                    "safety": 0.86,
                    "profit": 0.81,
                    "efficiency": 0.76,
                    "management": 0.79,
                    "technology": 0.74,
                },
                touchpoints=["/erp/orders"],
            ),
            "procurement": StageState(
                id="procurement",
                name="采购执行",
                owner="采购管理",
                status="in_progress",
                progress=58,
                duration_days=8,
                metrics={
                    "po_sent": 18,
                    "po_confirmed": 12,
                    "critical_items": 3,
                },
                risks=["关键芯片交期14天"],
                next_actions=["加急跟催供应商"],
                documents=["采购清单.xlsx"],
                dimension_scores={
                    "quality": 0.84,
                    "cost": 0.72,
                    "delivery": 0.68,
                    "safety": 0.9,
                    "profit": 0.77,
                    "efficiency": 0.69,
                    "management": 0.75,
                    "technology": 0.7,
                },
                touchpoints=["/erp/procurements"],
            ),
            "material_receipt": StageState(
                id="material_receipt",
                name="到料管理",
                owner="仓储部",
                status="planned",
                progress=20,
                duration_days=6,
                metrics={
                    "expected_shipments": 9,
                    "iqc_ready": 0,
                },
                next_actions=["准备IQC检验"],
                dimension_scores={
                    "quality": 0.8,
                    "cost": 0.75,
                    "delivery": 0.7,
                    "safety": 0.82,
                    "profit": 0.72,
                    "efficiency": 0.68,
                    "management": 0.7,
                    "technology": 0.65,
                },
                touchpoints=["/erp/inventory"],
            ),
            "production": StageState(
                id="production",
                name="生产执行",
                owner="制造中心",
                status="planned",
                progress=0,
                duration_days=14,
                metrics={
                    "units_committed": 0,
                    "efficiency_target": 92,
                },
                next_actions=["等待物料齐套"],
                dimension_scores={
                    "quality": 0.78,
                    "cost": 0.74,
                    "delivery": 0.7,
                    "safety": 0.83,
                    "profit": 0.76,
                    "efficiency": 0.72,
                    "management": 0.75,
                    "technology": 0.7,
                },
                touchpoints=["/erp/production/jobs"],
            ),
            "quality_check": StageState(
                id="quality_check",
                name="质量检验",
                owner="QA实验室",
                status="pending",
                progress=0,
                duration_days=4,
                dimension_scores={
                    "quality": 0.82,
                    "cost": 0.76,
                    "delivery": 0.7,
                    "safety": 0.9,
                    "profit": 0.78,
                    "efficiency": 0.71,
                    "management": 0.76,
                    "technology": 0.73,
                },
                touchpoints=["/erp/quality/inspections"],
            ),
            "warehousing": StageState(
                id="warehousing",
                name="入库管理",
                owner="仓库运营",
                status="pending",
                progress=0,
                duration_days=3,
                dimension_scores={
                    "quality": 0.8,
                    "cost": 0.78,
                    "delivery": 0.69,
                    "safety": 0.87,
                    "profit": 0.75,
                    "efficiency": 0.7,
                    "management": 0.73,
                    "technology": 0.69,
                },
                touchpoints=["/erp/inventory"],
            ),
            "delivery": StageState(
                id="delivery",
                name="交付与回款",
                owner="交付团队",
                status="pending",
                progress=0,
                duration_days=6,
                dimension_scores={
                    "quality": 0.82,
                    "cost": 0.76,
                    "delivery": 0.7,
                    "safety": 0.84,
                    "profit": 0.8,
                    "efficiency": 0.73,
                    "management": 0.76,
                    "technology": 0.71,
                },
                touchpoints=["/erp/logistics/shipments", "/erp/finance/settlements"],
            ),
        }

    def _bootstrap_stage_blueprints(self) -> Dict[str, Dict[str, Any]]:
        blueprints: Dict[str, Dict[str, Any]] = {}
        stage_ids = set(getattr(self, "stage_state", {}).keys()) | {"after_sales", "finance_settlement"}
        for stage_id in stage_ids:
            capabilities = _build_stage_capabilities(stage_id)
            state = self.stage_state.get(stage_id)
            dimension_summary = state.as_dict()["dimension_summary"] if state else []
            touchpoints = []
            if state:
                touchpoints = state.touchpoints
            elif stage_id == "after_sales":
                touchpoints = ["/erp/process/after-sales"]
            elif stage_id == "finance_settlement":
                touchpoints = ["/erp/process/finance"]
            blueprints[stage_id] = {
                "stage_id": stage_id,
                "name": _stage_label(stage_id),
                "capabilities": capabilities,
                "capability_count": len(capabilities),
                "capability_target": CAPABILITY_TARGETS.get(stage_id, len(capabilities)),
                "lifecycle": _get_stage_lifecycle(stage_id),
                "kpis": _get_stage_kpis(stage_id),
                "automations": _get_stage_automations(stage_id),
                "dimension_focus": dimension_summary,
                "touchpoints": touchpoints,
            }
        return blueprints

    def _bootstrap_timeline(self) -> List[Dict[str, Any]]:
        return [
            {
                "stage": "market_research",
                "title": "市场调研完成",
                "timestamp": "2025-10-07T18:00:00",
                "status": "completed",
                "summary": "锁定智能硬件和工业控制两个目标细分市场",
                "impact": "+12% 转化率",
            },
            {
                "stage": "customer_development",
                "title": "客户开发完成",
                "timestamp": "2025-10-18T18:00:00",
                "status": "completed",
                "summary": "签署 4 份意向书，预计订单金额 ¥4.8M",
                "impact": "+4 个关键客户",
            },
            {
                "stage": "production_planning",
                "title": "排产完成",
                "timestamp": "2025-11-05T18:00:00",
                "status": "completed",
                "summary": "锁定 2 条产线，交付周期 28 天",
                "impact": "产能利用率 86%",
            },
        ]

    # ... Bootstrap helpers for datasets ...
    def _bootstrap_orders(self) -> List[Dict[str, Any]]:
        records = self._safe_datasource_call("get_orders")
        if records:
            return [self._normalize_order_record(rec) for rec in records]
        return [
            {
                "order_id": "SO-24001",
                "customer": "星链智造",
                "industry": "智能制造",
                "value": 1_200_000,
                "currency": "CNY",
                "status": "confirming",
                "delivery_date": "2025-12-05",
                "priority": "high",
                "stage": "合同签署",
                "risk": "法务审查进行中",
                "dimensions": {
                    "quality": 0.93,
                    "cost": 0.77,
                    "delivery": 0.74,
                    "safety": 0.9,
                    "profit": 0.82,
                    "efficiency": 0.78,
                    "management": 0.81,
                    "technology": 0.76,
                },
            },
            {
                "order_id": "SO-24002",
                "customer": "聚能航空",
                "industry": "航空航天",
                "value": 1_800_000,
                "currency": "CNY",
                "status": "executing",
                "delivery_date": "2026-01-15",
                "priority": "urgent",
                "stage": "排产完成",
                "risk": "关键材料依赖单一供应商",
                "dimensions": {
                    "quality": 0.91,
                    "cost": 0.7,
                    "delivery": 0.68,
                    "safety": 0.88,
                    "profit": 0.8,
                    "efficiency": 0.72,
                    "management": 0.78,
                    "technology": 0.82,
                },
            },
            {
                "order_id": "SO-24003",
                "customer": "天阔能源",
                "industry": "新能源",
                "value": 950_000,
                "currency": "CNY",
                "status": "completed",
                "delivery_date": "2025-11-12",
                "priority": "normal",
                "stage": "回款中",
                "risk": "无",
                "dimensions": {
                    "quality": 0.95,
                    "cost": 0.82,
                    "delivery": 0.9,
                    "safety": 0.9,
                    "profit": 0.84,
                    "efficiency": 0.86,
                    "management": 0.8,
                    "technology": 0.79,
                },
            },
        ]

    def _bootstrap_projects(self) -> List[Dict[str, Any]]:
        return [
            {
                "project_id": "PRJ-FTS-01",
                "customer": "星链智造",
                "status": "frozen",
                "phase": "方案冻结",
                "lead": "Solutions-X",
                "bom_ready": True,
                "custom_features": 4,
                "engineering_hours": 320,
            },
            {
                "project_id": "PRJ-ENERGY-07",
                "customer": "天阔能源",
                "status": "executing",
                "phase": "工程验证",
                "lead": "Solutions-G",
                "bom_ready": False,
                "custom_features": 2,
                "engineering_hours": 140,
            },
        ]

    def _bootstrap_procurements(self) -> List[Dict[str, Any]]:
        records = self._safe_datasource_call("get_procurement_alerts")
        if records:
            return [self._normalize_procurement_record(rec) for rec in records]
        return [
            {
                "po_id": "PO-1001",
                "supplier": "华芯半导体",
                "category": "MCU",
                "amount": 360_000,
                "currency": "CNY",
                "status": "confirmed",
                "eta": "2025-11-28",
                "risk": "14天交期",
            },
            {
                "po_id": "PO-1002",
                "supplier": "北纬精密",
                "category": "结构件",
                "amount": 180_000,
                "currency": "CNY",
                "status": "sent",
                "eta": "2025-12-03",
                "risk": "等待供应商确认",
            },
        ]

    def _bootstrap_inventory(self) -> List[Dict[str, Any]]:
        records = self._safe_datasource_call("get_inventory_status")
        if records:
            return [self._normalize_inventory_record(rec) for rec in records]
        return [
            {
                "material_id": "MAT-5101",
                "name": "高频控制板",
                "on_hand": 420,
                "allocated": 260,
                "available": 160,
                "safety_stock": 120,
                "reorder_point": 150,
            },
            {
                "material_id": "MAT-8803",
                "name": "动力模组",
                "on_hand": 110,
                "allocated": 90,
                "available": 20,
                "safety_stock": 80,
                "reorder_point": 100,
            },
        ]

    def _bootstrap_production_jobs(self) -> List[Dict[str, Any]]:
        records = self._safe_datasource_call("get_production_jobs")
        if records:
            return [self._normalize_production_job(rec) for rec in records]
        return [
            {
                "job_id": "MO-5501",
                "order_id": "SO-24002",
                "line": "L2",
                "quantity": 600,
                "completed": 0,
                "start_plan": "2025-11-20",
                "end_plan": "2025-12-10",
                "status": "ready",
            },
            {
                "job_id": "MO-5502",
                "order_id": "SO-24001",
                "line": "L1",
                "quantity": 420,
                "completed": 280,
                "start_plan": "2025-11-05",
                "end_plan": "2025-11-18",
                "status": "executing",
            },
        ]

    def _bootstrap_quality_checks(self) -> List[Dict[str, Any]]:
        return [
            {
                "lot_id": "QC-20251115-01",
                "order_id": "SO-24001",
                "samples": 60,
                "defects": 1,
                "status": "in_progress",
                "method": "SPC",
            },
            {
                "lot_id": "QC-20251116-02",
                "order_id": "SO-24003",
                "samples": 80,
                "defects": 0,
                "status": "scheduled",
                "method": "6σ",
            },
        ]

    def _bootstrap_logistics(self) -> List[Dict[str, Any]]:
        return [
            {
                "shipment_id": "LG-7781",
                "order_id": "SO-24003",
                "carrier": "顺丰重货",
                "status": "in_transit",
                "eta": "2025-11-16",
                "milestones": ["打包完成", "已提货", "清关中"],
            },
            {
                "shipment_id": "LG-7782",
                "order_id": "SO-24001",
                "carrier": "德邦",
                "status": "ready",
                "eta": "2025-11-20",
                "milestones": ["装柜计划就绪"],
            },
        ]

    def _bootstrap_after_sales(self) -> List[Dict[str, Any]]:
        return [
            {
                "ticket_id": "AS-1001",
                "customer": "天阔能源",
                "issue": "设备固件升级",
                "status": "monitoring",
                "severity": "medium",
                "sla": "48h",
            },
            {
                "ticket_id": "AS-1002",
                "customer": "星链智造",
                "issue": "备件更换",
                "status": "scheduled",
                "severity": "low",
                "sla": "72h",
            },
        ]

    def _bootstrap_finance(self) -> List[Dict[str, Any]]:
        finance_items = [
            {
                "settlement_id": "FIN-9001",
                "order_id": "SO-24003",
                "amount": 950_000,
                "currency": "CNY",
                "status": "in_collection",
                "due_date": "2025-11-30",
                "received": 0.6,
            },
            {
                "settlement_id": "FIN-9002",
                "order_id": "SO-24001",
                "amount": 1_200_000,
                "currency": "CNY",
                "status": "awaiting_invoice",
                "due_date": "2025-12-20",
                "received": 0.0,
            },
        ]
        summary = self._safe_datasource_call("get_cash_flow_summary")
        if summary:
            balance = summary.get("balance") or 0
            collections = summary.get("total_collections") or 0
            payments = summary.get("total_payments") or 0
            finance_items.append(
                {
                    "settlement_id": "FIN-SUMMARY",
                    "order_id": "汇总",
                    "amount": collections,
                    "currency": "CNY",
                    "status": "summary",
                    "due_date": None,
                    "received": balance / (collections or 1),
                    "payments": payments,
                }
            )
        return finance_items

    # --------------------------------------------------------------------- #
    # Stage overview / timeline
    # --------------------------------------------------------------------- #

    def get_overview(self) -> Dict[str, Any]:
        stages = self.list_stages()
        completed = len([s for s in stages if s["status"] == "completed"])
        in_progress = len([s for s in stages if s["status"] == "in_progress"])
        planned = len(stages) - completed - in_progress
        avg_progress = round(sum(s["progress"] for s in stages) / len(stages), 1)
        return {
            "success": True,
            "summary": {
                "total_stages": len(stages),
                "completed": completed,
                "in_progress": in_progress,
                "planned": planned,
                "average_progress": avg_progress,
            },
            "stages": stages,
        }

    def list_stages(self) -> List[Dict[str, Any]]:
        items: List[Tuple[int, Dict[str, Any]]] = []
        for idx, stage in enumerate(self.stage_state.values(), start=1):
            payload = stage.as_dict()
            payload["order"] = idx
            if self.stage_manager:
                info = self.stage_manager.get_stage_info(stage.id)
                if info.get("success"):
                    payload["instances"] = {
                        "total": info.get("total_instances", 0),
                        "active": info.get("active_instances", 0),
                        "completed": info.get("completed_instances", 0),
                    }
            items.append((idx, payload))
        return [item for _, item in sorted(items, key=lambda x: x[0])]

    def get_stage(self, stage_id: str) -> Optional[Dict[str, Any]]:
        stage = self.stage_state.get(stage_id)
        if not stage:
            return None
        payload = stage.as_dict()
        payload["related_timeline"] = [
            event for event in self.timeline if event.get("stage") == stage_id
        ]
        return payload

    def get_timeline(self, stage_id: Optional[str] = None) -> Dict[str, Any]:
        events = self.timeline
        if stage_id:
            events = [event for event in events if event.get("stage") == stage_id]
        return {
            "success": True,
            "stage_filter": stage_id,
            "timeline": copy.deepcopy(events),
            "stage_count": len(self.stage_state),
        }

    def record_timeline_event(
        self,
        stage_id: str,
        title: str,
        summary: Optional[str] = None,
        impact: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Dict[str, Any]:
        event = {
            "stage": stage_id,
            "title": title,
            "summary": summary or "",
            "impact": impact,
            "status": status or self.stage_state.get(stage_id, StageState("", "", "", 0, "", 0)).status,
            "timestamp": _now(),
        }
        self.timeline.append(event)
        self.timeline = self.timeline[-200:]
        return {"success": True, "event": event}

    # --------------------------------------------------------------------- #
    # Stage instance lifecycle（封装ERP11StagesManager）
    # --------------------------------------------------------------------- #

    def create_stage_instance(
        self, stage_id: str, process_id: str, initial_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        if self.stage_manager:
            return self.stage_manager.create_stage_instance(stage_id, process_id, initial_data)
        instance_id = f"{process_id}_{stage_id}_{uuid.uuid4().hex[:6]}"
        instance = {
            "instance_id": instance_id,
            "stage_id": stage_id,
            "process_id": process_id,
            "status": "pending",
            "data": initial_data or {},
            "created_at": _now(),
        }
        self._local_instances[instance_id] = instance
        return {"success": True, "instance": instance}

    def start_stage_instance(self, instance_id: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if self.stage_manager:
            return self.stage_manager.start_stage(instance_id, data)
        instance = self._local_instances.get(instance_id)
        if not instance:
            return {"success": False, "error": "实例不存在"}
        instance["status"] = "in_progress"
        instance["started_at"] = _now()
        if data:
            instance["data"].update(data)
        return {"success": True, "instance": instance}

    def update_stage_metrics(self, instance_id: str, metrics: Dict[str, Any]) -> Dict[str, Any]:
        if self.stage_manager:
            return self.stage_manager.update_stage_metrics(instance_id, metrics)
        instance = self._local_instances.get(instance_id)
        if not instance:
            return {"success": False, "error": "实例不存在"}
        instance.setdefault("metrics", {}).update(metrics)
        return {"success": True, "instance": instance}

    def complete_stage_instance(
        self, instance_id: str, final_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        if self.stage_manager:
            return self.stage_manager.complete_stage(instance_id, final_data)
        instance = self._local_instances.get(instance_id)
        if not instance:
            return {"success": False, "error": "实例不存在"}
        instance["status"] = "completed"
        instance["completed_at"] = _now()
        if final_data:
            instance["data"].update(final_data)
        return {"success": True, "instance": instance}

    # --------------------------------------------------------------------- #
    # Orders & per-stage datasets
    # --------------------------------------------------------------------- #

    def get_orders_view(self) -> Dict[str, Any]:
        confirmed = len([o for o in self.orders if o["status"] in ("completed", "executing")])
        total_value = sum(order["value"] for order in self.orders)
        summary = {
            "total_orders": len(self.orders),
            "confirmed_orders": confirmed,
            "total_value": total_value,
            "currency": "CNY",
            "features": [
                "订单接收校验",
                "智能信用评级",
                "排程联动",
                "库存占用",
                "交付SLA看板",
                "8维度评分",
                "异常预警",
            ],
        }
        self._refresh_stage_from_orders()
        return {
            "success": True,
            "source": "erp_process_service",
            "summary": summary,
            "orders": copy.deepcopy(self.orders),
            "dimension_summary": self.stage_state["order_management"].as_dict()["dimension_summary"],
        }

    def add_order(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        order = copy.deepcopy(payload)
        order_id = order.get("order_id") or f"SO-{datetime.utcnow().strftime('%y%m%d%H%M%S')}"
        order["order_id"] = order_id
        order.setdefault("status", "confirming")
        order.setdefault("priority", "normal")
        order.setdefault("dimensions", {dim: 0.75 for dim in DIMENSIONS})
        order["created_at"] = _now()
        self.orders.append(order)
        self._refresh_stage_from_orders()
        self.record_timeline_event(
            stage_id="order_management",
            title=f"新增订单 {order_id}",
            summary=f"{order.get('customer')} 价值 ¥{order.get('value', 0):,.0f}",
            status="in_progress",
        )
        return {"success": True, "order": order}

    def _refresh_stage_from_orders(self) -> None:
        stage = self.stage_state["order_management"]
        total = len(self.orders)
        confirmed = len([o for o in self.orders if o["status"] in ("executing", "completed", "delivered")])
        if total:
            stage.progress = min(100, round(confirmed / total * 100))
        stage.status = "completed" if stage.progress >= 100 else ("in_progress" if confirmed else "planned")
        stage.metrics.update(
            {
                "orders_confirmed": confirmed,
                "orders_total": total,
                "value_confirmed": f"¥{sum(o['value'] for o in self.orders if o['status'] != 'confirming') / 1_000_000:.2f}M",
            }
        )

    def get_projects_view(self) -> Dict[str, Any]:
        frozen = len([p for p in self.projects if p["status"] == "frozen"])
        executing = len([p for p in self.projects if p["status"] == "executing"])
        return {
            "success": True,
            "projects": copy.deepcopy(self.projects),
            "summary": {
                "total_projects": len(self.projects),
                "frozen": frozen,
                "executing": executing,
                "features": ["立项→方案→工程验证→量产", "BOM健康度", "工程工时追踪"],
            },
        }

    def get_procurement_view(self) -> Dict[str, Any]:
        confirmed = len([po for po in self.procurements if po["status"] == "confirmed"])
        total_amount = sum(po["amount"] for po in self.procurements)
        return {
            "success": True,
            "procurements": copy.deepcopy(self.procurements),
            "summary": {
                "total_pos": len(self.procurements),
                "confirmed_pos": confirmed,
                "total_amount": total_amount,
                "features": [
                    "供应商评分",
                    "到料联动",
                    "风险预警",
                    "交期承诺跟踪",
                ],
            },
        }

    def get_inventory_view(self) -> Dict[str, Any]:
        total_on_hand = sum(item["on_hand"] for item in self.inventory)
        low_stock = len([item for item in self.inventory if item["available"] < item["safety_stock"]])
        return {
            "success": True,
            "inventory": copy.deepcopy(self.inventory),
            "summary": {
                "materials": len(self.inventory),
                "total_on_hand": total_on_hand,
                "low_stock_items": low_stock,
                "features": ["ABC分类", "安全库存预警", "ERP自动占用/释放"],
            },
        }

    def get_production_view(self) -> Dict[str, Any]:
        executing = len([job for job in self.production_jobs if job["status"] == "executing"])
        ready = len([job for job in self.production_jobs if job["status"] == "ready"])
        return {
            "success": True,
            "jobs": copy.deepcopy(self.production_jobs),
            "summary": {
                "total_jobs": len(self.production_jobs),
                "executing": executing,
                "ready": ready,
                "features": ["排程校验", "产线利用率", "物料齐套联动"],
            },
        }

    def get_quality_view(self) -> Dict[str, Any]:
        return {
            "success": True,
            "lots": copy.deepcopy(self.quality_checks),
            "summary": {
                "lots_pending": len([lot for lot in self.quality_checks if lot["status"] != "completed"]),
                "methods": list({lot["method"] for lot in self.quality_checks}),
                "features": ["SPC实时图", "6σ试算", "不良品闭环"],
            },
        }

    def get_logistics_view(self) -> Dict[str, Any]:
        in_transit = len([ship for ship in self.logistics if ship["status"] == "in_transit"])
        return {
            "success": True,
            "shipments": copy.deepcopy(self.logistics),
            "summary": {
                "total_shipments": len(self.logistics),
                "in_transit": in_transit,
                "features": ["多承运商追踪", "海陆空组合", "交付SLA预估"],
            },
        }

    def get_after_sales_view(self) -> Dict[str, Any]:
        open_cases = len([case for case in self.after_sales if case["status"] != "closed"])
        return {
            "success": True,
            "cases": copy.deepcopy(self.after_sales),
            "summary": {
                "total_cases": len(self.after_sales),
                "open_cases": open_cases,
                "features": ["SLA监控", "客户分层", "补件/维修联动"],
            },
        }

    def get_finance_view(self) -> Dict[str, Any]:
        total_amount = sum(item["amount"] for item in self.finance)
        collected_ratio = sum(item["amount"] * item["received"] for item in self.finance) / (total_amount or 1)
        return {
            "success": True,
            "settlements": copy.deepcopy(self.finance),
            "summary": {
                "total_amount": total_amount,
                "collected_ratio": round(collected_ratio, 3),
                "features": ["回款进度", "预算联动", "跨系统对账"],
            },
        }

    def _aggregate_dimension_scores(self) -> Dict[str, float]:
        aggregated: Dict[str, List[float]] = {dim: [] for dim in DIMENSIONS}
        for stage in self.stage_state.values():
            for dim, score in stage.dimension_scores.items():
                aggregated[dim].append(score)
        return {
            dim: (mean(values) if values else 0.75)
            for dim, values in aggregated.items()
        }

    def _build_dimension_payload(self, base_scores: Dict[str, float]) -> Dict[str, Dict[str, float]]:
        payload: Dict[str, Dict[str, float]] = {}
        for dim, config in DIMENSION_LIBRARY.items():
            score = base_scores.get(dim, 0.75)
            metrics: Dict[str, float] = {}
            for rule in config["metrics"]:
                if rule.direction == "higher":
                    metrics[rule.field] = round(rule.target * max(0.4, min(1.2, score + 0.1)), 4)
                else:
                    metrics[rule.field] = round(
                        max(0.001, rule.target / max(0.35, score + 0.05)), 4
                    )
            payload[dim] = metrics
        return payload

    def _virtual_stage_rows(self) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []
        after_sales_view = self.get_after_sales_view()
        after_summary = after_sales_view.get("summary", {})
        blueprint = self.stage_blueprints.get("after_sales", {})
        rows.append(
            {
                "stage_id": "after_sales",
                "name": blueprint.get("name", "售后服务"),
                "status": "in_progress" if after_summary.get("open_cases") else "planned",
                "progress": min(100, max(10, (after_summary.get("open_cases") or 1) * 10)),
                "owner": "售后团队",
                "risks": ["关键客户案件未关闭"] if after_summary.get("open_cases") else [],
                "next_actions": ["检查 SLA 达成"] if after_summary.get("open_cases") else [],
                "capability_count": blueprint.get("capability_count"),
                "capability_target": blueprint.get("capability_target"),
                "dimension_summary": blueprint.get("dimension_focus", []),
            }
        )

        finance_view = self.get_finance_view()
        finance_summary = finance_view.get("summary", {})
        blueprint_fin = self.stage_blueprints.get("finance_settlement", {})
        ratio = finance_summary.get("collected_ratio", 0)
        rows.append(
            {
                "stage_id": "finance_settlement",
                "name": blueprint_fin.get("name", "财务结算"),
                "status": "in_progress" if ratio < 1 else "completed",
                "progress": round(min(100, max(0, ratio * 100))),
                "owner": "财务中心",
                "risks": ["收款率低于目标"] if ratio < 0.8 else [],
                "next_actions": ["催收关键客户", "更新坏账准备"] if ratio < 0.8 else [],
                "capability_count": blueprint_fin.get("capability_count"),
                "capability_target": blueprint_fin.get("capability_target"),
                "dimension_summary": blueprint_fin.get("dimension_focus", []),
            }
        )
        return rows

    def get_stage_blueprint(self, stage_id: str) -> Optional[Dict[str, Any]]:
        blueprint = self.stage_blueprints.get(stage_id)
        if not blueprint:
            return None
        payload = copy.deepcopy(blueprint)
        dataset_fetchers = {
            "order_management": self.get_orders_view,
            "project_development": self.get_projects_view,
            "procurement": self.get_procurement_view,
            "material_receipt": self.get_inventory_view,
            "warehousing": self.get_inventory_view,
            "production": self.get_production_view,
            "quality_check": self.get_quality_view,
            "delivery": self.get_logistics_view,
            "after_sales": self.get_after_sales_view,
            "finance_settlement": self.get_finance_view,
        }
        fetcher = dataset_fetchers.get(stage_id)
        if fetcher:
            dataset = fetcher()
            payload["summary"] = dataset.get("summary")
            preview_key = next(
                (key for key in ("orders", "projects", "procurements", "inventory", "jobs", "lots", "shipments", "cases", "settlements") if key in dataset),
                None,
            )
            if preview_key:
                payload["dataset_preview"] = dataset[preview_key][:5]
        payload["updated_at"] = _now()
        return {"success": True, "blueprint": payload}

    def get_stage_matrix(self) -> Dict[str, Any]:
        stages = self.list_stages()
        matrix: List[Dict[str, Any]] = []
        for stage in stages:
            blueprint = self.stage_blueprints.get(stage["id"], {})
            matrix.append(
                {
                    "stage_id": stage["id"],
                    "name": stage["name"],
                    "status": stage["status"],
                    "progress": stage["progress"],
                    "owner": stage.get("owner"),
                    "risks": stage.get("risks", []),
                    "next_actions": stage.get("next_actions", []),
                    "dimension_summary": stage.get("dimension_summary"),
                    "capability_count": blueprint.get("capability_count"),
                    "capability_target": blueprint.get("capability_target"),
                }
            )
        matrix.extend(self._virtual_stage_rows())
        return {
            "success": True,
            "matrix": matrix,
            "dimension_analysis": self.get_dimension_analysis(),
            "updated_at": _now(),
            "count": len(matrix),
        }

    def get_dimension_analysis(self, stage_id: Optional[str] = None) -> Dict[str, Any]:
        if stage_id:
            if stage_id in self.stage_state:
                scores = self.stage_state[stage_id].dimension_scores
            elif stage_id in ("after_sales", "finance_settlement"):
                scores = {dim: 0.76 for dim in DIMENSIONS}
            else:
                return {"success": False, "error": f"阶段不存在: {stage_id}"}
            payload = self._build_dimension_payload(scores)
            result = analyze_8d(payload)
            result["scope"] = stage_id
            return result
        aggregated_scores = self._aggregate_dimension_scores()
        payload = self._build_dimension_payload(aggregated_scores)
        result = analyze_8d(payload)
        result["scope"] = "overall"
        return result

    def get_flow_map(self) -> Dict[str, Any]:
        stages = self.list_stages()
        nodes: List[Dict[str, Any]] = []
        for stage in stages:
            nodes.append(
                {
                    "id": stage["id"],
                    "label": stage["name"],
                    "status": stage["status"],
                    "progress": stage["progress"],
                    "owner": stage.get("owner"),
                    "dimension_summary": stage.get("dimension_summary"),
                }
            )
        blueprint_after = self.stage_blueprints.get("after_sales", {})
        nodes.append(
            {
                "id": "after_sales",
                "label": blueprint_after.get("name", "售后服务"),
                "status": "in_progress",
                "progress": 40,
                "owner": "售后团队",
                "dimension_summary": blueprint_after.get("dimension_focus", []),
            }
        )
        blueprint_fin = self.stage_blueprints.get("finance_settlement", {})
        nodes.append(
            {
                "id": "finance_settlement",
                "label": blueprint_fin.get("name", "财务结算"),
                "status": "planned",
                "progress": 20,
                "owner": "财务中心",
                "dimension_summary": blueprint_fin.get("dimension_focus", []),
            }
        )
        edges = [
            {"source": nodes[idx]["id"], "target": nodes[idx + 1]["id"], "type": "sequential"}
            for idx in range(len(nodes) - 1)
        ]
        return {
            "success": True,
            "nodes": nodes,
            "edges": edges,
            "updated_at": _now(),
        }


__all__ = ["ERPProcessService", "DIMENSIONS"]


