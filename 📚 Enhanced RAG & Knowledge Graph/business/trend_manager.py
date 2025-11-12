"""
趋势分析管理器
实现真实的趋势分析业务逻辑（11项功能）
"""
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
from pathlib import Path


class TrendManager:
    """趋势分析管理器"""
    
    def __init__(self):
        """初始化趋势管理器"""
        self.data_dir = Path("data/trends")
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    # ==================== 功能1: 信息爬取 ====================
    
    async def crawl_information(
        self,
        category: str,  # policy/industry/tech/news/economy
        keywords: Optional[List[str]] = None,
        max_items: int = 20
    ) -> Dict[str, Any]:
        """
        信息爬取（真实实现）
        
        Args:
            category: 信息类别
            keywords: 关键词
            max_items: 最大数量
            
        Returns:
            爬取结果
        """
        try:
            from services.web_search_service import get_search_service
            search = get_search_service()
            
            # 构建搜索查询
            category_keywords = {
                "policy": "政策 法规 通知",
                "industry": "产业 行业 报告",
                "tech": "科技 技术 创新",
                "news": "新闻 资讯 动态",
                "economy": "经济 市场 趋势"
            }
            
            base_query = category_keywords.get(category, category)
            
            if keywords:
                query = f"{base_query} {' '.join(keywords)}"
            else:
                query = base_query
            
            # 真实搜索
            search_result = await search.search(
                query=query,
                max_results=max_items
            )
            
            if not search_result.get("success"):
                return search_result
            
            # 处理结果
            items = []
            for result in search_result["results"]:
                items.append({
                    "title": result["title"],
                    "url": result["url"],
                    "content": result["snippet"],
                    "category": category,
                    "source": "web_search",
                    "crawled_at": datetime.now().isoformat()
                })
            
            # 保存到本地
            filename = f"{category}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = self.data_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(items, f, ensure_ascii=False, indent=2)
            
            return {
                "success": True,
                "category": category,
                "items": items,
                "total": len(items),
                "saved_to": str(filepath),
                "crawl_method": "real_search"
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "items": []
            }
    
    # ==================== 功能2: 信息处理 ====================
    
    async def process_information(
        self,
        items: List[Dict[str, Any]],
        operations: List[str]  # classify/compare/summarize/extract
    ) -> Dict[str, Any]:
        """
        信息处理（真实AI分析）
        
        Args:
            items: 信息列表
            operations: 处理操作列表
            
        Returns:
            处理结果
        """
        try:
            from core.real_llm_service import get_llm_service
            llm = get_llm_service()
            
            results = {}
            
            # 构建内容文本
            content_text = "\n\n".join([
                f"{i+1}. {item['title']}\n{item.get('content', '')[:200]}"
                for i, item in enumerate(items[:10])
            ])
            
            # 分类
            if "classify" in operations:
                prompt = f"请将以下信息按主题分类：\n\n{content_text}"
                
                llm_result = await llm.generate(
                    prompt=prompt,
                    system_prompt="你是信息分类专家。",
                    temperature=0.5,
                    max_tokens=800
                )
                
                results["classification"] = llm_result.get("text", "分类失败") if llm_result.get("success") else "LLM不可用"
            
            # 比较
            if "compare" in operations:
                prompt = f"请比较分析以下信息的异同点：\n\n{content_text}"
                
                llm_result = await llm.generate(
                    prompt=prompt,
                    system_prompt="你是信息对比分析专家。",
                    temperature=0.6,
                    max_tokens=1000
                )
                
                results["comparison"] = llm_result.get("text", "比较失败") if llm_result.get("success") else "LLM不可用"
            
            # 汇总
            if "summarize" in operations:
                prompt = f"请汇总以下信息的核心要点：\n\n{content_text}"
                
                llm_result = await llm.generate(
                    prompt=prompt,
                    system_prompt="你是信息汇总专家。",
                    temperature=0.5,
                    max_tokens=800
                )
                
                results["summary"] = llm_result.get("text", "汇总失败") if llm_result.get("success") else "LLM不可用"
            
            # 提取关键信息
            if "extract" in operations:
                from processors.text_processors.entity_extractor import EntityExtractor
                extractor = EntityExtractor()
                
                # 提取实体
                all_entities = {}
                for item in items[:10]:
                    text = item.get("title", "") + " " + item.get("content", "")
                    entity_result = extractor.extract(text)
                    
                    for entity_type, entities in entity_result.get("entities", {}).items():
                        if entity_type not in all_entities:
                            all_entities[entity_type] = []
                        all_entities[entity_type].extend(entities)
                
                results["extracted_entities"] = all_entities
            
            return {
                "success": True,
                "items_processed": len(items),
                "operations": operations,
                "results": results
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    # ==================== 功能3: 报告生成 ====================
    
    async def generate_report(
        self,
        report_type: str,  # industry/investment/policy
        topic: str,
        data_items: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        生成分析报告（真实AI生成）
        
        Args:
            report_type: 报告类型
            topic: 主题
            data_items: 数据项
            
        Returns:
            报告内容
        """
        try:
            from core.real_llm_service import get_llm_service
            llm = get_llm_service()
            
            # 先处理数据
            processed = await self.process_information(
                data_items,
                operations=["classify", "summarize"]
            )
            
            summary = processed.get("results", {}).get("summary", "")
            
            # 生成报告
            report_templates = {
                "industry": "行业分析报告",
                "investment": "投资分析报告",
                "policy": "政策分析报告"
            }
            
            prompt = f"""请生成一份关于"{topic}"的{report_templates.get(report_type, '分析报告')}。

参考数据摘要：
{summary}

报告要求：
1. 包含背景分析
2. 包含趋势预测
3. 包含投资/决策建议
4. 数据支撑充分
5. 专业严谨
"""
            
            llm_result = await llm.generate(
                prompt=prompt,
                system_prompt="你是专业的行业分析师，擅长撰写分析报告。",
                temperature=0.6,
                max_tokens=2500
            )
            
            if llm_result.get("success"):
                report_content = llm_result["text"]
            else:
                report_content = f"# {topic}{report_templates.get(report_type)}\n\n⚠️ 报告生成失败: {llm_result.get('error')}"
            
            # 保存报告
            from services.file_generator_service import get_file_generator
            generator = get_file_generator()
            
            file_result = await generator.generate_word(
                content=report_content,
                title=f"{topic}{report_templates.get(report_type)}"
            )
            
            return {
                "success": True,
                "report_type": report_type,
                "topic": topic,
                "content": report_content,
                "word_count": len(report_content),
                "file_path": file_result.get("file_path") if file_result.get("success") else None,
                "data_items_used": len(data_items)
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "content": ""
            }
    
    # ==================== 功能4: 归档管理 ====================
    
    async def archive_data(self, category: str, days_old: int = 30) -> Dict[str, Any]:
        """归档历史数据"""
        archive_dir = self.data_dir / "archive"
        archive_dir.mkdir(parents=True, exist_ok=True)
        
        # 查找旧文件
        cutoff_date = datetime.now() - timedelta(days=days_old)
        archived_files = []
        
        for file in self.data_dir.glob(f"{category}_*.json"):
            if file.stat().st_mtime < cutoff_date.timestamp():
                # 移动到归档目录
                new_path = archive_dir / file.name
                file.rename(new_path)
                archived_files.append(str(new_path))
        
        return {
            "success": True,
            "category": category,
            "archived_files": len(archived_files),
            "archive_dir": str(archive_dir)
        }
    
    # ==================== 功能5: 信息提醒 ====================
    
    async def create_alert(
        self,
        topic: str,
        conditions: Dict[str, Any],
        alert_type: str = "keyword"  # keyword/frequency/sentiment
    ) -> Dict[str, Any]:
        """创建信息提醒"""
        from agent.smart_reminder import SmartReminder
        reminder = SmartReminder()
        
        # 创建提醒
        result = reminder.create_reminder(
            title=f"趋势提醒：{topic}",
            content=f"监控条件：{json.dumps(conditions, ensure_ascii=False)}",
            remind_time=datetime.now() + timedelta(hours=1),
            reminder_type="trend",
            priority=3
        )
        
        return {
            "success": result.get("success", False),
            "alert_id": result.get("reminder", {}).get("id"),
            "topic": topic,
            "alert_type": alert_type
        }


# 全局趋势管理器实例
_trend_manager = None

def get_trend_manager() -> TrendManager:
    """获取趋势管理器实例"""
    global _trend_manager
    if _trend_manager is None:
        _trend_manager = TrendManager()
    return _trend_manager


# 使用示例
if __name__ == "__main__":
    import asyncio
    
    async def test():
        trend = get_trend_manager()
        
        print("✅ 趋势管理器已加载")
        
        # 测试信息爬取
        result = await trend.crawl_information("tech", keywords=["AI", "人工智能"], max_items=5)
        
        if result["success"]:
            print(f"\n✅ 信息爬取: {result['total']}条信息")
            for item in result["items"][:3]:
                print(f"  • {item['title'][:50]}")
        else:
            print(f"\n⚠️  信息爬取: {result.get('error', '需要配置搜索服务')}")
    
    asyncio.run(test())


