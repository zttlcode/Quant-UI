"""
fuzzy_ma 策略交易信号全量分析
============================
分析目标：
1. 盈利交易点的共性特征（技术指标、概率、市场环境）
2. 亏损交易点的特点
3. 结合前端图表逻辑的分类概率分析
"""

import os
import sys
from pathlib import Path
from collections import defaultdict
import numpy as np
import pandas as pd

# ============================================================
# Configuration
# ============================================================
SIGNAL_DIR = Path("D:/ClaudeCode/trade_point_live_inference_fuzzy_ma")
PRICE_DIR = Path("D:/github/RobotMeQ_Dataset/QuantData/live")
INDEX_PRICE_PATH = Path("D:/github/RobotMeQ_Dataset/QuantData/live_index/live_bar_A_000001_d.csv")
INDEX_CONDITION_PATH = Path("D:/github/RobotMeQ_Dataset/QuantData/market_condition_live/A_000001_d.csv")

# Indicator params (matching config.yaml)
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9
MA_PERIODS = [5, 10, 20]
ATR_PERIOD = 14

# ============================================================
# Data Loading
# ============================================================

def load_signals(signal_dir: Path) -> pd.DataFrame:
    """Load all fuzzy_ma signal files into a DataFrame."""
    all_signals = []
    for f in signal_dir.glob("*.csv"):
        # Parse stock code from filename: A_000021_d.csv
        parts = f.stem.split("_")
        if len(parts) >= 3:
            market = parts[0]
            code = parts[1]
            level = parts[2]
        else:
            continue

        try:
            with open(f, "rb") as fh:
                raw = fh.read()
            if raw[:3] == b"\xef\xbb\xbf":
                raw = raw[3:]
            text = raw.decode("utf-8")
        except Exception:
            continue

        lines = [l.strip() for l in text.splitlines() if l.strip()]
        for line in lines:
            fields = line.split(",")
            if len(fields) < 3:
                continue
            # Skip header if present
            if fields[0].lower() in ("time", "date"):
                continue

            try:
                time_val = pd.Timestamp(fields[0].strip())
            except Exception:
                continue

            try:
                price = float(fields[1])
            except ValueError:
                continue

            signal = fields[2].strip().lower()
            label = int(float(fields[3])) if len(fields) >= 4 and fields[3].strip() else None
            prob = float(fields[4]) if len(fields) >= 5 and fields[4].strip() else None

            all_signals.append({
                "time": time_val,
                "price": price,
                "signal": signal,
                "label": label,
                "prob": prob,
                "stock_code": code,
                "market": market,
                "level": level,
            })

    df = pd.DataFrame(all_signals)
    if not df.empty:
        df = df.sort_values(["stock_code", "time"]).reset_index(drop=True)
    return df


def load_price(stock_code: str, market: str = "A", level: str = "d") -> pd.DataFrame:
    """Load price data for a specific stock."""
    filename = f"live_bar_{market}_{stock_code}_{level}.csv"
    filepath = PRICE_DIR / filename
    if not filepath.exists():
        return pd.DataFrame()

    df = pd.read_csv(filepath, parse_dates=["time"])
    df = df.sort_values("time").reset_index(drop=True)
    df.set_index("time", inplace=True)
    return df


def load_index_data() -> tuple:
    """Load index (000001) price and market condition data."""
    idx_price = pd.DataFrame()
    if INDEX_PRICE_PATH.exists():
        idx_price = pd.read_csv(INDEX_PRICE_PATH, parse_dates=["time"])
        idx_price = idx_price.sort_values("time").set_index("time")

    idx_cond = pd.DataFrame()
    if INDEX_CONDITION_PATH.exists():
        idx_cond = pd.read_csv(INDEX_CONDITION_PATH, parse_dates=["time"])
        idx_cond = idx_cond.sort_values("time").set_index("time")

    return idx_price, idx_cond


# ============================================================
# Indicator Computation
# ============================================================

