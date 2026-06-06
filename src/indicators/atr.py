"""Average True Range (ATR) calculation.

Used for stop-loss placement and volatility assessment.
Pure pandas implementation.
"""

import logging
from typing import Optional

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


def compute_atr(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    period: int = 14,
) -> pd.Series:
    """Compute Average True Range (ATR).

    True Range = max(high - low, |high - prev_close|, |low - prev_close|)
    ATR = EMA(TR, period) or SMA(TR, period)

    Args:
        high: High price series.
        low: Low price series.
        close: Close price series.
        period: ATR lookback period (default 14).

    Returns:
        ATR series aligned to input index. First (period) values are NaN.
    """
    if period <= 0:
        raise ValueError(f"ATR period must be positive, got {period}")

    if len(high) < period + 1:
        logger.warning(
            "Series length (%d) insufficient for ATR(period=%d)",
            len(high), period,
        )
        return pd.Series([float("nan")] * len(high), index=high.index)

    prev_close = close.shift(1)

    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()

    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    # Use SMA for first ATR value, then EMA smoothing
    # RMA (Wilder's smoothing) approach: ATR = (prev_ATR * (n-1) + TR) / n
    # But SMA/EMA is more standard and simpler

    atr = true_range.ewm(span=period, adjust=False, min_periods=period).mean()

    return atr


def compute_stop_loss(
    entry_price: float,
    atr_value: float,
    multiplier: float = 1.0,
) -> Optional[float]:
    """Compute stop loss price for a long position.

    stop_loss = entry_price - multiplier * ATR

    Args:
        entry_price: Position entry price.
        atr_value: ATR value at entry or current ATR.
        multiplier: ATR multiplier for stop distance (default 1.0).

    Returns:
        Stop loss price, or None if inputs are invalid.
    """
    if entry_price <= 0:
        logger.warning("Invalid entry price: %.4f", entry_price)
        return None
    if atr_value is None or np.isnan(atr_value) or atr_value <= 0:
        logger.warning("Invalid ATR value: %s", atr_value)
        return None

    stop = entry_price - multiplier * atr_value
    return round(stop, 4)
