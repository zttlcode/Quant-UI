"""Concrete strategy adapters for built-in strategies.

- FuzzyMAAdapter: fuzzy_ma strategy with avmood extra data
- TeaRadicalNatureAdapter: tea_radical_nature strategy (standard MA-based)
"""

import logging
from typing import Optional, List

import pandas as pd

from .base import BaseStrategyAdapter
from ..config.settings import AppConfig
from ..data_loader.extra_data import FuzzyMAExtraDataLoader

logger = logging.getLogger(__name__)


class FuzzyMAAdapter(BaseStrategyAdapter):
    """Adapter for the fuzzy_ma strategy.

    Uses fuzzy inference for trend detection with avmood indicator.
    Provides extra avmood visualization layer.
    """

    strategy_name = "fuzzy_ma"
    display_name = "Fuzzy MA 策略"

    def __init__(self, config: AppConfig):
        super().__init__(config)
        self._extra_loader = FuzzyMAExtraDataLoader(config)

    @property
    def description(self) -> str:
        return (
            "基于模糊推理的自适应移动平均策略。"
            "使用 Kalman 滤波估计价格趋势参数，avmood 指标判断买卖方向。"
            "avmood > 0 为多头区间，avmood < 0 为空头区间。"
        )

    def get_extra_description(self) -> str:
        return self._extra_loader.get_description() if self._extra_loader else ""


class TeaRadicalNatureAdapter(BaseStrategyAdapter):
    """Adapter for the tea_radical_nature strategy.

    A trend-following strategy based on tea radical nature analysis.
    Standard MA-based signals without extra visualization data.
    """

    strategy_name = "tea_radical_nature"
    display_name = "Tea Radical Nature 策略"

    @property
    def description(self) -> str:
        return (
            "基于茶轴激进自然法则的趋势跟踪策略。"
            "利用多周期均线和价格行为识别买卖点。"
        )
