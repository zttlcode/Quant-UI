"""Risk indicator computation for strategy signal evaluation.

Provides functions to compute:
- avmood (fuzzy MA trend direction) via simplified fast proxy
- Pre-N-day returns for overbought detection
- ATR% for volatility assessment
- MA alignment (bullish/bearish) detection
- Composite risk scoring

These indicators are used by:
- Market classification page (index avmood visualization)
- Strategy detail page (risk columns in asset list)
"""

import logging
from typing import Optional, Dict, Tuple, List

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Default indicator parameters (match config.yaml)
_DEFAULT_MACD_FAST = 12
_DEFAULT_MACD_SLOW = 26
_DEFAULT_MACD_SIGNAL = 9
_DEFAULT_MA_PERIODS = [5, 10, 20]
_DEFAULT_ATR_PERIOD = 14

# Risk thresholds
RISK_RET_5D_HIGH = 15.0    # 前5日涨幅 > 15% → 追高风险
RISK_ATR_PCT_HIGH = 6.0    # ATR% > 6% → 高波动风险
RISK_VOL_RATIO_HIGH = 2.0  # 量比 > 2.0 → 异常放量


def compute_risk_indicators(
    price_df: pd.DataFrame,
    macd_fast: int = _DEFAULT_MACD_FAST,
    macd_slow: int = _DEFAULT_MACD_SLOW,
    macd_signal: int = _DEFAULT_MACD_SIGNAL,
    ma_periods: List[int] = _DEFAULT_MA_PERIODS,
    atr_period: int = _DEFAULT_ATR_PERIOD,
) -> pd.DataFrame:
    """Compute all risk-related indicators from OHLCV price data.

    Computes the following columns on a copy of the input DataFrame:

    Trend / Momentum:
    - ret_1d, ret_3d, ret_5d, ret_10d : rolling returns (%)
    - pct_ma_5, pct_ma_10, pct_ma_20   : distance from MAs (%)
    - ma_bullish                         : 1 if MA5 > MA10 > MA20, else 0

    MACD:
    - macd_dif, macd_dea, macd_hist

    Volatility / Volume:
    - atr, atr_pct    : ATR value and ATR as % of close
    - vol_ratio       : volume / 5-day avg volume

    Fuzzy trend:
    - avmood          : simplified avmood proxy (MACD + MA divergence + momentum)

    Args:
        price_df: DataFrame with 'open','high','low','close','volume' columns,
                  indexed by time (DatetimeIndex).

    Returns:
        DataFrame with all indicator columns added.
    """
    df = price_df.copy()
    close = df["close"].astype(float)
    high = df["high"].astype(float)
    low = df["low"].astype(float)
    vol = df["volume"].astype(float)

    # ---- Moving Averages ----
    for period in ma_periods:
        df[f"ma_{period}"] = close.rolling(period).mean()
        df[f"pct_ma_{period}"] = (
            (close - df[f"ma_{period}"]) / df[f"ma_{period}"] * 100
        )

    # MA bullish alignment: MA5 > MA10 > MA20
    df["ma_bullish"] = (
        (df["ma_5"] > df["ma_10"]) & (df["ma_10"] > df["ma_20"])
    ).astype(int)

    # ---- MACD ----
    ema_fast = close.ewm(span=macd_fast, adjust=False).mean()
    ema_slow = close.ewm(span=macd_slow, adjust=False).mean()
    df["macd_dif"] = ema_fast - ema_slow
    df["macd_dea"] = df["macd_dif"].ewm(span=macd_signal, adjust=False).mean()
    df["macd_hist"] = 2 * (df["macd_dif"] - df["macd_dea"])

    # ---- ATR ----
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    df["atr"] = tr.rolling(atr_period).mean()
    df["atr_pct"] = df["atr"] / close * 100  # ATR as % of price

    # ---- Volume ----
    df["vol_ma_5"] = vol.rolling(5).mean()
    df["vol_ratio"] = vol / df["vol_ma_5"]

    # ---- Returns (momentum) ----
    for lb in [1, 3, 5, 10]:
        df[f"ret_{lb}d"] = close.pct_change(lb) * 100

    # ---- avmood (simplified proxy, scaled to match real fuzzy() output) ----
    # Uses the same logic as the full fuzzy() inference but simplified.
    # All components are in raw decimal (NOT percentage) to match the scale
    # of FuzzyMAExtraDataLoader._compute_avmood() which produces values in
    # the [-0.10, +0.10] range from Kalman-filter-estimated log-return params.
    #   avmood = MACD_hist/close * 0.5 + MA_divergence * 0.3 + momentum_5d * 0.2
    macd_norm_raw = df["macd_hist"] / close          # raw ratio, e.g. 0.02
    ma_div_raw = (df["ma_5"] - df["ma_20"]) / df["ma_20"]  # raw ratio, e.g. 0.08
    momentum_5d_raw = close.pct_change(5)             # decimal, e.g. 0.12
    df["avmood"] = macd_norm_raw * 0.5 + ma_div_raw * 0.3 + momentum_5d_raw * 0.2

    # avmood trend strength: 3-day slope of avmood
    df["avmood_slope"] = df["avmood"].diff(3)

    return df


