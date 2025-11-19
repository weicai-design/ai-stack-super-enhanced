"""专家管理器"""
import logging
from typing import Dict, List
from .models import ExpertModel, ExpertPrompt, ExpertAdvice

logger = logging.getLogger(__name__)

class ExpertManager:
    def __init__(self):
        self.experts: Dict[str, ExpertModel] = {}
        self.prompts: Dict[str, List[ExpertPrompt]] = {}
        self._init_default_experts()
        logger.info("✅ 专家管理器已初始化")
    
    def _init_default_experts(self):
        """初始化默认专家模型"""
        domains = ["finance", "stock", "content", "trend", "operations", "erp"]
        for domain in domains:
            expert = ExpertModel(
                domain=domain,
                name=f"{domain.title()} Expert",
                description=f"Specialized in {domain} domain",
                capabilities=[f"{domain}_analysis", f"{domain}_advice"]
            )
            self.experts[domain] = expert
    
    def get_expert(self, domain: str) -> ExpertModel | None:
        return self.experts.get(domain)
    
    def get_advice(self, domain: str, question: str) -> ExpertAdvice:
        expert = self.get_expert(domain)
        if not expert:
            raise ValueError(f"Expert for {domain} not found")
        return ExpertAdvice(
            expert_id=expert.id,
            question=question,
            advice=f"Expert advice for: {question}"
        )

expert_manager = ExpertManager()



























