"""
Trend Scenario Engine

提供预测回测可视化数据与 What-if 情景模拟
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import random
from typing import Dict, List


@dataclass
class ScenarioInput:
    indicator: str
    scenario_name: str
    demand_shift: float
    policy_intensity: float
    supply_shift: float


class TrendScenarioEngine:
    def __init__(self):
        self.base_levels = {
            "industry_demand_velocity": 108.0,
            "region_capacity_utilization": 74.0,
            "policy_grants_tracker": 62.0,
            "policy_risk_index": 0.63,
            "EV_DEMAND": 108.0,
            "CLOUD_ADOPTION": 95.0,
            "CPI_FOOD": 102.0,
            "LOGISTICS_INDEX": 87.0
        }

    def _rng(self, key: str) -> random.Random:
        seed = abs(hash(key)) % (2**32)
        return random.Random(seed)

    def run_backtest(self, indicator: str, window: int = 90) -> Dict:
        indicator = indicator or "EV_DEMAND"
        window = max(30, min(window, 180))
        rng = self._rng(f"{indicator}:{window}")
        base_value = self.base_levels.get(indicator, 100.0)
        series: List[Dict] = []
        today = datetime.utcnow()
        for i in range(window):
            date = today - timedelta(days=window - i)
            drift = (i - window / 2) * 0.05
            noise = rng.uniform(-2, 2)
            actual = round(base_value + drift + noise, 2)
            prediction_error = rng.uniform(-1.5, 1.5)
            predicted = round(actual + prediction_error, 2)
            series.append({
                "date": date.strftime("%Y-%m-%d"),
                "actual": actual,
                "predicted": predicted
            })

        diff = [abs(item["actual"] - item["predicted"]) / max(item["actual"], 1) for item in series]
        mape = round(sum(diff) / len(diff) * 100, 2)
        hit_rate = round(rng.uniform(0.6, 0.88), 2)
        sharpe = round(rng.uniform(0.9, 1.8), 2)
        last_signal = "上行" if series[-1]["predicted"] >= series[-2]["predicted"] else "回调"
        predicted_change = round(series[-1]["predicted"] - series[-7]["predicted"], 2)

        events = [
            {
                "date": series[-idx]["date"],
                "event": desc,
                "impact": impact
            }
            for idx, (desc, impact) in enumerate(
                [
                    ("政策利好发布", "positive"),
                    ("行业竞争加剧", "warning"),
                    ("产能爬坡不及预期", "negative")
                ],
                start=5
            )
        ]

        return {
            "indicator": indicator,
            "window": window,
            "metrics": {
                "mape": mape,
                "hit_rate": hit_rate,
                "sharpe": sharpe,
                "last_signal": last_signal,
                "predicted_change": predicted_change
            },
            "series": series,
            "events": events
        }

    def simulate_scenario(self, scenario: ScenarioInput) -> Dict:
        base = self.base_levels.get(scenario.indicator, 100.0)
        demand_boost = base * scenario.demand_shift
        policy_effect = base * scenario.policy_intensity * 0.8
        supply_drag = base * scenario.supply_shift
        scenario_value = base + demand_boost + policy_effect - supply_drag
        delta = scenario_value - base

        rng = self._rng(f"{scenario.indicator}:{scenario.scenario_name}")
        timeline = []
        for month in range(1, 7):
            month_label = f"M{month}"
            base_line = round(base * (1 + 0.01 * month), 2)
            scenario_line = round(base_line + delta * (month / 6), 2)
            timeline.append({
                "period": month_label,
                "base": base_line,
                "scenario": scenario_line
            })

        recommendations = [
            "提前锁定供应链产能，确保交付弹性",
            "同步调整市场预算，聚焦高 ROI 渠道",
            "建立政策预警机制，跟踪刺激计划兑现率"
        ]
        rng.shuffle(recommendations)

        return {
            "indicator": scenario.indicator,
            "scenario": scenario.scenario_name,
            "assumptions": {
                "demand_shift": scenario.demand_shift,
                "policy_intensity": scenario.policy_intensity,
                "supply_shift": scenario.supply_shift
            },
            "forecast": {
                "base": round(base, 2),
                "scenario": round(scenario_value, 2),
                "delta": round(delta, 2),
                "probability": round(rng.uniform(0.55, 0.82), 2)
            },
            "timeline": timeline,
            "recommendations": recommendations[:2]
        }


trend_scenario_engine = TrendScenarioEngine()