def get_latest_indicators(price_df: pd.DataFrame) -> Dict[str, float]:
    """Get the latest (most recent) risk indicator values.

    Args:
        price_df: OHLCV DataFrame indexed by time.

    Returns:
        Dict of indicator_name → value for the most recent bar.
        Returns empty dict if price_df has insufficient data.
    """
    ind_df = compute_risk_indicators(price_df)
    if ind_df.empty:
        return {}

    latest = ind_df.iloc[-1]
    result = {}
    for col in [
        "ret_1d", "ret_3d", "ret_5d", "ret_10d",
        "pct_ma_5", "pct_ma_10", "pct_ma_20",
        "ma_bullish",
        "macd_dif", "macd_hist",
        "atr_pct", "vol_ratio",
        "avmood", "avmood_slope",
    ]:
        if col in ind_df.columns:
            val = latest[col]
            if pd.notna(val):
                result[col] = float(val)

    return result


def get_indicator_at_entry(
    price_df: pd.DataFrame,
    entry_time,
) -> Dict[str, float]:
    """Get risk indicators at a specific entry time (or nearest prior bar).

    Args:
        price_df: OHLCV DataFrame indexed by time.
        entry_time: Entry timestamp (datetime or str).

    Returns:
        Dict of indicator values at entry time.
    """
    ind_df = compute_risk_indicators(price_df)
    if ind_df.empty:
        return {}

    try:
        entry_ts = pd.Timestamp(entry_time)
        idx_pos = ind_df.index.get_indexer([entry_ts], method="ffill")[0]
        if idx_pos < 0 or idx_pos >= len(ind_df):
            return {}
    except Exception:
        return {}

    row = ind_df.iloc[idx_pos]
    result = {}
    for col in [
        "ret_1d", "ret_3d", "ret_5d", "ret_10d",
        "pct_ma_5", "pct_ma_10", "pct_ma_20",
        "ma_bullish",
        "macd_dif", "macd_hist",
        "atr_pct", "vol_ratio",
        "avmood", "avmood_slope",
    ]:
        if col in ind_df.columns:
            val = row[col]
            if pd.notna(val):
                result[col] = float(val)

    return result


def classify_risk_level(indicators: Dict[str, float]) -> Tuple[str, str, list]:
    """Classify risk level from indicator values.

    Args:
        indicators: Dict from get_latest_indicators() or get_indicator_at_entry().

    Returns:
        Tuple of (risk_level, risk_color, risk_warnings) where:
        - risk_level: "低风险" | "中风险" | "高风险"
        - risk_color: "green" | "orange" | "red"
        - risk_warnings: list of warning strings
    """
    warnings = []
    risk_score = 0

    # Check pre-5-day return (追高风险)
    ret_5d = indicators.get("ret_5d")
    if ret_5d is not None and ret_5d > RISK_RET_5D_HIGH:
        warnings.append(f"⚠️ 前5日涨幅 {ret_5d:.1f}%（追高风险）")
        risk_score += 3

    # Check ATR% (volatility risk)
    atr_pct = indicators.get("atr_pct")
    if atr_pct is not None and atr_pct > RISK_ATR_PCT_HIGH:
        warnings.append(f"⚠️ ATR 波动率 {atr_pct:.1f}%（高波动）")
        risk_score += 2

    # Check MA alignment
    ma_bull = indicators.get("ma_bullish")
    if ma_bull is not None and ma_bull == 0:
        warnings.append("⚠️ 均线非多头排列")
        risk_score += 2

    # Check avmood (trend direction) — real fuzzy scale: [-0.10, +0.10]
    avmood = indicators.get("avmood")
    if avmood is not None and avmood < 0:
        warnings.append(f"⚠️ avmood 空头区间 ({avmood:.4f})")
        risk_score += 3
    elif avmood is not None and avmood < 0.01:
        warnings.append(f"⚡ avmood 趋势偏弱 ({avmood:.4f})")
        risk_score += 1

    # Check volume ratio
    vol_ratio = indicators.get("vol_ratio")
    if vol_ratio is not None and vol_ratio > RISK_VOL_RATIO_HIGH:
        warnings.append(f"⚠️ 异常放量 (量比 {vol_ratio:.1f})")
        risk_score += 1

    # Check MACD
    macd_hist = indicators.get("macd_hist")
    macd_dif = indicators.get("macd_dif")
    if macd_dif is not None and macd_dif < 0:
        warnings.append(f"⚡ MACD DIF 为负 ({macd_dif:.3f})")
        risk_score += 1

    if risk_score >= 5:
        return "高风险", "red", warnings
    elif risk_score >= 2:
        return "中风险", "orange", warnings
    else:
        return "低风险", "green", warnings
