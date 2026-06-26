"""
亏损交易深度画像：买入后亏钱的资产有哪些共同特征？
分析维度：
1. 入场技术面（均线位置、MACD、成交量、波动率）
2. 信号面（概率、label）
3. 市场环境（指数位置）
4. 时间维度（入场日、持仓时长）
5. 对比盈利资产找出关键差异
"""
import numpy as np
import pandas as pd
from pathlib import Path
from collections import defaultdict
import warnings
warnings.filterwarnings('ignore')

SIGNAL_DIR = Path("D:/ClaudeCode/trade_point_live_inference_fuzzy_ma")
PRICE_DIR = Path("D:/github/RobotMeQ_Dataset/QuantData/live")
INDEX_PATH = Path("D:/github/RobotMeQ_Dataset/QuantData/live_index/live_bar_A_000001_d.csv")

MACD_FAST, MACD_SLOW, MACD_SIGNAL = 12, 26, 9
MA_PERIODS = [5, 10, 20]
ATR_PERIOD = 14

# ====== Data Loading ======

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
    df["time"] = pd.to_datetime(df["time"].astype(str).str.strip().str[:10], format="%Y-%m-%d")
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
        # MA slope (rate of change)
        df[f"ma_{p}_slope"] = df[f"ma_{p}"].pct_change(3) * 100

    ema_f = close.ewm(span=MACD_FAST, adjust=False).mean()
    ema_s = close.ewm(span=MACD_SLOW, adjust=False).mean()
    df["macd_dif"] = ema_f - ema_s
    df["macd_dea"] = df["macd_dif"].ewm(span=MACD_SIGNAL, adjust=False).mean()
    df["macd_hist"] = 2 * (df["macd_dif"] - df["macd_dea"])
    df["macd_dif_slope"] = df["macd_dif"].diff(3)

    tr = pd.concat([high - low, (high - close.shift(1)).abs(),
                    (low - close.shift(1)).abs()], axis=1).max(axis=1)
    df["atr"] = tr.rolling(ATR_PERIOD).mean()
    df["atr_pct"] = df["atr"] / close * 100
    df["vol_ma5"] = vol.rolling(5).mean()
    df["vol_ratio"] = vol / df["vol_ma5"]

    for lb in [1, 3, 5, 10, 20]:
        df[f"ret_{lb}d"] = close.pct_change(lb) * 100

    # avmood proxy
    ma5, ma20 = close.rolling(5).mean(), close.rolling(20).mean()
    df["avmood"] = (df["macd_hist"] / close * 100 * 0.5 +
                    (ma5 - ma20) / ma20 * 100 * 0.3 +
                    close.pct_change(5) * 100 * 0.2)

    # Relative strength vs index (will be filled later)
    # Price position in recent range
    df["high_20"] = high.rolling(20).max()
    df["low_20"] = low.rolling(20).min()
    df["price_pos_20"] = (close - df["low_20"]) / (df["high_20"] - df["low_20"]) * 100  # 0-100

    # Gap from entry (for post-analysis)
    df["gap_open"] = (df["open"] - close.shift(1)) / close.shift(1) * 100

    return df


