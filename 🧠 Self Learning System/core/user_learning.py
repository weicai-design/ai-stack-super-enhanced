"""
用户习惯学习器
学习用户的喜好、习惯、想法和执行思路
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from collections import Counter, defaultdict
import logging

logger = logging.getLogger(__name__)


class UserLearning:
    """用户习惯学习器"""
    
    def __init__(self):
        # 用户行为记录
        self.user_actions = []
        
        # 用户偏好
        self.preferences = {
            "favorite_modules": [],
            "frequent_functions": [],
            "preferred_time": {},
            "interaction_style": "unknown"
        }
        
        # 用户模式
        self.patterns = {
            "workflow_patterns": [],
            "problem_solving_patterns": [],
            "learning_patterns": []
        }
        
        logger.info("用户习惯学习器初始化完成")
    
    def record_user_action(
        self,
        action_type: str,
        module: str,
        function: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        记录用户行为
        
        Args:
            action_type: 行为类型（view/use/modify/query等）
            module: 模块名称
            function: 功能名称
            context: 上下文信息
        """
        action = {
            "timestamp": datetime.now().isoformat(),
            "type": action_type,
            "module": module,
            "function": function,
            "context": context or {},
            "hour": datetime.now().hour,
            "weekday": datetime.now().weekday()
        }
        
        self.user_actions.append(action)
        logger.debug(f"记录用户行为: {action_type} {module}::{function}")
    
    def analyze_user_preferences(self) -> Dict[str, Any]:
        """
        分析用户偏好
        
        Returns:
            用户偏好分析
        """
        if not self.user_actions:
            return {
                "has_data": False,
                "message": "暂无用户行为数据"
            }
        
        # 分析最常用模块
        module_counter = Counter(a["module"] for a in self.user_actions)
        favorite_modules = module_counter.most_common(5)
        
        # 分析最常用功能
        function_counter = Counter(
            f"{a['module']}::{a['function']}"
            for a in self.user_actions
            if a["function"]
        )
        frequent_functions = function_counter.most_common(10)
        
        # 分析使用时间偏好
        hour_counter = Counter(a["hour"] for a in self.user_actions)
        preferred_hours = hour_counter.most_common(5)
        
        # 分析行为类型分布
        action_type_counter = Counter(a["type"] for a in self.user_actions)
        
        # 更新偏好
        self.preferences = {
            "favorite_modules": [
                {"module": m, "count": c}
                for m, c in favorite_modules
            ],
            "frequent_functions": [
                {"function": f, "count": c}
                for f, c in frequent_functions
            ],
            "preferred_time": {
                "peak_hours": [h for h, _ in preferred_hours],
                "hour_distribution": dict(hour_counter)
            },
            "interaction_style": self._identify_interaction_style(action_type_counter)
        }
        
        return {
            "has_data": True,
            "total_actions": len(self.user_actions),
            "preferences": self.preferences,
            "insights": self._generate_preference_insights()
        }
    
    def _identify_interaction_style(self, action_type_counter: Counter) -> str:
        """识别交互风格"""
        total = sum(action_type_counter.values())
        if total == 0:
            return "unknown"
        
        # 计算各类行为占比
        use_ratio = action_type_counter.get("use", 0) / total
        query_ratio = action_type_counter.get("query", 0) / total
        modify_ratio = action_type_counter.get("modify", 0) / total
        
        if use_ratio > 0.6:
            return "action_oriented"  # 行动导向
        elif query_ratio > 0.5:
            return "exploration_oriented"  # 探索导向
        elif modify_ratio > 0.3:
            return "customization_oriented"  # 定制导向
        else:
            return "balanced"  # 平衡型
    
    def _generate_preference_insights(self) -> List[str]:
        """生成偏好洞察"""
        insights = []
        
        # 模块偏好洞察
        if self.preferences["favorite_modules"]:
            top_module = self.preferences["favorite_modules"][0]["module"]
            insights.append(f"您最常使用{top_module}模块")
        
        # 时间偏好洞察
        peak_hours = self.preferences["preferred_time"].get("peak_hours", [])
        if peak_hours:
            if any(h < 12 for h in peak_hours[:2]):
                insights.append("您习惯在上午使用系统")
            elif any(12 <= h < 18 for h in peak_hours[:2]):
                insights.append("您习惯在下午使用系统")
            else:
                insights.append("您习惯在晚上使用系统")
        
        # 交互风格洞察
        style = self.preferences["interaction_style"]
        style_descriptions = {
            "action_oriented": "您是行动派，喜欢直接使用功能",
            "exploration_oriented": "您喜欢探索和查询，注重了解系统",
            "customization_oriented": "您喜欢定制和调整，追求个性化",
            "balanced": "您的使用方式比较均衡"
        }
        insights.append(style_descriptions.get(style, ""))
        
        return insights
    
    def identify_workflow_patterns(self) -> List[Dict[str, Any]]:
        """
        识别工作流模式
        
        Returns:
            工作流模式列表
        """
        if len(self.user_actions) < 10:
            return []
        
        patterns = []
        
        # 识别常见的功能使用序列
        sequences = self._extract_action_sequences()
        
        # 统计序列频率
        sequence_counter = Counter(tuple(seq) for seq in sequences)
        
        for seq, count in sequence_counter.most_common(5):
            if count >= 3:  # 至少出现3次才算模式
                patterns.append({
                    "type": "workflow",
                    "sequence": list(seq),
                    "frequency": count,
                    "confidence": count / len(sequences) if sequences else 0,
                    "description": self._describe_workflow(list(seq))
                })
        
        self.patterns["workflow_patterns"] = patterns
        return patterns
    
    def _extract_action_sequences(self, window_size: int = 3) -> List[List[str]]:
        """提取行为序列"""
        sequences = []
        
        for i in range(len(self.user_actions) - window_size + 1):
            seq = [
                f"{a['module']}::{a['function']}"
                for a in self.user_actions[i:i+window_size]
                if a["function"]
            ]
            if len(seq) == window_size:
                sequences.append(seq)
        
        return sequences
    
    def _describe_workflow(self, sequence: List[str]) -> str:
        """描述工作流"""
        steps = [s.split("::")[-1] for s in sequence]
        return f"常用流程: {' → '.join(steps)}"
    
    def generate_personalized_suggestions(self) -> List[Dict[str, Any]]:
        """
        生成个性化建议
        
        Returns:
            个性化建议列表
        """
        suggestions = []
        
        # 基于偏好的建议
        preferences = self.preferences
        
        # 推荐相关功能
        if preferences["favorite_modules"]:
            top_module = preferences["favorite_modules"][0]["module"]
            suggestions.append({
                "type": "recommendation",
                "priority": "medium",
                "title": f"发现{top_module}的更多功能",
                "description": f"您经常使用{top_module}，这里有一些相关功能可能对您有帮助",
                "action": "explore_related_functions"
            })
        
        # 时间优化建议
        peak_hours = preferences["preferred_time"].get("peak_hours", [])
        if peak_hours:
            suggestions.append({
                "type": "optimization",
                "priority": "low",
                "title": "优化使用时间",
                "description": f"建议在{peak_hours[0]}:00时段进行重要操作，这是您的高效时段",
                "action": "schedule_tasks"
            })
        
        # 工作流优化建议
        workflows = self.patterns.get("workflow_patterns", [])
        if workflows:
            top_workflow = workflows[0]
            suggestions.append({
                "type": "workflow",
                "priority": "high",
                "title": "创建快捷工作流",
                "description": f"检测到您经常使用的流程，建议创建快捷方式",
                "workflow": top_workflow["sequence"],
                "action": "create_shortcut"
            })
        
        # 学习资源推荐
        if preferences["interaction_style"] == "exploration_oriented":
            suggestions.append({
                "type": "learning",
                "priority": "medium",
                "title": "推荐学习资源",
                "description": "基于您的探索习惯，推荐系统高级功能教程",
                "action": "show_tutorials"
            })
        
        return suggestions
    
    def interact_with_user(
        self,
        suggestion: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        与用户交互，获取反馈
        
        Args:
            suggestion: 建议内容
            
        Returns:
            用户反馈
        """
        # 模拟用户交互（实际应该是真实的UI交互）
        interaction = {
            "suggestion_type": suggestion.get("type"),
            "presented_at": datetime.now().isoformat(),
            "user_response": "pending",  # accepted/rejected/ignored
            "feedback": None
        }
        
        return interaction
    
    def learn_from_feedback(
        self,
        suggestion_id: str,
        feedback: Dict[str, Any]
    ):
        """
        从用户反馈中学习
        
        Args:
            suggestion_id: 建议ID
            feedback: 用户反馈
        """
        response = feedback.get("response", "ignored")
        
        if response == "accepted":
            # 用户接受建议，增强该类建议的权重
            logger.info(f"用户接受建议 {suggestion_id}，增强相关建议")
        elif response == "rejected":
            # 用户拒绝建议，降低该类建议的权重
            logger.info(f"用户拒绝建议 {suggestion_id}，降低相关建议")
        
        # 记录反馈用于后续优化
        self.user_actions.append({
            "timestamp": datetime.now().isoformat(),
            "type": "feedback",
            "suggestion_id": suggestion_id,
            "response": response,
            "feedback": feedback.get("comment", "")
        })
    
    def get_user_profile(self) -> Dict[str, Any]:
        """
        获取用户画像
        
        Returns:
            用户画像
        """
        preferences_analysis = self.analyze_user_preferences()
        workflows = self.identify_workflow_patterns()
        
        profile = {
            "user_id": "default_user",
            "created_at": datetime.now().isoformat(),
            "activity_level": self._calculate_activity_level(),
            "preferences": preferences_analysis.get("preferences", {}),
            "insights": preferences_analysis.get("insights", []),
            "workflow_patterns": workflows,
            "interaction_style": self.preferences.get("interaction_style", "unknown"),
            "total_actions": len(self.user_actions)
        }
        
        return profile
    
    def _calculate_activity_level(self) -> str:
        """计算活跃度"""
        count = len(self.user_actions)
        
        if count > 100:
            return "very_active"
        elif count > 50:
            return "active"
        elif count > 20:
            return "moderate"
        elif count > 5:
            return "low"
        else:
            return "very_low"
    
    def export_learning_data(self) -> Dict[str, Any]:
        """导出学习数据用于持久化"""
        return {
            "user_actions": self.user_actions[-1000:],  # 最近1000条
            "preferences": self.preferences,
            "patterns": self.patterns,
            "exported_at": datetime.now().isoformat()
        }
    
    def import_learning_data(self, data: Dict[str, Any]):
        """导入学习数据"""
        self.user_actions = data.get("user_actions", [])
        self.preferences = data.get("preferences", {})
        self.patterns = data.get("patterns", {})
        logger.info(f"导入了{len(self.user_actions)}条用户行为数据")

