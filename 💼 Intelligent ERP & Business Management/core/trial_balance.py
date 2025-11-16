"""
试算功能
计算达到目标需要的每日交付量等
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from decimal import Decimal

class TrialBalanceCalculator:
    """
    试算功能计算器
    
    功能：
    1. 试算达到周目标需要的每日交付量
    2. 自定义输入口
    3. 从ERP调取关联数据
    4. 试算结果展示
    """
    
    def __init__(self, erp_data_source=None):
        self.erp_data_source = erp_data_source
    
    async def calculate_daily_delivery(
        self,
        target_weekly_revenue: float,
        product_id: Optional[int] = None,
        product_code: Optional[str] = None,
        order_id: Optional[str] = None,
        start_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        试算达到周目标需要的每日交付量
        
        Args:
            target_weekly_revenue: 周目标营业额
            product_id: 产品ID（可选）
            start_date: 开始日期（可选）
            
        Returns:
            试算结果
        """
        # 从ERP获取关联数据
        product_data = await self._fetch_product_data(
            product_id=product_id,
            product_code=product_code,
            order_id=order_id
        )
        historical_data = await self._fetch_historical_delivery_data(
            product_id=product_id,
            product_code=product_code,
            order_id=order_id
        )
        
        # 获取产品单价
        unit_price = product_data.get("unit_price", 100.0)
        resolved_order_id = product_data.get("resolved_order_id")
        
        # 计算需要的总交付量
        total_quantity_needed = target_weekly_revenue / unit_price
        
        # 计算每日交付量（根据承诺交付窗口自动调整工作日）
        working_days = self._determine_working_days(product_data, start_date)
        daily_quantity = total_quantity_needed / working_days
        
        # 分析历史数据
        avg_daily = self._calculate_average_daily(historical_data)
        max_daily = self._calculate_max_daily(historical_data)
        
        # 可行性分析
        feasibility = self._analyze_feasibility(daily_quantity, avg_daily, max_daily)
        
        return {
            "target_weekly_revenue": target_weekly_revenue,
            "unit_price": unit_price,
            "total_quantity_needed": round(total_quantity_needed, 2),
            "daily_quantity": round(daily_quantity, 2),
            "working_days": working_days,
            "historical_average": round(avg_daily, 2),
            "historical_max": round(max_daily, 2),
            "feasibility": feasibility,
            "order_context": self._build_order_context(product_data),
            "historical_series": historical_data[:10],
            "recommendations": self._generate_recommendations(
                daily_quantity, avg_daily, max_daily
            ),
            "source_order_id": resolved_order_id,
            "calculated_at": datetime.now().isoformat()
        }
    
    async def custom_trial_calculation(
        self,
        calculation_type: str,
        target_value: float,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        自定义试算
        
        Args:
            calculation_type: 计算类型（如：daily_delivery, production_capacity等）
            target_value: 目标值
            parameters: 自定义参数
            
        Returns:
            试算结果
        """
        if calculation_type == "daily_delivery":
            return await self.calculate_daily_delivery(
                target_weekly_revenue=target_value,
                product_id=parameters.get("product_id"),
                product_code=parameters.get("product_code"),
                order_id=parameters.get("order_id"),
                start_date=parameters.get("start_date")
            )
        elif calculation_type == "production_capacity":
            return await self._calculate_production_capacity(target_value, parameters)
        elif calculation_type == "cost_breakdown":
            return await self._calculate_cost_breakdown(target_value, parameters)
        else:
            return {
                "success": False,
                "error": f"不支持的计算类型: {calculation_type}"
            }
    
    def _calculate_average_daily(self, historical_data: List[Dict]) -> float:
        """计算历史平均每日交付量"""
        if not historical_data:
            return 0.0
        
        total = sum(item.get("quantity", 0) for item in historical_data)
        return total / len(historical_data) if historical_data else 0.0
    
    def _calculate_max_daily(self, historical_data: List[Dict]) -> float:
        """计算历史最大每日交付量"""
        if not historical_data:
            return 0.0
        
        return max((item.get("quantity", 0) for item in historical_data), default=0.0)
    
    def _analyze_feasibility(
        self,
        required_daily: float,
        avg_daily: float,
        max_daily: float
    ) -> Dict[str, Any]:
        """分析可行性"""
        if required_daily <= avg_daily:
            feasibility_level = "easy"
            feasibility_score = 100
        elif required_daily <= max_daily:
            feasibility_level = "moderate"
            feasibility_score = 70
        elif required_daily <= max_daily * 1.2:
            feasibility_level = "challenging"
            feasibility_score = 50
        else:
            feasibility_level = "difficult"
            feasibility_score = 30
        
        return {
            "level": feasibility_level,
            "score": feasibility_score,
            "required_vs_avg": round(required_daily / avg_daily, 2) if avg_daily > 0 else 0,
            "required_vs_max": round(required_daily / max_daily, 2) if max_daily > 0 else 0
        }
    
    def _generate_recommendations(
        self,
        required_daily: float,
        avg_daily: float,
        max_daily: float
    ) -> List[str]:
        """生成建议"""
        recommendations = []
        
        if required_daily > max_daily:
            recommendations.append("目标交付量超过历史最大值，建议：")
            recommendations.append("1. 增加生产产能")
            recommendations.append("2. 提前备货")
            recommendations.append("3. 考虑外包部分生产")
        elif required_daily > avg_daily:
            recommendations.append("目标交付量高于平均水平，建议：")
            recommendations.append("1. 优化生产流程")
            recommendations.append("2. 增加工作时间")
            recommendations.append("3. 提高生产效率")
        else:
            recommendations.append("目标交付量在可达成范围内")
        
        return recommendations

    async def _fetch_product_data(
        self,
        product_id: Optional[int],
        product_code: Optional[str],
        order_id: Optional[str]
    ) -> Dict[str, Any]:
        if not self.erp_data_source:
            return {}

        legacy_identifier = str(product_id) if product_id is not None else None
        return await self.erp_data_source.get_product_data(
            order_id=order_id,
            product_code=product_code,
            legacy_identifier=legacy_identifier
        )

    async def _fetch_historical_delivery_data(
        self,
        product_id: Optional[int],
        product_code: Optional[str],
        order_id: Optional[str],
        days: int = 30
    ) -> List[Dict[str, Any]]:
        if not self.erp_data_source:
            return []

        legacy_identifier = str(product_id) if product_id is not None else None
        return await self.erp_data_source.get_historical_delivery_data(
            order_id=order_id,
            product_code=product_code,
            legacy_identifier=legacy_identifier,
            days=days
        )

    def _determine_working_days(
        self,
        product_data: Dict[str, Any],
        start_date: Optional[str]
    ) -> int:
        default_days = 5
        if not product_data:
            return default_days

        try:
            if start_date:
                start = datetime.fromisoformat(start_date).date()
            else:
                start = datetime.now().date()
        except ValueError:
            start = datetime.now().date()

        promise = product_data.get("promise_date")
        available_days = product_data.get("available_days")

        if promise:
            try:
                promise_date = datetime.fromisoformat(str(promise)).date()
                delta_days = max((promise_date - start).days, 1)
                return max(delta_days, 1)
            except ValueError:
                pass

        if available_days:
            return max(int(available_days), 1)

        window = product_data.get("order_window_days")
        if window:
            return max(int(window), 1)

        return default_days

    def _build_order_context(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        if not product_data:
            return {}

        return {
            "order_id": product_data.get("order_id"),
            "product_code": product_data.get("product_code"),
            "product_name": product_data.get("product_name"),
            "customer": product_data.get("customer"),
            "priority": product_data.get("priority"),
            "status": product_data.get("status"),
            "promise_date": product_data.get("promise_date"),
            "requested_date": product_data.get("requested_date"),
        }
    
    async def _calculate_production_capacity(
        self,
        target_value: float,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        计算生产产能
        
        Args:
            target_value: 目标产量
            parameters: 参数
                - production_line_count: 生产线数量
                - hours_per_day: 每天工作小时数
                - days_per_week: 每周工作天数
                - unit_time_minutes: 单位产品生产时间（分钟）
                - efficiency_rate: 效率系数（0-1）
        
        Returns:
            生产产能计算结果
        """
        production_line_count = parameters.get("production_line_count", 1)
        hours_per_day = parameters.get("hours_per_day", 8)
        days_per_week = parameters.get("days_per_week", 5)
        unit_time_minutes = parameters.get("unit_time_minutes", 60)
        efficiency_rate = parameters.get("efficiency_rate", 0.85)
        
        # 计算单条生产线日产能
        minutes_per_day = hours_per_day * 60
        units_per_line_per_day = (minutes_per_day / unit_time_minutes) * efficiency_rate
        
        # 计算总日产能
        total_daily_capacity = units_per_line_per_day * production_line_count
        
        # 计算周产能
        weekly_capacity = total_daily_capacity * days_per_week
        
        # 计算达到目标需要的天数
        days_needed = target_value / total_daily_capacity if total_daily_capacity > 0 else 0
        
        # 计算产能利用率
        capacity_utilization = (target_value / weekly_capacity * 100) if weekly_capacity > 0 else 0
        
        return {
            "target_quantity": target_value,
            "production_line_count": production_line_count,
            "daily_capacity_per_line": round(units_per_line_per_day, 2),
            "total_daily_capacity": round(total_daily_capacity, 2),
            "weekly_capacity": round(weekly_capacity, 2),
            "days_needed": round(days_needed, 2),
            "capacity_utilization": round(capacity_utilization, 2),
            "feasibility": self._analyze_capacity_feasibility(capacity_utilization),
            "recommendations": self._generate_capacity_recommendations(
                capacity_utilization, production_line_count, days_needed
            ),
            "calculated_at": datetime.now().isoformat()
        }
    
    async def _calculate_cost_breakdown(
        self,
        target_value: float,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        计算成本分解
        
        Args:
            target_value: 目标成本
            parameters: 参数
                - material_cost_ratio: 物料成本占比
                - labor_cost_ratio: 人工成本占比
                - overhead_cost_ratio: 制造费用占比
                - quantity: 数量
        
        Returns:
            成本分解结果
        """
        material_cost_ratio = parameters.get("material_cost_ratio", 0.6)
        labor_cost_ratio = parameters.get("labor_cost_ratio", 0.2)
        overhead_cost_ratio = parameters.get("overhead_cost_ratio", 0.2)
        quantity = parameters.get("quantity", 1)
        
        # 验证比例总和
        total_ratio = material_cost_ratio + labor_cost_ratio + overhead_cost_ratio
        if abs(total_ratio - 1.0) > 0.01:
            # 自动调整比例
            material_cost_ratio = material_cost_ratio / total_ratio
            labor_cost_ratio = labor_cost_ratio / total_ratio
            overhead_cost_ratio = overhead_cost_ratio / total_ratio
        
        # 计算总成本
        total_cost = target_value * quantity
        
        # 分解成本
        material_cost = total_cost * material_cost_ratio
        labor_cost = total_cost * labor_cost_ratio
        overhead_cost = total_cost * overhead_cost_ratio
        
        # 计算单位成本
        unit_material_cost = material_cost / quantity if quantity > 0 else 0
        unit_labor_cost = labor_cost / quantity if quantity > 0 else 0
        unit_overhead_cost = overhead_cost / quantity if quantity > 0 else 0
        unit_total_cost = total_cost / quantity if quantity > 0 else 0
        
        return {
            "target_cost": target_value,
            "quantity": quantity,
            "total_cost": round(total_cost, 2),
            "cost_breakdown": {
                "material": {
                    "total": round(material_cost, 2),
                    "unit": round(unit_material_cost, 2),
                    "ratio": round(material_cost_ratio * 100, 2)
                },
                "labor": {
                    "total": round(labor_cost, 2),
                    "unit": round(unit_labor_cost, 2),
                    "ratio": round(labor_cost_ratio * 100, 2)
                },
                "overhead": {
                    "total": round(overhead_cost, 2),
                    "unit": round(unit_overhead_cost, 2),
                    "ratio": round(overhead_cost_ratio * 100, 2)
                }
            },
            "unit_total_cost": round(unit_total_cost, 2),
            "recommendations": self._generate_cost_recommendations(
                material_cost_ratio, labor_cost_ratio, overhead_cost_ratio
            ),
            "calculated_at": datetime.now().isoformat()
        }
    
    def _analyze_capacity_feasibility(self, utilization: float) -> Dict[str, Any]:
        """分析产能可行性"""
        if utilization <= 80:
            level = "easy"
            score = 100
        elif utilization <= 90:
            level = "moderate"
            score = 80
        elif utilization <= 100:
            level = "challenging"
            score = 60
        else:
            level = "difficult"
            score = 30
        
        return {
            "level": level,
            "score": score,
            "utilization": round(utilization, 2)
        }
    
    def _generate_capacity_recommendations(
        self,
        utilization: float,
        line_count: int,
        days_needed: float
    ) -> List[str]:
        """生成产能建议"""
        recommendations = []
        
        if utilization > 100:
            recommendations.append("⚠️ 产能不足，建议：")
            recommendations.append("1. 增加生产线数量")
            recommendations.append("2. 延长工作时间")
            recommendations.append("3. 提高生产效率")
        elif utilization > 90:
            recommendations.append("📊 产能利用率较高，建议：")
            recommendations.append("1. 优化生产计划")
            recommendations.append("2. 准备应急预案")
        elif days_needed > 7:
            recommendations.append("⏰ 生产周期较长，建议：")
            recommendations.append("1. 提前安排生产")
            recommendations.append("2. 考虑并行生产")
        
        return recommendations
    
    def _generate_cost_recommendations(
        self,
        material_ratio: float,
        labor_ratio: float,
        overhead_ratio: float
    ) -> List[str]:
        """生成成本建议"""
        recommendations = []
        
        if material_ratio > 0.7:
            recommendations.append("💰 物料成本占比过高，建议：")
            recommendations.append("1. 优化采购策略")
            recommendations.append("2. 寻找替代材料")
            recommendations.append("3. 批量采购降低成本")
        
        if labor_ratio > 0.3:
            recommendations.append("👥 人工成本占比过高，建议：")
            recommendations.append("1. 提高自动化水平")
            recommendations.append("2. 优化人员配置")
            recommendations.append("3. 提高生产效率")
        
        if overhead_ratio > 0.25:
            recommendations.append("🏭 制造费用占比过高，建议：")
            recommendations.append("1. 优化设备利用率")
            recommendations.append("2. 降低能耗")
            recommendations.append("3. 优化生产流程")
        
        return recommendations
    
    async def calculate_inventory_requirement(
        self,
        target_production: float,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        计算物料需求
        
        Args:
            target_production: 目标产量
            parameters: 参数
                - material_list: 物料清单 [{material_name, unit_consumption, unit_price}]
                - safety_stock_ratio: 安全库存比例（默认0.2）
                - lead_time_days: 采购提前期（天）
                
        Returns:
            物料需求计算结果
        """
        material_list = parameters.get("material_list", [])
        safety_stock_ratio = parameters.get("safety_stock_ratio", 0.2)
        lead_time_days = parameters.get("lead_time_days", 7)
        
        material_requirements = []
        total_cost = 0
        
        for material in material_list:
            material_name = material.get("material_name", "")
            unit_consumption = material.get("unit_consumption", 0)
            unit_price = material.get("unit_price", 0)
            
            # 计算需求量
            required_quantity = target_production * unit_consumption
            safety_stock = required_quantity * safety_stock_ratio
            total_quantity = required_quantity + safety_stock
            
            # 计算成本
            material_cost = total_quantity * unit_price
            total_cost += material_cost
            
            material_requirements.append({
                "material_name": material_name,
                "unit_consumption": unit_consumption,
                "unit_price": unit_price,
                "required_quantity": round(required_quantity, 2),
                "safety_stock": round(safety_stock, 2),
                "total_quantity": round(total_quantity, 2),
                "material_cost": round(material_cost, 2)
            })
        
        return {
            "success": True,
            "target_production": target_production,
            "material_requirements": material_requirements,
            "total_material_cost": round(total_cost, 2),
            "lead_time_days": lead_time_days,
            "recommendations": self._generate_material_recommendations(
                material_requirements, total_cost
            ),
            "calculated_at": datetime.now().isoformat()
        }
    
    def _generate_material_recommendations(
        self,
        materials: List[Dict[str, Any]],
        total_cost: float
    ) -> List[str]:
        """生成物料建议"""
        recommendations = []
        
        # 找出成本最高的物料
        if materials:
            max_cost_material = max(materials, key=lambda x: x.get("material_cost", 0))
            if max_cost_material.get("material_cost", 0) > total_cost * 0.3:
                recommendations.append(
                    f"💡 {max_cost_material.get('material_name')}成本占比过高，建议："
                )
                recommendations.append("1. 寻找替代供应商")
                recommendations.append("2. 批量采购降低成本")
                recommendations.append("3. 优化物料消耗率")
        
        return recommendations
    
    async def calculate_delivery_schedule(
        self,
        order_list: List[Dict[str, Any]],
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        计算交付计划
        
        Args:
            order_list: 订单列表 [{order_no, quantity, delivery_date}]
            parameters: 参数
                - daily_capacity: 日产能
                - working_days_per_week: 每周工作天数
                
        Returns:
            交付计划计算结果
        """
        daily_capacity = parameters.get("daily_capacity", 100)
        working_days_per_week = parameters.get("working_days_per_week", 5)
        
        schedule = []
        current_date = datetime.now().date()
        total_days_needed = 0
        
        for order in order_list:
            quantity = order.get("quantity", 0)
            target_date = datetime.fromisoformat(order.get("delivery_date")).date() if order.get("delivery_date") else None
            
            days_needed = quantity / daily_capacity if daily_capacity > 0 else 0
            total_days_needed += days_needed
            
            start_date = current_date
            end_date = current_date + timedelta(days=int(days_needed))
            
            schedule.append({
                "order_no": order.get("order_no"),
                "quantity": quantity,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "target_date": target_date.isoformat() if target_date else None,
                "days_needed": round(days_needed, 1),
                "on_time": target_date and end_date <= target_date if target_date else None
            })
            
            current_date = end_date
        
        return {
            "success": True,
            "schedule": schedule,
            "total_days": round(total_days_needed, 1),
            "total_weeks": round(total_days_needed / (working_days_per_week * 7), 1),
            "recommendations": self._generate_schedule_recommendations(schedule),
            "calculated_at": datetime.now().isoformat()
        }
    
    def _generate_schedule_recommendations(
        self,
        schedule: List[Dict[str, Any]]
    ) -> List[str]:
        """生成交付计划建议"""
        recommendations = []
        
        late_orders = [s for s in schedule if s.get("on_time") == False]
        if late_orders:
            recommendations.append(f"⚠️ 发现{len(late_orders)}个订单可能延期，建议：")
            recommendations.append("1. 增加产能或延长工作时间")
            recommendations.append("2. 调整订单优先级")
            recommendations.append("3. 考虑外包部分生产")
        
        return recommendations