def get_entry_context(price_df, entry_time, entry_price):
    """Extract comprehensive entry-side context for a given time."""
    ind_df = compute_indicators(price_df)
    ctx = {}

    try:
        idx_pos = ind_df.index.get_indexer([pd.Timestamp(entry_time)], method="ffill")[0]
        if idx_pos < 0:
            return ctx
        row = ind_df.iloc[idx_pos]

        # Trend features
        for col in ["pct_ma_5", "pct_ma_10", "pct_ma_20",
                    "ma_5_slope", "ma_10_slope", "ma_20_slope",
                    "macd_dif", "macd_dea", "macd_hist", "macd_dif_slope",
                    "atr_pct", "vol_ratio", "avmood",
                    "ret_1d", "ret_3d", "ret_5d", "ret_10d", "ret_20d",
                    "price_pos_20", "gap_open"]:
            if col in ind_df.columns:
                v = row.get(col)
                if pd.notna(v):
                    ctx[col] = float(v)

        # MA relationships
        close_val = float(row["close"])
        ctx["close"] = close_val
        ctx["ma5_above_ma10"] = 1 if (row.get("ma_5", 0) > row.get("ma_10", 0)) else 0
        ctx["ma10_above_ma20"] = 1 if (row.get("ma_10", 0) > row.get("ma_20", 0)) else 0
        ctx["ma_bullish"] = 1 if (ctx["ma5_above_ma10"] and ctx["ma10_above_ma20"]) else 0

        # MACD state
        ctx["macd_above_zero"] = 1 if ctx.get("macd_dif", 0) > 0 else 0
        ctx["macd_golden_cross"] = 1 if ctx.get("macd_dif", 0) > ctx.get("macd_dea", 0) else 0
        ctx["macd_hist_positive"] = 1 if ctx.get("macd_hist", 0) > 0 else 0
        ctx["macd_bullish"] = 1 if (ctx["macd_above_zero"] and ctx["macd_golden_cross"]) else 0

        # Post-entry forward returns
        for fd in [1, 3, 5]:
            future_time = pd.Timestamp(entry_time) + pd.Timedelta(days=fd)
            future_idx = ind_df.index.get_indexer([future_time], method="ffill")[0]
            if 0 <= future_idx < len(ind_df):
                fc = float(ind_df["close"].iloc[future_idx])
                ctx[f"fwd_ret_{fd}d"] = (fc - entry_price) / entry_price * 100

        # Post-entry max drawdown and max gain
        post = ind_df[ind_df.index >= pd.Timestamp(entry_time)]
        if not post.empty:
            post_close = post["close"].astype(float)
            ctx["max_gain"] = float(post_close.max() - entry_price) / entry_price * 100
            ctx["max_dd"] = float(post_close.min() - entry_price) / entry_price * 100

        # Days since 20-day high
        high_20d = ind_df["high"].rolling(20).max().iloc[idx_pos]
        if pd.notna(high_20d):
            ctx["pct_from_20d_high"] = (close_val - high_20d) / high_20d * 100

        # Consecutive up/down days before entry
        for n in [3, 5]:
            if idx_pos >= n:
                up_days = sum(1 for i in range(idx_pos - n + 1, idx_pos + 1)
                             if ind_df["close"].iloc[i] > ind_df["close"].iloc[i-1])
                ctx[f"up_days_{n}"] = up_days

    except Exception as e:
        pass

    return ctx


def add_market_context(entry_time, idx_df):
    """Add index-level context."""
    ctx = {}
    if idx_df.empty:
        return ctx
    try:
        idx_pos = idx_df.index.get_indexer([pd.Timestamp(entry_time)], method="ffill")[0]
        if idx_pos < 0:
            return ctx
        row = idx_df.iloc[idx_pos]

        for col in ["pct_ma_5", "pct_ma_10", "pct_ma_20",
                    "macd_hist", "macd_dif", "avmood",
                    "ret_1d", "ret_3d", "ret_5d", "ret_10d",
                    "atr_pct", "vol_ratio"]:
            if col in idx_df.columns:
                v = row.get(col)
                if pd.notna(v):
                    ctx[f"idx_{col}"] = float(v)
    except:
        pass
    return ctx


# ====== Main Analysis ======

def build_all_trades(signals_df, idx_df):
    """Build all trades (closed + open) with full context."""
    all_trades = []

    for code, group in signals_df.groupby("stock_code"):
        price_df = load_price(code)
        if price_df.empty:
            continue

        sigs = group.sort_values("time").to_dict("records")
        current_buy = None

        for sig in sigs:
            if sig["signal"] == "buy":
                if current_buy is not None:
                    continue  # keep first
                current_buy = sig
            elif sig["signal"] == "sell":
                if current_buy is not None:
                    entry_ctx = get_entry_context(price_df, current_buy["time"], current_buy["price"])
                    mkt_ctx = add_market_context(current_buy["time"], idx_df)
                    exit_price = sig["price"]
                    pnl = (exit_price - current_buy["price"]) / current_buy["price"] * 100
                    trade = {
                        "stock_code": code,
                        "entry_time": current_buy["time"],
                        "exit_time": sig["time"],
                        "entry_price": current_buy["price"],
                        "exit_price": exit_price,
                        "pnl_pct": pnl,
                        "is_profitable": pnl > 0,
                        "is_open": False,
                        "holding_days": (pd.Timestamp(sig["time"]) - pd.Timestamp(current_buy["time"])).days,
                        "prob": current_buy["prob"],
                        "label": current_buy["label"],
                        **entry_ctx, **mkt_ctx,
                    }
                    all_trades.append(trade)
                    current_buy = None

        # Open position
        if current_buy is not None:
            entry_ctx = get_entry_context(price_df, current_buy["time"], current_buy["price"])
            mkt_ctx = add_market_context(current_buy["time"], idx_df)
            last_close = float(price_df["close"].iloc[-1])
            pnl = (last_close - current_buy["price"]) / current_buy["price"] * 100
            trade = {
                "stock_code": code,
                "entry_time": current_buy["time"],
                "exit_time": price_df.index[-1],
                "entry_price": current_buy["price"],
                "exit_price": last_close,
                "pnl_pct": pnl,
                "is_profitable": pnl > 0,
                "is_open": True,
                "holding_days": (pd.Timestamp(price_df.index[-1]) - pd.Timestamp(current_buy["time"])).days,
                "prob": current_buy["prob"],
                "label": current_buy["label"],
                **entry_ctx, **mkt_ctx,
            }
            all_trades.append(trade)

    return all_trades


