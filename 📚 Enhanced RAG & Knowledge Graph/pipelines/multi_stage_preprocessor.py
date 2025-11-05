"""
Multi-Stage Preprocessor
多阶段数据预处理器

功能概述：
1. 四阶段数据预处理流程
2. 智能内容清洗和标准化
3. 语义分析和增强
4. 质量验证和评分
5. 语义去重处理（增强）

版本: 1.1.0
依赖: Text Processors, Core Engine, Semantic Deduplication
"""

from __future__ import annotations

import hashlib
import logging
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class PreprocessResult(dict):
    pass


class PreprocessorStage:
    def process(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        return doc


class NormalizeStage(PreprocessorStage):
    """
    规范化阶段（增强版）
    
    功能：
    1. 文本标准化（换行符、空白字符）
    2. HTML标签清理
    3. 特殊字符处理
    4. 编码错误修复
    """
    
    def __init__(self, remove_html: bool = True, fix_encoding: bool = True):
        """
        初始化规范化阶段
        
        Args:
            remove_html: 是否移除HTML标签
            fix_encoding: 是否修复编码错误
        """
        self.remove_html = remove_html
        self.fix_encoding = fix_encoding
        # HTML标签模式
        self.html_pattern = re.compile(r'<[^>]+>', re.IGNORECASE)
        # 控制字符模式（保留换行符和制表符）
        self.control_char_pattern = re.compile(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F-\x9F]')
        # 常见乱码修复模式（简单的字符替换）
        self.encoding_fixes = {
            'â€™': "'",
            'â€œ': '"',
            'â€': '"',
            'â€"': '-',
            'â€"': '—',
        }
    
    def process(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        text = doc.get("text") or ""
        
        # 1. 修复编码错误
        if self.fix_encoding:
            for wrong, correct in self.encoding_fixes.items():
                text = text.replace(wrong, correct)
        
        # 2. 标准化换行符
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        
        # 3. 移除HTML标签（如果启用）
        if self.remove_html:
            text = self.html_pattern.sub(' ', text)
            # 解码HTML实体
            try:
                import html
                text = html.unescape(text)
            except Exception:
                pass
        
        # 4. 移除控制字符（保留换行符和制表符）
        text = self.control_char_pattern.sub('', text)
        
        # 5. 规范化空白字符
        text = re.sub(r"[^\S\n]+", " ", text)  # 多个空格合并为一个
        text = re.sub(r"[ \t]+\n", "\n", text)  # 移除行尾空白
        text = re.sub(r"\n{3,}", "\n\n", text)  # 多个换行合并为两个
        
        # 6. 首尾空白处理
        text = text.strip()
        
        doc["text"] = text
        doc["normalization"] = {
            "html_removed": self.remove_html,
            "encoding_fixed": self.fix_encoding,
            "original_length": len(doc.get("text", "") or ""),
            "normalized_length": len(text),
        }
        return doc


class SafetyFilterStage(PreprocessorStage):
    EMAIL = re.compile(r"([A-Za-z0-9._%+-]+)@([A-Za-z0-9.-]+\.[A-Za-z]{2,})")
    URL = re.compile(r"(https?://[^\s]+)")

    def __init__(
        self, redact_email: bool = True, redact_url: bool = False, max_len: int = 20000
    ):
        self.redact_email = redact_email
        self.redact_url = redact_url
        self.max_len = max_len

    def process(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        t = doc.get("text") or ""
        if self.redact_email:
            t = self.EMAIL.sub("[email_redacted]", t)
        if self.redact_url:
            t = self.URL.sub("[url_redacted]", t)
        if len(t) > self.max_len:
            t = t[: self.max_len]
            doc["truncated"] = True
        doc["text"] = t
        return doc


class QualityAssessStage(PreprocessorStage):
    """
    质量评估阶段（增强版）
    
    功能：
    1. 字符数统计
    2. 行数统计
    3. 唯一字符比例
    4. 语言检测
    5. 内容完整性检查
    6. 编码格式验证
    7. 恶意内容检测
    """
    
    def __init__(
        self,
        enable_language_detection: bool = True,
        enable_integrity_check: bool = True,
        enable_security_check: bool = True,
    ):
        """
        初始化质量评估阶段
        
        Args:
            enable_language_detection: 是否启用语言检测
            enable_integrity_check: 是否启用完整性检查
            enable_security_check: 是否启用安全检测
        """
        self.enable_language_detection = enable_language_detection
        self.enable_integrity_check = enable_integrity_check
        self.enable_security_check = enable_security_check
        
        # 尝试加载语言检测库
        self.lang_detector = None
        if enable_language_detection:
            try:
                from langdetect import detect, LangDetectException
                self.lang_detect_func = detect
                self.lang_detect_exception = LangDetectException
            except ImportError:
                try:
                    # 备用：使用polyglot（如果可用）
                    from polyglot.detect import Detector
                    self.lang_detect_func = lambda text: Detector(text).language.code
                    self.lang_detect_exception = Exception
                except ImportError:
                    self.lang_detector = None
                    logger.warning("语言检测库未安装，将跳过语言检测")
        
        # 恶意内容模式（基础检测）
        self.malicious_patterns = [
            r'eval\s*\(',
            r'exec\s*\(',
            r'script[^>]*>',
            r'javascript:',
            r'onerror\s*=',
            r'onclick\s*=',
            r'<iframe[^>]*>',
        ]
    
    def process(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        text = doc.get("text") or ""
        chars = len(text)
        lines = text.count("\n") + 1 if text else 0
        unique_ratio = len(set(text)) / (chars or 1)
        
        quality = {
            "chars": chars,
            "lines": lines,
            "unique_ratio": round(unique_ratio, 3),
            "basic_ok": (chars >= 10 and unique_ratio >= 0.1),
        }
        
        # 语言检测
        if self.enable_language_detection and self.lang_detect_func and chars >= 50:
            try:
                detected_lang = self.lang_detect_func(text)
                quality["detected_language"] = detected_lang
            except (self.lang_detect_exception if hasattr(self, 'lang_detect_exception') else Exception) as e:
                logger.debug(f"语言检测失败: {e}")
                quality["detected_language"] = "unknown"
        
        # 内容完整性检查
        if self.enable_integrity_check:
            integrity_issues = []
            
            # 检查文档结构完整性
            if chars > 100:
                # 检查是否有开头和结尾（简单的启发式）
                if not text.strip():
                    integrity_issues.append("empty_content")
                elif len(text.strip()) < 10:
                    integrity_issues.append("too_short")
                
                # 检查是否有基本的句子结构
                sentence_endings = text.count('.') + text.count('。') + text.count('!') + text.count('！') + text.count('?') + text.count('？')
                if sentence_endings == 0 and chars > 50:
                    integrity_issues.append("no_sentence_structure")
            
            quality["integrity_issues"] = integrity_issues
            quality["integrity_ok"] = len(integrity_issues) == 0
        
        # 编码格式验证
        try:
            # 尝试UTF-8编码验证
            text.encode('utf-8')
            quality["encoding"] = "utf-8"
            quality["encoding_valid"] = True
        except UnicodeEncodeError:
            quality["encoding"] = "unknown"
            quality["encoding_valid"] = False
        
        # 恶意内容检测
        if self.enable_security_check:
            security_issues = []
            for pattern in self.malicious_patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    security_issues.append(f"pattern_match: {pattern[:30]}")
            
            quality["security_issues"] = security_issues
            quality["security_ok"] = len(security_issues) == 0
        
        # 综合质量评分
        score = 0.0
        if quality["basic_ok"]:
            score += 0.4
        if quality.get("integrity_ok", True):
            score += 0.3
        if quality.get("security_ok", True):
            score += 0.2
        if quality.get("encoding_valid", True):
            score += 0.1
        
        quality["overall_score"] = round(score, 2)
        quality["quality_ok"] = score >= 0.7
        
        doc["quality"] = quality
        return doc


class MetadataUnifyStage(PreprocessorStage):
    def process(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        t = (doc.get("text") or "").encode("utf-8", errors="ignore")
        checksum = hashlib.md5(t).hexdigest()
        meta = doc.get("meta") or {}
        meta["checksum"] = checksum
        doc["meta"] = meta
        doc["checksum"] = checksum
        return doc


class SemanticDeduplicationStage(PreprocessorStage):
    """
    语义去重阶段（增强）
    
    功能：
    1. 语义相似度检测
    2. 跨文档去重
    3. 重复片段识别
    """

    def __init__(
        self,
        similarity_threshold: float = 0.95,
        min_chunk_size: int = 50,
        enable_semantic_dedup: bool = True,
    ):
        """
        初始化语义去重阶段
        
        Args:
            similarity_threshold: 相似度阈值（0-1）
            min_chunk_size: 最小文本块大小
            enable_semantic_dedup: 是否启用语义去重
        """
        self.similarity_threshold = similarity_threshold
        self.min_chunk_size = min_chunk_size
        self.enable_semantic_dedup = enable_semantic_dedup
        self._deduplicator = None

    def _get_deduplicator(self):
        """获取去重器实例（延迟加载）"""
        if self._deduplicator is None and self.enable_semantic_dedup:
            try:
                from .semantic_deduplication import get_deduplicator
                self._deduplicator = get_deduplicator(
                    similarity_threshold=self.similarity_threshold,
                    min_chunk_size=self.min_chunk_size,
                )
            except Exception as e:
                logger.warning(f"语义去重器加载失败，将使用简单去重: {e}")
                self.enable_semantic_dedup = False
        return self._deduplicator

    def process(
        self,
        doc: Dict[str, Any],
        existing_texts: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        处理文档，进行语义去重
        
        Args:
            doc: 文档字典
            existing_texts: 已有文本列表（用于跨文档去重）
            
        Returns:
            处理后的文档字典，如果为重复则标记为已过滤
        """
        text = doc.get("text") or ""
        
        # 如果文本太短，跳过去重
        if len(text.strip()) < self.min_chunk_size:
            doc["deduplication"] = {
                "skipped": True,
                "reason": "text_too_short",
            }
            return doc

        # 如果禁用语义去重，只进行简单检查
        if not self.enable_semantic_dedup:
            doc["deduplication"] = {
                "enabled": False,
            }
            return doc

        deduplicator = self._get_deduplicator()
        if deduplicator:
            # 检查是否为重复
            is_dup, matched_text, similarity = deduplicator.is_duplicate(
                text,
                existing_texts=existing_texts,
            )

            if is_dup:
                doc["deduplication"] = {
                    "is_duplicate": True,
                    "similarity": similarity,
                    "matched_text": matched_text[:100] if matched_text else None,  # 只保存前100字符
                    "filtered": True,
                }
                doc["filtered"] = True  # 标记为已过滤
            else:
                doc["deduplication"] = {
                    "is_duplicate": False,
                    "similarity": similarity if similarity else None,
                }
                # 注册到去重索引
                doc_id = doc.get("id") or doc.get("doc_id")
                if doc_id:
                    deduplicator.register_document(doc_id, text)
        else:
            # 回退到简单检查
            doc["deduplication"] = {
                "enabled": False,
                "fallback": True,
            }

        return doc


class MultiStagePreprocessor:
    """
    多阶段预处理器
    
    标准四阶段流程：
    1. NormalizeStage - 规范化
    2. SafetyFilterStage - 安全过滤
    3. QualityAssessStage - 质量评估
    4. MetadataUnifyStage - 元数据统一
    
    可选增强阶段：
    5. SemanticDeduplicationStage - 语义去重（可选）
    """

    def __init__(
        self,
        stages: List[PreprocessorStage] | None = None,
        enable_semantic_dedup: bool = False,
        semantic_dedup_threshold: float = 0.95,
    ):
        """
        初始化多阶段预处理器
        
        Args:
            stages: 自定义阶段列表（如果为None，使用默认四阶段）
            enable_semantic_dedup: 是否启用语义去重
            semantic_dedup_threshold: 语义去重相似度阈值
        """
        if stages is None:
            stages = [
                NormalizeStage(),
                SafetyFilterStage(),
                QualityAssessStage(),
                MetadataUnifyStage(),
            ]
            
            # 如果启用语义去重，添加去重阶段
            if enable_semantic_dedup:
                stages.append(
                    SemanticDeduplicationStage(
                        similarity_threshold=semantic_dedup_threshold,
                    )
                )
        
        self.stages = stages

    def run(
        self,
        doc: Dict[str, Any],
        existing_texts: Optional[List[str]] = None,
    ) -> PreprocessResult:
        """
        运行预处理流程
        
        Args:
            doc: 文档字典
            existing_texts: 已有文本列表（用于跨文档去重）
            
        Returns:
            预处理结果
        """
        for s in self.stages:
            if isinstance(s, SemanticDeduplicationStage):
                doc = s.process(doc, existing_texts=existing_texts)
            else:
                doc = s.process(doc)
        return PreprocessResult(doc)
