"""
Content Generator
内容生成器

根据需求4.4: 自主内容创作与生成，去AI化
"""

import requests
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import random
import re
from sources.material_collector import MaterialManager


class ContentGenerator:
    """内容生成器"""
    
    def __init__(self, llm_url: str = "http://localhost:11434"):
        """
        初始化内容生成器
        
        Args:
            llm_url: LLM服务地址
        """
        self.llm_url = llm_url
        self.model = "qwen2.5:7b"
    
    def generate_article(
        self,
        topic: str,
        platform: str = "xiaohongshu",
        style: str = "casual"
    ) -> Dict[str, Any]:
        """
        生成文章内容
        
        根据需求4.4: 自主内容创作
        
        Args:
            topic: 主题
            platform: 目标平台
            style: 风格
            
        Returns:
            生成的文章
        """
        # 构造提示词
        prompt = self._build_prompt(topic, platform, style)
        
        # 调用LLM生成（简化版）
        content = self._call_llm(prompt)
        
        # 去AI化处理
        content = self._deai_content(content)
        
        return {
            "topic": topic,
            "platform": platform,
            "title": self._generate_title(topic),
            "content": content,
            "tags": self._generate_tags(topic),
            "generated_at": datetime.now().isoformat(),
        }
    
    def _build_prompt(self, topic: str, platform: str, style: str) -> str:
        """构建提示词"""
        platform_styles = {
            "xiaohongshu": "轻松活泼，使用emoji，分享个人体验",
            "douyin": "简短有趣，吸引眼球，适合视频文案",
            "zhihu": "专业深度，逻辑清晰，提供价值",
            "toutiao": "信息丰富，标题党，引发讨论"
        }
        
        style_desc = platform_styles.get(platform, "自然真实")
        
        return f"""
请围绕主题"{topic}"创作一篇适合{platform}平台的内容。

要求：
1. 风格：{style_desc}
2. 字数：300-500字
3. 真实性：基于真实体验和感受
4. 独特性：避免AI痕迹，展现个性
5. 吸引力：标题吸引人，内容有价值

请直接输出内容，不要解释。
"""
    
    def _call_llm(self, prompt: str) -> str:
        """
        调用LLM生成内容
        
        Args:
            prompt: 提示词
            
        Returns:
            生成的内容
        """
        # TODO: 实际调用Ollama API
        # 这里返回模拟内容
        return f"""
今天要分享一个超级实用的技巧！😍

{prompt[:50]}...相关的内容真的太有用了！我自己试过之后，效果超级好✨

具体步骤：
1️⃣ 首先...
2️⃣ 然后...
3️⃣ 最后...

个人感受：真的很推荐大家试试，绝对不会后悔！💯

#实用技巧 #干货分享 #好物推荐
"""
    
    def _deai_content(self, content: str) -> str:
        """
        去AI化处理
        
        根据需求4.4: 去AI化，形成内容独特方案
        
        Args:
            content: 原始内容
            
        Returns:
            去AI化后的内容
        """
        # 添加个性化表达
        # 替换AI常用词汇
        # 增加口语化表达
        # 添加个人体验
        
        replacements = {
            "首先": random.choice(["第一步", "先说说", "一开始"]),
            "然后": random.choice(["接着", "然后呢", "下一步"]),
            "最后": random.choice(["最后啦", "终于", "压轴的"]),
            "非常": random.choice(["超级", "特别", "巨"]),
        }
        
        for old, new in replacements.items():
            content = content.replace(old, new)
        
        return content
    
    def _generate_title(self, topic: str) -> str:
        """
        生成标题
        
        Args:
            topic: 主题
            
        Returns:
            标题
        """
        templates = [
            f"🔥{topic}！这个方法你一定要知道",
            f"✨发现一个{topic}的神仙技巧",
            f"💯{topic}完整攻略，建议收藏",
            f"⚡真实测评！{topic}到底怎么样",
        ]
        
        return random.choice(templates)
    
    def _generate_tags(self, topic: str) -> List[str]:
        """
        生成标签
        
        Args:
            topic: 主题
            
        Returns:
            标签列表
        """
        common_tags = ["干货分享", "实用技巧", "好物推荐", "真实测评"]
        return [topic] + random.sample(common_tags, 2)