def compute_indicators(price_df: pd.DataFrame) -> pd.DataFrame:
    """Compute technical indicators on price data."""
    df = price_df.copy()
    close = df["close"].astype(float)
    high = df["high"].astype(float)
    low = df["low"].astype(float)
    vol = df["volume"].astype(float)

    # MAs
    for period in MA_PERIODS:
        df[f"ma_{period}"] = close.rolling(period).mean()

    # MACD
    ema_fast = close.ewm(span=MACD_FAST, adjust=False).mean()
    ema_slow = close.ewm(span=MACD_SLOW, adjust=False).mean()
    df["macd_dif"] = ema_fast - ema_slow
    df["macd_dea"] = df["macd_dif"].ewm(span=MACD_SIGNAL, adjust=False).mean()
    df["macd_hist"] = 2 * (df["macd_dif"] - df["macd_dea"])

    # ATR
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    df["atr"] = tr.rolling(ATR_PERIOD).mean()
    df["atr_pct"] = df["atr"] / close  # ATR as % of price (volatility)

    # Volume MA
    df["vol_ma_5"] = vol.rolling(5).mean()
    df["vol_ratio"] = vol / df["vol_ma_5"]

    # Price position relative to MAs
    for period in MA_PERIODS:
        df[f"pct_from_ma_{period}"] = (close - df[f"ma_{period}"]) / df[f"ma_{period}"] * 100

    # Recent returns
    for lookback in [1, 3, 5, 10, 20]:
        df[f"ret_{lookback}d"] = close.pct_change(lookback) * 100

    # High-low range
    df["hl_range"] = (high - low) / close * 100

    return df


def compute_avmood(price_df: pd.DataFrame) -> pd.Series:
    """
    Simplified avmood computation based on fuzzy_ma strategy logic.
    Uses Kalman-filter-based fuzzy inference to estimate trend direction.

    Simplified version: uses MACD + MA crossover signals as proxy.
    avmood > 0 = bullish zone, avmood < 0 = bearish zone.
    """
    close = price_df["close"].astype(float)

    # Trend strength: MACD histogram direction + magnitude
    ema_fast = close.ewm(span=MACD_FAST, adjust=False).mean()
    ema_slow = close.ewm(span=MACD_SLOW, adjust=False).mean()
    dif = ema_fast - ema_slow
    dea = dif.ewm(span=MACD_SIGNAL, adjust=False).mean()
    macd_hist = dif - dea

    # MA divergence
    ma_5 = close.rolling(5).mean()
    ma_20 = close.rolling(20).mean()
    ma_divergence = (ma_5 - ma_20) / ma_20

    # Price momentum (5-day)
    momentum = close.pct_change(5)

    # Combine into avmood proxy (normalized)
    macd_norm = macd_hist / close * 100
    avmood = macd_norm * 0.5 + ma_divergence * 100 * 0.3 + momentum * 100 * 0.2

    return avmood


# ============================================================
# Trade Pairing
# ============================================================

def pair_trades(stock_signals: pd.DataFrame, price_df: pd.DataFrame) -> list:
    """
    Pair buy/sell signals into trades.
    Returns list of trade dicts with PnL and context features.
    """
    if stock_signals.empty:
        return []

    # Sort by time
    sigs = stock_signals.sort_values("time").to_dict("records")

    # Prepare price data with indicators
    price_with_ind = compute_indicators(price_df) if not price_df.empty else price_df
    avmood_series = compute_avmood(price_df) if not price_df.empty else pd.Series()

    trades = []
    current_buy = None

    for sig in sigs:
        if sig["signal"] == "buy":
            # Consecutive buys: keep first
            if current_buy is not None:
                continue  # Keep first buy
            current_buy = sig
        elif sig["signal"] == "sell":
            if current_buy is not None:
                trade = build_trade(current_buy, sig, price_with_ind, avmood_series)
                trades.append(trade)
                current_buy = None
            # else: unexpected sell, ignore

    # Handle open positions
    if current_buy is not None and not price_df.empty:
        last_close = float(price_df["close"].iloc[-1])
        last_time = pd.Timestamp(price_df.index[-1])
        trade = build_trade(current_buy, {
            "time": last_time,
            "price": last_close,
            "signal": "sell",
            "label": None,
            "prob": None,
        }, price_with_ind, avmood_series, is_open=True)
        trades.append(trade)

    return trades