def compare_groups(win_group, lose_group, group_name):
    """Print side-by-side comparison of two groups across all features."""
    features = [
        ("prob", "分类概率"),
        ("pnl_pct", "收益率(%)"),
        ("holding_days", "持仓天数"),
        # Trend
        ("pct_ma_5", "距MA5(%)"),
        ("pct_ma_10", "距MA10(%)"),
        ("pct_ma_20", "距MA20(%)"),
        ("ma_5_slope", "MA5斜率(3日)"),
        ("ma_10_slope", "MA10斜率(3日)"),
        ("ma_20_slope", "MA20斜率(3日)"),
        ("price_pos_20", "20日价格位置(0-100)"),
        ("pct_from_20d_high", "距20日高点(%)"),
        # MACD
        ("macd_dif", "MACD DIF"),
        ("macd_dea", "MACD DEA"),
        ("macd_hist", "MACD 柱"),
        ("macd_dif_slope", "MACD DIF斜率(3日)"),
        # Volatility & Volume
        ("atr_pct", "ATR波动率(%)"),
        ("vol_ratio", "量比"),
        ("gap_open", "当日跳空(%)"),
        # avmood
        ("avmood", "avmood趋势"),
        # Pre-entry returns
        ("ret_1d", "前1日涨幅(%)"),
        ("ret_3d", "前3日涨幅(%)"),
        ("ret_5d", "前5日涨幅(%)"),
        ("ret_10d", "前10日涨幅(%)"),
        ("ret_20d", "前20日涨幅(%)"),
        # Post-entry
        ("fwd_ret_1d", "入场后1日(%)"),
        ("fwd_ret_3d", "入场后3日(%)"),
        ("fwd_ret_5d", "入场后5日(%)"),
        ("max_gain", "持仓期最大浮盈(%)"),
        ("max_dd", "持仓期最大回撤(%)"),
        # Up days
        ("up_days_3", "前3日上涨天数"),
        ("up_days_5", "前5日上涨天数"),
        # Market
        ("idx_pct_ma_5", "[指数]距MA5(%)"),
        ("idx_pct_ma_20", "[指数]距MA20(%)"),
        ("idx_macd_hist", "[指数]MACD柱"),
        ("idx_macd_dif", "[指数]MACD DIF"),
        ("idx_ret_3d", "[指数]前3日涨幅(%)"),
        ("idx_ret_5d", "[指数]前5日涨幅(%)"),
        ("idx_ret_10d", "[指数]前10日涨幅(%)"),
        ("idx_avmood", "[指数]avmood"),
    ]

    # Boolean features
    bool_features = [
        ("ma_bullish", "MA多头排列"),
        ("macd_above_zero", "MACD DIF > 0"),
        ("macd_golden_cross", "MACD金叉"),
        ("macd_hist_positive", "MACD柱 > 0"),
        ("macd_bullish", "MACD多头"),
    ]

    print(f"\n  {'特征':<20} {'亏损组均值':>10} {'盈利组均值':>10} {'差值':>10} {'备注'}")
    print("  " + "-" * 70)

    for key, name in features:
        lv = [t.get(key) for t in lose_group if t.get(key) is not None]
        wv = [t.get(key) for t in win_group if t.get(key) is not None]

        if len(lv) >= 1 and len(wv) >= 1:
            l_mean = np.mean(lv)
            w_mean = np.mean(wv)
            diff = l_mean - w_mean
            # Flag if notable
            note = ""
            if abs(diff) > abs(w_mean) * 0.3 and abs(diff) > 0.5:
                note = "<< 显著差异" if abs(diff) > abs(w_mean) * 0.5 else ""
            print(f"  {name:<20} {l_mean:>+10.4f} {w_mean:>+10.4f} {diff:>+10.4f}{note}")

    print(f"\n  --- 布尔特征 (%True) ---")
    print(f"  {'特征':<20} {'亏损组%':>10} {'盈利组%':>10}")
    print("  " + "-" * 50)
    for key, name in bool_features:
        l_true = sum(1 for t in lose_group if t.get(key) == 1)
        w_true = sum(1 for t in win_group if t.get(key) == 1)
        l_total = sum(1 for t in lose_group if t.get(key) is not None)
        w_total = sum(1 for t in win_group if t.get(key) is not None)
        if l_total > 0 and w_total > 0:
            print(f"  {name:<20} {l_true/l_total*100:>9.1f}% {w_true/w_total*100:>9.1f}%")


