"""
真实的Web搜索服务
支持多种搜索引擎
"""
from typing import Dict, Any, List, Optional


class WebSearchService:
    """Web搜索服务"""
    
    def __init__(self):
        """初始化搜索服务"""
        self.ddg_available = self._check_ddg()
    
    def _check_ddg(self) -> bool:
        """检查DuckDuckGo搜索是否可用"""
        try:
            from duckduckgo_search import DDGS
            return True
        except ImportError:
            return False
    
    async def search(
        self,
        query: str,
        engine: str = "duckduckgo",
        max_results: int = 10,
        region: str = "cn-zh"
    ) -> Dict[str, Any]:
        """
        Web搜索（真实实现）
        
        Args:
            query: 搜索查询
            engine: 搜索引擎
            max_results: 最大结果数
            region: 地区代码
            
        Returns:
            搜索结果
        """
        if engine == "duckduckgo":
            return await self._search_duckduckgo(query, max_results, region)
        else:
            return {
                "success": False,
                "error": f"搜索引擎{engine}暂不支持",
                "supported_engines": ["duckduckgo"]
            }
    
    async def _search_duckduckgo(
        self,
        query: str,
        max_results: int,
        region: str
    ) -> Dict[str, Any]:
        """使用DuckDuckGo搜索"""
        if not self.ddg_available:
            return {
                "success": False,
                "error": "duckduckgo-search未安装",
                "solution": "运行: pip install duckduckgo-search",
                "query": query,
                "results": []
            }
        
        try:
            from duckduckgo_search import DDGS
            
            results = []
            
            with DDGS() as ddgs:
                for r in ddgs.text(query, region=region, max_results=max_results):
                    results.append({
                        "title": r.get("title", ""),
                        "url": r.get("link", ""),
                        "snippet": r.get("body", ""),
                        "source": "duckduckgo"
                    })
            
            return {
                "success": True,
                "query": query,
                "engine": "duckduckgo",
                "results": results,
                "total": len(results)
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "query": query,
                "results": []
            }
    
    async def search_and_summarize(
        self,
        query: str,
        max_results: int = 5
    ) -> Dict[str, Any]:
        """
        搜索并生成摘要
        
        Args:
            query: 搜索查询
            max_results: 最大结果数
            
        Returns:
            搜索和摘要结果
        """
        # 执行搜索
        search_result = await self.search(query, max_results=max_results)
        
        if not search_result.get("success"):
            return search_result
        
        # 生成摘要（使用LLM）
        try:
            from core.real_llm_service import get_llm_service
            llm = get_llm_service()
            
            # 构建摘要提示
            snippets = "\n\n".join([
                f"{i+1}. {r['title']}\n{r['snippet']}"
                for i, r in enumerate(search_result["results"][:5])
            ])
            
            llm_result = await llm.generate(
                prompt=f"请基于以下搜索结果，生成关于'{query}'的简洁摘要：\n\n{snippets}",
                system_prompt="你是搜索结果分析专家，请提取关键信息并生成简洁摘要。",
                temperature=0.5,
                max_tokens=500
            )
            
            if llm_result.get("success"):
                search_result["summary"] = llm_result["text"]
            else:
                search_result["summary"] = "摘要生成失败"
        
        except Exception as e:
            search_result["summary"] = f"摘要生成错误: {str(e)}"
        
        return search_result
    
    def get_status(self) -> Dict[str, Any]:
        """获取搜索服务状态"""
        return {
            "search_available": self.ddg_available,
            "supported_engines": ["duckduckgo"],
            "supported_regions": ["cn-zh", "us-en", "uk-en", "jp-jp"],
            "installation_guide": "pip install duckduckgo-search"
        }


# 全局搜索服务实例
_search_service = None

def get_search_service() -> WebSearchService:
    """获取搜索服务实例"""
    global _search_service
    if _search_service is None:
        _search_service = WebSearchService()
    return _search_service


# 使用示例
if __name__ == "__main__":
    import asyncio
    
    async def test():
        search = get_search_service()
        
        print("✅ 搜索服务已加载")
        print(f"📊 状态: {search.get_status()}")
        
        # 测试搜索
        if search.ddg_available:
            result = await search.search("AI人工智能", max_results=3)
            
            if result["success"]:
                print(f"\n✅ 搜索成功:")
                for r in result["results"]:
                    print(f"  • {r['title'][:50]}")
            else:
                print(f"\n❌ 搜索失败: {result['error']}")
        else:
            print("\n⚠️  搜索服务不可用，请安装: pip install duckduckgo-search")
    
    asyncio.run(test())


