#!/usr/bin/env python3
"""
AI Stack Super Enhanced - 使用示例生成器
为每个API创建使用示例和测试脚本
"""

import json

examples = {
    "ERP系统": {
        "财务数据查询": {
            "url": "http://localhost:8013/api/finance/dashboard",
            "method": "GET",
            "params": {"period_type": "monthly"},
            "curl": 'curl "http://localhost:8013/api/finance/dashboard?period_type=monthly"',
            "description": "获取月度财务看板数据"
        },
        "创建财务记录": {
            "url": "http://localhost:8013/api/finance/data",
            "method": "POST",
            "body": {
                "date": "2025-11-04",
                "category": "revenue",
                "amount": 50000,
                "description": "测试收入"
            },
            "curl": '''curl -X POST http://localhost:8013/api/finance/data \\
  -H "Content-Type: application/json" \\
  -d '{
    "date": "2025-11-04",
    "category": "revenue",
    "amount": 50000,
    "description": "测试收入"
  }'
''',
            "description": "创建新的财务记录"
        }
    },
    "股票系统": {
        "获取股票列表": {
            "url": "http://localhost:8014/api/stocks/list",
            "method": "GET",
            "curl": 'curl "http://localhost:8014/api/stocks/list"',
            "description": "获取所有股票列表"
        },
        "获取实时行情": {
            "url": "http://localhost:8014/api/stocks/realtime/AAPL",
            "method": "GET",
            "curl": 'curl "http://localhost:8014/api/stocks/realtime/AAPL"',
            "description": "获取苹果股票实时行情"
        }
    },
    "RAG系统": {
        "上传文档": {
            "url": "http://localhost:8011/rag/ingest",
            "method": "POST",
            "curl": '''curl -X POST http://localhost:8011/rag/ingest \\
  -H "Content-Type: application/json" \\
  -d '{
    "text": "这是一个测试文档",
    "metadata": {"source": "test"}
  }'
''',
            "description": "上传文本到RAG知识库"
        },
        "检索文档": {
            "url": "http://localhost:8011/rag/retrieve",
            "method": "POST",
            "body": {"query": "测试查询", "limit": 5},
            "curl": '''curl -X POST http://localhost:8011/rag/retrieve \\
  -H "Content-Type: application/json" \\
  -d '{
    "query": "测试查询",
    "limit": 5
  }'
''',
            "description": "从知识库检索相关文档"
        }
    }
}

def generate_markdown():
    """生成Markdown格式的使用示例"""
    md = "# 🚀 AI Stack Super Enhanced - API使用示例\n\n"
    md += "**生成时间**: 2025-11-04\n\n"
    md += "---\n\n"
    
    for system, apis in examples.items():
        md += f"## 📌 {system}\n\n"
        
        for api_name, details in apis.items():
            md += f"### {api_name}\n\n"
            md += f"**描述**: {details['description']}\n\n"
            md += f"**URL**: `{details['url']}`  \n"
            md += f"**方法**: `{details['method']}`\n\n"
            
            if 'params' in details:
                md += f"**参数**: \n```json\n{json.dumps(details['params'], indent=2, ensure_ascii=False)}\n```\n\n"
            
            if 'body' in details:
                md += f"**请求体**: \n```json\n{json.dumps(details['body'], indent=2, ensure_ascii=False)}\n```\n\n"
            
            md += f"**Curl命令**:\n```bash\n{details['curl']}\n```\n\n"
            md += "---\n\n"
    
    return md

def main():
    # 生成Markdown文档
    markdown = generate_markdown()
    
    # 保存到文件
    with open('/Users/ywc/ai-stack-super-enhanced/API使用示例.md', 'w', encoding='utf-8') as f:
        f.write(markdown)
    
    print("✅ API使用示例已生成: API使用示例.md")
    
    # 打印快速参考
    print("\n📋 快速参考:")
    print("=" * 60)
    for system, apis in examples.items():
        print(f"\n{system}:")
        for api_name, details in apis.items():
            print(f"  • {api_name}: {details['method']} {details['url']}")

if __name__ == "__main__":
    main()

