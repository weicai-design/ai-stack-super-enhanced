"""
运营管理器
Operations Manager

版本: v1.0.0
"""

import logging
from typing import Any, Dict, List, Optional
from collections import defaultdict
from .models import Workflow, BusinessProcess, Issue, Dashboard, ProcessStatus
from .workflow_engine import WorkflowEngine
from .process_manager import ProcessManager
from .monitor import ProcessMonitor
from .analytics import OperationsAnalytics

logger = logging.getLogger(__name__)


class OperationsManager:
    """运营管理器（增强版）"""
    
    def __init__(self):
        self.workflows: Dict[str, List[Workflow]] = defaultdict(list)
        self.processes: Dict[str, List[BusinessProcess]] = defaultdict(list)
        self.issues: Dict[str, List[Issue]] = defaultdict(list)
        
        # 核心组件
        self.workflow_engine = WorkflowEngine()
        self.process_manager = ProcessManager()
        self.monitor = ProcessMonitor()
        self.analytics = OperationsAnalytics()
        
        logger.info("✅ 运营管理器（增强版）已初始化")
    
    # ==================== 工作流管理 ====================
    
    def create_workflow(self, tenant_id: str, workflow: Workflow) -> Workflow:
        """创建工作流"""
        workflow.tenant_id = tenant_id
        self.workflows[tenant_id].append(workflow)
        logger.info(f"工作流已创建: {workflow.name}")
        return workflow
    
    def get_workflows(self, tenant_id: str) -> List[Workflow]:
        """获取工作流列表"""
        return self.workflows.get(tenant_id, [])
    
    def get_workflow(self, tenant_id: str, workflow_id: str) -> Optional[Workflow]:
        """获取工作流"""
        for workflow in self.workflows.get(tenant_id, []):
            if workflow.id == workflow_id:
                return workflow
        return None
    
    # ==================== 业务流程管理 ====================
    
    def start_process(self, tenant_id: str, process: BusinessProcess) -> BusinessProcess:
        """启动业务流程"""
        process.tenant_id = tenant_id
        
        # 获取工作流
        workflow = self.get_workflow(tenant_id, process.workflow_id)
        if workflow:
            process = self.workflow_engine.execute_workflow(workflow, process)
        else:
            process.status = ProcessStatus.IN_PROGRESS
        
        self.processes[tenant_id].append(process)
        logger.info(f"业务流程已启动: {process.name}")
        return process
    
    def get_processes(
        self,
        tenant_id: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[BusinessProcess]:
        """查询业务流程"""
        all_processes = self.processes.get(tenant_id, [])
        return self.analytics.query_processes(tenant_id, all_processes, filters)
    
    def update_process_stage(
        self,
        tenant_id: str,
        process_id: str,
        stage: str,
        data: Dict[str, Any]
    ) -> Optional[BusinessProcess]:
        """更新流程阶段"""
        from .process_manager import BusinessStage
        
        process = self.get_process(tenant_id, process_id)
        if not process:
            return None
        
        # 转换stage字符串为枚举
        try:
            stage_enum = BusinessStage(stage)
            return self.process_manager.update_stage(process, stage_enum, data)
        except ValueError:
            logger.error(f"无效的业务阶段: {stage}")
            return None
    
    def get_process(self, tenant_id: str, process_id: str) -> Optional[BusinessProcess]:
        """获取业务流程"""
        for process in self.processes.get(tenant_id, []):
            if process.id == process_id:
                return process
        return None
    
    def get_process_progress(
        self,
        tenant_id: str,
        process_id: str
    ) -> Optional[Dict[str, Any]]:
        """获取流程进度"""
        process = self.get_process(tenant_id, process_id)
        if not process:
            return None
        
        return self.process_manager.calculate_progress(process)
    
    # ==================== 问题管理 ====================
    
    def report_issue(self, tenant_id: str, issue: Issue) -> Issue:
        """报告问题"""
        issue.tenant_id = tenant_id
        self.issues[tenant_id].append(issue)
        logger.info(f"问题已报告: {issue.title}")
        return issue
    
    def get_issues(
        self,
        tenant_id: str,
        status: Optional[str] = None
    ) -> List[Issue]:
        """获取问题列表"""
        issues = self.issues.get(tenant_id, [])
        if status:
            issues = [i for i in issues if i.status == status]
        return issues
    
    def resolve_issue(
        self,
        tenant_id: str,
        issue_id: str,
        resolution: str
    ) -> Optional[Issue]:
        """解决问题"""
        for issue in self.issues.get(tenant_id, []):
            if issue.id == issue_id:
                return self.monitor.track_issue_resolution(issue, resolution)
        return None
    
    def check_closed_loop(self, tenant_id: str) -> Dict[str, Any]:
        """检查闭环管理"""
        issues = self.issues.get(tenant_id, [])
        return self.monitor.check_closed_loop(tenant_id, issues)
    
    # ==================== 分析与看板 ====================
    
    def get_dashboard(self, tenant_id: str) -> Dashboard:
        """获取运营看板"""
        processes = self.processes.get(tenant_id, [])
        issues = self.issues.get(tenant_id, [])
        return self.analytics.generate_dashboard(tenant_id, processes, issues)
    
    def get_statistics(
        self,
        tenant_id: str,
        period: str = "month"
    ) -> Dict[str, Any]:
        """获取统计分析"""
        processes = self.processes.get(tenant_id, [])
        return self.analytics.generate_statistics(tenant_id, processes, period)
    
    def get_trend_data(
        self,
        tenant_id: str,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """获取趋势数据"""
        processes = self.processes.get(tenant_id, [])
        return self.analytics.generate_trend_chart(tenant_id, processes, days)
    
    # ==================== 监控检查 ====================
    
    def detect_anomalies(self, tenant_id: str) -> List[Dict[str, Any]]:
        """检测异常"""
        processes = self.processes.get(tenant_id, [])
        return self.monitor.detect_anomalies(processes)
    
    def collect_new_issues(self, tenant_id: str) -> List[Issue]:
        """收集新问题"""
        processes = self.processes.get(tenant_id, [])
        return self.monitor.collect_issues(tenant_id, processes)


operations_manager = OperationsManager()