class ContentPlan:
    """
    内容计划
    
    根据需求4.3: 制定内容计划
    """
    
    def __init__(self):
        """初始化内容计划"""
        self.plans = []
    
    def create_plan(
        self,
        topic: str,
        platforms: List[str],
        frequency: str = "daily",
        duration_days: int = 7
    ) -> Dict[str, Any]:
        """
        创建内容计划
        
        Args:
            topic: 主题
            platforms: 目标平台
            frequency: 发布频率
            duration_days: 持续天数
            
        Returns:
            内容计划
        """
        plan = {
            "id": len(self.plans) + 1,
            "topic": topic,
            "platforms": platforms,
            "frequency": frequency,
            "duration_days": duration_days,
            "status": "active",
            "created_at": datetime.now().isoformat(),
            "scheduled_posts": self._generate_schedule(platforms, frequency, duration_days),
        }
        
        self.plans.append(plan)
        return plan
    
    def _generate_schedule(
        self,
        platforms: List[str],
        frequency: str,
        duration_days: int
    ) -> List[Dict[str, Any]]:
        """
        生成发布计划
        
        Args:
            platforms: 平台列表
            frequency: 频率
            duration_days: 天数
            
        Returns:
            发布计划列表
        """
        schedule = []
        
        # 根据频率生成计划
        posts_per_day = 1 if frequency == "daily" else 2 if frequency == "twice_daily" else 3
        
        for day in range(duration_days):
            for i in range(posts_per_day):
                for platform in platforms:
                    schedule.append({
                        "day": day + 1,
                        "platform": platform,
                        "time": f"{random.randint(9, 21)}:00",
                        "status": "pending",
                    })
        
        return schedule
    
    def get_active_plans(self) -> List[Dict[str, Any]]:
        """获取活动中的计划"""
        return [p for p in self.plans if p.get("status") == "active"]


class ContentOptimizer:
    """
    内容优化器
    
    根据需求4.6: 内容创作成功率反思，自我进化
    """
    
    def __init__(self):
        """初始化内容优化器"""
        self.performance_history = []
    
    def analyze_performance(
        self,
        content_id: str,
        metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        分析内容表现
        
        Args:
            content_id: 内容ID
            metrics: 表现指标（浏览量、点赞、评论等）
            
        Returns:
            分析结果
        """
        # 记录表现
        performance = {
            "content_id": content_id,
            "metrics": metrics,
            "timestamp": datetime.now().isoformat(),
        }
        
        self.performance_history.append(performance)
        
        # 分析
        views = metrics.get("views", 0)
        likes = metrics.get("likes", 0)
        comments = metrics.get("comments", 0)
        
        # 计算互动率
        engagement_rate = (likes + comments) / views * 100 if views > 0 else 0
        
        # 评级
        if engagement_rate > 10:
            rating = "优秀"
        elif engagement_rate > 5:
            rating = "良好"
        elif engagement_rate > 2:
            rating = "一般"
        else:
            rating = "需改进"
        
        return {
            "engagement_rate": round(engagement_rate, 2),
            "rating": rating,
            "suggestions": self._generate_suggestions(rating, metrics),
        }
    
    def _generate_suggestions(
        self,
        rating: str,
        metrics: Dict[str, Any]
    ) -> List[str]:
        """
        生成优化建议
        
        Args:
            rating: 评级
            metrics: 指标
            
        Returns:
            建议列表
        """
        suggestions = []
        
        if rating == "需改进":
            suggestions.append("标题可能不够吸引人，建议优化")
            suggestions.append("内容价值需要提升")
            suggestions.append("尝试不同的话题方向")
        elif rating == "一般":
            suggestions.append("继续保持，可适当增加互动")
            suggestions.append("尝试优化配图或视频")
        else:
            suggestions.append("表现优秀，继续保持！")
            suggestions.append("可以尝试类似话题")
        
        return suggestions
    
    def get_optimization_insights(self) -> Dict[str, Any]:
        """
        获取优化洞察
        
        根据需求4.6: 自我学习和自我进化
        
        Returns:
            优化洞察
        """
        if not self.performance_history:
            return {"message": "暂无数据"}
        
        # 计算平均表现
        avg_engagement = sum(
            p["metrics"].get("likes", 0) / max(p["metrics"].get("views", 1), 1)
            for p in self.performance_history
        ) / len(self.performance_history) * 100
        
        return {
            "total_contents": len(self.performance_history),
            "avg_engagement_rate": round(avg_engagement, 2),
            "best_performing": max(
                self.performance_history,
                key=lambda x: x["metrics"].get("likes", 0)
            ) if self.performance_history else None,
            "insights": [
                "持续产出优质内容",
                "关注用户反馈",
                "保持内容新鲜度",
            ]
        }


# 默认实例
default_generator = ContentGenerator()
default_material_manager = MaterialManager()
default_content_plan = ContentPlan()
default_optimizer = ContentOptimizer()

