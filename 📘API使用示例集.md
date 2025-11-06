# 📘 AI-Stack API使用示例集

**文档版本**: V1.0  
**更新时间**: 2025-11-06  
**适用范围**: 所有AI-Stack API

---

## 📚 目录

1. [AI交互中心API](#ai交互中心api)
2. [RAG系统API](#rag系统api)
3. [ERP系统API](#erp系统api)
4. [股票交易API](#股票交易api)
5. [内容创作API](#内容创作api)

---

## 🤖 AI交互中心API

### 基础URL
```
http://localhost:8020
```

### 示例1: 发送聊天消息

#### Python示例

```python
import requests

url = "http://localhost:8020/api/chat"
data = {
    "message": "你好，请介绍一下RAG系统",
    "user_id": "user123",
    "stream": False
}

response = requests.post(url, json=data)
print(response.json())
```

#### cURL示例

```bash
curl -X POST "http://localhost:8020/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "你好，请介绍一下RAG系统",
    "user_id": "user123"
  }'
```

#### JavaScript示例

```javascript
fetch('http://localhost:8020/api/chat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    message: "你好，请介绍一下RAG系统",
    user_id: "user123"
  })
})
.then(response => response.json())
.then(data => console.log(data));
```

---

### 示例2: 上传文件处理

#### Python示例

```python
import requests

url = "http://localhost:8020/api/file/process"

files = {'file': open('document.pdf', 'rb')}
data = {'user_id': 'user123'}

response = requests.post(url, files=files, data=data)
print(response.json())
```

---

## 📚 RAG系统API

### 基础URL
```
http://localhost:8011
```

### 示例1: 上传文档到知识库

#### Python示例

```python
import requests

url = "http://localhost:8011/api/upload"

files = {'file': open('knowledge.pdf', 'rb')}
data = {
    'category': '产品文档',
    'tags': 'manual,guide'
}

response = requests.post(url, files=files, data=data)
print(response.json())
```

---

### 示例2: 知识检索

#### Python示例

```python
import requests

url = "http://localhost:8011/api/search"
data = {
    "query": "如何配置数据库",
    "top_k": 5,
    "filter": {"category": "技术文档"}
}

response = requests.post(url, json=data)
results = response.json()

for result in results['results']:
    print(f"相关度: {result['score']:.2f}")
    print(f"内容: {result['content']}")
    print("-" * 60)
```

#### cURL示例

```bash
curl -X POST "http://localhost:8011/api/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "如何配置数据库",
    "top_k": 5
  }'
```

---

## 💼 ERP系统API

### 基础URL
```
http://localhost:8013
```

### 示例1: 创建客户

#### Python示例

```python
import requests

url = "http://localhost:8013/api/customer/create"
data = {
    "customer_id": "CUST001",
    "name": "ABC科技公司",
    "industry": "电子制造",
    "contact": {
        "person": "张三",
        "phone": "13800138000",
        "email": "zhangsan@abc.com"
    },
    "credit_rating": "A"
}

response = requests.post(url, json=data)
print(response.json())
```

---

### 示例2: 创建订单

#### Python示例

```python
import requests

url = "http://localhost:8013/api/order/create"
data = {
    "customer_id": "CUST001",
    "items": [
        {
            "product_id": "PROD001",
            "quantity": 1000,
            "price": 100.00
        }
    ],
    "delivery_date": "2025-12-01",
    "payment_terms": "Net 30"
}

response = requests.post(url, json=data)
order = response.json()

print(f"订单创建成功: {order['order_id']}")
print(f"总金额: {order['total_amount']}")
```

---

### 示例3: 创建采购申请

#### Python示例

```python
import requests

url = "http://localhost:8013/api/erp/procurement/request/create"
data = {
    "requester": "采购员A",
    "items": [
        {
            "material_id": "MAT001",
            "quantity": 500,
            "spec": "标准规格"
        }
    ],
    "reason": "订单生产需求",
    "required_date": "2025-11-20",
    "priority": "high"
}

response = requests.post(url, json=data)
print(response.json())
```

---

### 示例4: 获取ERP总览

#### Python示例

```python
import requests

url = "http://localhost:8013/api/erp/dashboard/overview"

response = requests.get(url)
overview = response.json()

print("ERP系统总览:")
for module, stats in overview['overview']['modules'].items():
    print(f"  {module}: {stats}")
```

---

## 📈 股票交易API

### 基础URL
```
http://localhost:8014
```

### 示例1: 配置交易授权

#### Python示例

```python
import requests

url = "http://localhost:8014/api/trading/configure-authorization"
data = {
    "auth_level": "auto_limited",
    "max_single_trade": 50000,
    "max_daily_trade": 200000,
    "allowed_stocks": ["600000", "000001", "000002"],
    "forbidden_st": True
}

response = requests.post(url, json=data)
print(response.json())
```

---

### 示例2: 执行授权买入

#### Python示例

```python
import requests

url = "http://localhost:8014/api/trading/authorized-buy"
data = {
    "stock_code": "600000",
    "price": 11.50,
    "quantity": 1000,
    "strategy_id": "STRATEGY_001",
    "reason": "技术面突破，成交量放大"
}

response = requests.post(url, json=data)
result = response.json()

if result['success']:
    print(f"✅ 买入成功: {result['order']['order_id']}")
else:
    print(f"❌ 买入失败: {result['error']}")
```

---

### 示例3: 查询交易统计

#### Python示例

```python
import requests

url = "http://localhost:8014/api/trading/statistics"

response = requests.get(url)
stats = response.json()

print(f"总交易次数: {stats['total_trades']}")
print(f"买入次数: {stats['buy_trades']}")
print(f"卖出次数: {stats['sell_trades']}")
print(f"成功率: {stats.get('success_rate', 0)}%")
```

---

## 🎨 内容创作API

### 基础URL
```
http://localhost:8016
```

### 示例1: 创建内容并去AI化

#### Python示例

```python
import requests

# 步骤1: AI创建内容
url = "http://localhost:8016/api/content/create"
data = {
    "topic": "如何提高工作效率",
    "platform": "xiaohongshu",
    "style": "casual"
}

response = requests.post(url, json=data)
ai_content = response.json()['content']

# 步骤2: 去AI化处理
url = "http://localhost:8016/api/content/remove-ai"
data = {
    "content": ai_content,
    "differentiation_level": "high"
}

response = requests.post(url, json=data)
processed = response.json()

print(f"原始内容AI分数: {processed['ai_score_before']}")
print(f"处理后AI分数: {processed['ai_score_after']}")
print(f"\n处理后内容:\n{processed['processed_content']}")
```

---

### 示例2: 发布到平台

#### Python示例

```python
import requests

url = "http://localhost:8016/api/publish"
data = {
    "platform": "xiaohongshu",
    "content_data": {
        "title": "工作效率提升秘籍",
        "content": "这里是经过去AI化处理的内容...",
        "images": ["image1.jpg", "image2.jpg"],
        "tags": ["效率", "职场", "干货"]
    }
}

response = requests.post(url, json=data)
result = response.json()

if result['success']:
    print(f"✅ 发布成功!")
    print(f"内容ID: {result['content_id']}")
    print(f"链接: {result['url']}")
```

---

## 🔄 完整业务流程示例

### 端到端: 从客户到账款回收

```python
import requests
import time

base_url = "http://localhost:8013/api"

# 1. 创建客户
customer_response = requests.post(f"{base_url}/customer/create", json={
    "customer_id": "CUST001",
    "name": "测试公司"
})
print("✅ 步骤1: 客户创建完成")

# 2. 创建订单
order_response = requests.post(f"{base_url}/order/create", json={
    "customer_id": "CUST001",
    "items": [{"product_id": "PROD001", "quantity": 1000, "price": 100}]
})
order_id = order_response.json()['order_id']
print(f"✅ 步骤2: 订单创建完成 - {order_id}")

# 3. 创建采购申请
procurement_response = requests.post(f"{base_url}/erp/procurement/request/create", json={
    "requester": "采购员",
    "items": [{"material_id": "MAT001", "quantity": 500}],
    "reason": f"订单{order_id}",
    "required_date": "2025-11-20"
})
pr_id = procurement_response.json()['request_id']
print(f"✅ 步骤3: 采购申请创建 - {pr_id}")

# 4. 审批采购
approval_response = requests.post(f"{base_url}/erp/procurement/request/approve", json={
    "request_id": pr_id,
    "approver": "经理",
    "approved": True
})
print("✅ 步骤4: 采购审批通过")

# 5. 创建交付计划
delivery_response = requests.post(f"{base_url}/erp/delivery/plan/create", json={
    "sales_order_id": order_id,
    "customer_id": "CUST001",
    "delivery_date": "2025-12-01",
    "items": [{"material_id": "PROD001", "quantity": 1000}],
    "delivery_address": {"city": "上海", "address": "测试地址"}
})
print("✅ 步骤5: 交付计划创建")

print("\n🎉 完整流程演示完成！")
```

---

## 🧪 批量操作示例

### 批量创建物料

```python
import requests

url = "http://localhost:8013/api/erp/material/create"

materials = [
    {"material_id": f"MAT{i:04d}", "name": f"物料{i}", "unit": "个"}
    for i in range(1, 51)
]

for material in materials:
    response = requests.post(url, json=material)
    if response.json()['success']:
        print(f"✅ {material['material_id']} 创建成功")

print(f"\n🎉 批量创建完成: {len(materials)}个物料")
```

---

## 📊 数据查询示例

### 查询ERP关键指标

```python
import requests

url = "http://localhost:8013/api/erp/dashboard/kpi"

response = requests.get(url)
kpi = response.json()['kpi']

print("ERP关键指标:")
print(f"  交付准时率: {kpi['delivery_performance']['summary']['on_time_rate']}%")
print(f"  采购总额: {kpi['procurement_performance']['summary']['total_amount']}")
print(f"  设备可用率: {kpi['equipment_statistics']['summary']['availability_rate']}%")
```

---

## 🔄 异步请求示例

### 使用httpx进行异步调用

```python
import httpx
import asyncio

async def main():
    async with httpx.AsyncClient() as client:
        # 并行发送多个请求
        tasks = [
            client.get("http://localhost:8020/health"),
            client.get("http://localhost:8011/health"),
            client.get("http://localhost:8013/health")
        ]
        
        responses = await asyncio.gather(*tasks)
        
        for i, response in enumerate(responses):
            service = ["AI交互", "RAG", "ERP"][i]
            status = "✅ 正常" if response.status_code == 200 else "❌ 异常"
            print(f"{service}: {status}")

asyncio.run(main())
```

---

## 🛠️ 错误处理示例

### 完整的错误处理

```python
import requests
from requests.exceptions import RequestException, Timeout

def safe_api_call(url, method="GET", **kwargs):
    """
    安全的API调用
    
    Args:
        url: API URL
        method: 请求方法
        **kwargs: 其他参数
    
    Returns:
        响应数据或错误信息
    """
    try:
        if method == "GET":
            response = requests.get(url, timeout=10, **kwargs)
        elif method == "POST":
            response = requests.post(url, timeout=10, **kwargs)
        
        response.raise_for_status()
        return {"success": True, "data": response.json()}
    
    except Timeout:
        return {"success": False, "error": "请求超时"}
    
    except RequestException as e:
        return {"success": False, "error": f"请求失败: {str(e)}"}
    
    except Exception as e:
        return {"success": False, "error": f"未知错误: {str(e)}"}

# 使用示例
result = safe_api_call("http://localhost:8020/api/chat", method="POST", 
                       json={"message": "测试", "user_id": "user1"})

if result['success']:
    print("✅ 调用成功:", result['data'])
else:
    print("❌ 调用失败:", result['error'])
```

---

## 📊 数据分析示例

### 分析ERP绩效数据

```python
import requests
from datetime import datetime, timedelta

# 获取最近30天的数据
end_date = datetime.now().strftime('%Y-%m-%d')
start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

# 1. 获取交付绩效
delivery_url = f"http://localhost:8013/api/erp/delivery/performance?start_date={start_date}&end_date={end_date}"
delivery_data = requests.get(delivery_url).json()

# 2. 获取采购分析
procurement_url = f"http://localhost:8013/api/erp/procurement/analysis?start_date={start_date}&end_date={end_date}"
procurement_data = requests.get(procurement_url).json()

# 3. 生成分析报告
print("\n📊 最近30天ERP绩效分析")
print("=" * 60)

print(f"\n交付绩效:")
print(f"  总计划数: {delivery_data['summary']['total_plans']}")
print(f"  准时率: {delivery_data['summary']['on_time_rate']}%")
print(f"  验收通过率: {delivery_data['acceptance']['acceptance_rate']}%")

print(f"\n采购绩效:")
print(f"  总订单数: {procurement_data['summary']['total_orders']}")
print(f"  总金额: ¥{procurement_data['summary']['total_amount']:,.2f}")
print(f"  准时交货率: {procurement_data['performance']['on_time_delivery_rate']}%")

print("\n" + "=" * 60)
```

---

## 🎯 最佳实践

### 1. 使用连接池

```python
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# 配置重试策略
retry_strategy = Retry(
    total=3,
    status_forcelist=[429, 500, 502, 503, 504],
    method_whitelist=["HEAD", "GET", "OPTIONS", "POST"]
)

adapter = HTTPAdapter(max_retries=retry_strategy)
session = requests.Session()
session.mount("http://", adapter)
session.mount("https://", adapter)

# 使用session进行请求
response = session.post("http://localhost:8020/api/chat", 
                       json={"message": "测试"})
```

### 2. 设置超时

```python
# 推荐设置超时时间
response = requests.get("http://localhost:8011/api/search", timeout=10)
```

### 3. 批量请求优化

```python
import requests
from concurrent.futures import ThreadPoolExecutor

def create_customer(customer_data):
    """创建单个客户"""
    url = "http://localhost:8013/api/customer/create"
    return requests.post(url, json=customer_data)

# 批量数据
customers = [
    {"customer_id": f"CUST{i:03d}", "name": f"客户{i}"}
    for i in range(1, 101)
]

# 使用线程池并行处理
with ThreadPoolExecutor(max_workers=10) as executor:
    results = list(executor.map(create_customer, customers))

success_count = sum(1 for r in results if r.json().get('success'))
print(f"✅ 成功创建: {success_count}/{len(customers)}")
```

---

## 💡 调试技巧

### 1. 启用详细日志

```python
import requests
import logging

# 启用调试日志
logging.basicConfig(level=logging.DEBUG)

response = requests.get("http://localhost:8020/health")
```

### 2. 查看响应头

```python
response = requests.get("http://localhost:8020/api/chat")

print("响应头:")
for key, value in response.headers.items():
    print(f"  {key}: {value}")
```

### 3. 保存响应到文件

```python
response = requests.get("http://localhost:8011/api/documents")

with open("api_response.json", "w") as f:
    f.write(response.text)
```

---

## 📚 更多资源

- 完整API文档: [📚完整API文档汇总.md](📚完整API文档汇总.md)
- 快速入门: [🎯快速入门教程.md](🎯快速入门教程.md)
- 开发者指南: [📖开发者指南.md](📖开发者指南.md)

---

**最后更新**: 2025-11-06  
**维护者**: AI-Stack Team

