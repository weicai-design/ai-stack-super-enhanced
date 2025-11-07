"""
预处理器 - 四项预处理功能

1. 数据清洗
2. 标准化处理
3. 去重验证
4. 真实性验证
"""

import re
import hashlib
from typing import List, Dict, Any, Optional, Set
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Preprocessor:
    """
    预处理器
    
    实现四项预处理：
    1. 数据清洗 (Cleaning)
    2. 标准化处理 (Normalization)
    3. 去重验证 (Deduplication)
    4. 真实性验证 (Validation)
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """初始化预处理器"""
        self.config = config or self._get_default_config()
        self.seen_hashes: Set[str] = set()  # 用于去重
        
        logger.info("🔧 预处理器初始化完成")
        logger.info(f"   启用功能: 清洗={self.config['enable_cleaning']}, "
                   f"标准化={self.config['enable_normalization']}, "
                   f"去重={self.config['enable_deduplication']}, "
                   f"验证={self.config['enable_validation']}")
    
    def _get_default_config(self) -> Dict:
        """获取默认配置"""
        return {
            # 清洗配置
            "enable_cleaning": True,
            "remove_html": True,
            "remove_urls": True,
            "remove_emails": True,
            "remove_special_chars": False,
            "normalize_whitespace": True,
            
            # 标准化配置
            "enable_normalization": True,
            "lowercase": False,  # 保留大小写
            "remove_stopwords": False,  # 保留停用词
            
            # 去重配置
            "enable_deduplication": True,
            "similarity_threshold": 0.95,
            "dedup_method": "hash",  # hash, embedding
            
            # 验证配置
            "enable_validation": True,
            "min_length": 10,
            "max_length": 50000,
            "check_language": True,
            "allowed_languages": ["zh", "en"]
        }
    
    def preprocess(self, text: str, metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        完整的预处理流程
        
        Args:
            text: 输入文本
            metadata: 元数据
            
        Returns:
            预处理结果
        """
        logger.info(f"\n🔧 开始预处理: {len(text)}字符")
        
        result = {
            "original_text": text,
            "original_length": len(text),
            "processed_text": text,
            "metadata": metadata or {},
            "preprocessing_steps": [],
            "warnings": [],
            "passed_validation": True,
            "is_duplicate": False
        }
        
        # 1. 数据清洗
        if self.config["enable_cleaning"]:
            cleaned_text, cleaning_info = self.clean(text)
            result["processed_text"] = cleaned_text
            result["preprocessing_steps"].append({
                "step": "cleaning",
                "info": cleaning_info
            })
            logger.info(f"   ✅ 清洗完成: {len(cleaned_text)}字符")
        
        # 2. 标准化
        if self.config["enable_normalization"]:
            normalized_text, norm_info = self.normalize(result["processed_text"])
            result["processed_text"] = normalized_text
            result["preprocessing_steps"].append({
                "step": "normalization",
                "info": norm_info
            })
            logger.info(f"   ✅ 标准化完成: {len(normalized_text)}字符")
        
        # 3. 去重验证
        if self.config["enable_deduplication"]:
            is_duplicate, dedup_info = self.check_duplicate(result["processed_text"])
            result["is_duplicate"] = is_duplicate
            result["preprocessing_steps"].append({
                "step": "deduplication",
                "info": dedup_info
            })
            if is_duplicate:
                logger.warning(f"   ⚠️  检测到重复内容")
                result["warnings"].append("内容重复")
        
        # 4. 真实性验证
        if self.config["enable_validation"]:
            is_valid, validation_info = self.validate(result["processed_text"])
            result["passed_validation"] = is_valid
            result["preprocessing_steps"].append({
                "step": "validation",
                "info": validation_info
            })
            if not is_valid:
                logger.warning(f"   ⚠️  验证未通过: {validation_info.get('reason')}")
                result["warnings"].append(f"验证失败: {validation_info.get('reason')}")
            else:
                logger.info(f"   ✅ 验证通过")
        
        result["final_length"] = len(result["processed_text"])
        result["processed_at"] = datetime.now().isoformat()
        
        logger.info(f"✅ 预处理完成: {result['original_length']} → {result['final_length']}字符")
        
        return result
    
    def clean(self, text: str) -> tuple[str, Dict]:
        """
        数据清洗
        
        Returns:
            (清洗后的文本, 清洗信息)
        """
        original_length = len(text)
        cleaned_text = text
        operations = []
        
        # 删除HTML标签
        if self.config.get("remove_html"):
            before = len(cleaned_text)
            cleaned_text = re.sub(r'<[^>]+>', '', cleaned_text)
            if len(cleaned_text) < before:
                operations.append("removed_html")
        
        # 删除URL
        if self.config.get("remove_urls"):
            before = len(cleaned_text)
            cleaned_text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', cleaned_text)
            if len(cleaned_text) < before:
                operations.append("removed_urls")
        
        # 删除邮箱
        if self.config.get("remove_emails"):
            before = len(cleaned_text)
            cleaned_text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '', cleaned_text)
            if len(cleaned_text) < before:
                operations.append("removed_emails")
        
        # 删除特殊字符（保留基本标点）
        if self.config.get("remove_special_chars"):
            before = len(cleaned_text)
            cleaned_text = re.sub(r'[^\w\s\u4e00-\u9fff.,!?;:，。！？；：、]', '', cleaned_text)
            if len(cleaned_text) < before:
                operations.append("removed_special_chars")
        
        # 标准化空白
        if self.config.get("normalize_whitespace"):
            # 多个空格 → 单个空格
            cleaned_text = re.sub(r' +', ' ', cleaned_text)
            # 多个换行 → 最多2个换行
            cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text)
            # 删除行首行尾空白
            lines = [line.strip() for line in cleaned_text.split('\n')]
            cleaned_text = '\n'.join(lines)
            operations.append("normalized_whitespace")
        
        cleaned_text = cleaned_text.strip()
        
        info = {
            "original_length": original_length,
            "cleaned_length": len(cleaned_text),
            "reduction": original_length - len(cleaned_text),
            "operations": operations
        }
        
        return cleaned_text, info
    
    def normalize(self, text: str) -> tuple[str, Dict]:
        """
        标准化处理
        
        Returns:
            (标准化后的文本, 标准化信息)
        """
        normalized_text = text
        operations = []
        
        # 小写化（可选）
        if self.config.get("lowercase"):
            normalized_text = normalized_text.lower()
            operations.append("lowercased")
        
        # 删除停用词（可选）
        if self.config.get("remove_stopwords"):
            # TODO: 实现停用词删除
            # 需要停用词表
            operations.append("removed_stopwords")
        
        # 统一标点符号（中英文）
        # 中文标点 → 英文标点
        punctuation_map = {
            '，': ',',
            '。': '.',
            '！': '!',
            '？': '?',
            '；': ';',
            '：': ':',
            '（': '(',
            '）': ')',
            '【': '[',
            '】': ']',
            '《': '<',
            '》': '>',
            '"': '"',
            '"': '"',
            ''': "'",
            ''': "'"
        }
        
        for cn, en in punctuation_map.items():
            if cn in normalized_text:
                normalized_text = normalized_text.replace(cn, en)
        
        if any(cn in text for cn in punctuation_map.keys()):
            operations.append("normalized_punctuation")
        
        info = {
            "operations": operations
        }
        
        return normalized_text, info
    
    def check_duplicate(self, text: str) -> tuple[bool, Dict]:
        """
        去重验证
        
        Returns:
            (是否重复, 去重信息)
        """
        method = self.config.get("dedup_method", "hash")
        
        if method == "hash":
            # 基于哈希的去重
            text_hash = self._compute_hash(text)
            
            is_duplicate = text_hash in self.seen_hashes
            
            if not is_duplicate:
                self.seen_hashes.add(text_hash)
            
            info = {
                "method": "hash",
                "hash": text_hash[:16],  # 只显示前16位
                "is_duplicate": is_duplicate,
                "total_seen": len(self.seen_hashes)
            }
            
        elif method == "embedding":
            # 基于嵌入的去重（TODO: 需要向量化）
            info = {
                "method": "embedding",
                "is_duplicate": False,
                "note": "嵌入去重待实现"
            }
            is_duplicate = False
        
        else:
            info = {
                "method": "none",
                "is_duplicate": False
            }
            is_duplicate = False
        
        return is_duplicate, info
    
    def validate(self, text: str) -> tuple[bool, Dict]:
        """
        真实性验证
        
        包括：
        1. 长度验证
        2. 语言验证
        3. 内容质量验证
        
        Returns:
            (是否通过验证, 验证信息)
        """
        checks = []
        warnings = []
        
        # 1. 长度验证
        min_len = self.config.get("min_length", 10)
        max_len = self.config.get("max_length", 50000)
        
        if len(text) < min_len:
            checks.append({"check": "min_length", "passed": False})
            warnings.append(f"文本过短({len(text)} < {min_len})")
        elif len(text) > max_len:
            checks.append({"check": "max_length", "passed": False})
            warnings.append(f"文本过长({len(text)} > {max_len})")
        else:
            checks.append({"check": "length", "passed": True})
        
        # 2. 语言验证（简单实现）
        if self.config.get("check_language"):
            detected_lang = self._detect_language(text)
            allowed_langs = self.config.get("allowed_languages", ["zh", "en"])
            
            if detected_lang in allowed_langs or detected_lang == "mixed":
                checks.append({"check": "language", "passed": True, "detected": detected_lang})
            else:
                checks.append({"check": "language", "passed": False, "detected": detected_lang})
                warnings.append(f"语言不支持: {detected_lang}")
        
        # 3. 内容质量验证
        # 检查是否包含太多重复字符
        if self._has_too_many_repeats(text):
            checks.append({"check": "quality", "passed": False})
            warnings.append("包含过多重复字符")
        else:
            checks.append({"check": "quality", "passed": True})
        
        # 总体判断
        is_valid = all(check.get("passed", True) for check in checks)
        
        info = {
            "is_valid": is_valid,
            "checks": checks,
            "warnings": warnings,
            "reason": warnings[0] if warnings else "通过所有验证"
        }
        
        return is_valid, info
    
    def _compute_hash(self, text: str) -> str:
        """计算文本哈希"""
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
    def _detect_language(self, text: str) -> str:
        """
        检测语言（简单实现）
        
        Returns:
            "zh", "en", "mixed", "unknown"
        """
        # 计算中文字符和英文字符的比例
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        english_chars = len(re.findall(r'[a-zA-Z]', text))
        
        total_chars = len(re.findall(r'[\u4e00-\u9fffa-zA-Z]', text))
        
        if total_chars == 0:
            return "unknown"
        
        chinese_ratio = chinese_chars / total_chars
        english_ratio = english_chars / total_chars
        
        if chinese_ratio > 0.5:
            return "zh"
        elif english_ratio > 0.5:
            return "en"
        elif chinese_ratio > 0.1 and english_ratio > 0.1:
            return "mixed"
        else:
            return "unknown"
    
    def _has_too_many_repeats(self, text: str, threshold: int = 10) -> bool:
        """检查是否包含过多重复字符"""
        # 查找连续重复的字符
        pattern = r'(.)\1{' + str(threshold) + r',}'
        return bool(re.search(pattern, text))
    
    def reset_dedup_cache(self):
        """重置去重缓存"""
        self.seen_hashes.clear()
        logger.info("🔄 去重缓存已重置")


