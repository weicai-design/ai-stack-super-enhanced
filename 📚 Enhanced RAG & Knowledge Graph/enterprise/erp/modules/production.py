"""生产管理模块"""
import logging
from typing import Dict, List, Optional
from ..models import Production, Material

logger = logging.getLogger(__name__)

class ProductionManager:
    """生产管理器"""
    
    def __init__(self):
        self.productions: Dict[str, List[Production]] = {}
        self.materials: Dict[str, List[Material]] = {}
    
    def create_production_plan(self, tenant_id: str, production: Production) -> Production:
        """创建生产计划"""
        if tenant_id not in self.productions:
            self.productions[tenant_id] = []
        production.tenant_id = tenant_id
        self.productions[tenant_id].append(production)
        logger.info(f"生产计划已创建: {production.product_name}")
        return production
    
    def update_production_progress(
        self,
        tenant_id: str,
        production_id: str,
        actual_quantity: int,
        status: str
    ) -> Optional[Production]:
        """更新生产进度"""
        for prod in self.productions.get(tenant_id, []):
            if prod.id == production_id:
                prod.actual_quantity = actual_quantity
                prod.status = status
                logger.info(f"生产进度已更新: {prod.product_name}")
                return prod
        return None
    
    def manage_material(self, tenant_id: str, material: Material) -> Material:
        """管理物料"""
        if tenant_id not in self.materials:
            self.materials[tenant_id] = []
        material.tenant_id = tenant_id
        self.materials[tenant_id].append(material)
        return material
    
    def check_material_shortage(self, tenant_id: str) -> List[Material]:
        """检查物料短缺"""
        materials = self.materials.get(tenant_id, [])
        return [m for m in materials if m.quantity < m.min_stock]

production_manager = ProductionManager()



