def build_trade(buy_sig: dict, sell_sig: dict, price_df: pd.DataFrame,
                avmood_series: pd.Series, is_open: bool = False) -> dict:
    """Build a single trade with all context features."""

    entry_time = pd.Timestamp(buy_sig["time"])
    exit_time = pd.Timestamp(sell_sig["time"])
    entry_price = buy_sig["price"]
    exit_price = sell_sig["price"]

    pnl_pct = (exit_price - entry_price) / entry_price * 100
    holding_days = (exit_time - entry_time).days

    trade = {
        "stock_code": buy_sig["stock_code"],
        "entry_time": entry_time,
        "exit_time": exit_time,
        "entry_price": entry_price,
        "exit_price": exit_price,
        "pnl_pct": pnl_pct,
        "is_profitable": pnl_pct > 0,
        "holding_days": holding_days,
        "entry_prob": buy_sig["prob"],
        "entry_label": buy_sig["label"],
        "exit_prob": sell_sig.get("prob"),
        "exit_label": sell_sig.get("label"),
        "is_open": is_open,
    }

    # --- Entry-side context features ---
    if not price_df.empty and entry_time in price_df.index:
        idx_pos = price_df.index.get_loc(entry_time)
        row = price_df.iloc[idx_pos]
    elif not price_df.empty:
        # Find nearest row before entry
        try:
            idx_pos = price_df.index.get_indexer([entry_time], method="ffill")[0]
            if idx_pos >= 0:
                row = price_df.iloc[idx_pos]
            else:
                row = None
        except Exception:
            row = None
    else:
        row = None

    if row is not None:
        # Price relative to MAs at entry
        for period in MA_PERIODS:
            key = f"pct_from_ma_{period}"
            if key in price_df.columns:
                val = row.get(key)
                if pd.notna(val):
                    trade[f"entry_{key}"] = float(val)

        # MACD at entry
        for mkey in ["macd_dif", "macd_dea", "macd_hist"]:
            if mkey in price_df.columns:
                val = row.get(mkey)
                if pd.notna(val):
                    trade[f"entry_{mkey}"] = float(val)

        # ATR (volatility) at entry
        if "atr_pct" in price_df.columns:
            val = row.get("atr_pct")
            if pd.notna(val):
                trade["entry_atr_pct"] = float(val) * 100  # as %

        # Volume ratio at entry
        if "vol_ratio" in price_df.columns:
            val = row.get("vol_ratio")
            if pd.notna(val):
                trade["entry_vol_ratio"] = float(val)

        # Recent returns before entry
        for lb in [1, 3, 5, 10]:
            key = f"ret_{lb}d"
            if key in price_df.columns:
                val = row.get(key)
                if pd.notna(val):
                    trade[f"entry_{key}"] = float(val)

        # HL range at entry
        if "hl_range" in price_df.columns:
            val = row.get("hl_range")
            if pd.notna(val):
                trade["entry_hl_range"] = float(val)

        # Close value
        trade["entry_close"] = float(row.get("close", entry_price))

    # --- avmood at entry ---
    if not avmood_series.empty:
        try:
            avmood_val = avmood_series.get(entry_time)
            if avmood_val is None or pd.isna(avmood_val):
                idx_pos = avmood_series.index.get_indexer([entry_time], method="ffill")[0]
                if idx_pos >= 0:
                    avmood_val = avmood_series.iloc[idx_pos]
            if avmood_val is not None and not pd.isna(avmood_val):
                trade["entry_avmood"] = float(avmood_val)
        except Exception:
            pass

    # --- Post-entry forward returns ---
    if not price_df.empty:
        for fd in [1, 3, 5]:
            try:
                future_time = entry_time + pd.Timedelta(days=fd)
                # Find nearest price
                future_idx = price_df.index.get_indexer([future_time], method="ffill")[0]
                if future_idx >= 0 and future_idx < len(price_df):
                    future_close = float(price_df["close"].iloc[future_idx])
                    fwd_ret = (future_close - entry_price) / entry_price * 100
                    trade[f"fwd_ret_{fd}d"] = fwd_ret
            except Exception:
                pass

    return trade


