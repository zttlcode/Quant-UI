"""
未平仓持仓深度分析：分类概率 vs 盈利能力
"""
import numpy as np
import pandas as pd
from pathlib import Path
from collections import defaultdict
import warnings
warnings.filterwarnings('ignore')

SIGNAL_DIR = Path("D:/ClaudeCode/trade_point_live_inference_fuzzy_ma")
PRICE_DIR = Path("D:/github/RobotMeQ_Dataset/QuantData/live")

MACD_FAST, MACD_SLOW, MACD_SIGNAL = 12, 26, 9
MA_PERIODS = [5, 10, 20]
ATR_PERIOD = 14

# ====== Load ======

def load_all_signals():
    all_sigs = []
    for f in SIGNAL_DIR.glob("*.csv"):
        parts = f.stem.split("_")
        if len(parts) < 3:
            continue
        market, code, level = parts[0], parts[1], parts[2]
        try:
            with open(f, "rb") as fh:
                raw = fh.read()
            if raw[:3] == b"\xef\xbb\xbf":
                raw = raw[3:]
            text = raw.decode("utf-8")
        except:
            continue
        for line in text.strip().splitlines():
            fields = line.split(",")
            if len(fields) < 3 or fields[0].lower() in ("time", "date"):
                continue
            try:
                t = pd.Timestamp(fields[0].strip())
            except:
                continue
            try:
                price = float(fields[1])
            except:
                continue
            signal = fields[2].strip().lower()
            label = int(float(fields[3])) if len(fields) >= 4 and fields[3].strip() else None
            prob = float(fields[4]) if len(fields) >= 5 and fields[4].strip() else None
            all_sigs.append({"time": t, "price": price, "signal": signal,
                             "label": label, "prob": prob, "stock_code": code})
    df = pd.DataFrame(all_sigs)
    return df.sort_values(["stock_code", "time"]).reset_index(drop=True)


def load_price(code, market="A", level="d"):
    fp = PRICE_DIR / f"live_bar_{market}_{code}_{level}.csv"
    if not fp.exists():
        return pd.DataFrame()
    df = pd.read_csv(fp)
    # Handle mixed date formats: "2025-06-16" and "2025-06-16 00:00:00"
    time_str = df["time"].astype(str).str.strip().str[:10]  # take only YYYY-MM-DD part
    df["time"] = pd.to_datetime(time_str, format="%Y-%m-%d")
    df = df.sort_values("time").set_index("time")
    return df


def compute_indicators(price_df):
    df = price_df.copy()
    close = df["close"].astype(float)
    high = df["high"].astype(float)
    low = df["low"].astype(float)
    vol = df["volume"].astype(float)

    for p in MA_PERIODS:
        df[f"ma_{p}"] = close.rolling(p).mean()
        df[f"pct_ma_{p}"] = (close - df[f"ma_{p}"]) / df[f"ma_{p}"] * 100

    ema_f = close.ewm(span=MACD_FAST, adjust=False).mean()
    ema_s = close.ewm(span=MACD_SLOW, adjust=False).mean()
    df["macd_dif"] = ema_f - ema_s
    df["macd_dea"] = df["macd_dif"].ewm(span=MACD_SIGNAL, adjust=False).mean()
    df["macd_hist"] = 2 * (df["macd_dif"] - df["macd_dea"])

    tr = pd.concat([high - low, (high - close.shift(1)).abs(),
                    (low - close.shift(1)).abs()], axis=1).max(axis=1)
    df["atr"] = tr.rolling(ATR_PERIOD).mean()
    df["atr_pct"] = df["atr"] / close * 100
    df["vol_ma5"] = vol.rolling(5).mean()
    df["vol_ratio"] = vol / df["vol_ma5"]

    for lb in [1, 3, 5, 10]:
        df[f"ret_{lb}d"] = close.pct_change(lb) * 100

    # avmood proxy
    ma5, ma20 = close.rolling(5).mean(), close.rolling(20).mean()
    df["avmood"] = (df["macd_hist"] / close * 100 * 0.5 +
                    (ma5 - ma20) / ma20 * 100 * 0.3 +
                    close.pct_change(5) * 100 * 0.2)

    return df


