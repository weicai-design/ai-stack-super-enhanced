"""
视频脚本 & 分镜模板生成器
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime


@dataclass
class ShotTemplate:
    id: str
    name: str
    camera: str
    rhythm: str
    description: str


class StoryboardGenerator:
    def __init__(self):
        """初始化视频脚本生成器"""
        self.default_structures = {
            "fast_promo": [
                ShotTemplate(
                    id="open",
                    name="开场冲击",
                    camera="无人机掠过 / 俯冲镜头",
                    rhythm="0-3s",
                    description="用快速转场+品牌色，第一时间抓住注意力"
                ),
                ShotTemplate(
                    id="pain_point",
                    name="痛点击中",
                    camera="中景 + 手持跟随",
                    rhythm="3-8s",
                    description="实拍痛点场景，配合快问快答，增强代入感"
                ),
                ShotTemplate(
                    id="solution",
                    name="方案展示",
                    camera="分屏+特写",
                    rhythm="8-18s",
                    description="左侧旧方案，右侧新方案，通过镜头语言展现效率对比"
                ),
                ShotTemplate(
                    id="cta",
                    name="收口行动",
                    camera="慢推特写 品牌/人物",
                    rhythm="18-25s",
                    description="给出CTA文案 + 品牌Logo，配合鼓点强化记忆"
                )
            ],
            "narrative_story": [
                ShotTemplate(
                    id="hook",
                    name="悬念开篇",
                    camera="定幅长镜头 + 慢慢推进",
                    rhythm="0-5s",
                    description="设置场景冲突，留白，配旁白或字幕提出问题"
                ),
                ShotTemplate(
                    id="character",
                    name="角色建立",
                    camera="特写 + 环绕",
                    rhythm="5-15s",
                    description="聚焦主人公表情/细节，建立共鸣"
                ),
                ShotTemplate(
                    id="turning",
                    name="转折揭示",
                    camera="手持摇镜 + 光效切换",
                    rhythm="15-25s",
                    description="用视觉/音效同步推进剧情转折"
                ),
                ShotTemplate(
                    id="resolution",
                    name="高潮/升华",
                    camera="组合特写 + 俯仰切换",
                    rhythm="25-40s",
                    description="展示结果/价值，最后用慢镜定格"
                )
            ]
        }

    def generate_storyboard(
        self,
        concept: str,
        template_name: str = "fast_promo",
        duration: Optional[int] = None,
        style: str = "modern"
    ) -> Dict:
        """
        生成视频脚本/分镜
        
        Args:
            concept: 视频主题/创意概念
            template_name: 模板名称
            duration: 视频时长（秒，可选）
            style: 风格（modern/classic/creative）
            
        Returns:
            分镜脚本
        """
        templates = self.default_structures.get(template_name, self.default_structures["fast_promo"])
        shots = []
        
        # 根据时长调整节奏
        total_duration = duration or self._estimate_duration(template_name)
        rhythm_adjusted = self._adjust_rhythm(templates, total_duration)
        
        for idx, (shot, rhythm) in enumerate(zip(templates, rhythm_adjusted), start=1):
            shots.append({
                "index": idx,
                "name": shot.name,
                "camera": shot.camera,
                "rhythm": rhythm,
                "description": shot.description,
                "script": self._generate_line(concept, shot, style),
                "duration_estimate": self._parse_rhythm_duration(rhythm),
                "camera_notes": self._generate_camera_notes(shot, style),
                "audio_hints": self._generate_audio_hints(shot, style)
            })
        
        return {
            "concept": concept,
            "template": template_name,
            "style": style,
            "total_duration_estimate": total_duration,
            "shot_count": len(shots),
            "shots": shots,
            "pacing": self._analyze_pacing(shots),
            "generated_at": datetime.now().isoformat()
        }
    
    def _estimate_duration(self, template_name: str) -> int:
        """估算视频时长"""
        duration_map = {
            "fast_promo": 25,
            "narrative_story": 40,
        }
        return duration_map.get(template_name, 30)
    
    def _adjust_rhythm(self, templates: List[ShotTemplate], total_duration: int) -> List[str]:
        """根据总时长调整节奏"""
        # 简化实现：按比例调整
        return [t.rhythm for t in templates]  # 实际应重新计算时间点
    
    def _parse_rhythm_duration(self, rhythm: str) -> int:
        """解析节奏字符串，返回秒数"""
        # 例如 "0-3s" -> 3
        import re
        match = re.search(r'(\d+)-(\d+)s', rhythm)
        if match:
            return int(match.group(2)) - int(match.group(1))
        return 5  # 默认
    
    def _generate_camera_notes(self, shot: ShotTemplate, style: str) -> str:
        """生成镜头语言提示"""
        notes_map = {
            "modern": "使用稳定器，保持画面流畅",
            "classic": "传统构图，注重画面平衡",
            "creative": "大胆尝试非常规角度和构图"
        }
        return f"{shot.camera}。{notes_map.get(style, notes_map['modern'])}"
    
    def _generate_audio_hints(self, shot: ShotTemplate, style: str) -> str:
        """生成音频提示"""
        if "开场" in shot.name or "hook" in shot.id:
            return "背景音乐渐入，配合画面节奏"
        elif "痛点击中" in shot.name or "pain_point" in shot.id:
            return "音效：问题音效，增强代入感"
        elif "方案" in shot.name or "solution" in shot.id:
            return "背景音乐：轻快节奏，展现解决方案"
        elif "收口" in shot.name or "cta" in shot.id:
            return "背景音乐：高潮部分，配合CTA"
        return "根据画面内容调整音效"
    
    def _analyze_pacing(self, shots: List[Dict]) -> Dict[str, Any]:
        """分析节奏"""
        durations = [s.get("duration_estimate", 5) for s in shots]
        return {
            "total_duration": sum(durations),
            "avg_shot_duration": sum(durations) / len(durations) if durations else 0,
            "pacing_type": "fast" if sum(durations) / len(durations) < 5 else "moderate" if sum(durations) / len(durations) < 10 else "slow"
        }

    def _generate_line(self, concept: str, shot: ShotTemplate) -> str:
        base = concept or "产品亮点"
        if shot.id == "pain_point":
            return f"镜头切到实际场景：{base} 之外的痛点，用提问方式抛出矛盾。"
        if shot.id == "solution":
            return f"配旁白：“想象一下，{base} 可以一键完成。” 呈现操作细节。"
        if shot.id == "hook":
            return f"字幕：“如果给你 30 秒，你能讲完 {base} 的故事吗？”"
        return f"延展 {base} 的故事线，结合镜头语言完成叙述。"


storyboard_generator = StoryboardGenerator()