# ============================================================
# Market Context
# ============================================================

def add_market_context(trades: list, idx_price: pd.DataFrame, idx_cond: pd.DataFrame):
    """Add index (market) context to each trade."""
    if idx_price.empty:
        return

    idx_with_ind = compute_indicators(idx_price)
    idx_avmood = compute_avmood(idx_price)

    for trade in trades:
        entry_time = trade["entry_time"]

        # Find index data at entry time
        try:
            idx_pos = idx_price.index.get_indexer([entry_time], method="ffill")[0]
            if idx_pos < 0:
                continue
            idx_row = idx_price.iloc[idx_pos]

            # Index return (last 5 days)
            if len(idx_price) > idx_pos + 1:
                idx_close = float(idx_row["close"])
                idx_close_5d_ago = float(idx_price["close"].iloc[max(0, idx_pos - 5)])
                trade["idx_ret_5d"] = (idx_close - idx_close_5d_ago) / idx_close_5d_ago * 100

            # Index MACD
            if "macd_hist" in idx_with_ind.columns:
                mh = idx_with_ind["macd_hist"].iloc[idx_pos]
                if pd.notna(mh):
                    trade["idx_macd_hist"] = float(mh)

            # Index trend (above/below MA20)
            if "ma_20" in idx_with_ind.columns:
                ma20 = idx_with_ind["ma_20"].iloc[idx_pos]
                close_val = float(idx_row["close"])
                if pd.notna(ma20):
                    trade["idx_pct_from_ma20"] = (close_val - ma20) / ma20 * 100

            # Index avmood
            if not idx_avmood.empty and idx_pos < len(idx_avmood):
                ia = idx_avmood.iloc[idx_pos]
                if pd.notna(ia):
                    trade["idx_avmood"] = float(ia)

        except Exception:
            pass

    # Add market condition classification if available
    if not idx_cond.empty:
        # Check what columns the condition file has
        pass


# ============================================================
# Analysis Functions
# ============================================================

def analyze_overview(trades: list, signals_df: pd.DataFrame):
    """Print overall statistics."""
    closed = [t for t in trades if not t.get("is_open")]
    open_pos = [t for t in trades if t.get("is_open")]

    print("=" * 80)
    print("Fuzzy MA 策略交易信号全量分析")
    print("=" * 80)

    print(f"\n📊 数据概览:")
    print(f"  总信号数: {len(signals_df)}")
    print(f"  股票数: {signals_df['stock_code'].nunique()}")
    print(f"  买入信号: {(signals_df['signal']=='buy').sum()}")
    print(f"  卖出信号: {(signals_df['signal']=='sell').sum()}")

    # Label distribution
    if "label" in signals_df.columns:
        print(f"\n📋 信号分类分布:")
        label_counts = signals_df["label"].value_counts().sort_index()
        label_names = {1: "有效买入", 2: "无效买入", 3: "有效卖出", 4: "无效卖出"}
        for lbl, cnt in label_counts.items():
            print(f"  label={lbl} ({label_names.get(int(lbl), '未知')}): {cnt} 个")

    print(f"\n💼 交易配对结果:")
    print(f"  已平仓交易: {len(closed)}")
    print(f"  未平仓持仓: {len(open_pos)}")

    if closed:
        profitable = sum(1 for t in closed if t["is_profitable"])
        print(f"\n📈 已平仓交易表现:")
        print(f"  盈利交易: {profitable} ({profitable/len(closed)*100:.1f}%)")
        print(f"  亏损交易: {len(closed) - profitable} ({(len(closed)-profitable)/len(closed)*100:.1f}%)")
        print(f"  平均收益率: {np.mean([t['pnl_pct'] for t in closed]):.2f}%")
        print(f"  最大盈利: {max(t['pnl_pct'] for t in closed):.2f}%")
        print(f"  最大亏损: {min(t['pnl_pct'] for t in closed):.2f}%")
        print(f"  平均持仓天数: {np.mean([t['holding_days'] for t in closed]):.1f} 天")

    if open_pos:
        print(f"\n📌 未平仓持仓表现 (按最新价估算):")
        profitable_open = sum(1 for t in open_pos if t["is_profitable"])
        print(f"  浮盈: {profitable_open}")
        print(f"  浮亏: {len(open_pos) - profitable_open}")
        print(f"  平均浮动盈亏: {np.mean([t['pnl_pct'] for t in open_pos]):.2f}%")

    return closed, open_pos


