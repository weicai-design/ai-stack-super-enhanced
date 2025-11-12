from fastapi import FastAPI
import sys
import os

# 添加路径以导入图表专家API
sys.path.append(os.path.dirname(__file__))

app = FastAPI(title="AI Stack API", version="1.0.0")

# 注册图表专家API
try:
    from api.chart_expert_api import router as chart_expert_router
    app.include_router(chart_expert_router)
    print("✅ 图表专家API已注册")
except Exception as e:
    print(f"⚠️ 图表专家API注册失败: {e}")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/api/groups")
async def get_groups():
    return {"groups": []}

@app.get("/api/customers")
async def get_customers():
    return {"customers": []}

@app.get("/rag/search")
async def rag_search(query: str = "test"):
    return {"results": [], "query": query}
