#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
示例：趋势分析 Sidecar 微服务

运行：`uvicorn services.trend_sidecar:app --port 8022`
"""

from fastapi import FastAPI
from pydantic import BaseModel, Field

from 🚀 Super Agent Main Interface.core.trend_scenario_engine import TrendScenarioEngine, ScenarioInput

app = FastAPI(title="Trend Ops Service", version="v1")
scenario_engine = TrendScenarioEngine()


class BacktestRequest(BaseModel):
    indicator: str = Field("EV_DEMAND")
    window: int = Field(90, ge=30, le=180)


class ScenarioRequest(BaseModel):
    indicator: str = Field(..., description="指标ID，如 EV_DEMAND")
    scenario_name: str = Field(..., description="情景名称")
    demand_shift: float = 0.05
    policy_intensity: float = 0.08
    supply_shift: float = 0.02


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/v1/trend/backtest")
async def run_backtest(req: BacktestRequest):
    return scenario_engine.run_backtest(indicator=req.indicator, window=req.window)


@app.post("/v1/trend/scenario")
async def run_scenario(req: ScenarioRequest):
    scenario = ScenarioInput(
        indicator=req.indicator,
        scenario_name=req.scenario_name,
        demand_shift=req.demand_shift,
        policy_intensity=req.policy_intensity,
        supply_shift=req.supply_shift,
    )
    return scenario_engine.simulate_scenario(scenario)