def test_preprocessor():
    """测试预处理器"""
    print("="*70)
    print("  预处理器测试")
    print("="*70)
    
    preprocessor = Preprocessor()
    
    # 测试文本
    test_cases = [
        {
            "name": "普通文本",
            "text": "这是一段正常的中文文本。It also contains English. 用于测试预处理功能。"
        },
        {
            "name": "包含HTML",
            "text": "<p>这是<strong>HTML</strong>文本</p><a href='http://example.com'>链接</a>"
        },
        {
            "name": "包含URL和邮箱",
            "text": "访问 https://example.com 或发送邮件到 test@example.com"
        },
        {
            "name": "文本过短",
            "text": "短"
        },
        {
            "name": "重复文本",
            "text": "这是一段正常的中文文本。It also contains English. 用于测试预处理功能。"
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n{'='*70}")
        print(f"测试 {i}: {case['name']}")
        print(f"{'='*70}")
        
        result = preprocessor.preprocess(case['text'])
        
        print(f"原文: {case['text'][:50]}...")
        print(f"处理后: {result['processed_text'][:50]}...")
        print(f"长度变化: {result['original_length']} → {result['final_length']}")
        print(f"是否重复: {result['is_duplicate']}")
        print(f"通过验证: {result['passed_validation']}")
        
        if result['warnings']:
            print(f"⚠️  警告: {', '.join(result['warnings'])}")
        
        print(f"\n处理步骤:")
        for step in result['preprocessing_steps']:
            print(f"  - {step['step']}: {step['info']}")
    
    print(f"\n{'='*70}")
    print("✅ 预处理器测试完成！")
    print(f"{'='*70}")


if __name__ == "__main__":
    test_preprocessor()




