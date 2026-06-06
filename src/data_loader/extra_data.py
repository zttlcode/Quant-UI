"""Strategy extra data loader.

Provides an abstract interface for loading strategy-specific supplemental data.
Implements the FuzzyMA extra data loader (aa/avmood data).
"""

import logging
from abc import ABC, abstractmethod
from typing import Optional

import numpy as np
import pandas as pd

from ..config.settings import AppConfig

logger = logging.getLogger(__name__)


def _meb(x: float, w1: float, w2: float, w3: float) -> float:
    """Fuzzy membership function — 7 fuzzy sets.

    Piecewise membership function μ(x) with three anchor points w1, w2, w3.
    Returns μ value in [0, 1].
    """
    y = 0.0
    if x <= w1:
        y = 0.0
    if w1 < x <= w2:
        y = (x - w1) / (w2 - w1) if w2 != w1 else 0.0
    if w2 < x <= w3:
        y = (w3 - x) / (w3 - w2) if w3 != w2 else 0.0
    if x > w3:
        y = 0.0

    if w1 == w2:
        if x <= w2:
            y = 1.0
        if w2 < x <= w3:
            y = (w3 - x) / (w3 - w2) if w3 != w2 else 0.0
        if x > w3:
            y = 0.0

    if w2 == w3:
        if x <= w1:
            y = 0.0
        if w1 < x <= w2:
            y = (x - w1) / (w2 - w1) if w2 != w1 else 0.0
        if x > w2:
            y = 1.0

    return y


def fuzzy(windowDF: pd.DataFrame):
    """Core fuzzy_ma inference algorithm.

    Runs fuzzy Kalman-filter-based parameter estimation on OHLCV data.

    Args:
        windowDF: DataFrame with 'close' column. Expected length: ~250 bars.

    Returns:
        Tuple of (n1, n2, aa) where:
        - n1: start index (fixed 1)
        - n2: end index (len(windowDF))
        - aa: (2, 1, n) numpy array of adaptive parameters
    """
    p = windowDF["close"].tolist()
    n = len(windowDF)
    c = 0.01
    n1 = 1
    n2 = n
    ma1 = 5
    lmd = 0.95
    P = np.eye(2) * windowDF.iloc[0]["close"]
    aa = np.zeros((2, 1, n))
    error = np.zeros(n)

    for k in range(n1 + ma1):
        aa[:, :, k] = np.array([[0.0], [0.0]])

    for k in range(n1 + ma1, n2 - 1):
        try:
            pa = np.sum(p[k - ma1 : k]) / ma1
            x3 = np.log(p[k] / pa) if p[k] > 0 and pa > 0 else 0.0

            y1 = _meb(x3, 0, c, 2 * c)
            y2 = _meb(x3, c, 2 * c, 3 * c)
            y3 = _meb(x3, 2 * c, 3 * c, 3 * c)
            y4 = _meb(x3, -2 * c, -c, 0)
            y5 = _meb(x3, -3 * c, -2 * c, -c)
            y6 = _meb(x3, -3 * c, -3 * c, -2 * c)
            y7 = _meb(x3, -c, 0, c)

            y = y1 + y2 + y3 + y7
            ed1 = 0.0
            if y != 0:
                ed1 = (-0.1 * y1 - 0.2 * y2 - 0.4 * y3) / y

            y = y4 + y5 + y6 + y7
            ed2 = 0.0
            if y != 0:
                ed2 = (0.1 * y4 + 0.2 * y5 + 0.4 * y6) / y

            x = np.array([[ed1], [ed2]])

            error[k] = (
                np.log(p[k + 1] / p[k]) - np.dot(x.T, aa[:, :, k - 1])
            ).item()

            K = np.dot(P, x) / (np.dot(np.dot(x.T, P), x) + lmd)
            aa[:, :, k] = aa[:, :, k - 1] + np.dot(K, error[k])
            P = (P - np.dot(np.dot(K, x.T), P)) / lmd

        except Exception as e:
            logger.debug("Fuzzy iteration %d failed: %s", k, e)

    return n1, n2, aa


