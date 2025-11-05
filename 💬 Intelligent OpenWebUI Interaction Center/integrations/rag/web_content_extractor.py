"""
Web Content Extractor
网页内容提取器

根据需求1.4：完善网络信息抓取
功能：
1. 智能网页内容提取（去除广告和无关内容）
2. 提取核心正文
3. 保留结构化信息（表格、列表等）
4. 网页元数据提取（作者、日期、分类等）
5. 多语言网页支持
"""

import logging
import re
from typing import Dict, Optional, Any, List
from datetime import datetime
from urllib.parse import urlparse
import html

logger = logging.getLogger(__name__)


class WebContentExtractor:
    """
    网页内容提取器
    
    从网页HTML中提取有用内容，去除广告和无关信息
    """

    def __init__(self):
        """初始化提取器"""
        # 常见的广告和无关内容选择器（简化版，实际可以使用BeautifulSoup等）
        self.noise_patterns = [
            r'<script[^>]*>.*?</script>',
            r'<style[^>]*>.*?</style>',
            r'<nav[^>]*>.*?</nav>',
            r'<footer[^>]*>.*?</footer>',
            r'<header[^>]*>.*?</header>',
            r'<aside[^>]*>.*?</aside>',
            r'<div[^>]*class=["\'].*?(?:ad|advertisement|ads|banner|sidebar)[^"\']*["\'][^>]*>.*?</div>',
            r'<!--.*?-->',
        ]
        
        # 正文内容选择器（简化版）
        self.content_patterns = [
            r'<article[^>]*>(.*?)</article>',
            r'<main[^>]*>(.*?)</main>',
            r'<div[^>]*class=["\'].*?(?:content|post|article|main-content)[^"\']*["\'][^>]*>(.*?)</div>',
            r'<p[^>]*>(.*?)</p>',
        ]
        
        # 元数据提取模式
        self.metadata_patterns = {
            "author": [
                r'<meta[^>]*name=["\']author["\'][^>]*content=["\']([^"\']+)["\']',
                r'<span[^>]*class=["\'].*?author[^"\']*["\'][^>]*>(.*?)</span>',
                r'<a[^>]*rel=["\']author["\'][^>]*>(.*?)</a>',
            ],
            "date": [
                r'<meta[^>]*property=["\']article:published_time["\'][^>]*content=["\']([^"\']+)["\']',
                r'<time[^>]*datetime=["\']([^"\']+)["\']',
                r'<span[^>]*class=["\'].*?date[^"\']*["\'][^>]*>(.*?)</span>',
            ],
            "title": [
                r'<title>(.*?)</title>',
                r'<meta[^>]*property=["\']og:title["\'][^>]*content=["\']([^"\']+)["\']',
                r'<h1[^>]*>(.*?)</h1>',
            ],
            "description": [
                r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']+)["\']',
                r'<meta[^>]*property=["\']og:description["\'][^>]*content=["\']([^"\']+)["\']',
            ],
        }

    def extract_content(self, html_content: str, url: str) -> Dict[str, Any]:
        """
        从HTML中提取内容
        
        Args:
            html_content: HTML内容
            url: 网页URL
            
        Returns:
            提取的内容字典，包含文本、元数据等
        """
        if not html_content:
            return {
                "success": False,
                "error": "HTML内容为空",
            }

        try:
            # 1. 去除噪声内容
            cleaned_html = self._remove_noise(html_content)
            
            # 2. 提取正文内容
            main_content = self._extract_main_content(cleaned_html)
            
            # 3. 提取元数据
            metadata = self._extract_metadata(html_content, url)
            
            # 4. 提取结构化内容
            structured_content = self._extract_structured_content(cleaned_html)
            
            # 5. 构建最终文本
            formatted_text = self._format_extracted_content(
                metadata.get("title", ""),
                url,
                main_content,
                metadata,
            )
            
            return {
                "success": True,
                "text": formatted_text,
                "main_content": main_content,
                "metadata": metadata,
                "structured_content": structured_content,
                "source": url,
            }
            
        except Exception as e:
            logger.error(f"网页内容提取失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "source": url,
            }

    def _remove_noise(self, html_content: str) -> str:
        """
        去除噪声内容（脚本、样式、广告等）
        
        Args:
            html_content: HTML内容
            
        Returns:
            清理后的HTML
        """
        cleaned = html_content
        
        # 使用正则表达式去除噪声
        for pattern in self.noise_patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.DOTALL | re.IGNORECASE)
        
        return cleaned

    def _extract_main_content(self, html_content: str) -> str:
        """
        提取正文内容
        
        Args:
            html_content: 清理后的HTML
            
        Returns:
            正文文本
        """
        # 尝试多种模式提取正文
        for pattern in self.content_patterns:
            matches = re.findall(pattern, html_content, re.DOTALL | re.IGNORECASE)
            if matches:
                # 使用最长的匹配
                longest_match = max(matches, key=len)
                if len(longest_match.strip()) > 100:  # 至少100字符
                    return self._html_to_text(longest_match)
        
        # 如果都没找到，提取所有段落
        paragraphs = re.findall(r'<p[^>]*>(.*?)</p>', html_content, re.DOTALL)
        if paragraphs:
            text = ' '.join(paragraphs)
            return self._html_to_text(text)
        
        # 最后回退：直接去除HTML标签
        return self._html_to_text(html_content)

    def _html_to_text(self, html_content: str) -> str:
        """
        将HTML转换为纯文本
        
        Args:
            html_content: HTML内容
            
        Returns:
            纯文本
        """
        # 解码HTML实体
        text = html.unescape(html_content)
        
        # 去除HTML标签
        text = re.sub(r'<[^>]+>', ' ', text)
        
        # 规范化空白字符
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text

    def _extract_metadata(self, html_content: str, url: str) -> Dict[str, Any]:
        """
        提取网页元数据
        
        Args:
            html_content: HTML内容
            url: 网页URL
            
        Returns:
            元数据字典
        """
        metadata = {
            "url": url,
            "domain": urlparse(url).netloc if url else "",
            "extracted_at": datetime.now().isoformat(),
        }
        
        # 提取各种元数据
        for key, patterns in self.metadata_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, html_content, re.IGNORECASE | re.DOTALL)
                if match:
                    value = match.group(1) if match.lastindex >= 1 else match.group(0)
                    value = self._html_to_text(value).strip()
                    if value:
                        metadata[key] = value
                        break
        
        # 如果没有提取到标题，使用URL
        if "title" not in metadata or not metadata["title"]:
            metadata["title"] = urlparse(url).path.split('/')[-1] if url else "未知标题"
        
        return metadata

    def _extract_structured_content(self, html_content: str) -> Dict[str, Any]:
        """
        提取结构化内容（表格、列表等）
        
        Args:
            html_content: HTML内容
            
        Returns:
            结构化内容字典
        """
        structured = {
            "tables": [],
            "lists": [],
        }
        
        # 提取表格
        table_pattern = r'<table[^>]*>(.*?)</table>'
        tables = re.findall(table_pattern, html_content, re.DOTALL | re.IGNORECASE)
        for table in tables[:3]:  # 最多3个表格
            table_text = self._html_to_text(table)
            if len(table_text.strip()) > 20:  # 至少20字符
                structured["tables"].append(table_text[:500])  # 限制长度
        
        # 提取列表
        list_pattern = r'<[uo]l[^>]*>(.*?)</[uo]l>'
        lists = re.findall(list_pattern, html_content, re.DOTALL | re.IGNORECASE)
        for list_html in lists[:3]:  # 最多3个列表
            list_text = self._html_to_text(list_html)
            if len(list_text.strip()) > 20:
                structured["lists"].append(list_text[:500])
        
        return structured

    def _format_extracted_content(
        self,
        title: str,
        url: str,
        main_content: str,
        metadata: Dict[str, Any],
    ) -> str:
        """
        格式化提取的内容
        
        Args:
            title: 标题
            url: URL
            main_content: 正文内容
            metadata: 元数据
            
        Returns:
            格式化后的文本
        """
        parts = []
        
        # 标题
        if title:
            parts.append(f"标题: {title}")
        
        # URL
        if url:
            parts.append(f"来源: {url}")
        
        # 作者和日期
        if metadata.get("author"):
            parts.append(f"作者: {metadata['author']}")
        if metadata.get("date"):
            parts.append(f"日期: {metadata['date']}")
        
        parts.append("")  # 空行分隔
        parts.append("内容:")
        parts.append(main_content)
        
        # 结构化内容
        if metadata.get("structured_content"):
            structured = metadata["structured_content"]
            if structured.get("tables"):
                parts.append("")
                parts.append("表格内容:")
                for i, table in enumerate(structured["tables"], 1):
                    parts.append(f"[表格 {i}]")
                    parts.append(table)
            
            if structured.get("lists"):
                parts.append("")
                parts.append("列表内容:")
                for i, list_content in enumerate(structured["lists"], 1):
                    parts.append(f"[列表 {i}]")
                    parts.append(list_content)
        
        return "\n".join(parts)

    def detect_language(self, text: str) -> str:
        """
        检测文本语言（简化版）
        
        Args:
            text: 文本内容
            
        Returns:
            语言代码（如 'zh', 'en'）
        """
        # 简化实现：基于字符范围判断
        # 实际可以使用langdetect库
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        total_chars = len(re.findall(r'\w', text))
        
        if total_chars > 0 and chinese_chars / total_chars > 0.3:
            return "zh"
        else:
            return "en"


