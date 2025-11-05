"""
OpenWebUI ERP Integration Plugin
OpenWebUI ERP集成插件

功能：
1. 从聊天框查询ERP数据
2. 从聊天框创建订单/客户
3. 查看财务报表
4. 查询流程状态
"""

import requests
import json
import re
from typing import Optional, Dict, Any
from datetime import datetime, date


class ERPIntegrationPlugin:
    """ERP集成插件"""
    
    def __init__(self, erp_api_url: str = "http://localhost:8013"):
        """
        初始化ERP集成插件
        
        Args:
            erp_api_url: ERP API地址
        """
        self.erp_api_url = erp_api_url
        self.enabled = True
    
    def parse_intent(self, message: str) -> Optional[Dict[str, Any]]:
        """
        解析用户意图
        
        识别用户是否在查询ERP相关信息
        
        Args:
            message: 用户消息
            
        Returns:
            意图信息
        """
        message_lower = message.lower()
        
        # 财务查询意图
        if any(keyword in message_lower for keyword in ['财务', '收入', '支出', '利润', '看板']):
            return {
                "type": "finance_query",
                "keywords": ['财务', '收入', '支出', '利润']
            }
        
        # 订单查询意图
        if any(keyword in message_lower for keyword in ['订单', 'order', '订单数量']):
            return {
                "type": "order_query",
                "keywords": ['订单']
            }
        
        # 客户查询意图
        if any(keyword in message_lower for keyword in ['客户', 'customer', 'vip']):
            return {
                "type": "customer_query",
                "keywords": ['客户']
            }
        
        # 流程查询意图
        if any(keyword in message_lower for keyword in ['流程', '进度', 'process']):
            return {
                "type": "process_query",
                "keywords": ['流程', '进度']
            }
        
        return None
    
    async def get_finance_dashboard(
        self,
        period_type: str = "monthly"
    ) -> Dict[str, Any]:
        """
        获取财务看板数据
        
        Args:
            period_type: 周期类型
            
        Returns:
            财务看板数据
        """
        try:
            response = requests.get(
                f"{self.erp_api_url}/api/finance/dashboard",
                params={"period_type": period_type},
                timeout=5
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": "获取财务数据失败"}
                
        except Exception as e:
            return {"error": f"API调用异常: {str(e)}"}
    
    async def query_orders(
        self,
        status: Optional[str] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        查询订单信息
        
        Args:
            status: 订单状态
            limit: 返回数量
            
        Returns:
            订单列表
        """
        try:
            params = {"limit": limit}
            if status:
                params["status"] = status
            
            response = requests.get(
                f"{self.erp_api_url}/api/business/orders",
                params=params,
                timeout=5
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": "获取订单数据失败"}
                
        except Exception as e:
            return {"error": f"API调用异常: {str(e)}"}
    
    async def query_customers(
        self,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        查询客户信息
        
        Args:
            category: 客户类别
            
        Returns:
            客户列表
        """
        try:
            params = {}
            if category:
                params["category"] = category
            
            response = requests.get(
                f"{self.erp_api_url}/api/business/customers",
                params=params,
                timeout=5
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": "获取客户数据失败"}
                
        except Exception as e:
            return {"error": f"API调用异常: {str(e)}"}
    
    async def handle_user_query(
        self,
        message: str,
        user_id: str
    ) -> Optional[str]:
        """
        处理用户查询
        
        自动识别并响应ERP相关查询
        
        Args:
            message: 用户消息
            user_id: 用户ID
            
        Returns:
            自动回复内容（如果适用）
        """
        if not self.enabled:
            return None
        
        # 解析意图
        intent = self.parse_intent(message)
        if not intent:
            return None
        
        # 根据意图类型处理
        if intent["type"] == "finance_query":
            # 获取财务数据
            data = await self.get_finance_dashboard()
            if "error" not in data:
                return self._format_finance_response(data)
        
        elif intent["type"] == "order_query":
            # 获取订单数据
            data = await self.query_orders()
            if "error" not in data:
                return self._format_order_response(data)
        
        elif intent["type"] == "customer_query":
            # 获取客户数据
            data = await self.query_customers()
            if "error" not in data:
                return self._format_customer_response(data)
        
        return None
    
    def _format_finance_response(self, data: Dict[str, Any]) -> str:
        """格式化财务数据响应"""
        return f"""
📊 **本月财务概况**

💰 收入：¥ {data.get('revenue', 0):,.2f}
💸 支出：¥ {data.get('expense', 0):,.2f}
📈 利润：¥ {data.get('profit', 0):,.2f}
🏦 资产：¥ {data.get('assets', 0):,.2f}

📅 统计周期：{data.get('start_date')} 至 {data.get('end_date')}

更多详情请访问：http://localhost:8012/finance/dashboard
"""
    
    def _format_order_response(self, data: Dict[str, Any]) -> str:
        """格式化订单数据响应"""
        orders = data.get('orders', [])
        total = len(orders)
        
        response = f"📦 **订单统计**\n\n"
        response += f"订单总数：{total} 个\n\n"
        
        if orders:
            response += "最近订单：\n"
            for order in orders[:5]:
                response += f"- {order.get('order_number')}: ¥{order.get('total_amount', 0):,.2f} ({order.get('status')})\n"
        
        response += f"\n更多详情请访问：http://localhost:8012/business/orders"
        return response
    
    def _format_customer_response(self, data: Dict[str, Any]) -> str:
        """格式化客户数据响应"""
        customers = data.get('customers', [])
        total = len(customers)
        
        # 按类别统计
        vip = len([c for c in customers if c.get('category') == 'VIP'])
        normal = len([c for c in customers if c.get('category') == '普通'])
        new_customers = len([c for c in customers if c.get('category') == '新客户'])
        
        return f"""
👥 **客户统计**

客户总数：{total} 个
  - VIP客户：{vip} 个
  - 普通客户：{normal} 个
  - 新客户：{new_customers} 个

更多详情请访问：http://localhost:8012/business/customers
"""
    
    def get_status(self) -> Dict[str, Any]:
        """获取插件状态"""
        try:
            response = requests.get(
                f"{self.erp_api_url}/health",
                timeout=2
            )
            
            return {
                "enabled": self.enabled,
                "erp_api": self.erp_api_url,
                "erp_status": "online" if response.status_code == 200 else "offline",
                "version": "1.0.0"
            }
        except:
            return {
                "enabled": self.enabled,
                "erp_api": self.erp_api_url,
                "erp_status": "offline",
                "version": "1.0.0"
            }


# 全局插件实例
erp_plugin = ERPIntegrationPlugin()


# OpenWebUI插件接口
async def on_startup():
    """插件启动"""
    print("🚀 ERP集成插件已启动")
    status = erp_plugin.get_status()
    print(f"📊 ERP状态: {status}")


async def inlet(body: dict, __user__: dict) -> dict:
    """请求前处理 - 识别ERP查询"""
    messages = body.get("messages", [])
    if not messages:
        return body
    
    last_message = messages[-1]
    user_query = last_message.get("content", "")
    
    # 处理ERP查询
    auto_response = await erp_plugin.handle_user_query(
        message=user_query,
        user_id=__user__.get("id", "")
    )
    
    # 如果有自动回复，添加到消息
    if auto_response:
        system_message = {
            "role": "system",
            "content": f"[ERP系统数据]\n{auto_response}"
        }
        body["messages"].insert(-1, system_message)
    
    return body