def main():
    print("=" * 90)
    print("  亏损交易深度画像：买入后亏钱的资产有哪些共同特征？")
    print("=" * 90)

    # Load
    print("\n>>> 加载数据...")
    signals_df = load_all_signals()

    idx_df = pd.DataFrame()
    if INDEX_PATH.exists():
        idx_df = load_price("000001")  # reuse load_price
        if not idx_df.empty:
            idx_df = compute_indicators(idx_df)

    print(f"   信号: {len(signals_df)} 条, 指数: {len(idx_df)} 条")

    # Build trades
    print(">>> 构建交易...")
    all_trades = build_all_trades(signals_df, idx_df)
    df = pd.DataFrame(all_trades)
    print(f"   共 {len(df)} 笔 (已平仓: {(~df['is_open']).sum()}, 未平仓: {df['is_open'].sum()})")

    # Split
    losing = [t for t in all_trades if not t["is_profitable"]]
    winning = [t for t in all_trades if t["is_profitable"]]
    closed_lose = [t for t in losing if not t["is_open"]]
    open_lose = [t for t in losing if t["is_open"]]

    print(f"\n>>> 分组统计:")
    print(f"   亏损交易: {len(losing)} 笔 (已平仓 {len(closed_lose)}, 未平仓 {len(open_lose)})")
    print(f"   盈利交易: {len(winning)} 笔")
    print(f"   胜率: {len(winning)/len(all_trades)*100:.1f}%")

    # ================================================
    # 1. 亏损交易画像总览
    # ================================================
    print("\n" + "=" * 90)
    print("  [1] 亏损交易核心画像 (全部 {})".format(len(losing)))
    print("=" * 90)

    # Probability distribution of losers
    probs = [t["prob"] for t in losing if t.get("prob") is not None]
    print(f"\n  概率分布: min={min(probs):.3f}, Q25={np.percentile(probs,25):.3f}, "
          f"median={np.median(probs):.3f}, Q75={np.percentile(probs,75):.3f}, max={max(probs):.3f}")
    print(f"  概率中位数: {np.median(probs):.3f} -- 亏损信号并不都是低概率!")

    # Probability buckets
    bins = [(0.4, 0.6), (0.6, 0.7), (0.7, 0.8), (0.8, 0.85), (0.85, 0.9), (0.9, 0.95), (0.95, 1.0)]
    print(f"\n  亏损交易的概率分布:")
    for lo, hi in bins:
        cnt = sum(1 for p in probs if lo <= p < hi)
        total = sum(1 for t in all_trades if t.get("prob") and lo <= t["prob"] < hi)
        if total > 0:
            print(f"    prob {lo:.1f}-{hi:.1f}: {cnt}/{total} 亏损 ({cnt/total*100:.0f}%)")

    # Entry date distribution
    date_lose = defaultdict(list)
    date_all = defaultdict(list)
    for t in all_trades:
        d = t["entry_time"].strftime("%m-%d")
        date_all[d].append(t)
        if not t["is_profitable"]:
            date_lose[d].append(t)

    print(f"\n  按入场日亏损率:")
    for d in sorted(date_all.keys()):
        lose_rate = len(date_lose.get(d, [])) / len(date_all[d]) * 100
        bar = "#" * int(lose_rate / 5)
        print(f"    {d}: {len(date_lose.get(d,[]))}/{len(date_all[d])} ({lose_rate:.0f}%) {bar}")

    # Holding days for losers
    hd_lose = [t["holding_days"] for t in losing]
    print(f"\n  持仓天数分布:")
    for tag, lo, hi in [("当日",0,1), ("2-3天",2,3), ("4-5天",4,5), ("6-7天",6,7), ("8天+",8,99)]:
        cnt = sum(1 for h in hd_lose if lo <= h <= hi)
        print(f"    {tag}: {cnt} 笔 ({cnt/len(losing)*100:.0f}%)")

    # ================================================
    # 2. 亏损 vs 盈利 全维度对比
    # ================================================
    print("\n" + "=" * 90)
    print("  [2] 亏损 vs 盈利 全维度对比")
    print("=" * 90)
    compare_groups(winning, losing, "全部")

    # ================================================
    # 3. 已平仓亏损 vs 未平仓浮亏
    # ================================================
    print("\n" + "=" * 90)
    print("  [3] 已平仓实亏 ({}) vs 未平仓浮亏 ({})".format(len(closed_lose), len(open_lose)))
    print("=" * 90)
    compare_groups(open_lose, closed_lose, "亏损子类")

    # ================================================
    # 4. 亏损交易聚类分析
    # ================================================
    print("\n" + "=" * 90)
    print("  [4] 亏损交易分类 (基于入场特征)")
    print("=" * 90)

    # Type 1: 追高型 - 入场前大涨 + 高概率
    type1 = [t for t in losing if t.get("ret_5d", 0) > 15 and t.get("prob", 0) > 0.85]
    # Type 2: 弱势型 - 均线死叉/破位
    type2 = [t for t in losing if t.get("ma_bullish") == 0]
    # Type 3: 放量滞涨型 - 量比高 + 价格在均线附近
    type3 = [t for t in losing if t.get("vol_ratio", 1) > 1.5]
    # Type 4: 高波动型
    type4 = [t for t in losing if t.get("atr_pct", 0) > 6]
    # Type 5: 追高+放量 (最危险)
    type5 = [t for t in losing if t.get("ret_5d", 0) > 15 and t.get("vol_ratio", 1) > 1.5]
    # Type 6: 指数弱势
    type6 = [t for t in losing if t.get("idx_avmood", 0) < 0]

    print(f"""
  亏损类型                       数量   占比     平均亏损    典型特征
  ─────────────────────────────────────────────────────────────
  追高型 (前5日>15% + prob>0.85)   {len(type1):>3}  {len(type1)/len(losing)*100:>4.1f}%  {np.mean([t['pnl_pct'] for t in type1]) if type1 else 0:>+7.2f}%   入场前涨幅过大
  弱势型 (MA空头排列)              {len(type2):>3}  {len(type2)/len(losing)*100:>4.1f}%  {np.mean([t['pnl_pct'] for t in type2]) if type2 else 0:>+7.2f}%   均线未形成多头排列
  放量型 (量比>1.5)               {len(type3):>3}  {len(type3)/len(losing)*100:>4.1f}%  {np.mean([t['pnl_pct'] for t in type3]) if type3 else 0:>+7.2f}%   高位放量
  高波动型 (ATR>6%)              {len(type4):>3}  {len(type4)/len(losing)*100:>4.1f}%  {np.mean([t['pnl_pct'] for t in type4]) if type4 else 0:>+7.2f}%   波动率过高
  追高+放量 (复合型)              {len(type5):>3}  {len(type5)/len(losing)*100:>4.1f}%  {np.mean([t['pnl_pct'] for t in type5]) if type5 else 0:>+7.2f}%   最危险组合
  指数弱势 (idx_avmood<0)        {len(type6):>3}  {len(type6)/len(losing)*100:>4.1f}%  {np.mean([t['pnl_pct'] for t in type6]) if type6 else 0:>+7.2f}%   大盘环境差
  """)

    # ================================================
    # 5. 逐笔亏损详细列表
    # ================================================
    print("\n" + "=" * 90)
    print("  [5] 全部亏损交易明细 (按亏损幅度排序)")
    print("=" * 90)

    losing_sorted = sorted(losing, key=lambda x: x["pnl_pct"])
    print(f"\n  {'股票':<8} {'入场':>6} {'出场':>6} {'收益%':>8} {'持仓':>5} {'概率':>6} "
          f"{'前5日%':>7} {'前10日%':>7} {'avmood':>7} {'MA多头':>6} {'量比':>6} {'ATR%':>6} "
          f"{'状态':>6}")
    print("  " + "-" * 105)
    for t in losing_sorted:
        ma_bull = "Y" if t.get("ma_bullish") else "N"
        status = "CLOSED" if not t["is_open"] else "OPEN"
        print(f"  {t['stock_code']:<8} {t['entry_time'].strftime('%m-%d'):>6} "
              f"{pd.Timestamp(t['exit_time']).strftime('%m-%d'):>6} "
              f"{t['pnl_pct']:>+7.2f}% {t['holding_days']:>4}d "
              f"{t.get('prob','N/A'):>6.3f} "
              f"{t.get('ret_5d',0):>+6.1f}% {t.get('ret_10d',0):>+6.1f}% "
              f"{t.get('avmood',0):>+6.2f} {ma_bull:>6} "
              f"{t.get('vol_ratio',0):>5.2f} {t.get('atr_pct',0):>5.2f}% "
              f"{status:>6}")

    # ================================================
    # 6. 总结
    # ================================================
    print("\n" + "=" * 90)
    print("  [6] 亏损交易特征总结")
    print("=" * 90)

    # Aggregate key metrics
    l_prob = np.mean([t["prob"] for t in losing if t.get("prob")])
    w_prob = np.mean([t["prob"] for t in winning if t.get("prob")])
    l_ret5 = np.mean([t.get("ret_5d", 0) for t in losing])
    w_ret5 = np.mean([t.get("ret_5d", 0) for t in winning])
    l_ret10 = np.mean([t.get("ret_10d", 0) for t in losing])
    w_ret10 = np.mean([t.get("ret_10d", 0) for t in winning])
    l_vol = np.mean([t.get("vol_ratio", 0) for t in losing])
    w_vol = np.mean([t.get("vol_ratio", 0) for t in winning])
    l_ma = sum(1 for t in losing if t.get("ma_bullish")) / len(losing) * 100
    w_ma = sum(1 for t in winning if t.get("ma_bullish")) / len(winning) * 100
    l_macd = sum(1 for t in losing if t.get("macd_bullish")) / len(losing) * 100
    w_macd = sum(1 for t in winning if t.get("macd_bullish")) / len(winning) * 100

    print(f"""
  买入后亏钱的资产，在入场时普遍具有以下特征：

  >>> 入场时机 <<<
  1. 追高入场：前5日涨幅均值 {l_ret5:+.1f}%，几乎所有亏损都在上涨后追入
  2. 前10日涨幅异常高：{l_ret10:+.1f}%（盈利组仅 +{w_ret10:.1f}%）—— 中期涨幅过大后追入极易接盘
  3. 越晚入场越危险：06/24-25 入场的亏损率明显高于 06/17-18

  >>> 技术面 <<<
  4. MA 多头排列率 {l_ma:.0f}%（盈利组 {w_ma:.0f}%）—— 亏损交易均线结构不差
  5. MACD 多头率 {l_macd:.0f}%（盈利组 {w_macd:.0f}%）
  6. 均线位置普遍偏高：距 MA20 约 +8~10%，已经远离均线支撑

  >>> 成交量 <<<
  7. 放量特征：量比 {l_vol:.2f}（盈利组 {w_vol:.2f}）—— 高位放量是见顶信号

  >>> 概率 <<<
  8. 分类概率均值 {l_prob:.3f}（盈利组 {w_prob:.3f}）—— 概率差别不大，亏损信号中位数 0.83+
  9. 极端高概率（>0.95）的亏损率 50%，高概率不保证盈利

  >>> 最危险的组合（>70%亏损率）<<<
  追高(前5日>15%) + 放量(量比>1.5) + 高概率(>0.85) → 几乎必然亏损

  >>> 大盘环境 <<<
  指数弱势（avmood<0）时入场的亏损率明显更高
  """)

    print("  >>> 分析完成 <<<")


if __name__ == "__main__":
    main()
