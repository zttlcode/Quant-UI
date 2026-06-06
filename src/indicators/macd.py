"""MACD indicator calculation.

Standard MACD computation:
  EMA_fast = EMA(close, fast_period)
  EMA_slow = EMA(close, slow_period)
  DIF = EMA_fast - EMA_slow
  DEA = EMA(DIF, signal_period)
  MACD = 2 * (DIF - DEA)

Pure pandas implementation to minimize external dependencies.
"""

import logging
from typing import Tuple

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


def compute_ema(series: pd.Series, period: int) -> pd.Series:
    """Compute Exponential Moving Average (EMA).

    Uses pandas ewm for efficient computation.
    First (period-1) values will be NaN.

    Args:
        series: Price series.
        period: EMA period.

    Returns:
        EMA series aligned with input.
    """
    if period <= 0:
        raise ValueError(f"EMA period must be positive, got {period}")
    if len(series) < period:
        logger.warning(
            "Series length (%d) < EMA period (%d), returning all NaN",
            len(series), period,
        )
        return pd.Series([float("nan")] * len(series), index=series.index)

    return series.ewm(span=period, adjust=False, min_periods=period).mean()


def compute_macd(
    series: pd.Series,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> pd.DataFrame:
    """Compute MACD indicator.

    Args:
        series: Close price series.
        fast: Fast EMA period (default 12).
        slow: Slow EMA period (default 26).
        signal: Signal line EMA period (default 9).

    Returns:
        DataFrame with columns: EMA_fast, EMA_slow, DIF, DEA, MACD.
        All aligned to input series index.
        NaN for insufficient data periods.
    """
    if len(series) < slow + signal:
        logger.warning(
            "Series length (%d) insufficient for MACD (need at least %d bars)",
            len(series), slow + signal,
        )
        result = pd.DataFrame(index=series.index)
        result["DIF"] = float("nan")
        result["DEA"] = float("nan")
        result["MACD"] = float("nan")
        return result

    ema_fast = compute_ema(series, fast)
    ema_slow = compute_ema(series, slow)

    dif = ema_fast - ema_slow
    dea = compute_ema(dif, signal)
    macd_bar = 2.0 * (dif - dea)

    result = pd.DataFrame(index=series.index)
    result["DIF"] = dif
    result["DEA"] = dea
    result["MACD"] = macd_bar

    return result
