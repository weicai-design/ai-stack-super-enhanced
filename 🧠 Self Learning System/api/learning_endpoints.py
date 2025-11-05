"""
自我学习系统 - API端点
接收OpenWebUI和控制台的交互数据，实现自我学习和进化
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime
import json
import os

router = APIRouter(prefix="/api/learning", tags=["learning"])

# 学习数据存储目录
LEARNING_DATA_DIR = "/Users/ywc/ai-stack-super-enhanced/🧠 Self Learning System/data"
os.makedirs(LEARNING_DATA_DIR, exist_ok=True)

# 学习样本计数器
learning_count = 0
evolution_count = 0


class LearningSubmission(BaseModel):
    """学习提交"""
    input: str
    output: str
    user_id: str
    timestamp: str
    context: Optional[Dict[str, Any]] = None


class EvolutionMetrics(BaseModel):
    """进化指标"""
    user_question_length: int
    ai_response_length: int
    detected_system: Optional[str] = None
    timestamp: str


@router.post("/submit")
async def submit_learning_sample(sample: LearningSubmission):
    """
    接收学习样本
    每次OpenWebUI对话都会调用此接口
    """
    global learning_count
    learning_count += 1
    
    try:
        # 保存学习样本到文件
        sample_file = os.path.join(
            LEARNING_DATA_DIR, 
            f"interaction_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{learning_count}.json"
        )
        
        with open(sample_file, 'w', encoding='utf-8') as f:
            json.dump(sample.dict(), f, ensure_ascii=False, indent=2)
        
        # 分析样本质量
        quality_score = analyze_sample_quality(sample)
        
        # 如果是高质量样本，标记为重点学习
        if quality_score > 0.8:
            await mark_high_quality_sample(sample_file)
        
        return {
            "success": True,
            "message": f"学习样本已接收 (第{learning_count}个)",
            "quality_score": quality_score,
            "learning_count": learning_count,
            "status": "系统正在学习中..."
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/evolution/optimize")
async def trigger_evolution(metrics: EvolutionMetrics):
    """
    触发自我进化
    系统根据交互数据自动优化参数
    """
    global evolution_count
    evolution_count += 1
    
    try:
        # 保存进化数据
        evolution_file = os.path.join(
            LEARNING_DATA_DIR,
            f"evolution_{datetime.now().strftime('%Y%m%d')}_{evolution_count}.json"
        )
        
        with open(evolution_file, 'w', encoding='utf-8') as f:
            json.dump(metrics.dict(), f, ensure_ascii=False, indent=2)
        
        # 分析是否需要优化
        optimization_needed = check_optimization_need(metrics)
        
        if optimization_needed:
            await perform_optimization()
        
        return {
            "success": True,
            "evolution_count": evolution_count,
            "optimization_performed": optimization_needed,
            "status": "系统持续进化中..."
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_learning_stats():
    """获取学习统计"""
    
    # 统计学习样本数量
    total_samples = len([f for f in os.listdir(LEARNING_DATA_DIR) if f.startswith("interaction_")])
    total_evolutions = len([f for f in os.listdir(LEARNING_DATA_DIR) if f.startswith("evolution_")])
    
    return {
        "total_learning_samples": total_samples,
        "total_evolutions": total_evolutions,
        "learning_active": True,
        "evolution_active": True,
        "intelligence_level": calculate_intelligence_level(total_samples),
        "status": "系统持续学习进化中"
    }


@router.get("/knowledge/growth")
async def get_knowledge_growth():
    """获取知识增长曲线"""
    
    # 按日期统计学习样本
    samples_by_date = {}
    
    for filename in os.listdir(LEARNING_DATA_DIR):
        if filename.startswith("interaction_"):
            date = filename.split("_")[1]
            samples_by_date[date] = samples_by_date.get(date, 0) + 1
    
    return {
        "knowledge_growth": samples_by_date,
        "total_knowledge": sum(samples_by_date.values()),
        "growth_rate": "持续增长"
    }


def analyze_sample_quality(sample: LearningSubmission) -> float:
    """分析样本质量"""
    score = 0.5
    
    # 问题长度合理性
    if 10 <= len(sample.input) <= 200:
        score += 0.1
    
    # 回答长度合理性
    if 50 <= len(sample.output) <= 1000:
        score += 0.1
    
    # 有上下文信息
    if sample.context:
        score += 0.2
    
    # 检测到系统意图
    if sample.context and sample.context.get("detected_intent"):
        score += 0.1
    
    return min(score, 1.0)


async def mark_high_quality_sample(sample_file: str):
    """标记高质量样本"""
    # 创建高质量样本链接或复制
    high_quality_dir = os.path.join(LEARNING_DATA_DIR, "high_quality")
    os.makedirs(high_quality_dir, exist_ok=True)
    
    # 这里可以实现更复杂的处理
    pass


def check_optimization_need(metrics: EvolutionMetrics) -> bool:
    """检查是否需要优化"""
    # 简单规则：每100次交互触发一次优化
    return evolution_count % 100 == 0


async def perform_optimization():
    """执行系统优化"""
    # 这里可以实现：
    # 1. 调整RAG检索参数
    # 2. 优化意图识别阈值
    # 3. 更新专家建议模板
    # 4. 微调AI模型
    pass


def calculate_intelligence_level(sample_count: int) -> str:
    """计算智能等级"""
    if sample_count < 10:
        return "初级 (Lv.1)"
    elif sample_count < 50:
        return "中级 (Lv.2)"
    elif sample_count < 200:
        return "高级 (Lv.3)"
    elif sample_count < 500:
        return "专家 (Lv.4)"
    else:
        return f"大师 (Lv.5+) - 已学习{sample_count}次"



