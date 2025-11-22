#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
趋势分析：指数平滑与 Holt-Winters

提供轻量级的预测算法，避免依赖外部 SciPy/Statsmodels。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple


def simple_exponential_smoothing(series: List[float], alpha: float = 0.4) -> List[float]:
    if not series:
        return []
    smoothed = [series[0]]
    for value in series[1:]:
        smoothed.append(alpha * value + (1 - alpha) * smoothed[-1])
    return smoothed


@dataclass
class HoltWintersParams:
    alpha: float = 0.4  # level
    beta: float = 0.3   # trend
    gamma: float = 0.3  # season
    season_length: int = 4


def holt_winters_forecast(series: List[float], steps: int = 4, params: HoltWintersParams | None = None) -> Tuple[List[float], float]:
    if params is None:
        params = HoltWintersParams()
    if len(series) < params.season_length:
        return simple_exponential_smoothing(series), 0.0

    seasonals = _initial_seasonal_components(series, params.season_length)
    level = sum(series[:params.season_length]) / params.season_length
    trend = _initial_trend(series, params.season_length)

    result = []
    for i, value in enumerate(series):
        seasonal = seasonals[i % params.season_length]
        last_level = level
        level = params.alpha * (value / seasonal) + (1 - params.alpha) * (level + trend)
        trend = params.beta * (level - last_level) + (1 - params.beta) * trend
        seasonals[i % params.season_length] = params.gamma * (value / level) + (1 - params.gamma) * seasonal
        result.append((level + trend) * seasonals[i % params.season_length])

    forecasts = []
    for h in range(1, steps + 1):
        seasonal = seasonals[(len(series) + h - 1) % params.season_length]
        forecasts.append((level + h * trend) * seasonal)

    mape = _mape(series[-params.season_length:], result[-params.season_length:])
    return forecasts, mape


def _initial_trend(series: List[float], season_length: int) -> float:
    sum_val = 0.0
    for i in range(season_length):
        sum_val += (series[i + season_length] - series[i]) / season_length
    return sum_val / season_length


def _initial_seasonal_components(series: List[float], season_length: int) -> List[float]:
    seasonals = [0.0] * season_length
    season_averages = [
        sum(series[season_length * i: season_length * (i + 1)]) / season_length
        for i in range(len(series) // season_length)
    ]
    for i in range(season_length):
        sum_of_vals = sum(series[season_length * j + i] - season_averages[j] for j in range(len(season_averages)))
        seasonals[i] = sum_of_vals / len(season_averages)
    return seasonals


def _mape(actual: List[float], forecast: List[float]) -> float:
    if not actual or not forecast:
        return 0.0
    errors = [
        abs(a - f) / a
        for a, f in zip(actual, forecast)
        if a != 0
    ]
    return round(sum(errors) / len(errors) * 100, 2) if errors else 0.0


