"""
Stock Factor Engine

构建情绪/新闻/公告/财务等多因子画像，并输出预测信号。
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import random
from typing import Dict, List


def _score_to_label(score: float) -> str:
    if score >= 0.7:
        return "积极"
    if score >= 0.5:
        return "中性"
    return "偏弱"


@dataclass
class FactorWeights:
    sentiment: float = 0.3
    social: float = 0.15
    announcements: float = 0.15
    financials: float = 0.25
    flow: float = 0.1
    risk: float = 0.05


class StockFactorEngine:
    """构建股票多因子画像"""

    def __init__(self):
        self.sample_news = [
            "公司发布第三季度业绩预告，净利润同比增长 35%。",
            "新一代产品线通过国家级技术认证，预计下半年放量。",
            "管理层回应降价传闻称：将保持稳健的价格策略和渠道管控。",
            "海外订单恢复，欧洲客户恢复采购计划。",
            "原材料价格回落，毛利率有望抬升。"
        ]
        self.sample_announcements = [
            "拟回购股份 2-3 亿元用于员工激励",
            "完成收购智能终端供应链公司 70% 股权",
            "收到国家重大专项补贴 4500 万元",
            "董事长增持 120 万股，彰显长期信心"
        ]
        self.weights = FactorWeights()

    def _seed(self, stock_code: str) -> random.Random:
        seed = abs(hash(stock_code)) % (2 ** 32)
        return random.Random(seed)

    def build_factor_profile(self, stock_code: str) -> Dict:
        rng = self._seed(stock_code)
        news_score = round(0.45 + rng.random() * 0.45, 2)
        social_score = round(0.35 + rng.random() * 0.5, 2)
        announcement_score = round(0.4 + rng.random() * 0.5, 2)
        financial_score = round(0.5 + rng.random() * 0.4, 2)
        flow_score = round(0.3 + rng.random() * 0.6, 2)
        risk_score = round(0.2 + rng.random() * 0.5, 2)

        news_samples = rng.sample(self.sample_news, k=min(3, len(self.sample_news)))
        announcement_samples = rng.sample(
            self.sample_announcements, k=min(2, len(self.sample_announcements))
        )

        factors = {
            "news_sentiment": {
                "score": news_score,
                "label": _score_to_label(news_score),
                "news_count": 12 + rng.randint(0, 8),
                "samples": news_samples,
            },
            "social_buzz": {
                "score": social_score,
                "label": _score_to_label(social_score),
                "volume_index": round(0.8 + rng.random() * 0.7, 2),
                "heat_rank": rng.randint(3, 15),
            },
            "announcement_heat": {
                "score": announcement_score,
                "label": _score_to_label(announcement_score),
                "items": announcement_samples,
                "net_effect": "略偏多" if announcement_score > 0.6 else "影响有限",
            },
            "financial_health": {
                "score": financial_score,
                "label": _score_to_label(financial_score),
                "revenue_yoy": round(0.05 + rng.random() * 0.18, 2),
                "margin_trend": "改善" if rng.random() > 0.4 else "稳定",
                "cashflow_quality": "充裕" if financial_score > 0.65 else "稳健",
            },
            "capital_flow": {
                "score": flow_score,
                "label": _score_to_label(flow_score),
                "northbound_flow": round(-0.3 + rng.random() * 0.8, 2),
                "inst_position_change": round(-0.2 + rng.random() * 0.6, 2),
            },
            "risk_events": {
                "score": 1 - risk_score,
                "label": "风险可控" if risk_score < 0.5 else "需关注",
                "watch_items": [
                    "汇率波动" if rng.random() > 0.5 else "原材料价格",
                    "行业监管动态",
                ],
            },
        }

        composites = {
            "alpha_score": round(
                news_score * self.weights.sentiment
                + social_score * self.weights.social
                + announcement_score * self.weights.announcements
                + financial_score * self.weights.financials
                + flow_score * self.weights.flow
                + (1 - risk_score) * self.weights.risk,
                3,
            ),
            "bullish_probability": round(0.5 + rng.random() * 0.4, 2),
            "volatility_outlook": round(0.25 + rng.random() * 0.5, 2),
        }

        return {
            "stock_code": stock_code,
            "as_of": datetime.now().isoformat(),
            "factors": factors,
            "composite": composites,
        }

    def predict_signal(self, factor_profile: Dict) -> Dict:
        factors = factor_profile["factors"]
        composite = factor_profile["composite"]["alpha_score"]
        drivers: List[str] = []
        critical = []

        for key, entry in factors.items():
            score = entry.get("score")
            if score is None:
                continue
            if score >= 0.7:
                drivers.append(f"{key}↑ ({entry.get('label')})")
            elif score <= 0.4:
                critical.append(f"{key}↓ ({entry.get('label')})")

        if composite >= 0.68:
            signal = "BUY"
            bias = "多头"
        elif composite <= 0.45:
            signal = "SELL"
            bias = "空头"
        else:
            signal = "HOLD"
            bias = "观望"

        confidence = round(0.55 + abs(composite - 0.5), 2)
        reasoning = (
            "多因素共振，资金与基本面同向"
            if signal == "BUY"
            else "风险与机会交织，建议轻仓" if signal == "HOLD" else "多项因子走弱，建议防守"
        )

        return {
            "signal": signal,
            "bias": bias,
            "confidence": confidence,
            "alpha_score": composite,
            "reasoning": reasoning,
            "drivers": drivers[:3],
            "risks": critical[:3],
            "horizon": "1-3 天" if signal != "SELL" else "即时",
        }

    def get_factor_analysis(self, stock_code: str) -> Dict:
        """获取因子分析（增强版：支持更多因子类型）"""
        profile = self.build_factor_profile(stock_code)
        prediction = self.predict_signal(profile)
        profile["prediction"] = prediction
        
        # 添加因子相关性分析
        profile["factor_correlation"] = self._analyze_factor_correlation(profile["factors"])
        
        # 添加因子稳定性分析
        profile["factor_stability"] = self._analyze_factor_stability(stock_code)
        
        return profile
    
    def _analyze_factor_correlation(self, factors: Dict) -> Dict[str, Any]:
        """分析因子相关性"""
        # 简化实现：基于因子得分计算相关性
        scores = {k: v.get("score", 0.5) for k, v in factors.items() if isinstance(v, dict) and "score" in v}
        
        # 计算因子之间的相关性（简化版）
        correlations = {}
        factor_names = list(scores.keys())
        for i, name1 in enumerate(factor_names):
            for name2 in factor_names[i+1:]:
                # 简化的相关性计算（实际应使用历史数据）
                score1 = scores[name1]
                score2 = scores[name2]
                correlation = abs(score1 - score2) / max(score1, score2, 0.1) if max(score1, score2) > 0 else 0.0
                correlations[f"{name1}_{name2}"] = round(1 - correlation, 3)
        
        return {
            "method": "基于当前得分计算",
            "correlations": correlations,
            "note": "真实实现应使用历史因子数据计算相关性"
        }
    
    def _analyze_factor_stability(self, stock_code: str) -> Dict[str, Any]:
        """分析因子稳定性"""
        # 简化实现：基于股票代码生成稳定性指标
        rng = self._seed(stock_code)
        stability_scores = {
            "news_sentiment": round(0.6 + rng.random() * 0.3, 2),
            "social_buzz": round(0.4 + rng.random() * 0.4, 2),
            "announcement_heat": round(0.5 + rng.random() * 0.3, 2),
            "financial_health": round(0.7 + rng.random() * 0.2, 2),
            "capital_flow": round(0.3 + rng.random() * 0.5, 2),
            "risk_events": round(0.5 + rng.random() * 0.3, 2),
        }
        
        avg_stability = sum(stability_scores.values()) / len(stability_scores)
        
        return {
            "stability_scores": stability_scores,
            "avg_stability": round(avg_stability, 2),
            "stability_level": "高" if avg_stability > 0.7 else "中" if avg_stability > 0.5 else "低",
            "note": "真实实现应基于历史因子波动率计算"
        }
    
    def get_factor_importance(self, stock_code: str) -> Dict[str, Any]:
        """获取因子重要性排序"""
        profile = self.build_factor_profile(stock_code)
        factors = profile["factors"]
        
        # 基于因子得分和权重计算重要性
        importance_scores = {}
        for factor_name, factor_data in factors.items():
            if isinstance(factor_data, dict) and "score" in factor_data:
                score = factor_data["score"]
                # 获取权重
                weight_map = {
                    "news_sentiment": self.weights.sentiment,
                    "social_buzz": self.weights.social,
                    "announcement_heat": self.weights.announcements,
                    "financial_health": self.weights.financials,
                    "capital_flow": self.weights.flow,
                    "risk_events": self.weights.risk,
                }
                weight = weight_map.get(factor_name, 0.1)
                importance_scores[factor_name] = round(score * weight, 3)
        
        # 排序
        sorted_importance = sorted(importance_scores.items(), key=lambda x: x[1], reverse=True)
        
        return {
            "stock_code": stock_code,
            "importance_ranking": [
                {"factor": name, "importance_score": score}
                for name, score in sorted_importance
            ],
            "top_factor": sorted_importance[0][0] if sorted_importance else None,
        }


stock_factor_engine = StockFactorEngine()

