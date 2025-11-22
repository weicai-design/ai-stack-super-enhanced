import math
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.algorithms.exponential_smoothing import (
    holt_winters_forecast,
    HoltWintersParams,
    simple_exponential_smoothing,
)


def test_simple_exponential_smoothing_monotonic():
    series = [10, 12, 14, 16]
    smoothed = simple_exponential_smoothing(series, alpha=0.5)
    assert len(smoothed) == len(series)
    assert smoothed[-1] > smoothed[0]


def test_holt_winters_forecast_reasonable():
    series = [100 + math.sin(i / 2) * 5 for i in range(48)]
    params = HoltWintersParams(alpha=0.4, beta=0.2, gamma=0.3, season_length=8)
    forecasts, mape = holt_winters_forecast(series, steps=6, params=params)
    assert len(forecasts) == 6
    assert 0 <= mape < 20

