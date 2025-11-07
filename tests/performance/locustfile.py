"""
Locust负载测试文件
用于模拟大量用户并发访问
"""

from locust import HttpUser, task, between
import random


class AIStackUser(HttpUser):
    """AI Stack用户行为模拟"""
    
    # 用户等待时间（秒）
    wait_time = between(1, 3)
    
    def on_start(self):
        """用户启动时执行"""
        # 可以在这里进行登录等初始化操作
        pass
    
    @task(10)
    def health_check(self):
        """健康检查（高频）"""
        self.client.get("/health")
    
    @task(5)
    def search_knowledge(self):
        """搜索知识库"""
        queries = ["AI", "机器学习", "数据分析", "企业管理", "股票"]
        query = random.choice(queries)
        
        self.client.get(f"/rag/search?query={query}&top_k=5")
    
    @task(3)
    def get_financial_summary(self):
        """获取财务概览"""
        self.client.get("/api/finance/summary")
    
    @task(2)
    def list_customers(self):
        """列出客户"""
        self.client.get("/api/customers?page=1&size=20")
    
    @task(2)
    def list_orders(self):
        """列出订单"""
        self.client.get("/api/orders?page=1&size=20")
    
    @task(1)
    def create_order(self):
        """创建订单（低频）"""
        order_data = {
            "customer_id": random.randint(1, 100),
            "product": "测试产品",
            "quantity": random.randint(10, 100),
            "unit_price": random.uniform(10, 1000)
        }
        
        self.client.post("/api/orders", json=order_data)
    
    @task(1)
    def ingest_document(self):
        """文档摄入（低频）"""
        doc_data = {
            "text": "这是一段测试文本，用于负载测试。" * 10,
            "metadata": {"source": "load_test"}
        }
        
        self.client.post("/rag/ingest/text", json=doc_data)


class ERPUser(HttpUser):
    """ERP系统用户"""
    
    host = "http://localhost:8013"
    wait_time = between(2, 5)
    
    @task(5)
    def view_dashboard(self):
        """查看仪表板"""
        self.client.get("/api/finance/summary")
    
    @task(3)
    def manage_customers(self):
        """管理客户"""
        self.client.get("/api/customers")
    
    @task(2)
    def manage_orders(self):
        """管理订单"""
        self.client.get("/api/orders")


class RAGUser(HttpUser):
    """RAG系统用户"""
    
    host = "http://localhost:8011"
    wait_time = between(1, 2)
    
    @task(8)
    def search(self):
        """搜索"""
        queries = ["技术", "管理", "分析", "系统", "优化"]
        query = random.choice(queries)
        
        self.client.get(f"/rag/search?query={query}&top_k=5")
    
    @task(2)
    def ingest(self):
        """摄入"""
        text = "测试文本" * random.randint(10, 100)
        self.client.post("/rag/ingest/text", json={"text": text})

