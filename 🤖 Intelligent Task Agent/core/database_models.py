"""
智能任务代理 - 数据库模型
支持任务规划、执行、监控、分析
"""

from sqlalchemy import Column, Integer, String, DateTime, Float, Text, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class Task(Base):
    """任务主表"""
    __tablename__ = 'tasks'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False, comment='任务名称')
    description = Column(Text, comment='任务描述')
    task_type = Column(String(50), comment='任务类型: scheduled/manual/triggered')
    priority = Column(Integer, default=5, comment='优先级: 1-10')
    status = Column(String(50), default='pending', comment='状态: pending/running/paused/completed/failed/cancelled')
    
    # 任务配置
    config = Column(JSON, comment='任务配置参数')
    schedule_config = Column(JSON, comment='调度配置')
    
    # 时间信息
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    scheduled_time = Column(DateTime, comment='计划执行时间')
    started_at = Column(DateTime, comment='开始时间')
    completed_at = Column(DateTime, comment='完成时间')
    
    # 执行信息
    progress = Column(Float, default=0.0, comment='进度: 0-100')
    result = Column(JSON, comment='执行结果')
    error_message = Column(Text, comment='错误信息')
    
    # 关联关系
    steps = relationship("TaskStep", back_populates="task", cascade="all, delete-orphan")
    executions = relationship("TaskExecution", back_populates="task", cascade="all, delete-orphan")
    monitoring_records = relationship("TaskMonitoring", back_populates="task", cascade="all, delete-orphan")


class TaskStep(Base):
    """任务步骤表"""
    __tablename__ = 'task_steps'
    
    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey('tasks.id'), nullable=False)
    
    step_order = Column(Integer, nullable=False, comment='步骤顺序')
    name = Column(String(200), nullable=False, comment='步骤名称')
    description = Column(Text, comment='步骤描述')
    step_type = Column(String(50), comment='步骤类型: api_call/data_processing/ai_task/notification')
    
    # 步骤配置
    config = Column(JSON, comment='步骤配置参数')
    dependencies = Column(JSON, comment='依赖的步骤ID列表')
    
    # 执行状态
    status = Column(String(50), default='pending', comment='状态')
    progress = Column(Float, default=0.0, comment='进度')
    result = Column(JSON, comment='执行结果')
    error_message = Column(Text, comment='错误信息')
    
    # 时间信息
    started_at = Column(DateTime, comment='开始时间')
    completed_at = Column(DateTime, comment='完成时间')
    
    # 关联关系
    task = relationship("Task", back_populates="steps")


class TaskExecution(Base):
    """任务执行记录表"""
    __tablename__ = 'task_executions'
    
    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey('tasks.id'), nullable=False)
    
    execution_id = Column(String(100), unique=True, comment='执行ID')
    trigger_type = Column(String(50), comment='触发类型: manual/scheduled/event')
    trigger_info = Column(JSON, comment='触发信息')
    
    # 执行状态
    status = Column(String(50), default='running', comment='执行状态')
    progress = Column(Float, default=0.0, comment='进度')
    
    # 时间信息
    started_at = Column(DateTime, default=datetime.now, comment='开始时间')
    completed_at = Column(DateTime, comment='完成时间')
    duration = Column(Float, comment='执行时长(秒)')
    
    # 结果信息
    result = Column(JSON, comment='执行结果')
    success = Column(Boolean, comment='是否成功')
    error_message = Column(Text, comment='错误信息')
    
    # 资源使用
    resource_usage = Column(JSON, comment='资源使用情况')
    
    # 关联关系
    task = relationship("Task", back_populates="executions")