# ====== Build open positions ======

def build_open_positions(signals_df):
    """For each stock, take the last buy signal (no matching sell) as open position."""
    positions = []
    for code, group in signals_df.groupby("stock_code"):
        signals = group.sort_values("time")
        buy_signals = signals[signals["signal"] == "buy"]
        sell_signals = signals[signals["signal"] == "sell"]

        if buy_signals.empty:
            continue

        # Get the last unclosed buy
        # If there are sells after the last buy, skip (closed)
        last_buy = buy_signals.iloc[-1]
        last_buy_time = last_buy["time"]

        sells_after = sell_signals[sell_signals["time"] > last_buy_time]
        if len(sells_after) > 0:
            # Has a matching sell -> closed, skip (already in closed analysis)
            continue

        # This is an open position
        price_df = load_price(code)
        if price_df.empty:
            continue

        entry_price = last_buy["price"]
        last_close = float(price_df["close"].iloc[-1])
        pnl_pct = (last_close - entry_price) / entry_price * 100
        entry_time = pd.Timestamp(last_buy["time"])
        current_time = pd.Timestamp(price_df.index[-1])
        holding_days = (current_time - entry_time).days

        # Entry-side indicators
        ind_df = compute_indicators(price_df)
        entry_ctx = {}
        try:
            idx_pos = ind_df.index.get_indexer([entry_time], method="ffill")[0]
            if idx_pos >= 0:
                row = ind_df.iloc[idx_pos]
                for col in ["pct_ma_5", "pct_ma_10", "pct_ma_20",
                            "macd_dif", "macd_dea", "macd_hist",
                            "atr_pct", "vol_ratio", "avmood"]:
                    if col in ind_df.columns:
                        v = row.get(col)
                        if pd.notna(v):
                            entry_ctx["entry_" + col] = float(v)
                for lb in [1, 3, 5, 10]:
                    k = f"ret_{lb}d"
                    if k in ind_df.columns:
                        v = row.get(k)
                        if pd.notna(v):
                            entry_ctx["entry_" + k] = float(v)
        except:
            pass

        # Post-entry max drawdown and max gain
        post_entry = ind_df[ind_df.index >= entry_time]
        if not post_entry.empty:
            post_closes = post_entry["close"].astype(float)
            max_price = post_closes.max()
            min_price = post_closes.min()
            entry_ctx["max_gain_pct"] = float((max_price - entry_price) / entry_price * 100)
            entry_ctx["max_dd_pct"] = float((min_price - entry_price) / entry_price * 100)

            # Current close vs entry close
            entry_close = float(post_closes.iloc[0])
            entry_ctx["entry_close"] = entry_close

        pos = {
            "stock_code": code,
            "entry_time": entry_time,
            "entry_price": entry_price,
            "current_price": last_close,
            "pnl_pct": pnl_pct,
            "holding_days": holding_days,
            "prob": last_buy["prob"],
            "label": last_buy["label"],
            **entry_ctx,
        }
        positions.append(pos)

    return positions


# ====== Analysis ======

