"""
知识沉淀到RAG的条目模板系统
P0-019: 知识沉淀到RAG的条目模板与自动入库策略
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field, asdict
from enum import Enum
import json
import logging

logger = logging.getLogger(__name__)


class KnowledgeType(Enum):
    """知识类型"""
    TASK_EXECUTION = "task_execution"  # 任务执行结果
    WORKFLOW_INSIGHT = "workflow_insight"  # 工作流洞察
    ERROR_SOLUTION = "error_solution"  # 错误解决方案
    BEST_PRACTICE = "best_practice"  # 最佳实践
    CONFIGURATION = "configuration"  # 配置信息
    API_USAGE = "api_usage"  # API使用示例
    CODE_SNIPPET = "code_snippet"  # 代码片段
    DOCUMENTATION = "documentation"  # 文档
    Q_A = "q_a"  # 问答对
    ANALYSIS_RESULT = "analysis_result"  # 分析结果
    LEARNING_OUTCOME = "learning_outcome"  # 学习成果


class KnowledgePriority(Enum):
    """知识优先级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class KnowledgeEntry:
    """知识条目"""
    entry_id: str
    knowledge_type: KnowledgeType
    title: str
    content: str
    summary: Optional[str] = None
    priority: KnowledgePriority = KnowledgePriority.MEDIUM
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    source: Optional[str] = None
    source_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    quality_score: float = 0.0  # 0-100
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data["knowledge_type"] = self.knowledge_type.value
        data["priority"] = self.priority.value
        data["created_at"] = self.created_at.isoformat()
        data["updated_at"] = self.updated_at.isoformat()
        if self.last_accessed:
            data["last_accessed"] = self.last_accessed.isoformat()
        return data
    
    def to_rag_format(self) -> Dict[str, Any]:
        """转换为RAG格式"""
        # 构建完整的知识文本
        text_parts = []
        
        # 标题
        text_parts.append(f"# {self.title}\n")
        
        # 类型和优先级
        text_parts.append(f"**类型**: {self.knowledge_type.value}\n")
        text_parts.append(f"**优先级**: {self.priority.value}\n")
        
        # 摘要
        if self.summary:
            text_parts.append(f"**摘要**: {self.summary}\n")
        
        # 标签
        if self.tags:
            text_parts.append(f"**标签**: {', '.join(self.tags)}\n")
        
        # 内容
        text_parts.append(f"\n## 内容\n{self.content}\n")
        
        # 元数据（如果有重要信息）
        if self.metadata:
            important_meta = {k: v for k, v in self.metadata.items() 
                           if k not in ['timestamp', 'user_id', 'session_id']}
            if important_meta:
                text_parts.append(f"\n## 元数据\n{json.dumps(important_meta, ensure_ascii=False, indent=2)}\n")
        
        # 来源
        if self.source:
            text_parts.append(f"\n**来源**: {self.source}")
            if self.source_id:
                text_parts.append(f" (ID: {self.source_id})")
            text_parts.append("\n")
        
        full_text = "\n".join(text_parts)
        
        # RAG元数据
        rag_metadata = {
            "knowledge_entry_id": self.entry_id,
            "knowledge_type": self.knowledge_type.value,
            "priority": self.priority.value,
            "tags": self.tags,
            "quality_score": self.quality_score,
            "source": self.source,
            "source_id": self.source_id,
            "created_at": self.created_at.isoformat(),
            **self.metadata
        }
        
        return {
            "text": full_text,
            "metadata": rag_metadata,
            "doc_id": f"knowledge_{self.entry_id}"
        }


