"""
工厂数据源模块
"""

from typing import Dict, Any, Optional


class FactoryDataSource:
    """工厂数据源"""
    
    def __init__(self):
        self.data = {}
    
    def get_factory_data(self, factory_id: str) -> Optional[Dict[str, Any]]:
        """获取工厂数据"""
        return {
            "factory_id": factory_id,
            "name": "Demo Factory",
            "status": "active",
            "production_capacity": 1000
        }