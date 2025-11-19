"""
版权 / 侵权检测工作流
"""
from __future__ import annotations

import difflib
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class PlatformSourceComparison:
    platform: str
    similarity: float
    sample: str
    source: str


class CopyrightInspector:
    def __init__(self):
        self.platform_samples = {
            "douyin": [
                "原创音乐版权声明：未经许可不得用于商业传播。",
                "平台每日对热点内容进行版权扫描，涉及影视片段将触发人工复核。",
            ],
            "xiaohongshu": [
                "图文内容需注明拍摄版权，转载需附带来源链接。",
                "品牌合作需上传授权函，避免侵权纠纷。"
            ],
            "kuaishou": [
                "主播在直播中使用音乐需确认已购买版权包。",
                "涉及时政报道的二次创作素材需要官方授权。"
            ]
        }

    async def run_workflow(
        self,
        text: str,
        sources: Optional[List[str]] = None,
        platforms: Optional[List[str]] = None,
        threshold: float = 0.75
    ) -> Dict[str, any]:
        normalized = self._normalize_text(text)

        reference_hits = self._compare_with_sources(normalized, sources or [])
        platform_hits = self._compare_with_platforms(normalized, platforms or list(self.platform_samples.keys()))

        matches = reference_hits + platform_hits

        summary = self._build_summary(matches, threshold)

        workflow = {
            "steps": [
                {"stage": "预处理", "status": "completed", "description": "文本清洗 + 去噪"},
                {"stage": "多平台相似度比对", "status": "completed", "description": f"对比平台：{', '.join(platforms or self.platform_samples.keys())}"},
                {"stage": "参考库匹配", "status": "completed", "description": f"参考条目: {len(sources or [])}"},
                {"stage": "人工复核建议", "status": "pending", "description": "待审核" if summary["risk_level"] != "安全" else "可略"}
            ],
            "timestamp": datetime.now().isoformat()
        }

        return {"matches": matches, "summary": summary, "workflow": workflow}

    def _normalize_text(self, text: str) -> str:
        return text.strip().replace("\n", " ")

    def _compare_with_sources(self, text: str, sources: List[str]) -> List[Dict[str, any]]:
        hits = []
        for idx, src in enumerate(sources):
            ratio = difflib.SequenceMatcher(None, text, src).ratio()
            if ratio > 0.35:
                hits.append({
                    "type": "reference",
                    "source_id": f"ref_{idx}",
                    "similarity": round(ratio, 3),
                    "excerpt": src[:160]
                })
        return hits

    def _compare_with_platforms(self, text: str, platforms: List[str]) -> List[Dict[str, any]]:
        """
        多平台相似度比对（增强版）
        支持更智能的相似度计算和跨平台检测
        """
        matches = []
        
        # 扩展平台样本库（真实环境应从数据库或API获取）
        extended_samples = {
            "douyin": [
                "原创音乐版权声明：未经许可不得用于商业传播。",
                "平台每日对热点内容进行版权扫描，涉及影视片段将触发人工复核。",
                "视频内容需标注原创或转载来源，避免侵权风险。",
            ],
            "xiaohongshu": [
                "图文内容需注明拍摄版权，转载需附带来源链接。",
                "品牌合作需上传授权函，避免侵权纠纷。",
                "笔记内容需保证原创性，平台会进行相似度检测。",
            ],
            "kuaishou": [
                "主播在直播中使用音乐需确认已购买版权包。",
                "涉及时政报道的二次创作素材需要官方授权。",
                "短视频内容需避免使用未授权素材。",
            ],
            "weibo": [
                "微博内容需遵守版权法规，转载需注明来源。",
                "长文章需保证原创性，平台会进行查重检测。",
            ],
            "bilibili": [
                "视频投稿需标注素材来源，避免版权纠纷。",
                "二次创作需获得原作品授权。",
            ],
        }
        
        for platform in platforms:
            samples = extended_samples.get(platform.lower(), self.platform_samples.get(platform.lower(), []))
            
            # 使用多种相似度算法
            for sample in samples:
                # 1. 序列相似度
                seq_ratio = difflib.SequenceMatcher(None, text, sample).ratio()
                
                # 2. 关键词重叠度
                text_words = set(text.split())
                sample_words = set(sample.split())
                if text_words and sample_words:
                    word_overlap = len(text_words & sample_words) / len(text_words | sample_words)
                else:
                    word_overlap = 0.0
                
                # 3. 综合相似度（加权平均）
                similarity = (seq_ratio * 0.7 + word_overlap * 0.3)
                
                if similarity > 0.3:  # 降低阈值以捕获更多潜在匹配
                    matches.append({
                        "type": "platform",
                        "platform": platform,
                        "similarity": round(similarity, 3),
                        "seq_similarity": round(seq_ratio, 3),
                        "word_overlap": round(word_overlap, 3),
                        "sample": sample[:160],
                        "matched_segments": self._extract_matched_segments(text, sample)
                    })
        
        # 按相似度排序
        matches.sort(key=lambda x: x["similarity"], reverse=True)
        return matches
    
    def _extract_matched_segments(self, text: str, sample: str) -> List[str]:
        """提取匹配的文本片段"""
        segments = []
        matcher = difflib.SequenceMatcher(None, text, sample)
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal" and (i2 - i1) > 10:  # 匹配片段长度>10
                segments.append(text[i1:i2])
        return segments[:3]  # 最多返回3个片段

    def _build_summary(self, matches: List[Dict[str, any]], threshold: float) -> Dict[str, any]:
        high_risk = [m for m in matches if m["similarity"] >= threshold]
        medium = [m for m in matches if threshold * 0.8 <= m["similarity"] < threshold]
        if high_risk:
            level = "高风险"
            note = "检测到高相似度内容，建议人工复核并上传授权凭证。"
        elif medium:
            level = "中风险"
            note = "存在可疑相似内容，建议保留溯源证据。"
        else:
            level = "安全"
            note = "未发现显著侵权风险，可正常发布。"
        return {
            "risk_level": level,
            "total_matches": len(matches),
            "high_count": len(high_risk),
            "medium_count": len(medium),
            "threshold": threshold,
            "note": note
        }