class StrategyExtraDataLoader(ABC):
    """Abstract base class for loading strategy-specific extra data.

    Subclasses implement _load_extra_data to provide strategy-specific
    visualizations (e.g., avmood for fuzzy_ma).
    """

    def __init__(self, config: AppConfig):
        self.config = config

    @property
    @abstractmethod
    def strategy_name(self) -> str:
        """Name of the strategy this loader handles."""
        ...

    @abstractmethod
    def _load_extra_data(
        self,
        stock_code: str,
        price_df: pd.DataFrame,
        market: str,
        level: str,
    ) -> Optional[pd.DataFrame]:
        """Load extra data for a specific stock."""
        ...

    def load(
        self,
        stock_code: str,
        price_df: pd.DataFrame,
        market: str = "A",
        level: str = "d",
    ) -> Optional[pd.DataFrame]:
        """Public interface for loading extra data."""
        try:
            return self._load_extra_data(stock_code, price_df, market, level)
        except Exception as e:
            logger.error(
                "Failed to load extra data for %s (strategy=%s): %s",
                stock_code, self.strategy_name, e,
            )
            return None

    def get_description(self) -> str:
        """Description of what extra data this loader provides."""
        return ""

    def needs_subplot(self) -> bool:
        """Whether this extra data requires its own subplot."""
        return True


class FuzzyMAExtraDataLoader(StrategyExtraDataLoader):
    """Fuzzy MA extra indicators — computes avmood from price data via fuzzy().

    The fuzzy_ma strategy uses fuzzy inference (Kalman filter on fuzzy
    membership values) to produce:
    - aa: 2x1xN array of adaptive parameters (a0, a1)
    - mood: a1 - a0  (positive → bullish, negative → bearish)
    - avmood: 5-period rolling mean of mood
    - avmood_cross: +1 when avmood crosses above 0, -1 when below

    Since price data is always 250 bars, fuzzy() is called in real time
    for every request — no pre-computed CSV needed.
    """

    strategy_name = "fuzzy_ma"

    def _compute_avmood(self, price_df: pd.DataFrame) -> pd.DataFrame:
        """Compute avmood from price data using the fuzzy inference engine.

        Args:
            price_df: DataFrame with 'close' column, indexed by time.

        Returns:
            DataFrame indexed by time with columns: mood, avmood, avmood_cross.
        """
        n = len(price_df)
        result = pd.DataFrame(index=price_df.index)

        if n < 10:
            logger.warning("Insufficient data for fuzzy inference (n=%d < 10)", n)
            result["mood"] = np.nan
            result["avmood"] = np.nan
            result["avmood_cross"] = 0
            return result

        # Run fuzzy inference
        n1, n2, aa = fuzzy(price_df)

        # Compute mood = a1 - a0
        mood = np.full(n, np.nan, dtype=float)
        for k in range(n):
            a0 = aa[0, 0, k]
            a1 = aa[1, 0, k]
            mood[k] = a1 - a0

        # Compute avmood = 5-period rolling mean of mood
        avmood = np.full(n, np.nan, dtype=float)
        for k in range(5, n):
            avmood[k] = np.nanmean(mood[k - 4 : k + 1])

        # Detect zero-crossings
        avmood_cross = np.zeros(n, dtype=int)
        for k in range(1, n):
            if np.isnan(avmood[k]) or np.isnan(avmood[k - 1]):
                continue
            if avmood[k] > 0 and avmood[k - 1] <= 0:
                avmood_cross[k] = 1
            elif avmood[k] < 0 and avmood[k - 1] >= 0:
                avmood_cross[k] = -1

        result["mood"] = mood
        result["avmood"] = avmood
        result["avmood_cross"] = avmood_cross

        logger.info(
            "Computed avmood for %s: n=%d, mood_range=[%.4f, %.4f]",
            price_df.index[0] if len(price_df) > 0 else "?",
            n,
            float(np.nanmin(mood)) if not np.all(np.isnan(mood)) else 0.0,
            float(np.nanmax(mood)) if not np.all(np.isnan(mood)) else 0.0,
        )

        return result

    def _load_extra_data(
        self,
        stock_code: str,
        price_df: pd.DataFrame,
        market: str = "A",
        level: str = "d",
    ) -> Optional[pd.DataFrame]:
        """Compute fuzzy_ma extra data (avmood) from price data."""
        logger.info("Computing fuzzy extra data for %s (%d bars)", stock_code, len(price_df))
        return self._compute_avmood(price_df)

    def get_description(self) -> str:
        return (
            "Fuzzy MA 辅助图层: avmood 曲线, "
            "avmood 上穿 0 / 下穿 0 标记, "
            "MA 买点相对 avmood 上穿 0 的滞后/领先 K 线数"
        )

    def needs_subplot(self) -> bool:
        return True