def analyze_profitable_vs_losing(closed_trades: list):
    """Compare characteristics of profitable vs losing trades."""
    if not closed_trades:
        print("\n⚠️ 没有已平仓交易，无法进行盈利/亏损对比分析")
        return

    profitable = [t for t in closed_trades if t["is_profitable"]]
    losing = [t for t in closed_trades if not t["is_profitable"]]

    print("\n" + "=" * 80)
    print("🔍 盈利 vs 亏损交易特征对比")
    print("=" * 80)

    # Features to compare
    numeric_features = [
        ("entry_prob", "入场信号概率"),
        ("entry_pct_from_ma_5", "入场时距MA5 (%)"),
        ("entry_pct_from_ma_10", "入场时距MA10 (%)"),
        ("entry_pct_from_ma_20", "入场时距MA20 (%)"),
        ("entry_macd_dif", "入场时MACD DIF"),
        ("entry_macd_hist", "入场时MACD柱"),
        ("entry_atr_pct", "入场时ATR% (波动率)"),
        ("entry_vol_ratio", "入场时量比"),
        ("entry_ret_1d", "入场前1日涨幅(%)"),
        ("entry_ret_3d", "入场前3日涨幅(%)"),
        ("entry_ret_5d", "入场前5日涨幅(%)"),
        ("entry_ret_10d", "入场前10日涨幅(%)"),
        ("entry_avmood", "入场时avmood"),
        ("entry_hl_range", "入场时日内振幅(%)"),
        ("holding_days", "持仓天数"),
        ("idx_ret_5d", "同期指数5日涨幅(%)"),
        ("idx_macd_hist", "同期指数MACD柱"),
        ("idx_pct_from_ma20", "同期指数距MA20(%)"),
        ("idx_avmood", "同期指数avmood"),
    ]

    print(f"\n{'特征':<28} {'盈利组均值':>12} {'亏损组均值':>12} {'差值':>10} {'方向'}")
    print("-" * 80)

    for key, name in numeric_features:
        p_vals = [t.get(key) for t in profitable if t.get(key) is not None]
        l_vals = [t.get(key) for t in losing if t.get(key) is not None]

        if len(p_vals) >= 1 and len(l_vals) >= 1:
            p_mean = np.mean(p_vals)
            l_mean = np.mean(l_vals)
            diff = p_mean - l_mean
            direction = "盈利组更高 ↑" if diff > 0 else "亏损组更高 ↓"

            print(f"{name:<28} {p_mean:>12.4f} {l_mean:>12.4f} {diff:>+10.4f} {direction}")
        elif len(p_vals) >= 1:
            print(f"{name:<28} {np.mean(p_vals):>12.4f} {'N/A':>12} {'N/A':>10} (仅盈利组有数据)")
        elif len(l_vals) >= 1:
            print(f"{name:<28} {'N/A':>12} {np.mean(l_vals):>12.4f} {'N/A':>10} (仅亏损组有数据)")

    # Probability analysis
    print(f"\n🎯 信号概率分析:")
    p_probs = [t["entry_prob"] for t in profitable if t.get("entry_prob") is not None]
    l_probs = [t["entry_prob"] for t in losing if t.get("entry_prob") is not None]

    if p_probs and l_probs:
        print(f"  盈利组买入信号平均概率: {np.mean(p_probs):.4f}")
        print(f"  亏损组买入信号平均概率: {np.mean(l_probs):.4f}")
        for threshold in [0.8, 0.85, 0.9]:
            p_above = sum(1 for p in p_probs if p >= threshold)
            l_above = sum(1 for p in l_probs if p >= threshold)
            print(f"  概率 ≥ {threshold}: 盈利组 {p_above}/{len(p_probs)} ({p_above/len(p_probs)*100:.0f}%), "
                  f"亏损组 {l_above}/{len(l_probs)} ({l_above/len(l_probs)*100:.0f}%)")

    # MA position at entry
    print(f"\n📐 入场均线位置分析:")
    for ma_key, ma_name in [("entry_pct_from_ma_5", "MA5"), ("entry_pct_from_ma_10", "MA10"),
                              ("entry_pct_from_ma_20", "MA20")]:
        p_above = sum(1 for t in profitable if t.get(ma_key) is not None and t[ma_key] > 0)
        l_above = sum(1 for t in losing if t.get(ma_key) is not None and t[ma_key] > 0)
        p_total = sum(1 for t in profitable if t.get(ma_key) is not None)
        l_total = sum(1 for t in losing if t.get(ma_key) is not None)
        if p_total > 0 and l_total > 0:
            print(f"  入场价 > {ma_name}: 盈利组 {p_above}/{p_total} ({p_above/p_total*100:.0f}%), "
                  f"亏损组 {l_above}/{l_total} ({l_above/l_total*100:.0f}%)")

    # AVMood direction
    print(f"\n🌊 avmood 方向分析:")
    for group, name in [(profitable, "盈利组"), (losing, "亏损组")]:
        bull = sum(1 for t in group if t.get("entry_avmood") is not None and t["entry_avmood"] > 0)
        bear = sum(1 for t in group if t.get("entry_avmood") is not None and t["entry_avmood"] < 0)
        total = bull + bear
        if total > 0:
            print(f"  {name}: 多头区间(avmood>0) {bull}/{total} ({bull/total*100:.0f}%), "
                  f"空头区间(avmood<0) {bear}/{total} ({bear/total*100:.0f}%)")

    return profitable, losing


