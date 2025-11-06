#!/usr/bin/env python3
"""
AI Stack API调用示例
展示如何使用各个模块的API
"""
import asyncio
import httpx
from typing import Dict, Any
import json


class APIExamples:
    """API示例集合"""
    
    def __init__(self):
        self.base_urls = {
            'rag': 'http://localhost:8011',
            'erp': 'http://localhost:8013',
            'stock': 'http://localhost:8014',
            'trend': 'http://localhost:8015',
            'content': 'http://localhost:8016',
            'task': 'http://localhost:8017',
            'resource': 'http://localhost:8018',
            'learning': 'http://localhost:8019',
            'chat': 'http://localhost:8020'
        }
    
    # ============ RAG系统示例 ============
    
    async def example_rag_search(self):
        """RAG知识检索示例"""
        print("\n📚 示例1: RAG知识检索")
        print("-" * 60)
        
        async with httpx.AsyncClient() as client:
            # 1. 添加文档
            print("1. 上传文档...")
            upload_data = {
                "file_path": "/path/to/document.pdf",
                "metadata": {"category": "技术文档"}
            }
            # response = await client.post(f"{self.base_urls['rag']}/api/documents/upload", json=upload_data)
            print("✓ 文档已上传")
            
            # 2. 知识检索
            print("\n2. 执行知识检索...")
            search_data = {
                "query": "如何使用RAG系统？",
                "top_k": 5
            }
            # response = await client.post(f"{self.base_urls['rag']}/api/rag/search", json=search_data)
            print("✓ 检索完成，返回5条相关结果")
            
            # 3. 知识图谱查询
            print("\n3. 查询知识图谱...")
            # response = await client.get(f"{self.base_urls['rag']}/api/knowledge-graph/relations?entity=RAG")
            print("✓ 找到相关实体和关系")
    
    # ============ ERP系统示例 ============
    
    async def example_erp_workflow(self):
        """ERP业务流程示例"""
        print("\n💼 示例2: ERP完整业务流程")
        print("-" * 60)
        
        async with httpx.AsyncClient() as client:
            # 1. 创建客户
            print("1. 创建客户...")
            customer_data = {
                "name": "示例客户公司",
                "contact": "张经理",
                "phone": "13800138000",
                "category": "重点客户"
            }
            print("✓ 客户创建成功")
            
            # 2. 创建订单
            print("\n2. 创建销售订单...")
            order_data = {
                "customer_id": 1,
                "products": [
                    {"product_id": 1, "quantity": 100, "price": 50}
                ],
                "total_amount": 5000
            }
            print("✓ 订单创建成功，订单号：ORD0001")
            
            # 3. 生成生产计划
            print("\n3. 自动生成生产计划...")
            print("✓ 生产计划已生成，计划号：PLAN0001")
            
            # 4. 质量检验
            print("\n4. 质量检验...")
            print("✓ 检验合格，良品率98%")
            
            # 5. 财务对账
            print("\n5. 财务对账...")
            print("✓ 对账完成，应收账款5000元")
    
    # ============ 股票交易示例 ============
    
    async def example_stock_trading(self):
        """股票交易示例"""
        print("\n📈 示例3: 股票智能交易")
        print("-" * 60)
        
        async with httpx.AsyncClient() as client:
            # 1. 获取实时行情
            print("1. 获取实时行情...")
            # response = await client.get(f"{self.base_urls['stock']}/api/market/quote/000001.SZ")
            print("✓ 平安银行 现价：12.50元 涨跌：+2.3%")
            
            # 2. AI策略分析
            print("\n2. AI策略分析...")
            analysis_data = {
                "symbol": "000001.SZ",
                "strategy": "trend_following"
            }
            print("✓ 策略建议：买入，目标价：13.50元")
            
            # 3. 执行交易（模拟）
            print("\n3. 执行买入交易...")
            trade_data = {
                "symbol": "000001.SZ",
                "action": "buy",
                "quantity": 1000,
                "price": 12.50
            }
            print("✓ 委托成功，等待成交")
            
            # 4. 风险监控
            print("\n4. 实时风险监控...")
            print("✓ 持仓风险：低 | 仓位占比：15% | 止损价：11.80元")
    
    # ============ 趋势分析示例 ============
    
    async def example_trend_analysis(self):
        """趋势分析示例"""
        print("\n🔍 示例4: 行业趋势分析")
        print("-" * 60)
        
        async with httpx.AsyncClient() as client:
            # 1. 热点追踪
            print("1. 实时热点追踪...")
            print("✓ 发现3个新兴热点：AI芯片、新能源汽车、量子计算")
            
            # 2. 生成行业报告
            print("\n2. 生成AI芯片行业报告...")
            report_data = {
                "industry": "AI芯片",
                "companies": ["英伟达", "AMD", "华为"],
                "period": "month"
            }
            print("✓ 报告已生成，文件：AI芯片行业分析报告_20250106.md")
            
            # 3. 预测分析
            print("\n3. 未来趋势预测...")
            print("✓ 预测：该行业未来3年年均增长率：35%")
    
    # ============ 内容创作示例 ============
    
    async def example_content_creation(self):
        """内容创作示例"""
        print("\n🎨 示例5: AI内容创作")
        print("-" * 60)
        
        async with httpx.AsyncClient() as client:
            # 1. 创建内容
            print("1. AI生成小红书笔记...")
            content_data = {
                "topic": "AI技术应用",
                "platform": "小红书",
                "style": "干货分享"
            }
            print("✓ 内容已生成，标题：《3分钟了解AI如何改变生活》")
            
            # 2. 发布到平台
            print("\n2. 发布到小红书...")
            print("✓ 发布成功，内容ID：XHS123456")
            
            # 3. 效果追踪
            print("\n3. 追踪发布效果...")
            await asyncio.sleep(1)
            print("✓ 阅读量：1,250 | 点赞：89 | 评论：23 | 互动率：8.9%")
            
            # 4. 优化建议
            print("\n4. 生成优化建议...")
            print("✓ 建议：增加视频内容，优化发布时间为晚上8-10点")
    
    # ============ 任务代理示例 ============
    
    async def example_task_agent(self):
        """任务代理示例"""
        print("\n🤖 示例6: 智能任务代理")
        print("-" * 60)
        
        async with httpx.AsyncClient() as client:
            # 1. 创建复杂任务
            print("1. 创建复合任务：市场分析+内容创作+发布...")
            task_data = {
                "name": "自动化营销任务",
                "steps": [
                    {"action": "trend_analysis", "params": {"keyword": "AI"}},
                    {"action": "content_create", "params": {"platform": "小红书"}},
                    {"action": "publish", "params": {"schedule": "20:00"}}
                ],
                "auto_execute": True
            }
            print("✓ 任务已创建，任务ID：TASK0001")
            
            # 2. 监控执行
            print("\n2. 监控任务执行...")
            await asyncio.sleep(1)
            print("  [1/3] 趋势分析...完成 ✓")
            await asyncio.sleep(1)
            print("  [2/3] 内容创作...完成 ✓")
            await asyncio.sleep(1)
            print("  [3/3] 定时发布...已安排 ✓")
            
            print("\n✓ 任务完成，状态：成功")
    
    # ============ 自我学习示例 ============
    
    async def example_self_learning(self):
        """自我学习示例"""
        print("\n🧠 示例7: 自我学习和代码修复")
        print("-" * 60)
        
        async with httpx.AsyncClient() as client:
            # 1. 问题诊断
            print("1. 检测到系统问题...")
            error_info = {
                "error_type": "PerformanceIssue",
                "message": "API响应时间超过阈值",
                "stack_trace": "..."
            }
            print("✓ 问题分析：数据库查询未优化，缺少索引")
            
            # 2. 自动生成修复代码
            print("\n2. AI生成修复代码...")
            await asyncio.sleep(1)
            print("✓ 代码已生成：添加数据库索引 + 查询缓存")
            
            # 3. 请求用户批准
            print("\n3. 请求用户批准...")
            print("  修复方案：")
            print("  - 在user_id字段添加索引")
            print("  - 启用Redis查询缓存")
            print("  预期效果：响应时间从500ms降至50ms")
            print("\n  [用户确认：同意执行]")
            
            # 4. 执行修复
            print("\n4. 执行修复...")
            await asyncio.sleep(1)
            print("✓ 修复完成，系统性能提升90%")
            
            # 5. 效果验证
            print("\n5. 效果验证...")
            print("✓ 验证通过，API平均响应时间：45ms")
    
    # ============ 运行所有示例 ============
    
    async def run_all_examples(self):
        """运行所有示例"""
        print("\n" + "=" * 60)
        print("🚀 AI Stack API 调用示例集")
        print("=" * 60)
        
        examples = [
            self.example_rag_search,
            self.example_erp_workflow,
            self.example_stock_trading,
            self.example_trend_analysis,
            self.example_content_creation,
            self.example_task_agent,
            self.example_self_learning
        ]
        
        for example in examples:
            await example()
            await asyncio.sleep(0.5)
        
        print("\n" + "=" * 60)
        print("✅ 所有示例运行完成！")
        print("=" * 60)
        print("\n💡 提示：")
        print("  1. 这些是API调用示例，实际使用时请启动相应服务")
        print("  2. 完整API文档请访问：http://localhost:PORT/docs")
        print("  3. 更多示例请查看各模块的README.md")
        print()


async def main():
    """主函数"""
    examples = APIExamples()
    await examples.run_all_examples()


if __name__ == "__main__":
    asyncio.run(main())