class KnowledgeTemplate:
    """知识模板"""
    
    def __init__(self, template_id: str, name: str, knowledge_type: KnowledgeType):
        self.template_id = template_id
        self.name = name
        self.knowledge_type = knowledge_type
        self.required_fields: List[str] = []
        self.optional_fields: List[str] = []
        self.field_templates: Dict[str, Any] = {}
        self.default_priority: KnowledgePriority = KnowledgePriority.MEDIUM
        self.default_tags: List[str] = []
    
    def create_entry(
        self,
        title: str,
        content: str,
        **kwargs
    ) -> KnowledgeEntry:
        """
        根据模板创建知识条目
        
        Args:
            title: 标题
            content: 内容
            **kwargs: 其他字段
            
        Returns:
            知识条目
        """
        import uuid
        entry_id = f"entry_{int(datetime.now().timestamp() * 1000)}_{uuid.uuid4().hex[:8]}"
        
        # 提取字段
        summary = kwargs.get("summary")
        priority = kwargs.get("priority", self.default_priority)
        if isinstance(priority, str):
            priority = KnowledgePriority(priority)
        
        tags = kwargs.get("tags", []) + self.default_tags
        metadata = kwargs.get("metadata", {})
        source = kwargs.get("source")
        source_id = kwargs.get("source_id")
        
        # 计算质量分数
        quality_score = self._calculate_quality_score(title, content, summary, metadata)
        
        entry = KnowledgeEntry(
            entry_id=entry_id,
            knowledge_type=self.knowledge_type,
            title=title,
            content=content,
            summary=summary,
            priority=priority,
            tags=list(set(tags)),  # 去重
            metadata=metadata,
            source=source,
            source_id=source_id,
            quality_score=quality_score
        )
        
        return entry
    
    def _calculate_quality_score(
        self,
        title: str,
        content: str,
        summary: Optional[str],
        metadata: Dict[str, Any]
    ) -> float:
        """计算质量分数"""
        score = 50.0  # 基础分数
        
        # 标题长度
        if len(title) >= 10:
            score += 10
        elif len(title) >= 5:
            score += 5
        
        # 内容长度
        if len(content) >= 500:
            score += 20
        elif len(content) >= 200:
            score += 10
        elif len(content) >= 100:
            score += 5
        
        # 有摘要
        if summary and len(summary) >= 50:
            score += 10
        
        # 有标签
        if metadata.get("tags"):
            score += 5
        
        # 有来源
        if metadata.get("source"):
            score += 5
        
        return min(100.0, score)


