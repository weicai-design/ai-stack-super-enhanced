"""
缓存使用示例
Cache Usage Examples

展示如何为关键端点添加缓存

版本: 1.0.0 (v2.7.0)
"""

from api.cache_manager import cached, cache_manager

# ==================== RAG搜索缓存示例 ====================

# 示例1: 使用装饰器（推荐）
@cached(ttl=600, key_prefix="rag_search")
async def rag_search_cached(query: str, top_k: int = 5):
    """
    带缓存的RAG搜索
    
    自动缓存10分钟，相同查询直接返回缓存结果
    """
    # 原始搜索逻辑
    results = perform_rag_search(query, top_k)
    return results


# 示例2: 手动缓存控制
async def rag_search_manual(query: str, top_k: int = 5, use_cache: bool = True):
    """
    手动控制缓存的RAG搜索
    """
    if use_cache:
        # 生成缓存key
        cache_key = f"rag_search:{query}:{top_k}"
        
        # 尝试从缓存获取
        cached_result = cache_manager.get(cache_key)
        if cached_result:
            return cached_result
    
    # 执行搜索
    results = perform_rag_search(query, top_k)
    
    # 存入缓存
    if use_cache:
        cache_manager.set(cache_key, results, ttl=600)
    
    return results


# ==================== 图谱数据缓存示例 ====================

# 示例3: 图谱查询缓存
@cached(ttl=3600, key_prefix="kg_graph")
async def get_kg_graph_cached(limit: int = 100, include_properties: bool = True):
    """
    带缓存的图谱查询
    
    自动缓存1小时，图谱数据变化不频繁
    """
    graph_data = fetch_knowledge_graph(limit, include_properties)
    return graph_data


# 示例4: 节点查询缓存
@cached(ttl=1800, key_prefix="kg_node")
async def get_node_cached(node_id: str):
    """
    带缓存的节点查询
    
    自动缓存30分钟
    """
    node = fetch_node_by_id(node_id)
    return node


# ==================== 索引信息缓存示例 ====================

# 示例5: 索引信息缓存
@cached(ttl=60, key_prefix="index_info")
def get_index_info_cached():
    """
    带缓存的索引信息
    
    自动缓存1分钟（变化不频繁但需要相对新鲜）
    """
    info = collect_index_info()
    return info


# ==================== 智能缓存失效示例 ====================

# 示例6: 数据更新时失效缓存
async def ingest_document(text: str):
    """
    导入文档时，智能失效相关缓存
    """
    # 导入文档
    doc_id = perform_document_ingest(text)
    
    # 失效所有搜索缓存（因为索引变化了）
    cache_manager.clear("rag_search:*")
    
    # 失效索引信息缓存
    cache_manager.clear("index_info:*")
    
    return doc_id


# 示例7: 图谱更新时失效缓存
async def update_knowledge_graph(node_data):
    """
    更新图谱时，失效相关缓存
    """
    # 更新图谱
    result = perform_kg_update(node_data)
    
    # 失效所有图谱相关缓存
    cache_manager.clear("kg_*")
    
    return result


# ==================== 性能测试示例 ====================

import time

async def test_cache_performance():
    """
    测试缓存性能提升
    
    对比有缓存和无缓存的性能差异
    """
    test_query = "人工智能"
    
    # 测试无缓存（首次请求）
    start = time.time()
    result1 = await rag_search_cached(test_query)
    time_no_cache = time.time() - start
    
    # 测试有缓存（第二次请求）
    start = time.time()
    result2 = await rag_search_cached(test_query)
    time_with_cache = time.time() - start
    
    # 计算提升
    speedup = time_no_cache / max(time_with_cache, 0.001)
    
    return {
        "without_cache": f"{time_no_cache*1000:.2f}ms",
        "with_cache": f"{time_with_cache*1000:.2f}ms",
        "speedup": f"{speedup:.1f}x",
        "improvement": f"{(1 - time_with_cache/time_no_cache)*100:.1f}%"
    }


# ==================== 辅助函数（模拟） ====================

def perform_rag_search(query, top_k):
    """模拟RAG搜索"""
    import time
    time.sleep(0.05)  # 模拟50ms延迟
    return {"items": [], "query": query}

def fetch_knowledge_graph(limit, include_properties):
    """模拟图谱获取"""
    import time
    time.sleep(0.03)  # 模拟30ms延迟
    return {"nodes": [], "edges": []}

def fetch_node_by_id(node_id):
    """模拟节点查询"""
    return {"id": node_id, "label": "test"}

def collect_index_info():
    """模拟索引信息收集"""
    return {"size": 0, "count": 0}

def perform_document_ingest(text):
    """模拟文档导入"""
    return "doc_123"

def perform_kg_update(data):
    """模拟图谱更新"""
    return {"success": True}

