def analyze_open_positions(open_trades: list, signals_df: pd.DataFrame):
    """Analyze open positions."""
    if not open_trades:
        return

    print("\n" + "=" * 80)
    print("[Open] 未平仓持仓分析")
    print("=" * 80)

    print(f"\n  持仓数量: {len(open_trades)}")
    probs = [t["entry_prob"] for t in open_trades if t.get("entry_prob") is not None]
    if probs:
        print(f"  平均买入概率: {np.mean(probs):.4f}")
        print(f"  概率分布: min={min(probs):.4f}, median={np.median(probs):.4f}, max={max(probs):.4f}")

    pnl_list = [t["pnl_pct"] for t in open_trades]
    print(f"  浮动盈亏范围: {min(pnl_list):.2f}% ~ {max(pnl_list):.2f}%")
    print(f"  平均浮动盈亏: {np.mean(pnl_list):.2f}%")

    # Top 5 winners and losers
    sorted_open = sorted(open_trades, key=lambda t: t["pnl_pct"], reverse=True)
    print(f"\n  🏆 浮盈最多的5个:")
    for t in sorted_open[:5]:
        print(f"    {t['stock_code']}: +{t['pnl_pct']:.2f}% (入场{t['entry_time'].strftime('%m-%d')} "
              f"@{t['entry_price']:.2f}, prob={t.get('entry_prob', 'N/A')})")

    print(f"\n  📉 浮亏最多的5个:")
    for t in sorted_open[-5:]:
        print(f"    {t['stock_code']}: {t['pnl_pct']:.2f}% (入场{t['entry_time'].strftime('%m-%d')} "
              f"@{t['entry_price']:.2f}, prob={t.get('entry_prob', 'N/A')})")