class ImprovedNetworkInfoExtractor:
    """
    改进的网络信息提取器
    
    结合WebContentExtractor提供更好的提取能力
    """

    def __init__(self):
        self.web_extractor = WebContentExtractor()
        self.min_content_length = 100  # 提高最小长度要求
        self.max_content_length = 50000

    def extract_from_web_search_result(
        self, search_result: Dict[str, Any], fetch_full_content: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        从网络搜索结果中提取信息（增强版）
        
        Args:
            search_result: 搜索结果字典
            fetch_full_content: 是否获取完整网页内容（需要网络请求）
            
        Returns:
            提取的信息字典
        """
        if not search_result:
            return None

        title = search_result.get("title", "").strip()
        url = search_result.get("url", "").strip()
        snippet = search_result.get("snippet", "").strip()
        content = search_result.get("content", "").strip()
        
        # 如果提供了HTML内容，使用WebContentExtractor提取
        html_content = search_result.get("html_content") or search_result.get("html", "")
        
        if html_content:
            # 使用增强提取器
            extracted = self.web_extractor.extract_content(html_content, url)
            if extracted.get("success"):
                formatted_text = extracted["text"]
                metadata = extracted.get("metadata", {})
                metadata.update({
                    "type": "web_search_result",
                    "title": title or metadata.get("title", ""),
                    "url": url,
                    "snippet": snippet[:200] if snippet else "",
                    "source_type": "network",
                    "extraction_method": "enhanced",
                })
                
                # 检测语言
                language = self.web_extractor.detect_language(formatted_text)
                metadata["language"] = language
                
                return {
                    "text": formatted_text,
                    "source": url,
                    "metadata": metadata,
                }
        
        # 回退到简单提取
        text_content = content if content else snippet
        
        if not text_content or len(text_content) < self.min_content_length:
            return None

        if len(text_content) > self.max_content_length:
            text_content = text_content[:self.max_content_length]

        # 格式化文本
        formatted_text = self._format_network_info(title, url, text_content)

        return {
            "text": formatted_text,
            "source": url,
            "metadata": {
                "type": "web_search_result",
                "title": title,
                "url": url,
                "snippet": snippet[:200] if snippet else "",
                "timestamp": datetime.now().isoformat(),
                "source_type": "network",
                "extraction_method": "simple",
            },
        }

    def _format_network_info(self, title: str, url: str, content: str) -> str:
        """
        格式化网络信息
        
        Args:
            title: 标题
            url: URL
            content: 内容
            
        Returns:
            格式化后的文本
        """
        parts = []
        if title:
            parts.append(f"标题: {title}")
        if url:
            parts.append(f"来源: {url}")
        parts.append("")
        parts.append("内容:")
        parts.append(content)
        return "\n".join(parts)

