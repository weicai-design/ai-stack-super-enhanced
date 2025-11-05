"""
AI Stack 命令网关
简单的命令解析服务，解析用户命令并调用相应的API
可以通过Web界面或API使用
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import requests
from typing import Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Stack 命令网关",
    description="统一的命令解析和API调用服务",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API配置
APIS = {
    "rag": "http://localhost:8011",
    "erp": "http://localhost:8013",
    "stock": "http://localhost:8014",
    "trend": "http://localhost:8015",
    "content": "http://localhost:8016",
    "task": "http://localhost:8017",
    "resource": "http://localhost:8018",
    "learning": "http://localhost:8019"
}


class CommandRequest(BaseModel):
    """命令请求"""
    command: str


def parse_and_execute(command: str) -> dict:
    """
    解析命令并执行
    
    Args:
        command: 用户命令
        
    Returns:
        执行结果
    """
    command_lower = command.lower()
    
    try:
        # ==================== 系统状态类命令 ====================
        
        if "所有系统" in command or "系统状态" in command:
            return check_all_systems()
        
        if "系统资源" in command or "资源使用" in command:
            return get_system_resources()
        
        if "服务状态" in command:
            return get_services_status()
        
        # ==================== ERP类命令 ====================
        
        if "财务" in command:
            period_type = "monthly"
            if "日" in command or "今天" in command or "今日" in command:
                period_type = "daily"
            elif "周" in command or "本周" in command:
                period_type = "weekly"
            elif "季" in command or "本季" in command:
                period_type = "quarterly"
            elif "年" in command or "今年" in command:
                period_type = "yearly"
            
            return get_financial_dashboard(period_type)
        
        if "客户" in command:
            return get_customers()
        
        if "订单" in command:
            # 检查是否指定订单号
            import re
            order_match = re.search(r'ORD\d+', command.upper())
            if order_match:
                return get_order_status(order_match.group())
            else:
                return get_orders_list()
        
        # ==================== RAG类命令 ====================
        
        if "知识库统计" in command or "rag统计" in command:
            return get_rag_stats()
        
        if "搜索知识库" in command:
            query = command.replace("搜索知识库", "").replace("中", "").replace("的", "").replace("关于", "").strip()
            return search_rag(query)
        
        if "保存" in command and "知识库" in command:
            # 提取要保存的内容
            content = command.split("：")[-1] if "：" in command else command.split(":")[-1]
            return save_to_rag(content.strip())
        
        # ==================== 股票类命令 ====================
        
        if "股票" in command or "stock" in command_lower:
            # 提取股票代码
            import re
            symbol_match = re.search(r'\b[A-Z]{1,5}\b', command.upper())
            if symbol_match:
                return get_stock_quote(symbol_match.group())
            else:
                return {"error": "请指定股票代码，如：查看AAPL股票"}
        
        # ==================== 任务类命令 ====================
        
        if "运行" in command and "任务" in command:
            return get_running_tasks()
        
        if "创建任务" in command:
            task_name = command.replace("创建", "").replace("任务", "").strip()
            return create_task(task_name)
        
        # ==================== 帮助命令 ====================
        
        if "帮助" in command or "help" in command_lower or "功能" in command:
            return get_help()
        
        # 未识别的命令
        return {
            "error": "未识别的命令",
            "suggestion": "输入'帮助'查看可用命令",
            "command": command
        }
        
    except Exception as e:
        logger.error(f"执行命令失败: {e}")
        return {
            "error": str(e),
            "command": command
        }


# ==================== 具体功能实现 ====================

def check_all_systems() -> dict:
    """检查所有系统状态"""
    result = {
        "title": "🌐 AI Stack 系统状态",
        "systems": {}
    }
    
    for name, url in APIS.items():
        try:
            response = requests.get(f"{url}/health", timeout=2)
            status = "✅ 运行中" if response.status_code == 200 else "❌ 异常"
        except:
            status = "⭕ 离线"
        
        result["systems"][name] = status
    
    online_count = sum(1 for s in result["systems"].values() if "运行中" in s)
    result["summary"] = f"总计: {online_count}/{len(APIS)} 系统在线"
    
    return result


def get_system_resources() -> dict:
    """获取系统资源"""
    try:
        response = requests.get(f"{APIS['resource']}/api/resources/system", timeout=5)
        if response.status_code == 200:
            data = response.json()
            resources = data.get("resources", {})
            
            return {
                "title": "⚙️ 系统资源状态",
                "cpu": f"{resources.get('cpu', {}).get('total_percent', 0):.1f}%",
                "memory": f"{resources.get('memory', {}).get('used_gb', 0):.1f}GB / {resources.get('memory', {}).get('total_gb', 32):.1f}GB",
                "memory_percent": f"{resources.get('memory', {}).get('percent', 0):.1f}%",
                "status": data.get("status", {}).get("overall", "unknown")
            }
        else:
            return {"error": "资源管理服务未运行"}
    except Exception as e:
        return {"error": f"无法获取资源信息: {str(e)}"}


def get_services_status() -> dict:
    """获取服务状态"""
    try:
        response = requests.get(f"{APIS['resource']}/api/resources/startup/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            services = data.get("services", [])
            
            running = [s for s in services if s.get("running")]
            stopped = [s for s in services if not s.get("running")]
            
            return {
                "title": "🌐 服务状态",
                "running": [s.get("service") for s in running],
                "stopped": [s.get("service") for s in stopped],
                "summary": f"{len(running)}/{len(services)} 服务运行中"
            }
        else:
            return {"error": "资源管理服务未运行"}
    except Exception as e:
        return {"error": f"无法获取服务状态: {str(e)}"}


def get_financial_dashboard(period_type: str = "monthly") -> dict:
    """获取财务看板"""
    try:
        response = requests.get(
            f"{APIS['erp']}/api/finance/dashboard",
            params={"period_type": period_type},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            summary = data.get("summary", {})
            
            return {
                "title": f"📊 {period_type.upper()} 财务看板",
                "income": f"¥{summary.get('total_income', 0):,.2f}",
                "expense": f"¥{summary.get('total_expense', 0):,.2f}",
                "profit": f"¥{summary.get('profit', 0):,.2f}",
                "profit_margin": f"{summary.get('profit_margin', 0):.1f}%",
                "period": period_type
            }
        else:
            return {"error": "ERP服务未运行"}
    except Exception as e:
        return {"error": f"无法获取财务数据: {str(e)}"}


def get_customers() -> dict:
    """获取客户列表"""
    try:
        response = requests.get(f"{APIS['erp']}/api/business/customers", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            customers = data.get("customers", [])
            
            return {
                "title": "👥 客户列表",
                "count": len(customers),
                "customers": [
                    {
                        "name": c.get("name"),
                        "category": c.get("category"),
                        "level": c.get("level")
                    }
                    for c in customers[:10]
                ]
            }
        else:
            return {"error": "ERP服务未运行"}
    except Exception as e:
        return {"error": f"无法获取客户列表: {str(e)}"}


def get_orders_list() -> dict:
    """获取订单列表"""
    try:
        response = requests.get(f"{APIS['erp']}/api/business/orders", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            orders = data.get("orders", [])
            
            return {
                "title": "📦 订单列表",
                "count": len(orders),
                "orders": [
                    {
                        "order_no": o.get("order_no"),
                        "customer": o.get("customer_name"),
                        "amount": f"¥{o.get('amount', 0):,.2f}",
                        "status": o.get("status")
                    }
                    for o in orders[:10]
                ]
            }
        else:
            return {"error": "ERP服务未运行"}
    except Exception as e:
        return {"error": f"无法获取订单列表: {str(e)}"}


def get_order_status(order_no: str) -> dict:
    """获取订单状态"""
    try:
        response = requests.get(f"{APIS['erp']}/api/business/orders/{order_no}", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            order = data.get("order", {})
            
            return {
                "title": f"📦 订单 {order_no}",
                "customer": order.get("customer_name"),
                "product": order.get("product_name"),
                "quantity": order.get("quantity"),
                "amount": f"¥{order.get('amount', 0):,.2f}",
                "status": order.get("status")
            }
        else:
            return {"error": f"订单 {order_no} 不存在"}
    except Exception as e:
        return {"error": f"无法获取订单: {str(e)}"}


def get_rag_stats() -> dict:
    """获取RAG统计"""
    try:
        response = requests.get(f"{APIS['rag']}/rag/stats", timeout=5)
        
        if response.status_code == 200:
            stats = response.json()
            
            return {
                "title": "📚 RAG知识库统计",
                "documents": stats.get("total_documents", 0),
                "chunks": stats.get("total_chunks", 0),
                "queries": stats.get("total_queries", 0),
                "storage_mb": f"{(stats.get('storage_bytes', 0) / 1024 / 1024):.2f} MB"
            }
        else:
            return {"error": "RAG服务未运行"}
    except Exception as e:
        return {"error": f"无法获取RAG统计: {str(e)}"}


def search_rag(query: str) -> dict:
    """搜索RAG知识库"""
    try:
        response = requests.get(
            f"{APIS['rag']}/rag/search",
            params={"query": query, "top_k": 5},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [])
            
            return {
                "title": f"🔍 搜索结果: {query}",
                "count": len(results),
                "results": [
                    {
                        "content": r.get("content", "")[:200],
                        "score": f"{r.get('score', 0) * 100:.1f}%",
                        "source": r.get("metadata", {}).get("source", "未知")
                    }
                    for r in results
                ]
            }
        else:
            return {"error": "RAG服务未运行"}
    except Exception as e:
        return {"error": f"搜索失败: {str(e)}"}


def save_to_rag(content: str) -> dict:
    """保存到RAG库"""
    try:
        response = requests.post(
            f"{APIS['rag']}/rag/ingest",
            json={"content": content, "metadata": {"source": "command_gateway"}},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            return {
                "title": "✅ 保存成功",
                "doc_id": result.get("id"),
                "chunks": result.get("num_chunks", 0)
            }
        else:
            return {"error": "RAG服务未运行"}
    except Exception as e:
        return {"error": f"保存失败: {str(e)}"}


def get_stock_quote(symbol: str) -> dict:
    """获取股票行情"""
    try:
        response = requests.get(f"{APIS['stock']}/api/stock/quote/{symbol}", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            quote = data.get("quote", {})
            
            return {
                "title": f"📈 {symbol} 股票行情",
                "price": f"${quote.get('price', 0):.2f}",
                "change": f"{quote.get('change', 0):+.2f}",
                "change_percent": f"{quote.get('change_percent', 0):+.2f}%",
                "volume": f"{quote.get('volume', 0):,}"
            }
        else:
            return {"error": "股票服务未运行"}
    except Exception as e:
        return {"error": f"获取行情失败: {str(e)}"}


def get_running_tasks() -> dict:
    """获取运行中的任务"""
    try:
        response = requests.get(f"{APIS['task']}/api/tasks/monitoring/active", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            tasks = data.get("tasks", [])
            
            return {
                "title": "⚙️ 运行中的任务",
                "count": len(tasks),
                "tasks": [
                    {
                        "name": t.get("task_name"),
                        "progress": f"{t.get('progress', 0):.0f}%",
                        "current_step": t.get("current_step")
                    }
                    for t in tasks
                ]
            }
        else:
            return {"error": "任务服务未运行"}
    except Exception as e:
        return {"error": f"获取任务失败: {str(e)}"}


def create_task(task_name: str) -> dict:
    """创建任务"""
    try:
        response = requests.post(
            f"{APIS['task']}/api/tasks/create",
            json={"name": task_name, "task_type": "general", "description": task_name},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            task = result.get("task", {})
            
            return {
                "title": "✅ 任务创建成功",
                "task_id": task.get("id"),
                "name": task_name,
                "status": task.get("status")
            }
        else:
            return {"error": "任务服务未运行"}
    except Exception as e:
        return {"error": f"创建任务失败: {str(e)}"}


def get_help() -> dict:
    """获取帮助信息"""
    return {
        "title": "🎯 AI Stack 可用命令",
        "commands": {
            "系统状态": [
                "查看所有系统状态",
                "查看系统资源",
                "查看服务状态"
            ],
            "ERP管理": [
                "查看本月财务",
                "查看本周财务",
                "查看客户列表",
                "查看订单列表",
                "查看订单ORD001"
            ],
            "RAG知识库": [
                "查看知识库统计",
                "搜索知识库中的Python内容",
                "保存到知识库：[你的文本]"
            ],
            "股票交易": [
                "查看AAPL股票",
                "查看TSLA股票"
            ],
            "任务管理": [
                "查看运行中的任务",
                "创建测试任务"
            ],
            "帮助": [
                "帮助",
                "有什么功能"
            ]
        }
    }


# ==================== API端点 ====================

@app.post("/execute")
async def execute_command_api(request: CommandRequest):
    """
    执行命令API
    
    POST /execute
    {"command": "查看本月财务"}
    """
    result = parse_and_execute(request.command)
    return result


@app.get("/execute")
async def execute_command_get(command: str):
    """
    执行命令API (GET方式)
    
    GET /execute?command=查看本月财务
    """
    result = parse_and_execute(command)
    return result


@app.get("/", response_class=HTMLResponse)
async def root():
    """Web界面"""
    return """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Stack 命令中心</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 900px; margin: 0 auto; }
        .header {
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            margin-bottom: 30px;
            text-align: center;
        }
        .header h1 { color: #333; margin-bottom: 10px; }
        .header p { color: #666; }
        .command-box {
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            margin-bottom: 20px;
        }
        .input-group {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }
        input {
            flex: 1;
            padding: 15px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            font-size: 16px;
            outline: none;
        }
        input:focus { border-color: #667eea; }
        button {
            padding: 15px 30px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            font-size: 16px;
            font-weight: bold;
        }
        button:hover { transform: scale(1.05); }
        .result {
            background: #f9f9f9;
            padding: 20px;
            border-radius: 10px;
            border-left: 4px solid #667eea;
            white-space: pre-wrap;
            font-family: monospace;
            max-height: 500px;
            overflow-y: auto;
        }
        .examples {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 10px;
            margin-top: 20px;
        }
        .example-btn {
            padding: 10px;
            background: #f0f0f0;
            border: 1px solid #ddd;
            border-radius: 8px;
            cursor: pointer;
            text-align: center;
            font-size: 13px;
            transition: all 0.3s;
        }
        .example-btn:hover {
            background: #667eea;
            color: white;
            transform: translateY(-2px);
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 AI Stack 命令中心</h1>
            <p>在这里输入命令，操作所有AI Stack功能</p>
        </div>

        <div class="command-box">
            <div class="input-group">
                <input type="text" id="commandInput" placeholder="输入命令，如：查看本月财务" />
                <button onclick="executeCommand()">执行</button>
            </div>

            <div class="examples">
                <div class="example-btn" onclick="setCommand('查看所有系统状态')">查看系统状态</div>
                <div class="example-btn" onclick="setCommand('查看本月财务')">查看财务</div>
                <div class="example-btn" onclick="setCommand('查看客户列表')">查看客户</div>
                <div class="example-btn" onclick="setCommand('查看系统资源')">查看资源</div>
                <div class="example-btn" onclick="setCommand('查看知识库统计')">RAG统计</div>
                <div class="example-btn" onclick="setCommand('查看AAPL股票')">股票行情</div>
                <div class="example-btn" onclick="setCommand('查看运行中的任务')">任务状态</div>
                <div class="example-btn" onclick="setCommand('帮助')">帮助</div>
            </div>

            <div id="result" class="result" style="margin-top: 20px; display: none;"></div>
        </div>
    </div>

    <script>
        function setCommand(cmd) {
            document.getElementById('commandInput').value = cmd;
            executeCommand();
        }

        async function executeCommand() {
            const command = document.getElementById('commandInput').value;
            if (!command) return;

            const resultDiv = document.getElementById('result');
            resultDiv.style.display = 'block';
            resultDiv.textContent = '执行中...';

            try {
                const response = await fetch(`/execute?command=${encodeURIComponent(command)}`);
                const data = await response.json();
                
                resultDiv.textContent = JSON.stringify(data, null, 2);
            } catch (error) {
                resultDiv.textContent = '错误: ' + error.message;
            }
        }

        document.getElementById('commandInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') executeCommand();
        });
    </script>
</body>
</html>
    """


@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "healthy", "service": "command-gateway"}


if __name__ == "__main__":
    import uvicorn
    print("🚀 启动AI Stack命令网关...")
    print("访问: http://localhost:8020")
    uvicorn.run(app, host="0.0.0.0", port=8020)


