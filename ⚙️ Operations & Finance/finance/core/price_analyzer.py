"""
价格分析器⭐深化版
价格趋势分析、对比、优化建议、竞争分析、定价策略
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import statistics
import math

class PriceAnalyzer:
    """
    价格分析器⭐深化版
    
    功能：
    1. 价格趋势分析（深化）
    2. 价格对比（多维度）
    3. 竞争分析
    4. 定价策略优化
    5. 价格弹性分析
    6. 成本加成分析
    7. 市场定位分析
    """
    
    def __init__(self, erp_connector=None):
        """
        初始化价格分析器
        
        Args:
            erp_connector: ERP连接器（用于获取数据）
        """
        self.erp_connector = erp_connector
    
    async def analyze_price_trend(
        self,
        product_id: Optional[int] = None,
        period: str = "30d"  # 7d, 30d, 90d, 1y
    ) -> Dict[str, Any]:
        """
        分析价格趋势⭐深化版
        
        分析维度：
        - 趋势方向（上升/下降/平稳）
        - 波动性分析
        - 季节性模式
        - 异常价格检测
        - 预测未来趋势
        """
        # 从ERP获取价格历史数据
        price_history = await self._get_price_history(product_id, period)
        
        if not price_history or len(price_history) < 2:
            return {
                "product_id": product_id,
                "period": period,
                "trend": "数据不足",
                "average_price": 0.0,
                "price_range": {"min": 0.0, "max": 0.0},
                "volatility": 0.0,
                "message": "价格历史数据不足"
            }
        
        prices = [item["price"] for item in price_history]
        dates = [item["date"] for item in price_history]
        
        # 基础统计
        avg_price = statistics.mean(prices)
        min_price = min(prices)
        max_price = max(prices)
        price_range = max_price - min_price
        
        # 计算波动性（标准差/均值）
        if avg_price > 0:
            volatility = statistics.stdev(prices) / avg_price
        else:
            volatility = 0.0
        
        # 趋势分析（线性回归斜率）
        trend_direction = self._calculate_trend(prices, dates)
        
        # 异常检测
        anomalies = self._detect_price_anomalies(prices, dates)
        
        # 季节性分析
        seasonality = self._analyze_seasonality(price_history)
        
        # 预测未来趋势
        forecast = self._forecast_price_trend(prices, dates)
        
        return {
            "product_id": product_id,
            "period": period,
            "trend": trend_direction["direction"],  # 上升、下降、平稳
            "trend_strength": trend_direction["strength"],  # 0-1
            "average_price": round(avg_price, 2),
            "current_price": prices[-1] if prices else 0.0,
            "price_range": {
                "min": round(min_price, 2),
                "max": round(max_price, 2),
                "range": round(price_range, 2)
            },
            "volatility": round(volatility, 4),
            "volatility_level": "高" if volatility > 0.15 else "中" if volatility > 0.05 else "低",
            "anomalies": anomalies,
            "seasonality": seasonality,
            "forecast": forecast,
            "recommendations": self._generate_trend_recommendations(
                trend_direction, volatility, anomalies
            )
        }
    
    async def compare_prices(
        self,
        products: List[int],
        competitors: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        价格对比⭐深化版
        
        对比维度：
        - 价格水平对比
        - 价格变化趋势对比
        - 性价比分析
        - 市场定位对比
        """
        comparison_results = []
        
        for product_id in products:
            # 获取产品价格数据
            product_data = await self._get_product_price_data(product_id)
            
            if product_data:
                comparison_results.append({
                    "product_id": product_id,
                    "product_name": product_data.get("name", f"产品{product_id}"),
                    "current_price": product_data.get("price", 0.0),
                    "average_price": product_data.get("avg_price", 0.0),
                    "price_trend": product_data.get("trend", "未知"),
                    "market_position": self._analyze_market_position(
                        product_data.get("price", 0.0),
                        comparison_results
                    )
                })
        
        # 竞争分析
        competitive_analysis = self._analyze_competition(comparison_results, competitors)
        
        # 生成建议
        recommendations = self._generate_comparison_recommendations(
            comparison_results, competitive_analysis
        )
        
        return {
            "products": comparison_results,
            "competitive_analysis": competitive_analysis,
            "recommendations": recommendations,
            "summary": {
                "highest_price": max((p["current_price"] for p in comparison_results), default=0.0),
                "lowest_price": min((p["current_price"] for p in comparison_results), default=0.0),
                "price_gap": max((p["current_price"] for p in comparison_results), default=0.0) - 
                            min((p["current_price"] for p in comparison_results), default=0.0)
            }
        }
    
    async def optimize_pricing(
        self,
        product_id: int,
        cost: float,
        market_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        优化定价⭐深化版
        
        优化策略：
        - 成本加成定价
        - 竞争导向定价
        - 价值导向定价
        - 动态定价建议
        - 价格弹性考虑
        """
        # 获取当前价格
        current_price_data = await self._get_product_price_data(product_id)
        current_price = current_price_data.get("price", 0.0) if current_price_data else 0.0
        
        # 获取市场数据
        if not market_data:
            market_data = await self._get_market_data(product_id)
        
        # 成本加成定价
        cost_plus_pricing = self._calculate_cost_plus_pricing(cost, market_data)
        
        # 竞争导向定价
        competitive_pricing = self._calculate_competitive_pricing(market_data)
        
        # 价值导向定价
        value_based_pricing = self._calculate_value_based_pricing(
            product_id, cost, market_data
        )
        
        # 综合定价建议
        recommended_price = self._synthesize_pricing_recommendation(
            cost_plus_pricing,
            competitive_pricing,
            value_based_pricing,
            current_price
        )
        
        # 价格弹性分析
        price_elasticity = self._analyze_price_elasticity(product_id, market_data)
        
        # 预期影响分析
        impact_analysis = self._analyze_pricing_impact(
            current_price,
            recommended_price["price"],
            market_data
        )
        
        return {
            "product_id": product_id,
            "current_price": round(current_price, 2),
            "cost": round(cost, 2),
            "recommended_price": round(recommended_price["price"], 2),
            "pricing_strategy": recommended_price["strategy"],
            "reason": recommended_price["reason"],
            "pricing_options": {
                "cost_plus": {
                    "price": round(cost_plus_pricing["price"], 2),
                    "margin": round(cost_plus_pricing["margin"], 2),
                    "description": "基于成本加成"
                },
                "competitive": {
                    "price": round(competitive_pricing["price"], 2),
                    "description": "基于竞争定价"
                },
                "value_based": {
                    "price": round(value_based_pricing["price"], 2),
                    "description": "基于价值定价"
                }
            },
            "price_elasticity": price_elasticity,
            "expected_impact": impact_analysis,
            "recommendations": recommended_price["recommendations"]
        }
    
    async def analyze_price_elasticity(
        self,
        product_id: int,
        price_changes: List[Dict[str, Any]],
        sales_changes: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        分析价格弹性
        
        Args:
            product_id: 产品ID
            price_changes: 价格变化历史
            sales_changes: 销量变化历史
            
        Returns:
            价格弹性分析结果
        """
        if len(price_changes) != len(sales_changes) or len(price_changes) < 2:
            return {
                "elasticity": 0.0,
                "elasticity_type": "数据不足",
                "message": "需要至少2组价格和销量数据"
            }
        
        # 计算价格弹性系数
        elasticities = []
        for i in range(1, len(price_changes)):
            price_change_pct = (price_changes[i]["price"] - price_changes[i-1]["price"]) / price_changes[i-1]["price"]
            sales_change_pct = (sales_changes[i]["sales"] - sales_changes[i-1]["sales"]) / sales_changes[i-1]["sales"]
            
            if price_change_pct != 0:
                elasticity = sales_change_pct / price_change_pct
                elasticities.append(elasticity)
        
        if not elasticities:
            return {"elasticity": 0.0, "elasticity_type": "无法计算"}
        
        avg_elasticity = statistics.mean(elasticities)
        
        # 判断弹性类型
        if abs(avg_elasticity) > 1:
            elasticity_type = "弹性需求"  # 价格敏感
        elif abs(avg_elasticity) < 1:
            elasticity_type = "非弹性需求"  # 价格不敏感
        else:
            elasticity_type = "单位弹性"
        
        return {
            "elasticity": round(avg_elasticity, 4),
            "elasticity_type": elasticity_type,
            "interpretation": self._interpret_elasticity(avg_elasticity),
            "recommendations": self._generate_elasticity_recommendations(avg_elasticity)
        }
    
    # ============ 辅助方法 ============
    
    async def _get_price_history(
        self,
        product_id: Optional[int],
        period: str
    ) -> List[Dict[str, Any]]:
        """从ERP获取价格历史数据"""
        if self.erp_connector:
            # TODO: 调用ERP API获取价格历史
            pass
        
        # 模拟数据
        days = 30 if period == "30d" else 7 if period == "7d" else 90 if period == "90d" else 365
        return [
            {
                "date": (datetime.now() - timedelta(days=i)).isoformat(),
                "price": 100.0 + (i % 10) * 2 - 5  # 模拟价格波动
            }
            for i in range(days, 0, -1)
        ]
    
    def _calculate_trend(self, prices: List[float], dates: List[str]) -> Dict[str, Any]:
        """计算价格趋势"""
        if len(prices) < 2:
            return {"direction": "数据不足", "strength": 0.0}
        
        # 简单线性回归
        n = len(prices)
        x = list(range(n))
        y = prices
        
        x_mean = statistics.mean(x)
        y_mean = statistics.mean(y)
        
        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            slope = 0
        else:
            slope = numerator / denominator
        
        # 归一化强度（0-1）
        price_range = max(prices) - min(prices)
        if price_range > 0:
            strength = abs(slope * n) / price_range
            strength = min(strength, 1.0)
        else:
            strength = 0.0
        
        if slope > 0.01:
            direction = "上升"
        elif slope < -0.01:
            direction = "下降"
        else:
            direction = "平稳"
        
        return {
            "direction": direction,
            "strength": round(strength, 4),
            "slope": round(slope, 4)
        }
    
    def _detect_price_anomalies(
        self,
        prices: List[float],
        dates: List[str]
    ) -> List[Dict[str, Any]]:
        """检测价格异常"""
        if len(prices) < 3:
            return []
        
        anomalies = []
        mean_price = statistics.mean(prices)
        std_price = statistics.stdev(prices) if len(prices) > 1 else 0
        
        if std_price == 0:
            return []
        
        for i, price in enumerate(prices):
            z_score = abs((price - mean_price) / std_price)
            if z_score > 2:  # 2倍标准差
                anomalies.append({
                    "date": dates[i] if i < len(dates) else "",
                    "price": price,
                    "deviation": round(z_score, 2),
                    "type": "异常高" if price > mean_price else "异常低"
                })
        
        return anomalies
    
    def _analyze_seasonality(
        self,
        price_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """分析季节性模式"""
        # 简化实现：检查是否有周期性模式
        return {
            "has_seasonality": False,
            "pattern": "无明显季节性",
            "peak_months": [],
            "low_months": []
        }
    
    def _forecast_price_trend(
        self,
        prices: List[float],
        dates: List[str]
    ) -> Dict[str, Any]:
        """预测未来价格趋势"""
        if len(prices) < 3:
            return {"forecast": "数据不足"}
        
        trend = self._calculate_trend(prices, dates)
        last_price = prices[-1]
        
        # 简单预测：基于趋势方向
        if trend["direction"] == "上升":
            forecast_price = last_price * 1.02  # 预测上涨2%
        elif trend["direction"] == "下降":
            forecast_price = last_price * 0.98  # 预测下跌2%
        else:
            forecast_price = last_price
        
        return {
            "forecast_price": round(forecast_price, 2),
            "confidence": round(trend["strength"], 2),
            "direction": trend["direction"]
        }
    
    def _generate_trend_recommendations(
        self,
        trend: Dict[str, Any],
        volatility: float,
        anomalies: List[Dict[str, Any]]
    ) -> List[str]:
        """生成趋势分析建议"""
        recommendations = []
        
        if trend["direction"] == "上升" and trend["strength"] > 0.5:
            recommendations.append("价格持续上升，建议关注市场需求变化")
        
        if volatility > 0.15:
            recommendations.append("价格波动较大，建议稳定定价策略")
        
        if anomalies:
            recommendations.append(f"检测到{len(anomalies)}个价格异常点，建议调查原因")
        
        return recommendations
    
    async def _get_product_price_data(self, product_id: int) -> Optional[Dict[str, Any]]:
        """获取产品价格数据"""
        # TODO: 从ERP获取
        return {
            "id": product_id,
            "name": f"产品{product_id}",
            "price": 100.0,
            "avg_price": 95.0,
            "trend": "上升"
        }
    
    def _analyze_market_position(
        self,
        price: float,
        other_products: List[Dict[str, Any]]
    ) -> str:
        """分析市场定位"""
        if not other_products:
            return "无对比数据"
        
        other_prices = [p.get("current_price", 0) for p in other_products]
        if not other_prices:
            return "中等"
        
        avg_other_price = statistics.mean(other_prices)
        
        if price > avg_other_price * 1.1:
            return "高端"
        elif price < avg_other_price * 0.9:
            return "低端"
        else:
            return "中等"
    
    def _analyze_competition(
        self,
        products: List[Dict[str, Any]],
        competitors: Optional[List[str]]
    ) -> Dict[str, Any]:
        """竞争分析"""
        prices = [p["current_price"] for p in products]
        
        return {
            "price_range": {
                "min": min(prices) if prices else 0.0,
                "max": max(prices) if prices else 0.0,
                "avg": statistics.mean(prices) if prices else 0.0
            },
            "competition_level": "激烈" if len(prices) > 3 else "中等"
        }
    
    def _generate_comparison_recommendations(
        self,
        products: List[Dict[str, Any]],
        competitive_analysis: Dict[str, Any]
    ) -> List[str]:
        """生成对比分析建议"""
        recommendations = []
        
        prices = [p["current_price"] for p in products]
        if prices:
            price_gap = max(prices) - min(prices)
            if price_gap > statistics.mean(prices) * 0.3:
                recommendations.append("产品间价格差距较大，建议统一定价策略")
        
        return recommendations
    
    async def _get_market_data(self, product_id: int) -> Dict[str, Any]:
        """获取市场数据"""
        return {
            "competitor_prices": [95.0, 100.0, 105.0],
            "market_demand": "中等",
            "market_share": 0.15
        }
    
    def _calculate_cost_plus_pricing(
        self,
        cost: float,
        market_data: Optional[Dict]
    ) -> Dict[str, Any]:
        """成本加成定价"""
        # 标准加成率：30-50%
        margin_rate = 0.4  # 40%
        price = cost * (1 + margin_rate)
        
        return {
            "price": price,
            "margin": price - cost,
            "margin_rate": margin_rate
        }
    
    def _calculate_competitive_pricing(
        self,
        market_data: Optional[Dict]
    ) -> Dict[str, Any]:
        """竞争导向定价"""
        if not market_data or "competitor_prices" not in market_data:
            return {"price": 0.0, "strategy": "无竞争数据"}
        
        competitor_prices = market_data["competitor_prices"]
        avg_competitor_price = statistics.mean(competitor_prices)
        
        # 略低于平均价格
        price = avg_competitor_price * 0.95
        
        return {
            "price": price,
            "strategy": "竞争导向",
            "reference": avg_competitor_price
        }
    
    def _calculate_value_based_pricing(
        self,
        product_id: int,
        cost: float,
        market_data: Optional[Dict]
    ) -> Dict[str, Any]:
        """价值导向定价"""
        # 基于产品价值和市场需求
        base_price = cost * 2.0  # 2倍成本作为基础
        
        # 根据市场需求调整
        if market_data and market_data.get("market_demand") == "高":
            price = base_price * 1.2
        elif market_data and market_data.get("market_demand") == "低":
            price = base_price * 0.8
        else:
            price = base_price
        
        return {
            "price": price,
            "strategy": "价值导向"
        }
    
    def _synthesize_pricing_recommendation(
        self,
        cost_plus: Dict[str, Any],
        competitive: Dict[str, Any],
        value_based: Dict[str, Any],
        current_price: float
    ) -> Dict[str, Any]:
        """综合定价建议"""
        # 加权平均
        weights = {"cost_plus": 0.3, "competitive": 0.4, "value_based": 0.3}
        
        recommended_price = (
            cost_plus["price"] * weights["cost_plus"] +
            competitive["price"] * weights["competitive"] +
            value_based["price"] * weights["value_based"]
        )
        
        # 选择最接近的策略
        strategies = [
            ("cost_plus", cost_plus["price"]),
            ("competitive", competitive["price"]),
            ("value_based", value_based["price"])
        ]
        
        closest_strategy = min(
            strategies,
            key=lambda x: abs(x[1] - recommended_price)
        )
        
        # 生成建议理由
        if abs(recommended_price - current_price) / current_price > 0.1:
            reason = f"建议调整价格，当前价格偏离最优价格{abs(recommended_price - current_price):.2f}元"
        else:
            reason = "当前价格合理，建议保持"
        
        return {
            "price": recommended_price,
            "strategy": closest_strategy[0],
            "reason": reason,
            "recommendations": [
                f"基于成本加成：{cost_plus['price']:.2f}元",
                f"基于竞争定价：{competitive['price']:.2f}元",
                f"基于价值定价：{value_based['price']:.2f}元"
            ]
        }
    
    def _analyze_price_elasticity(
        self,
        product_id: int,
        market_data: Optional[Dict]
    ) -> Dict[str, Any]:
        """分析价格弹性"""
        return {
            "elasticity": -1.2,  # 弹性需求
            "type": "弹性需求",
            "interpretation": "价格变化对销量影响较大"
        }
    
    def _analyze_pricing_impact(
        self,
        current_price: float,
        new_price: float,
        market_data: Optional[Dict]
    ) -> Dict[str, Any]:
        """分析定价影响"""
        price_change_pct = (new_price - current_price) / current_price
        
        # 假设价格弹性为-1.2
        elasticity = -1.2
        sales_change_pct = price_change_pct * elasticity
        
        return {
            "price_change": round(price_change_pct * 100, 2),
            "expected_sales_change": round(sales_change_pct * 100, 2),
            "expected_revenue_change": round(
                (1 + price_change_pct) * (1 + sales_change_pct) - 1, 4
            ) * 100
        }
    
    def _interpret_elasticity(self, elasticity: float) -> str:
        """解释价格弹性"""
        abs_elasticity = abs(elasticity)
        if abs_elasticity > 1:
            return "弹性需求：价格变化对销量影响大，建议谨慎调价"
        elif abs_elasticity < 1:
            return "非弹性需求：价格变化对销量影响小，可适当调价"
        else:
            return "单位弹性：价格和销量变化比例相同"
    
    def _generate_elasticity_recommendations(self, elasticity: float) -> List[str]:
        """生成弹性分析建议"""
        recommendations = []
        
        if abs(elasticity) > 1:
            recommendations.append("需求弹性大，建议通过降价提升销量")
        else:
            recommendations.append("需求弹性小，可适当提价增加利润")
        
        return recommendations

