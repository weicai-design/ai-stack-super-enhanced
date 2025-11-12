"""
8维度企业经营分析系统
提供全方位的企业经营健康度分析
"""
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from enum import Enum


class DimensionLevel(str, Enum):
    """维度评级"""
    EXCELLENT = "excellent"      # 优秀 (90-100分)
    GOOD = "good"               # 良好 (80-89分)
    AVERAGE = "average"         # 一般 (70-79分)
    POOR = "poor"               # 较差 (60-69分)
    CRITICAL = "critical"       # 危险 (<60分)


class EightDimensionsAnalyzer:
    """8维度企业经营分析器"""
    
    def __init__(self):
        """初始化8维度分析器"""
        self.dimensions = {
            "profitability": "盈利能力",
            "growth": "成长能力",
            "operational_efficiency": "运营效率",
            "financial_health": "财务健康",
            "market_competitiveness": "市场竞争力",
            "innovation_capability": "创新能力",
            "risk_control": "风险控制",
            "sustainability": "可持续发展"
        }
    
    def analyze(self, business_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行8维度分析
        
        Args:
            business_data: 企业经营数据
        
        Returns:
            8维度分析结果
        """
        results = {}
        
        # 1. 盈利能力分析
        results["profitability"] = self._analyze_profitability(business_data)
        
        # 2. 成长能力分析
        results["growth"] = self._analyze_growth(business_data)
        
        # 3. 运营效率分析
        results["operational_efficiency"] = self._analyze_operational_efficiency(business_data)
        
        # 4. 财务健康分析
        results["financial_health"] = self._analyze_financial_health(business_data)
        
        # 5. 市场竞争力分析
        results["market_competitiveness"] = self._analyze_market_competitiveness(business_data)
        
        # 6. 创新能力分析
        results["innovation_capability"] = self._analyze_innovation(business_data)
        
        # 7. 风险控制分析
        results["risk_control"] = self._analyze_risk_control(business_data)
        
        # 8. 可持续发展分析
        results["sustainability"] = self._analyze_sustainability(business_data)
        
        # 计算综合得分
        overall_score = self._calculate_overall_score(results)
        
        # 生成综合报告
        report = self._generate_comprehensive_report(results, overall_score)
        
        return {
            "dimensions": results,
            "overall_score": overall_score,
            "overall_level": self._get_level(overall_score),
            "report": report,
            "timestamp": datetime.now().isoformat(),
            "recommendations": self._generate_recommendations(results)
        }
    
    def _analyze_profitability(self, data: Dict) -> Dict:
        """维度1：盈利能力分析"""
        # 提取关键指标
        revenue = data.get("revenue", 0)
        cost = data.get("cost", 0)
        net_profit = data.get("net_profit", revenue - cost)
        assets = data.get("total_assets", 1)
        equity = data.get("equity", 1)
        
        # 计算指标
        profit_margin = (net_profit / revenue * 100) if revenue > 0 else 0
        roa = (net_profit / assets * 100) if assets > 0 else 0  # 资产回报率
        roe = (net_profit / equity * 100) if equity > 0 else 0  # 净资产收益率
        
        # 综合评分
        score = self._calculate_profitability_score(profit_margin, roa, roe)
        
        return {
            "dimension": "盈利能力",
            "score": round(score, 2),
            "level": self._get_level(score),
            "indicators": {
                "profit_margin": round(profit_margin, 2),
                "roa": round(roa, 2),
                "roe": round(roe, 2)
            },
            "analysis": f"利润率{profit_margin:.1f}%，ROA{roa:.1f}%，ROE{roe:.1f}%",
            "suggestions": self._get_profitability_suggestions(score, profit_margin, roa, roe)
        }
    
    def _analyze_growth(self, data: Dict) -> Dict:
        """维度2：成长能力分析"""
        # 提取增长数据
        revenue_growth = data.get("revenue_growth", 0)  # 营收增长率
        profit_growth = data.get("profit_growth", 0)    # 利润增长率
        customer_growth = data.get("customer_growth", 0)  # 客户增长率
        market_share_growth = data.get("market_share_growth", 0)  # 市场份额增长
        
        # 综合评分
        score = (
            revenue_growth * 0.35 +
            profit_growth * 0.35 +
            customer_growth * 0.2 +
            market_share_growth * 0.1
        )
        
        # 转换为百分制
        score = min(100, max(0, score * 100 + 70))  # 基础分70，增长加分
        
        return {
            "dimension": "成长能力",
            "score": round(score, 2),
            "level": self._get_level(score),
            "indicators": {
                "revenue_growth": round(revenue_growth * 100, 2),
                "profit_growth": round(profit_growth * 100, 2),
                "customer_growth": round(customer_growth * 100, 2),
                "market_share_growth": round(market_share_growth * 100, 2)
            },
            "analysis": f"营收增长{revenue_growth*100:.1f}%，利润增长{profit_growth*100:.1f}%",
            "suggestions": self._get_growth_suggestions(score, revenue_growth, profit_growth)
        }
    
    def _analyze_operational_efficiency(self, data: Dict) -> Dict:
        """维度3：运营效率分析"""
        # 提取效率指标
        inventory_turnover = data.get("inventory_turnover", 5.0)  # 库存周转率
        receivable_turnover = data.get("receivable_turnover", 8.0)  # 应收账款周转率
        asset_turnover = data.get("asset_turnover", 1.5)  # 总资产周转率
        employee_productivity = data.get("employee_productivity", 100000)  # 人均产值
        
        # 评分逻辑
        score_inventory = min(100, (inventory_turnover / 10) * 100)
        score_receivable = min(100, (receivable_turnover / 12) * 100)
        score_asset = min(100, (asset_turnover / 2) * 100)
        score_productivity = min(100, (employee_productivity / 150000) * 100)
        
        score = (score_inventory + score_receivable + score_asset + score_productivity) / 4
        
        return {
            "dimension": "运营效率",
            "score": round(score, 2),
            "level": self._get_level(score),
            "indicators": {
                "inventory_turnover": round(inventory_turnover, 2),
                "receivable_turnover": round(receivable_turnover, 2),
                "asset_turnover": round(asset_turnover, 2),
                "employee_productivity": round(employee_productivity, 2)
            },
            "analysis": f"库存周转{inventory_turnover:.1f}次/年，资产周转{asset_turnover:.1f}次/年",
            "suggestions": self._get_efficiency_suggestions(score, inventory_turnover, asset_turnover)
        }
    
    def _analyze_financial_health(self, data: Dict) -> Dict:
        """维度4：财务健康分析"""
        # 提取财务指标
        current_ratio = data.get("current_ratio", 1.5)  # 流动比率
        quick_ratio = data.get("quick_ratio", 1.0)  # 速动比率
        debt_ratio = data.get("debt_ratio", 0.5)  # 资产负债率
        cash_flow = data.get("operating_cash_flow", 1000000)  # 经营现金流
        
        # 评分逻辑
        score_current = min(100, (current_ratio / 2) * 100)
        score_quick = min(100, (quick_ratio / 1.5) * 100)
        score_debt = min(100, (1 - debt_ratio) * 100)  # 负债率越低越好
        score_cash = min(100, (cash_flow / 1000000) * 80) if cash_flow > 0 else 20
        
        score = (score_current * 0.3 + score_quick * 0.3 + score_debt * 0.3 + score_cash * 0.1)
        
        return {
            "dimension": "财务健康",
            "score": round(score, 2),
            "level": self._get_level(score),
            "indicators": {
                "current_ratio": round(current_ratio, 2),
                "quick_ratio": round(quick_ratio, 2),
                "debt_ratio": round(debt_ratio, 2),
                "cash_flow": round(cash_flow, 2)
            },
            "analysis": f"流动比率{current_ratio:.2f}，负债率{debt_ratio*100:.1f}%",
            "suggestions": self._get_financial_suggestions(score, current_ratio, debt_ratio)
        }
    
    def _analyze_market_competitiveness(self, data: Dict) -> Dict:
        """维度5：市场竞争力分析"""
        # 提取市场指标
        market_share = data.get("market_share", 0.05)  # 市场份额
        brand_value = data.get("brand_value", 5000000)  # 品牌价值
        customer_satisfaction = data.get("customer_satisfaction", 85)  # 客户满意度
        nps_score = data.get("nps", 40)  # 净推荐值
        
        # 评分逻辑
        score_market = min(100, (market_share / 0.1) * 100)
        score_brand = min(100, (brand_value / 10000000) * 100)
        score_satisfaction = customer_satisfaction
        score_nps = min(100, (nps_score + 50))  # NPS范围-100到100
        
        score = (score_market * 0.3 + score_brand * 0.2 + score_satisfaction * 0.3 + score_nps * 0.2)
        
        return {
            "dimension": "市场竞争力",
            "score": round(score, 2),
            "level": self._get_level(score),
            "indicators": {
                "market_share": round(market_share * 100, 2),
                "brand_value": round(brand_value, 2),
                "customer_satisfaction": round(customer_satisfaction, 2),
                "nps": round(nps_score, 2)
            },
            "analysis": f"市场份额{market_share*100:.2f}%，客户满意度{customer_satisfaction:.1f}%",
            "suggestions": self._get_competitiveness_suggestions(score, market_share, nps_score)
        }
    
    def _analyze_innovation(self, data: Dict) -> Dict:
        """维度6：创新能力分析"""
        # 提取创新指标
        rd_investment_ratio = data.get("rd_investment_ratio", 0.03)  # 研发投入比例
        new_product_revenue_ratio = data.get("new_product_revenue", 0.2)  # 新产品营收占比
        patents_count = data.get("patents", 5)  # 专利数量
        innovation_projects = data.get("innovation_projects", 3)  # 创新项目数
        
        # 评分逻辑
        score_rd = min(100, (rd_investment_ratio / 0.05) * 100)
        score_new_product = min(100, (new_product_revenue_ratio / 0.3) * 100)
        score_patents = min(100, (patents_count / 10) * 100)
        score_projects = min(100, (innovation_projects / 5) * 100)
        
        score = (score_rd * 0.3 + score_new_product * 0.3 + score_patents * 0.2 + score_projects * 0.2)
        
        return {
            "dimension": "创新能力",
            "score": round(score, 2),
            "level": self._get_level(score),
            "indicators": {
                "rd_investment_ratio": round(rd_investment_ratio * 100, 2),
                "new_product_revenue": round(new_product_revenue_ratio * 100, 2),
                "patents": patents_count,
                "innovation_projects": innovation_projects
            },
            "analysis": f"研发投入{rd_investment_ratio*100:.1f}%，新产品营收占比{new_product_revenue_ratio*100:.1f}%",
            "suggestions": self._get_innovation_suggestions(score, rd_investment_ratio)
        }
    
    def _analyze_risk_control(self, data: Dict) -> Dict:
        """维度7：风险控制分析"""
        # 提取风险指标
        debt_ratio = data.get("debt_ratio", 0.5)
        liquidity_ratio = data.get("current_ratio", 1.5)
        concentration_risk = data.get("customer_concentration", 0.3)  # 客户集中度
        inventory_risk = data.get("inventory_aging_ratio", 0.1)  # 库存老化率
        
        # 评分逻辑（风险越低越好）
        score_debt = min(100, (1 - debt_ratio) * 120)
        score_liquidity = min(100, liquidity_ratio * 50)
        score_concentration = min(100, (1 - concentration_risk) * 100)
        score_inventory = min(100, (1 - inventory_risk) * 100)
        
        score = (score_debt * 0.3 + score_liquidity * 0.3 + score_concentration * 0.2 + score_inventory * 0.2)
        
        return {
            "dimension": "风险控制",
            "score": round(score, 2),
            "level": self._get_level(score),
            "indicators": {
                "debt_ratio": round(debt_ratio, 2),
                "liquidity_ratio": round(liquidity_ratio, 2),
                "customer_concentration": round(concentration_risk, 2),
                "inventory_aging_ratio": round(inventory_risk, 2)
            },
            "analysis": f"负债率{debt_ratio*100:.1f}%，流动比率{liquidity_ratio:.2f}",
            "suggestions": self._get_risk_suggestions(score, debt_ratio, liquidity_ratio)
        }
    
    def _analyze_sustainability(self, data: Dict) -> Dict:
        """维度8：可持续发展分析"""
        # 提取可持续发展指标
        employee_retention = data.get("employee_retention", 0.85)  # 员工保留率
        energy_efficiency = data.get("energy_efficiency", 0.7)  # 能源效率
        supplier_stability = data.get("supplier_stability", 0.8)  # 供应商稳定性
        social_responsibility = data.get("social_responsibility_score", 70)  # 社会责任评分
        
        # 评分逻辑
        score_retention = employee_retention * 100
        score_energy = energy_efficiency * 100
        score_supplier = supplier_stability * 100
        score_social = social_responsibility
        
        score = (score_retention * 0.3 + score_energy * 0.2 + score_supplier * 0.3 + score_social * 0.2)
        
        return {
            "dimension": "可持续发展",
            "score": round(score, 2),
            "level": self._get_level(score),
            "indicators": {
                "employee_retention": round(employee_retention * 100, 2),
                "energy_efficiency": round(energy_efficiency * 100, 2),
                "supplier_stability": round(supplier_stability * 100, 2),
                "social_responsibility": round(social_responsibility, 2)
            },
            "analysis": f"员工保留率{employee_retention*100:.1f}%，供应商稳定性{supplier_stability*100:.1f}%",
            "suggestions": self._get_sustainability_suggestions(score, employee_retention)
        }
    
    def _calculate_profitability_score(self, profit_margin: float, roa: float, roe: float) -> float:
        """计算盈利能力得分"""
        # 行业标准参考
        target_margin = 15  # 目标利润率15%
        target_roa = 10  # 目标ROA 10%
        target_roe = 15  # 目标ROE 15%
        
        score_margin = min(100, (profit_margin / target_margin) * 100)
        score_roa = min(100, (roa / target_roa) * 100)
        score_roe = min(100, (roe / target_roe) * 100)
        
        return (score_margin * 0.4 + score_roa * 0.3 + score_roe * 0.3)
    
    def _calculate_overall_score(self, results: Dict) -> float:
        """计算综合得分"""
        weights = {
            "profitability": 0.2,        # 盈利能力 20%
            "growth": 0.15,              # 成长能力 15%
            "operational_efficiency": 0.15,  # 运营效率 15%
            "financial_health": 0.15,    # 财务健康 15%
            "market_competitiveness": 0.15,  # 市场竞争力 15%
            "innovation_capability": 0.1,  # 创新能力 10%
            "risk_control": 0.05,        # 风险控制 5%
            "sustainability": 0.05       # 可持续发展 5%
        }
        
        total_score = sum(
            results[dim]["score"] * weight
            for dim, weight in weights.items()
        )
        
        return round(total_score, 2)
    
    def _get_level(self, score: float) -> str:
        """根据得分获取等级"""
        if score >= 90:
            return DimensionLevel.EXCELLENT
        elif score >= 80:
            return DimensionLevel.GOOD
        elif score >= 70:
            return DimensionLevel.AVERAGE
        elif score >= 60:
            return DimensionLevel.POOR
        else:
            return DimensionLevel.CRITICAL
    
    def _generate_comprehensive_report(self, results: Dict, overall_score: float) -> str:
        """生成综合分析报告"""
        report = f"# 企业8维度经营分析报告\n\n"
        report += f"**分析时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        report += f"**综合得分**: {overall_score:.2f}分\n"
        report += f"**综合评级**: {self._get_level_name(self._get_level(overall_score))}\n\n"
        
        report += "## 📊 各维度得分\n\n"
        for dim_key, dim_data in results.items():
            report += f"### {dim_data['dimension']} - {dim_data['score']:.1f}分 ({self._get_level_name(dim_data['level'])})\n\n"
            report += f"{dim_data['analysis']}\n\n"
        
        # 优势分析
        report += "## 💪 核心优势\n\n"
        strengths = [dim for dim, data in results.items() if data['score'] >= 80]
        for dim_key in strengths[:3]:
            dim_data = results[dim_key]
            report += f"- **{dim_data['dimension']}**: {dim_data['score']:.1f}分\n"
        
        # 待改进项
        report += "\n## ⚠️ 待改进领域\n\n"
        weaknesses = sorted(results.items(), key=lambda x: x[1]['score'])[:3]
        for dim_key, dim_data in weaknesses:
            report += f"- **{dim_data['dimension']}**: {dim_data['score']:.1f}分\n"
        
        return report
    
    def _get_level_name(self, level: str) -> str:
        """获取等级中文名"""
        names = {
            "excellent": "优秀",
            "good": "良好",
            "average": "一般",
            "poor": "较差",
            "critical": "危险"
        }
        return names.get(level, "未知")
    
    def _generate_recommendations(self, results: Dict) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        # 找出得分最低的3个维度
        sorted_dims = sorted(results.items(), key=lambda x: x[1]['score'])
        
        for dim_key, dim_data in sorted_dims[:3]:
            if dim_data.get('suggestions'):
                recommendations.extend(dim_data['suggestions'][:2])  # 每个维度取2条建议
        
        return recommendations[:5]  # 总共返回5条建议
    
    # ==================== 建议生成方法 ====================
    
    def _get_profitability_suggestions(self, score: float, margin: float, roa: float, roe: float) -> List[str]:
        """盈利能力改进建议"""
        suggestions = []
        if margin < 10:
            suggestions.append("💡 建议提高产品定价或降低成本以提升利润率")
        if roa < 8:
            suggestions.append("📊 建议优化资产使用效率，提高资产回报率")
        if roe < 12:
            suggestions.append("💰 建议优化资本结构，提升股东回报")
        if score >= 90:
            suggestions.append("✅ 盈利能力优秀，继续保持")
        return suggestions
    
    def _get_growth_suggestions(self, score: float, revenue_growth: float, profit_growth: float) -> List[str]:
        """成长能力改进建议"""
        suggestions = []
        if revenue_growth < 0.1:
            suggestions.append("📈 建议加大市场拓展力度，提升营收增长")
        if profit_growth < 0.1:
            suggestions.append("💹 建议优化成本结构，提升利润增长")
        if score >= 85:
            suggestions.append("🚀 成长势头良好，建议加大投资")
        return suggestions
    
    def _get_efficiency_suggestions(self, score: float, inventory: float, asset: float) -> List[str]:
        """运营效率改进建议"""
        suggestions = []
        if inventory < 6:
            suggestions.append("📦 建议优化库存管理，提高库存周转率")
        if asset < 1.2:
            suggestions.append("🔄 建议提高资产利用效率")
        return suggestions
    
    def _get_financial_suggestions(self, score: float, current: float, debt: float) -> List[str]:
        """财务健康改进建议"""
        suggestions = []
        if current < 1.2:
            suggestions.append("⚠️ 流动比率偏低，建议增加流动资产")
        if debt > 0.7:
            suggestions.append("💰 负债率偏高，建议降低负债或增加资本")
        return suggestions
    
    def _get_risk_suggestions(self, score: float, debt: float, liquidity: float) -> List[str]:
        """风险控制改进建议"""
        suggestions = []
        if debt > 0.6:
            suggestions.append("⚠️ 负债率偏高，存在财务风险")
        if liquidity < 1.5:
            suggestions.append("💰 流动比率偏低，建议增强短期偿债能力")
        return suggestions
    
    def _get_competitiveness_suggestions(self, score: float, market_share: float, nps: float) -> List[str]:
        """市场竞争力改进建议"""
        suggestions = []
        if market_share < 0.05:
            suggestions.append("🎯 建议加大市场推广，提升市场份额")
        if nps < 30:
            suggestions.append("😊 建议提升客户体验，增加客户推荐意愿")
        return suggestions
    
    def _get_innovation_suggestions(self, score: float, rd_ratio: float) -> List[str]:
        """创新能力改进建议"""
        suggestions = []
        if rd_ratio < 0.03:
            suggestions.append("🔬 建议加大研发投入")
        return suggestions
    
    def _get_sustainability_suggestions(self, score: float, retention: float) -> List[str]:
        """可持续发展改进建议"""
        suggestions = []
        if retention < 0.8:
            suggestions.append("👥 建议改善员工福利，提高保留率")
        return suggestions


# 全局实例
eight_dimensions_analyzer = EightDimensionsAnalyzer()