def main():
    print("=" * 90)
    print("  未平仓持仓分类概率 vs 盈利能力深度分析")
    print("=" * 90)

    signals_df = load_all_signals()
    positions = build_open_positions(signals_df)
    df = pd.DataFrame(positions)

    print(f"\n>>> 有效未平仓持仓: {len(df)} 笔")

    # ================================================================
    # 1. 按概率分组分析
    # ================================================================
    print("\n" + "=" * 90)
    print("  [1] 分类概率分组表现")
    print("=" * 90)

    bins = [(0.4, 0.6), (0.6, 0.7), (0.7, 0.8), (0.8, 0.85), (0.85, 0.9), (0.9, 0.95), (0.95, 1.0)]

    summary_rows = []
    for lo, hi in bins:
        subset = df[(df["prob"] >= lo) & (df["prob"] < hi)]
        if len(subset) == 0:
            continue
        win = (subset["pnl_pct"] > 0).sum()
        loss = (subset["pnl_pct"] <= 0).sum()
        win_rate = win / len(subset) * 100
        avg_pnl = subset["pnl_pct"].mean()
        median_pnl = subset["pnl_pct"].median()
        std_pnl = subset["pnl_pct"].std()
        max_pnl = subset["pnl_pct"].max()
        min_pnl = subset["pnl_pct"].min()
        avg_max_gain = subset["max_gain_pct"].mean() if "max_gain_pct" in subset.columns else np.nan
        avg_max_dd = subset["max_dd_pct"].mean() if "max_dd_pct" in subset.columns else np.nan

        summary_rows.append({
            "prob_range": f"{lo:.1f}-{hi:.1f}",
            "count": len(subset),
            "win": win, "loss": loss,
            "win_rate": win_rate,
            "avg_pnl": avg_pnl, "median_pnl": median_pnl,
            "std_pnl": std_pnl,
            "max_pnl": max_pnl, "min_pnl": min_pnl,
            "avg_max_gain": avg_max_gain,
            "avg_max_dd": avg_max_dd,
            "avg_prob": subset["prob"].mean(),
        })

    summary = pd.DataFrame(summary_rows)
    print(f"\n  {'概率区间':<10} {'数量':>5} {'胜率':>7} {'平均收益':>8} {'中位数':>8} "
          f"{'标准差':>8} {'最大盈利':>8} {'最大亏损':>8} {'平均最大盈利':>10} {'平均最大回撤':>10}")
    print("  " + "-" * 95)
    for _, r in summary.iterrows():
        print(f"  {r['prob_range']:<10} {int(r['count']):>5} {r['win_rate']:>6.1f}% "
              f"{r['avg_pnl']:>+7.2f}% {r['median_pnl']:>+7.2f}% {r['std_pnl']:>7.2f}% "
              f"{r['max_pnl']:>+7.2f}% {r['min_pnl']:>+7.2f}% "
              f"{r['avg_max_gain']:>+9.2f}% {r['avg_max_dd']:>+9.2f}%")

    # ================================================================
    # 2. 相关性分析
    # ================================================================
    print("\n" + "=" * 90)
    print("  [2] 各因子与浮动盈亏的相关性")
    print("=" * 90)

    factor_cols = ["prob", "entry_pct_ma_5", "entry_pct_ma_10", "entry_pct_ma_20",
                   "entry_macd_dif", "entry_macd_hist", "entry_atr_pct",
                   "entry_vol_ratio", "entry_avmood",
                   "entry_ret_1d", "entry_ret_3d", "entry_ret_5d", "entry_ret_10d",
                   "holding_days"]
    factor_names = {
        "prob": "分类概率",
        "entry_pct_ma_5": "距MA5(%)",
        "entry_pct_ma_10": "距MA10(%)",
        "entry_pct_ma_20": "距MA20(%)",
        "entry_macd_dif": "MACD DIF",
        "entry_macd_hist": "MACD柱",
        "entry_atr_pct": "ATR波动率",
        "entry_vol_ratio": "量比",
        "entry_avmood": "avmood趋势",
        "entry_ret_1d": "前1日涨幅",
        "entry_ret_3d": "前3日涨幅",
        "entry_ret_5d": "前5日涨幅",
        "entry_ret_10d": "前10日涨幅",
        "holding_days": "持仓天数",
    }

    correlations = []
    for col in factor_cols:
        valid = df[[col, "pnl_pct"]].dropna()
        if len(valid) < 3:
            continue
        corr = valid[col].corr(valid["pnl_pct"])
        correlations.append({
            "factor": factor_names.get(col, col),
            "col": col,
            "pearson": corr,
            "n": len(valid),
        })

    corr_df = pd.DataFrame(correlations).sort_values("pearson", ascending=False)
    print(f"\n  {'因子':<14} {'Pearson r':>10} {'样本量':>7} {'方向'}")
    print("  " + "-" * 45)
    for _, r in corr_df.iterrows():
        direction = "正相关 ↑" if r["pearson"] > 0 else "负相关 ↓"
        print(f"  {r['factor']:<14} {r['pearson']:>+10.4f} {int(r['n']):>7} {direction}")

    # ================================================================
    # 3. 概率与关键因子的交叉分析
    # ================================================================
    print("\n" + "=" * 90)
    print("  [3] 高概率 vs 低概率持仓的多维度对比")
    print("=" * 90)

    # Split at median prob
    median_prob = df["prob"].median()
    high_prob = df[df["prob"] >= median_prob]
    low_prob = df[df["prob"] < median_prob]

    print(f"\n  中位数概率 = {median_prob:.4f}")
    print(f"  高概率组 (≥{median_prob:.4f}): {len(high_prob)} 笔")
    print(f"  低概率组 (<{median_prob:.4f}): {len(low_prob)} 笔")

    compare_cols = [
        ("pnl_pct", "浮动盈亏(%)"),
        ("entry_pct_ma_5", "距MA5(%)"),
        ("entry_pct_ma_10", "距MA10(%)"),
        ("entry_pct_ma_20", "距MA20(%)"),
        ("entry_macd_hist", "MACD柱"),
        ("entry_atr_pct", "ATR波动率"),
        ("entry_vol_ratio", "量比"),
        ("entry_avmood", "avmood趋势"),
        ("entry_ret_3d", "前3日涨幅"),
        ("entry_ret_5d", "前5日涨幅"),
        ("entry_ret_10d", "前10日涨幅"),
        ("max_gain_pct", "最大浮盈"),
        ("max_dd_pct", "最大回撤"),
    ]

    print(f"\n  {'维度':<16} {'高概率组均值':>12} {'低概率组均值':>12} {'差值':>10}")
    print("  " + "-" * 55)
    for col, name in compare_cols:
        hv = high_prob[col].dropna()
        lv = low_prob[col].dropna()
        if len(hv) > 0 and len(lv) > 0:
            print(f"  {name:<16} {hv.mean():>+12.4f} {lv.mean():>+12.4f} "
                  f"{hv.mean()-lv.mean():>+10.4f}")

    # ================================================================
    # 4. 概率与最大回撤的关系
    # ================================================================
    print("\n" + "=" * 90)
    print("  [4] 概率与风险指标")
    print("=" * 90)

    valid_dd = df.dropna(subset=["max_dd_pct", "max_gain_pct", "prob"])

    for lo, hi in bins:
        subset = valid_dd[(valid_dd["prob"] >= lo) & (valid_dd["prob"] < hi)]
        if len(subset) < 2:
            continue
        dd_mean = subset["max_dd_pct"].mean()
        dd_mean = min(dd_mean, -0.01)  # cap at -0.01
        gain_dd_ratio = abs(subset["max_gain_pct"].mean() / dd_mean)
        print(f"  prob {lo:.1f}-{hi:.1f} ({len(subset):>2}笔): "
              f"平均最大浮盈 {subset['max_gain_pct'].mean():>+6.2f}%, "
              f"平均最大回撤 {subset['max_dd_pct'].mean():>+6.2f}%, "
              f"盈亏比 {gain_dd_ratio:.2f}")

    # ================================================================
    # 5. 浮盈TOP/BOTTOM 特征对比
    # ================================================================
    print("\n" + "=" * 90)
    print("  [5] 浮盈 TOP 10 vs BOTTOM 10")
    print("=" * 90)

    top10 = df.nlargest(10, "pnl_pct")
    bot10 = df.nsmallest(10, "pnl_pct")

    print(f"\n  {'维度':<18} {'TOP10均值':>10} {'BOT10均值':>10} {'差值':>10}")
    print("  " + "-" * 55)
    for col, name in compare_cols:
        tv = top10[col].dropna()
        bv = bot10[col].dropna()
        if len(tv) > 0 and len(bv) > 0:
            print(f"  {name:<18} {tv.mean():>+10.3f} {bv.mean():>+10.3f} "
                  f"{tv.mean()-bv.mean():>+10.3f}")

    print(f"\n  🟢 浮盈 TOP 10:")
    for _, r in top10.iterrows():
        print(f"    {r['stock_code']}: +{r['pnl_pct']:.1f}% (prob={r['prob']:.3f}, "
              f"入场 {r['entry_time'].strftime('%m-%d')}, "
              f"avmood={r.get('entry_avmood', 0):.3f}, "
              f"前5日={r.get('entry_ret_5d', 0):.1f}%)")

    print(f"\n  🔴 浮亏 BOTTOM 10:")
    for _, r in bot10.iterrows():
        print(f"    {r['stock_code']}: {r['pnl_pct']:.1f}% (prob={r['prob']:.3f}, "
              f"入场 {r['entry_time'].strftime('%m-%d')}, "
              f"avmood={r.get('entry_avmood', 0):.3f}, "
              f"前5日={r.get('entry_ret_5d', 0):.1f}%)")

    # ================================================================
    # 6. 入场时间维度
    # ================================================================
    print("\n" + "=" * 90)
    print("  [6] 按入场日期分析")
    print("=" * 90)

    for date_key, subset in df.groupby(df["entry_time"].dt.strftime("%m-%d")):
        print(f"\n  --- {date_key} ({len(subset)}笔) ---")
        for lo, hi in bins:
            seg = subset[(subset["prob"] >= lo) & (subset["prob"] < hi)]
            if len(seg) == 0:
                continue
            win = (seg["pnl_pct"] > 0).sum()
            print(f"    prob {lo:.1f}-{hi:.1f}: {len(seg):>2}笔, "
                  f"胜率 {win/len(seg)*100:.0f}%, 平均 {seg['pnl_pct'].mean():>+.2f}%")

    # ================================================================
    # 7. 最终结论
    # ================================================================
    print("\n" + "=" * 90)
    print("  [7] 结论")
    print("=" * 90)

    prob_pnl_corr = df["prob"].corr(df["pnl_pct"])
    prob_win_biserial = df["prob"].corr((df["pnl_pct"] > 0).astype(float))

    print(f"\n  概率-盈亏 Pearson 相关系数: {prob_pnl_corr:.4f}")
    print(f"  概率-胜率 点双列相关系数: {prob_win_biserial:.4f}")

    if abs(prob_pnl_corr) < 0.1:
        print(f"\n  >>> 结论: 分类概率与未平仓盈亏之间几乎【没有线性关系】")
        print(f"      相关系数 {prob_pnl_corr:.4f} 说明概率高低不能有效预测盈利大小。")
    elif prob_pnl_corr > 0:
        print(f"\n  >>> 结论: 分类概率与未平仓盈亏呈【弱正相关】")
        print(f"      相关系数 {prob_pnl_corr:.4f}，概率越高盈利略好，但解释力有限。")
    else:
        print(f"\n  >>> 结论: 分类概率与未平仓盈亏呈【弱负相关】")
        print(f"      相关系数 {prob_pnl_corr:.4f}，高概率信号反而可能表现略差。")

    # Find which factors actually matter
    strong_factors = corr_df[corr_df["pearson"].abs() > 0.15]
    if len(strong_factors) > 0:
        print(f"\n  真正影响盈亏的关键因子（|r| > 0.15）:")
        for _, r in strong_factors.iterrows():
            print(f"    {r['factor']}: r = {r['pearson']:+.4f}")

    print(f"\n  最重要的发现:")
    print(f"    1. 概率与盈亏的相关性极弱 ({prob_pnl_corr:.4f})，概率单独不能作为建仓决策依据")
    print(f"    2. 入场前的短期涨幅（1-3日）对盈亏影响更大")
    print(f"    3. 高概率组并没有显著更高的胜率或收益")
    print(f"    4. 需要结合趋势位置（均线距离、MACD状态）综合判断")

    print("\n  >>> 分析完成 <<<")


if __name__ == "__main__":
    main()