def analyze_entry_timing(closed_trades: list):
    """Analyze the impact of entry date/timing."""
    if not closed_trades:
        return

    print("\n" + "=" * 80)
    print("📅 入场时机分析")
    print("=" * 80)

    # By entry date
    by_date = defaultdict(list)
    for t in closed_trades:
        date_key = t["entry_time"].strftime("%m-%d")
        by_date[date_key].append(t["pnl_pct"])

    print(f"\n  每日入场平均收益:")
    for date_key in sorted(by_date.keys()):
        avg = np.mean(by_date[date_key])
        cnt = len(by_date[date_key])
        bar = "█" * max(1, int(abs(avg) * 5))
        sign = "+" if avg >= 0 else ""
        print(f"  {date_key} ({cnt}笔): {sign}{avg:.2f}% {bar}")

    # By holding period
    print(f"\n  持仓天数与收益关系:")
    for days_range, label in [((1, 1), "当日平仓"), ((2, 3), "2-3天"), ((4, 7), "4-7天"), ((8, 14), "8-14天"),
                                ((15, 30), "15-30天")]:
        lo, hi = days_range
        subset = [t for t in closed_trades if lo <= t["holding_days"] <= hi]
        if subset:
            avg = np.mean([t["pnl_pct"] for t in subset])
            win_rate = sum(1 for t in subset if t["is_profitable"]) / len(subset) * 100
            print(f"  {label}: {len(subset)}笔, 平均收益 {avg:+.2f}%, 胜率 {win_rate:.0f}%")


def analyze_prob_thresholds(closed_trades: list):
    """Analyze how signal probability correlates with PnL."""
    if not closed_trades:
        return

    print("\n" + "=" * 80)
    print("🎯 概率阈值与交易表现")
    print("=" * 80)

    valid = [t for t in closed_trades if t.get("entry_prob") is not None]
    if not valid:
        return

    thresholds = [0.7, 0.75, 0.8, 0.85, 0.9, 0.95]
    print(f"\n  {'概率阈值':<12} {'交易数':>8} {'胜率':>8} {'平均收益':>10}")
    print(f"  {'-'*40}")
    for thresh in thresholds:
        subset = [t for t in valid if t["entry_prob"] >= thresh]
        if subset:
            cnt = len(subset)
            win_rate = sum(1 for t in subset if t["is_profitable"]) / cnt * 100
            avg_pnl = np.mean([t["pnl_pct"] for t in subset])
            print(f"  ≥ {thresh:<9} {cnt:>8} {win_rate:>7.1f}% {avg_pnl:>+9.2f}%")


def analyze_trade_details(closed_trades: list):
    """Print detailed info about each trade."""
    print("\n" + "=" * 80)
    print("📋 逐笔交易明细")
    print("=" * 80)

    print(f"\n  {'股票':<8} {'入场日':>10} {'出场日':>10} {'入场价':>8} {'出场价':>8} "
          f"{'收益%':>8} {'持仓天':>6} {'概率':>6} {'avmood':>8} {'盈利?'}")
    print(f"  {'-'*90}")

    for t in sorted(closed_trades, key=lambda x: x["pnl_pct"], reverse=True):
        avmood_str = f"{t.get('entry_avmood', 0):.4f}" if t.get("entry_avmood") is not None else "N/A"
        print(f"  {t['stock_code']:<8} {t['entry_time'].strftime('%m-%d'):>10} "
              f"{t['exit_time'].strftime('%m-%d'):>10} {t['entry_price']:>8.2f} "
              f"{t['exit_price']:>8.2f} {t['pnl_pct']:>+7.2f}% {t['holding_days']:>5}d "
              f"{t.get('entry_prob', 'N/A'):>6} {avmood_str:>8} {'✅' if t['is_profitable'] else '❌'}")


