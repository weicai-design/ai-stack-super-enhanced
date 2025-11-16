"""客户管理模块（CRM）"""
import logging
from typing import Dict, List, Optional
from datetime import datetime
from ..models import Customer

logger = logging.getLogger(__name__)

class CustomerManager:
    """客户管理器"""
    
    def __init__(self):
        self.customers: Dict[str, List[Customer]] = {}
    
    def add_customer(self, tenant_id: str, customer: Customer) -> Customer:
        """添加客户"""
        if tenant_id not in self.customers:
            self.customers[tenant_id] = []
        customer.tenant_id = tenant_id
        self.customers[tenant_id].append(customer)
        logger.info(f"客户已添加: {customer.name}")
        return customer
    
    def get_customers(self, tenant_id: str, filters: Optional[Dict] = None) -> List[Customer]:
        """获取客户列表"""
        customers = self.customers.get(tenant_id, [])
        if filters:
            if "industry" in filters:
                customers = [c for c in customers if c.industry == filters["industry"]]
            if "credit_level" in filters:
                customers = [c for c in customers if c.credit_level == filters["credit_level"]]
        return customers
    
    def search_customers(self, tenant_id: str, keyword: str) -> List[Customer]:
        """搜索客户"""
        customers = self.customers.get(tenant_id, [])
        keyword_lower = keyword.lower()
        return [c for c in customers if keyword_lower in c.name.lower() or 
                (c.contact_person and keyword_lower in c.contact_person.lower())]

customer_manager = CustomerManager()






















