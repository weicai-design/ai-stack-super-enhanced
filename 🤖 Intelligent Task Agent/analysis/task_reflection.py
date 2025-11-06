"""
任务效果反思系统
- 任务完成度分析
- 问题总结
- 经验提取
- 改进建议
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from collections import defaultdict


class TaskReflection:
    """任务反思系统"""
    
    def __init__(self):
        # 反思记录
        self.reflections = []
        
        # 经验库
        self.lessons_learned = []
    
    # ============ 任务反思 ============
    
    def reflect_on_task(
        self,
        task_id: str,
        task_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        对已完成任务进行反思
        
        Args:
            task_id: 任务ID
            task_data: {
                "task_name": "任务名称",
                "planned_duration": 计划工期（天）,
                "actual_duration": 实际工期（天）,
                "planned_cost": 计划成本,
                "actual_cost": 实际成本,
                "quality_score": 质量评分（1-5）,
                "issues_encountered": ["遇到的问题"],
                "success_factors": ["成功因素"],
                "failure_factors": ["失败因素"]
            }
        
        Returns:
            反思结果
        """
        try:
            # 1. 计算偏差
            schedule_variance = task_data['actual_duration'] - task_data['planned_duration']
            schedule_variance_rate = (schedule_variance / task_data['planned_duration'] * 100) \
                                    if task_data['planned_duration'] > 0 else 0
            
            cost_variance = task_data['actual_cost'] - task_data['planned_cost']
            cost_variance_rate = (cost_variance / task_data['planned_cost'] * 100) \
                                if task_data['planned_cost'] > 0 else 0
            
            # 2. 评估任务等级
            task_rating = self._rate_task_performance(
                schedule_variance_rate,
                cost_variance_rate,
                task_data['quality_score']
            )
            
            # 3. 提取经验教训
            lessons = self._extract_lessons(task_data, task_rating)
            
            # 4. 生成改进建议
            improvements = self._generate_improvements(
                task_data,
                schedule_variance_rate,
                cost_variance_rate
            )
            
            # 5. 构建反思记录
            reflection = {
                "reflection_id": f"REF{len(self.reflections) + 1:04d}",
                "task_id": task_id,
                "task_name": task_data['task_name'],
                "variances": {
                    "schedule_days": schedule_variance,
                    "schedule_rate": float(schedule_variance_rate),
                    "cost_amount": float(cost_variance),
                    "cost_rate": float(cost_variance_rate)
                },
                "quality_score": task_data['quality_score'],
                "task_rating": task_rating,
                "lessons_learned": lessons,
                "improvement_suggestions": improvements,
                "issues_summary": task_data.get('issues_encountered', []),
                "success_factors": task_data.get('success_factors', []),
                "reflected_at": datetime.utcnow().isoformat()
            }
            
            self.reflections.append(reflection)
            
            # 保存到经验库
            for lesson in lessons:
                self.lessons_learned.append({
                    "lesson": lesson,
                    "task_id": task_id,
                    "task_name": task_data['task_name'],
                    "created_at": datetime.utcnow().isoformat()
                })
            
            return {
                "success": True,
                "reflection": reflection,
                "message": "任务反思已完成"
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    # ============ 经验提取 ============
    
    def _extract_lessons(
        self,
        task_data: Dict[str, Any],
        task_rating: str
    ) -> List[str]:
        """提取经验教训"""
        lessons = []
        
        # 根据任务评级提取经验
        if task_rating == "优秀":
            lessons.extend([
                f"成功因素：{', '.join(task_data.get('success_factors', ['无']))}",
                "可复制的成功经验，建议推广到其他任务"
            ])
        
        elif task_rating in ["良好", "一般"]:
            lessons.extend([
                "任务基本完成，但仍有改进空间",
                f"遇到的问题：{', '.join(task_data.get('issues_encountered', ['无']))}"
            ])
        
        else:  # 待改进
            lessons.extend([
                f"需要重点关注的问题：{', '.join(task_data.get('issues_encountered', ['无']))}",
                "建议重新评估任务计划和资源分配"
            ])
        
        return lessons
    
    def _generate_improvements(
        self,
        task_data: Dict[str, Any],
        schedule_variance_rate: float,
        cost_variance_rate: float
    ) -> List[str]:
        """生成改进建议"""
        improvements = []
        
        # 工期建议
        if schedule_variance_rate > 20:
            improvements.append("工期超期严重，建议：\n  - 优化任务分解\n  - 增加资源投入\n  - 识别并移除障碍")
        elif schedule_variance_rate > 10:
            improvements.append("工期略有延迟，建议加强进度监控")
        
        # 成本建议
        if cost_variance_rate > 20:
            improvements.append("成本超支严重，建议：\n  - 加强成本控制\n  - 审查预算编制\n  - 优化资源使用")
        elif cost_variance_rate > 10:
            improvements.append("成本略有超支，建议优化成本管理")
        
        # 质量建议
        if task_data['quality_score'] < 3:
            improvements.append("质量有待提升，建议：\n  - 加强质量检查\n  - 提升团队能力\n  - 优化工作流程")
        
        if not improvements:
            improvements.append("整体表现良好，继续保持！")
        
        return improvements
    
    def _rate_task_performance(
        self,
        schedule_variance_rate: float,
        cost_variance_rate: float,
        quality_score: float
    ) -> str:
        """评级任务表现"""
        # 综合评分
        schedule_score = max(0, 100 - abs(schedule_variance_rate))
        cost_score = max(0, 100 - abs(cost_variance_rate))
        quality_score_normalized = quality_score / 5 * 100
        
        overall_score = (schedule_score + cost_score + quality_score_normalized) / 3
        
        if overall_score >= 90:
            return "优秀"
        elif overall_score >= 75:
            return "良好"
        elif overall_score >= 60:
            return "一般"
        else:
            return "待改进"
    
    # ============ 统计分析 ============
    
    def get_reflection_statistics(self) -> Dict[str, Any]:
        """获取反思统计"""
        try:
            total = len(self.reflections)
            
            if total == 0:
                return {
                    "success": True,
                    "statistics": {
                        "total_reflections": 0,
                        "message": "暂无反思记录"
                    }
                }
            
            # 评级分布
            rating_distribution = defaultdict(int)
            for ref in self.reflections:
                rating_distribution[ref['task_rating']] += 1
            
            # 平均偏差
            avg_schedule_variance = sum(
                ref['variances']['schedule_rate'] for ref in self.reflections
            ) / total
            
            avg_cost_variance = sum(
                ref['variances']['cost_rate'] for ref in self.reflections
            ) / total
            
            # 平均质量分数
            avg_quality = sum(
                ref['quality_score'] for ref in self.reflections
            ) / total
            
            return {
                "success": True,
                "statistics": {
                    "total_reflections": total,
                    "rating_distribution": dict(rating_distribution),
                    "average_schedule_variance": float(avg_schedule_variance),
                    "average_cost_variance": float(avg_cost_variance),
                    "average_quality_score": float(avg_quality),
                    "total_lessons_learned": len(self.lessons_learned)
                }
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def search_lessons(self, keyword: str) -> Dict[str, Any]:
        """搜索经验教训"""
        try:
            matched = [
                lesson for lesson in self.lessons_learned
                if keyword.lower() in lesson['lesson'].lower() or
                   keyword.lower() in lesson['task_name'].lower()
            ]
            
            return {
                "success": True,
                "keyword": keyword,
                "matched_lessons": matched,
                "total": len(matched)
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


# 全局实例
task_reflection = TaskReflection()