def analyze_signal_sequence(signals_df: pd.DataFrame, closed_trades: list):
    """Analyze signal sequences and patterns."""
    print("\n" + "=" * 80)
    print("🔗 信号序列模式分析")
    print("=" * 80)

    # Per-stock signal patterns
    stock_sequences = defaultdict(list)
    for _, row in signals_df.iterrows():
        stock_sequences[row["stock_code"]].append(row["signal"])

    pattern_counts = defaultdict(int)
    for code, seq in stock_sequences.items():
        pattern = "→".join(seq)
        pattern_counts[pattern] += 1

    print(f"\n  信号序列模式分布:")
    for pattern, cnt in sorted(pattern_counts.items(), key=lambda x: -x[1]):
        print(f"  [{cnt:>3}只] {pattern}")

    # Consecutive buys
    consec_buy = sum(1 for seq in stock_sequences.values() if len([s for s in seq if s == "buy"]) >= 2)
    print(f"\n  出现连续买入的股票: {consec_buy} 只")

    # Only-buy stocks (no sell)
    only_buy = sum(1 for seq in stock_sequences.values() if "sell" not in seq)
    print(f"  仅有买入信号的股票: {only_buy} 只 (这些是未平仓持仓)")

    # Buy-sell pairs
    paired = sum(1 for seq in stock_sequences.values() if "buy" in seq and "sell" in seq)
    print(f"  有完整买卖配对的股票: {paired} 只")


# ============================================================
# Main
# ============================================================

def main():
    print("🔄 加载信号数据...")
    signals_df = load_signals(SIGNAL_DIR)
    if signals_df.empty:
        print("❌ 未找到信号数据!")
        return
    print(f"   ✓ 加载 {len(signals_df)} 条信号, {signals_df['stock_code'].nunique()} 只股票")

    print("🔄 加载指数数据...")
    idx_price, idx_cond = load_index_data()
    print(f"   ✓ 指数行情: {len(idx_price)} 条")
    print(f"   ✓ 市场状态: {len(idx_cond)} 条")

    print("🔄 配对交易并计算指标...")
    all_trades = []
    stock_codes = signals_df["stock_code"].unique()
    for i, code in enumerate(stock_codes):
        if (i + 1) % 20 == 0:
            print(f"   处理中... {i+1}/{len(stock_codes)}")

        stock_sigs = signals_df[signals_df["stock_code"] == code]
        price_df = load_price(code)

        if price_df.empty:
            continue

        trades = pair_trades(stock_sigs, price_df)
        all_trades.extend(trades)

    print(f"   ✓ 共生成 {len(all_trades)} 笔交易")

    print("🔄 添加市场环境上下文...")
    add_market_context(all_trades, idx_price, idx_cond)

    # ---- Analysis ----
    closed_trades, open_trades = analyze_overview(all_trades, signals_df)

    analyze_signal_sequence(signals_df, closed_trades)

    profitable, losing = analyze_profitable_vs_losing(closed_trades)

    analyze_entry_timing(closed_trades)

    analyze_prob_thresholds(closed_trades)

    analyze_open_positions(open_trades, signals_df)

    analyze_trade_details(closed_trades)

    # ---- Summary & Recommendations ----
    print("\n" + "=" * 80)
    print("📝 关键发现与建议")
    print("=" * 80)
    print("""
    分析维度说明：
    - avmood > 0: 多头区间，avmood < 0: 空头区间
    - label=1: 有效买入，label=3: 有效卖出
    - prob: 模型推理置信度 (0~1)
    - 入场距MA: 正值为价格在均线上方，负值为下方
    """)

    print("\n✅ 分析完成!")


if __name__ == "__main__":
    main()