class KnowledgeTemplateManager:
    """知识模板管理器"""
    
    def __init__(self):
        self.templates: Dict[str, KnowledgeTemplate] = {}
        self._init_default_templates()
    
    def _init_default_templates(self):
        """初始化默认模板"""
        # 任务执行结果模板
        task_template = KnowledgeTemplate(
            template_id="task_execution",
            name="任务执行结果",
            knowledge_type=KnowledgeType.TASK_EXECUTION
        )
        task_template.required_fields = ["title", "content", "task_id"]
        task_template.optional_fields = ["summary", "result", "error", "duration"]
        task_template.default_priority = KnowledgePriority.HIGH
        task_template.default_tags = ["task", "execution"]
        self.templates["task_execution"] = task_template
        
        # 工作流洞察模板
        workflow_template = KnowledgeTemplate(
            template_id="workflow_insight",
            name="工作流洞察",
            knowledge_type=KnowledgeType.WORKFLOW_INSIGHT
        )
        workflow_template.required_fields = ["title", "content", "workflow_id"]
        workflow_template.optional_fields = ["summary", "optimization", "metrics"]
        workflow_template.default_priority = KnowledgePriority.HIGH
        workflow_template.default_tags = ["workflow", "insight"]
        self.templates["workflow_insight"] = workflow_template
        
        # 错误解决方案模板
        error_template = KnowledgeTemplate(
            template_id="error_solution",
            name="错误解决方案",
            knowledge_type=KnowledgeType.ERROR_SOLUTION
        )
        error_template.required_fields = ["title", "content", "error_type"]
        error_template.optional_fields = ["summary", "solution", "prevention"]
        error_template.default_priority = KnowledgePriority.CRITICAL
        error_template.default_tags = ["error", "solution"]
        self.templates["error_solution"] = error_template
        
        # 最佳实践模板
        practice_template = KnowledgeTemplate(
            template_id="best_practice",
            name="最佳实践",
            knowledge_type=KnowledgeType.BEST_PRACTICE
        )
        practice_template.required_fields = ["title", "content"]
        practice_template.optional_fields = ["summary", "context", "examples"]
        practice_template.default_priority = KnowledgePriority.HIGH
        practice_template.default_tags = ["best-practice"]
        self.templates["best_practice"] = practice_template
        
        # 配置信息模板
        config_template = KnowledgeTemplate(
            template_id="configuration",
            name="配置说明",
            knowledge_type=KnowledgeType.CONFIGURATION
        )
        config_template.required_fields = ["title", "content"]
        config_template.optional_fields = ["summary", "environment", "versions"]
        config_template.default_priority = KnowledgePriority.MEDIUM
        config_template.default_tags = ["configuration", "setup"]
        self.templates["configuration"] = config_template
        
        # API使用模板
        api_template = KnowledgeTemplate(
            template_id="api_usage",
            name="API使用示例",
            knowledge_type=KnowledgeType.API_USAGE
        )
        api_template.required_fields = ["title", "content", "api_name"]
        api_template.optional_fields = ["summary", "request", "response", "code_sample"]
        api_template.default_priority = KnowledgePriority.MEDIUM
        api_template.default_tags = ["api", "usage"]
        self.templates["api_usage"] = api_template
        
        # 代码片段模板
        code_template = KnowledgeTemplate(
            template_id="code_snippet",
            name="代码片段",
            knowledge_type=KnowledgeType.CODE_SNIPPET
        )
        code_template.required_fields = ["title", "content", "language"]
        code_template.optional_fields = ["summary", "context", "dependencies"]
        code_template.default_priority = KnowledgePriority.MEDIUM
        code_template.default_tags = ["code", "snippet"]
        self.templates["code_snippet"] = code_template
        
        # 文档条目模板
        doc_template = KnowledgeTemplate(
            template_id="documentation",
            name="文档条目",
            knowledge_type=KnowledgeType.DOCUMENTATION
        )
        doc_template.required_fields = ["title", "content"]
        doc_template.optional_fields = ["summary", "section", "related_links"]
        doc_template.default_priority = KnowledgePriority.MEDIUM
        doc_template.default_tags = ["documentation"]
        self.templates["documentation"] = doc_template
        
        # 学习成果模板
        learning_template = KnowledgeTemplate(
            template_id="learning_outcome",
            name="学习成果",
            knowledge_type=KnowledgeType.LEARNING_OUTCOME
        )
        learning_template.required_fields = ["title", "content", "topic"]
        learning_template.optional_fields = ["summary", "impact", "next_steps"]
        learning_template.default_priority = KnowledgePriority.MEDIUM
        learning_template.default_tags = ["learning", "insight"]
        self.templates["learning_outcome"] = learning_template
        
        # 问答对模板
        qa_template = KnowledgeTemplate(
            template_id="q_a",
            name="问答对",
            knowledge_type=KnowledgeType.Q_A
        )
        qa_template.required_fields = ["title", "content", "question"]
        qa_template.optional_fields = ["summary", "answer", "context"]
        qa_template.default_priority = KnowledgePriority.MEDIUM
        qa_template.default_tags = ["qa"]
        self.templates["q_a"] = qa_template
        
        # 分析结果模板
        analysis_template = KnowledgeTemplate(
            template_id="analysis_result",
            name="分析结果",
            knowledge_type=KnowledgeType.ANALYSIS_RESULT
        )
        analysis_template.required_fields = ["title", "content", "analysis_type"]
        analysis_template.optional_fields = ["summary", "findings", "recommendations"]
        analysis_template.default_priority = KnowledgePriority.MEDIUM
        analysis_template.default_tags = ["analysis"]
        self.templates["analysis_result"] = analysis_template
    
    def get_template(self, template_id: str) -> Optional[KnowledgeTemplate]:
        """获取模板"""
        return self.templates.get(template_id)
    
    def list_templates(self) -> List[Dict[str, Any]]:
        """列出所有模板"""
        return [
            {
                "template_id": t.template_id,
                "name": t.name,
                "knowledge_type": t.knowledge_type.value,
                "required_fields": t.required_fields,
                "optional_fields": t.optional_fields,
                "default_priority": t.default_priority.value,
                "default_tags": t.default_tags
            }
            for t in self.templates.values()
        ]
    
    def create_entry_from_template(
        self,
        template_id: str,
        title: str,
        content: str,
        **kwargs
    ) -> Optional[KnowledgeEntry]:
        """根据模板创建知识条目"""
        template = self.get_template(template_id)
        if not template:
            return None
        
        return template.create_entry(title, content, **kwargs)

