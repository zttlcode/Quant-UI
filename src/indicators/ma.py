"""Moving Average calculations.

Pure pandas implementation for MA5, MA10, MA20.
Returns NaN for periods where there isn't enough data (no padding/filling).
"""

import logging
from typing import List

import pandas as pd

logger = logging.getLogger(__name__)


def compute_ma(series: pd.Series, period: int) -> pd.Series:
    """Compute Simple Moving Average (SMA) for a given period.

    Args:
        series: Price series (typically close prices).
        period: MA window size (e.g., 5, 10, 20).

    Returns:
        Series of same length with MA values. First (period-1) values are NaN.
    """
    if period <= 0:
        raise ValueError(f"MA period must be positive, got {period}")
    if len(series) < period:
        logger.warning(
            "Series length (%d) < MA period (%d), returning all NaN", len(series), period
        )
        return pd.Series([float("nan")] * len(series), index=series.index)

    return series.rolling(window=period, min_periods=period).mean()


def compute_multiple_mas(
    series: pd.Series,
    periods: List[int],
) -> pd.DataFrame:
    """Compute multiple MAs for a price series.

    Args:
        series: Price series (close prices).
        periods: List of MA periods (e.g., [5, 10, 20]).

    Returns:
        DataFrame with columns MA{period} for each period, indexed same as input.
    """
    result = pd.DataFrame(index=series.index)
    for p in periods:
        col_name = f"MA{p}"
        result[col_name] = compute_ma(series, p)
    return result