class TaskMonitoring(Base):
    """任务监控记录表"""
    __tablename__ = 'task_monitoring'
    
    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey('tasks.id'), nullable=False)
    execution_id = Column(String(100), comment='执行ID')
    
    # 监控时间
    timestamp = Column(DateTime, default=datetime.now, comment='监控时间')
    
    # 状态信息
    status = Column(String(50), comment='任务状态')
    progress = Column(Float, comment='进度')
    current_step = Column(String(200), comment='当前步骤')
    
    # 性能指标
    cpu_usage = Column(Float, comment='CPU使用率')
    memory_usage = Column(Float, comment='内存使用(MB)')
    disk_io = Column(Float, comment='磁盘IO')
    network_io = Column(Float, comment='网络IO')
    
    # 业务指标
    metrics = Column(JSON, comment='业务指标')
    
    # 告警信息
    alerts = Column(JSON, comment='告警信息')
    
    # 关联关系
    task = relationship("Task", back_populates="monitoring_records")


class TaskTemplate(Base):
    """任务模板表"""
    __tablename__ = 'task_templates'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False, comment='模板名称')
    description = Column(Text, comment='模板描述')
    category = Column(String(100), comment='模板分类')
    
    # 模板配置
    template_config = Column(JSON, comment='模板配置')
    default_schedule = Column(JSON, comment='默认调度配置')
    
    # 使用统计
    usage_count = Column(Integer, default=0, comment='使用次数')
    success_rate = Column(Float, comment='成功率')
    avg_duration = Column(Float, comment='平均执行时长')
    
    # 时间信息
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 是否启用
    is_active = Column(Boolean, default=True)


class TaskEvolution(Base):
    """任务进化记录表 - 自我学习和优化"""
    __tablename__ = 'task_evolution'
    
    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey('tasks.id'))
    
    # 进化类型
    evolution_type = Column(String(50), comment='进化类型: optimization/error_fix/performance_improvement')
    
    # 问题描述
    problem_description = Column(Text, comment='发现的问题')
    problem_severity = Column(String(20), comment='严重程度: low/medium/high/critical')
    
    # 优化建议
    suggestion = Column(Text, comment='优化建议')
    suggestion_source = Column(String(50), comment='建议来源: ai_analysis/historical_data/rag_knowledge')
    
    # 实施情况
    implemented = Column(Boolean, default=False, comment='是否已实施')
    implementation_date = Column(DateTime, comment='实施日期')
    implementation_result = Column(JSON, comment='实施结果')
    
    # 效果评估
    before_metrics = Column(JSON, comment='优化前指标')
    after_metrics = Column(JSON, comment='优化后指标')
    improvement_percentage = Column(Float, comment='改进百分比')
    
    # 时间信息
    discovered_at = Column(DateTime, default=datetime.now, comment='发现时间')
    
    # RAG关联
    rag_references = Column(JSON, comment='RAG知识库引用')


class TaskSchedule(Base):
    """任务调度配置表"""
    __tablename__ = 'task_schedules'
    
    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey('tasks.id'), nullable=False)
    
    # 调度配置
    schedule_type = Column(String(50), comment='调度类型: cron/interval/once')
    cron_expression = Column(String(100), comment='Cron表达式')
    interval_seconds = Column(Integer, comment='间隔秒数')
    
    # 执行时间窗口
    start_date = Column(DateTime, comment='开始日期')
    end_date = Column(DateTime, comment='结束日期')
    execution_time = Column(String(10), comment='执行时间(HH:MM)')
    
    # 重试配置
    retry_on_failure = Column(Boolean, default=True, comment='失败时重试')
    max_retries = Column(Integer, default=3, comment='最大重试次数')
    retry_interval = Column(Integer, default=300, comment='重试间隔(秒)')
    
    # 状态
    is_active = Column(Boolean, default=True, comment='是否启用')
    last_run_time = Column(DateTime, comment='上次运行时间')
    next_run_time = Column(DateTime, comment='下次运行时间')
    
    # 时间信息
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class TaskDependency(Base):
    """任务依赖关系表"""
    __tablename__ = 'task_dependencies'
    
    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey('tasks.id'), nullable=False, comment='当前任务ID')
    depends_on_task_id = Column(Integer, ForeignKey('tasks.id'), nullable=False, comment='依赖的任务ID')
    
    dependency_type = Column(String(50), comment='依赖类型: success/completion/data')
    condition = Column(JSON, comment='依赖条件')
    
    created_at = Column(DateTime, default=datetime.now)

