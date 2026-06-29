"""
Quant-UI API Server — serves strategy, trade, and market data as JSON.

Uses Starlette + Uvicorn — install via `pip install starlette uvicorn`.

Start:
    python api_server.py
    # Runs on http://localhost:8765

Endpoints:
    GET /api/health                    — health check
    GET /api/strategies                — list all registered strategies
    GET /api/strategies/{name}/stocks  — stock list for a strategy
    GET /api/strategies/{name}/stocks/{code} — asset detail (price, signals, trades)
    GET /api/market-condition          — index market condition data
    GET /api/chart/{strategy}/{code}   — Plotly chart JSON
"""

import sys
import json
import math
from pathlib import Path
from datetime import datetime, date

sys.path.insert(0, str(Path(__file__).parent))

from starlette.applications import Starlette
from starlette.routing import Route
from starlette.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware
import uvicorn
import pandas as pd

from src.config.settings import get_config
from src.strategy.registry import init_registry
from src.data_loader.price_loader import PriceLoader
from src.trade_engine.pairer import TradePairer
from src.trade_engine.pnl import PnLCalculator
from src.visualizer.chart_builder import ChartBuilder
from src.indicators.risk import get_indicator_at_entry, classify_risk_level

# ------------------------------------------------
# Init
# ------------------------------------------------
config = get_config()
registry = init_registry(config)
price_loader = PriceLoader(config)
pairer = TradePairer(config)
pnl_calc = PnLCalculator(config.commission, config.slippage)
chart_builder = ChartBuilder(ma_periods=config.ma_periods)

MARKET = config.default_market
LEVEL = config.default_level


# ------------------------------------------------
# Helpers
# ------------------------------------------------
def _serialize(obj):
    """Recursively convert numpy/pandas types to plain Python for JSON."""
    if isinstance(obj, (pd.Timestamp, datetime, date)):
        return obj.isoformat()
    if isinstance(obj, (pd.Series,)):
        return obj.to_dict()
    if isinstance(obj, (pd.DataFrame,)):
        return obj.to_dict(orient="records")
    if hasattr(obj, "item"):  # numpy scalars
        return obj.item()
    if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
        return None
    if isinstance(obj, dict):
        return {k: _serialize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_serialize(v) for v in obj]
    return obj


def _load_stock_name_map():
    """Load stock names from CSV, falling back to hardcoded ETF names."""
    csv_path = config.stock_name_csv_path
    mapping: dict[str, str] = {}

    if csv_path and Path(csv_path).exists():
        try:
            df = pd.read_csv(csv_path)
            for _, row in df.iterrows():
                raw_code = str(row["code"]).strip()
                if "." in raw_code:
                    raw_code = raw_code.split(".", 1)[1]
                mapping[raw_code] = str(row["code_name"]).strip()
        except Exception:
            pass  # keep going — fallback names may still help

    # Merge fallback ETF/index names (CSV values take precedence)
    for code, name in _FALLBACK_STOCK_NAMES.items():
        mapping.setdefault(code, name)

    return mapping


# Fallback names for ETFs / index funds not in a800_stocks.csv
_FALLBACK_STOCK_NAMES: dict[str, str] = {
    "513030": "德国",
    "159329": "沙特",
    "159100": "巴西",
    "164824": "印度",
    "513880": "日经225",
    "159509": "纳指科技",
    "513290": "纳指生物科技",
    "159518": "标普油气",
    "162415": "美国消费",
    "513730": "东南亚科技",
    "513310": "中韩半导体",
    "501225": "全球芯片",
    "513050": "中概互联网",
    "159131": "港股信息技术",
    "513120": "港股创新药",
    "520600": "港股汽车",
    "513950": "恒生红利",
    "513970": "恒生消费",
    "513090": "香港证券",
    "513360": "教育",
    "159985": "豆粕",
    "159980": "有色",
    "518880": "黄金",
    "161226": "白银",
    "161129": "原油",
    "163208": "全球油气能源",
    "159981": "能源化工",
    "159915": "创业板",
    "510300": "沪深300指数",
    "563300": "中证2000指数",
    "588000": "科创50",
    "512690": "酒",
    "510880": "红利",
    "512880": "证券",
    "159870": "化工",
    "560080": "中药",
    "563010": "电信",
    "159852": "软件",
    "159995": "芯片",
    "512980": "传媒",
    "159855": "影视",
    "561360": "石油",
    "516910": "物流",
    "159755": "电池",
    "515790": "光伏",
    "516970": "基建",
    "512660": "军工",
    "159611": "电力",
    "512170": "医疗",
    "512800": "银行",
    "515220": "煤炭",
    "159766": "旅游",
    "159865": "养殖",
    "159698": "粮食",
    "159996": "家电",
    "159869": "游戏",
    "515880": "通信",
    "562500": "机器人",
    "512200": "房地产",
    "159326": "电网设备",
    "512400": "有色金属",
    "159227": "航空航天",
    "560280": "工程机械",
    "159667": "工业母机",
    "159819": "人工智能",
    "588760": "科创人工智能",
}


# ------------------------------------------------
# Endpoints
# ------------------------------------------------
async def health(_request):
    return JSONResponse({"status": "ok", "strategies": registry.list_names()})


async def list_strategies(_request):
    """Return all registered strategies with summary stats."""
    strategies = []
    stock_name_map = _load_stock_name_map()

    for name in registry.list_names():
        adapter = registry.get(name)
        try:
            signals = adapter.load_signals()
        except Exception:
            signals = []

        stocks = sorted(set(s.stock_code for s in signals))
        total_trades = 0
        total_pnl_sum = 0.0
        trade_count = 0

        for stock_code in stocks:
            stock_signals = [s for s in signals if s.stock_code == stock_code]
            stock_signals.sort(key=lambda s: s.time)
            try:
                price_df = adapter.load_price_data(stock_code, MARKET, LEVEL)
            except Exception:
                price_df = pd.DataFrame()
            closed_trades, open_pos = pairer.pair_signals(stock_signals, price_df)
            total_trades += len(closed_trades) + (1 if open_pos else 0)
            for t in closed_trades:
                if t.pnl_pct is not None:
                    total_pnl_sum += t.pnl_pct
                    trade_count += 1
            if open_pos and open_pos.pnl_pct is not None:
                total_pnl_sum += open_pos.pnl_pct
                trade_count += 1

        strategies.append({
            "id": name,
            "name": adapter.display_name,
            "description": adapter.description,
            "markets": [MARKET],
            "pnl": round(total_pnl_sum / max(trade_count, 1) * 100, 1),
            "maxDrawdown": 0,  # placeholder
            "sharpe": 0,        # placeholder
            "winRate": 0,       # placeholder
            "status": "running",
            "totalTrades": total_trades,
            "profitTrades": 0,
            "lossTrades": 0,
            "avgProfit": 0,
            "avgLoss": 0,
            "profitFactor": 0,
            "stockCount": len(stocks),
        })

    return JSONResponse({"strategies": strategies})


async def strategy_stocks(request):
    """Return stock list for a strategy with metrics."""
    strategy_name = request.path_params["name"]
    adapter = registry.get(strategy_name)
    if adapter is None:
        return JSONResponse({"error": f"Strategy not found: {strategy_name}"}, status_code=404)

    try:
        signals = adapter.load_signals()
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

    all_signals = []
    try:
        all_signals = adapter.load_all_signals()
    except Exception:
        pass

    stocks = sorted(set(s.stock_code for s in signals))
    stock_name_map = _load_stock_name_map()

    stock_data = []
    for stock_code in stocks:
        stock_signals = [s for s in signals if s.stock_code == stock_code]
        stock_signals.sort(key=lambda s: s.time)

        try:
            price_df = adapter.load_price_data(stock_code, MARKET, LEVEL)
        except Exception:
            price_df = pd.DataFrame()

        closed_trades, open_pos = pairer.pair_signals(stock_signals, price_df)
        is_holding = open_pos is not None

        pnl = None
        if is_holding and open_pos.pnl_pct is not None:
            pnl = round(open_pos.pnl_pct * 100, 2)
        elif closed_trades and closed_trades[-1].pnl_pct is not None:
            pnl = round(closed_trades[-1].pnl_pct * 100, 2)

        entry_price = open_pos.entry_price if is_holding else (
            closed_trades[-1].entry_price if closed_trades else None
        )
        current_price = open_pos.exit_price if is_holding else (
            closed_trades[-1].exit_price if closed_trades else None
        )
        last_date = stock_signals[-1].date_str if stock_signals else "—"

        # Stop-loss info
        stop_loss_price = None
        stop_loss_date = None
        if all_signals:
            all_stock = [s for s in all_signals if s.stock_code == stock_code]
            ineffective = [s for s in all_stock if s.is_sell and s.label is not None and s.label != 3]
            if ineffective:
                ineffective.sort(key=lambda s: s.time)
                sl = ineffective[-1]
                stop_loss_price = sl.price
                stop_loss_date = sl.date_str

        stock_data.append({
            "code": stock_code,
            "name": stock_name_map.get(stock_code, ""),
            "isHolding": is_holding,
            "pnlPct": pnl,
            "entryPrice": float(entry_price) if entry_price else None,
            "currentPrice": float(current_price) if current_price else None,
            "signalCount": len(stock_signals),
            "tradeCount": len(closed_trades) + (1 if is_holding else 0),
            "lastDate": last_date,
            "stopLossPrice": float(stop_loss_price) if stop_loss_price else None,
            "stopLossDate": stop_loss_date,
        })

    return JSONResponse({"stocks": _serialize(stock_data)})


async def stock_detail(request):
    """Return full detail for one stock: price, signals, trades."""
    strategy_name = request.path_params["name"]
    stock_code = request.path_params["code"]

    adapter = registry.get(strategy_name)
    if adapter is None:
        return JSONResponse({"error": f"Strategy not found: {strategy_name}"}, status_code=404)

    try:
        signals = adapter.load_stock_signals(stock_code)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

    if not signals:
        return JSONResponse({"error": "No signals"}, status_code=404)

    try:
        price_df = adapter.load_price_data(stock_code, MARKET, LEVEL)
    except Exception as e:
        return JSONResponse({"error": f"No price data: {e}"}, status_code=404)

    closed_trades, open_pos = pairer.pair_signals(signals, price_df)

    # Serialize signals
    signal_list = []
    for s in signals:
        signal_list.append({
            "time": s.time.isoformat() if hasattr(s.time, 'isoformat') else str(s.time),
            "type": "buy" if s.is_buy else "sell",
            "price": float(s.price),
            "label": s.label,
        })

    # Serialize trades
    trade_list = []
    for t in closed_trades:
        trade_list.append({
            "entryTime": t.entry_time.isoformat() if hasattr(t.entry_time, 'isoformat') else str(t.entry_time),
            "exitTime": t.exit_time.isoformat() if hasattr(t.exit_time, 'isoformat') else str(t.exit_time),
            "entryPrice": float(t.entry_price),
            "exitPrice": float(t.exit_price),
            "pnlPct": round(float(t.pnl_pct) * 100, 2) if t.pnl_pct is not None else None,
            "isHolding": False,
        })

    if open_pos:
        trade_list.append({
            "entryTime": open_pos.entry_time.isoformat() if hasattr(open_pos.entry_time, 'isoformat') else str(open_pos.entry_time),
            "exitTime": None,
            "entryPrice": float(open_pos.entry_price),
            "exitPrice": float(open_pos.exit_price) if open_pos.exit_price else None,
            "pnlPct": round(float(open_pos.pnl_pct) * 100, 2) if open_pos.pnl_pct is not None else None,
            "isHolding": True,
        })

    # Price data summary (last 200 bars)
    if not price_df.empty:
        price_data = []
        df_tail = price_df.tail(200)
        for _, row in df_tail.iterrows():
            price_data.append({
                "time": str(row.get("time", row.name)),
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": float(row.get("volume", 0)),
            })
    else:
        price_data = []

    # Extra data (avmood for fuzzy_ma strategy)
    avmood_data = None
    if adapter.has_extra_data:
        try:
            extra_df = adapter.load_extra_data(stock_code, price_df, MARKET, LEVEL)
            if extra_df is not None and "avmood" in extra_df.columns:
                avmood_data = []
                for idx, row in extra_df.iterrows():
                    avmood_val = row.get("avmood")
                    if avmood_val is not None and not (isinstance(avmood_val, float) and math.isnan(avmood_val)):
                        avmood_data.append({
                            "time": str(idx),
                            "value": float(avmood_val),
                        })
        except Exception:
            pass

    # Computed stats
    closed_stats = pnl_calc.get_closed_trade_stats(closed_trades, stock_code)

    return JSONResponse(_serialize({
        "stockCode": stock_code,
        "strategyName": strategy_name,
        "priceData": price_data,
        "signals": signal_list,
        "avmoodData": avmood_data,
        "trades": trade_list,
        "hasOpenPosition": open_pos is not None,
        "stats": {
            "totalTrades": closed_stats.get("total_trades", 0),
            "winCount": closed_stats.get("win_count", 0),
            "winRate": round(closed_stats.get("win_rate", 0) * 100, 1),
            "totalPnlPct": round(closed_stats.get("total_pnl_pct", 0), 2),
            "latestPrice": float(price_df["close"].iloc[-1]) if not price_df.empty else 0,
        },
    }))


async def market_condition(request):
    """Return index market condition data + avmood trend data.

    Query params:
        code (str): index code, e.g. 000001 (default), 399006, …
    """
    try:
        import csv
        from src.data_loader.extra_data import FuzzyMAExtraDataLoader

        # ── Resolve index code ──
        code = request.query_params.get("code", "000001")

        INDEX_NAME_MAP: dict[str, str] = {
            "000001": "上证指数",
            "399006": "创业板指",
        }
        index_name = INDEX_NAME_MAP.get(code, code)

        DATA_ROOT = str(Path(config.index_price_csv_path).parent.parent)

        price_path = str(Path(DATA_ROOT) / "live_index" / f"live_bar_A_{code}_d.csv")
        condition_path = str(Path(DATA_ROOT) / "market_condition_live" / f"A_{code}_d.csv")

        bars = []
        price_map = {}
        if price_path and Path(price_path).exists():
            with open(price_path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    time_str = str(row.get("time", "")).strip()[:10]
                    if not time_str:
                        continue
                    price_map[time_str] = {
                        "time": time_str,
                        "open": float(row.get("open", 0)),
                        "high": float(row.get("high", 0)),
                        "low": float(row.get("low", 0)),
                        "close": float(row.get("close", 0)),
                        "volume": float(row.get("volume", 0)),
                    }

        condition_map = {}
        if condition_path and Path(condition_path).exists():
            with open(condition_path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    date_str = str(row.get("date", row.get("time", ""))).strip()[:10]
                    if not date_str:
                        continue
                    condition_map[date_str] = {
                        "marketCondition": str(row.get("market_condition", row.get("condition", ""))).strip(),
                        "probability": float(row.get("probability", 0)),
                    }

        for date_str in sorted(price_map.keys()):
            bar = dict(price_map[date_str])
            cond = condition_map.get(date_str, {})
            bar["marketCondition"] = cond.get("marketCondition") or None
            bar["probability"] = cond.get("probability") or None
            bars.append(bar)

        condition_counts = {"trend_up": 0, "trend_down": 0, "range": 0}
        for b in bars:
            mc = b.get("marketCondition")
            if mc in condition_counts:
                condition_counts[mc] += 1

        bars_with_condition = [b for b in bars if b.get("marketCondition")]

        # ── avmood computation (same as stock detail) ──
        avmood_data = None
        try:
            # Build price DataFrame for avmood computation
            price_df = pd.DataFrame(bars)
            if not price_df.empty and "time" in price_df.columns:
                price_df["time"] = pd.to_datetime(price_df["time"])
                price_df = price_df.set_index("time").sort_index()
                if "close" in price_df.columns and len(price_df) >= 10:
                    loader = FuzzyMAExtraDataLoader(config)
                    avmood_df = loader._compute_avmood(price_df)
                    if not avmood_df.empty and "avmood" in avmood_df.columns:
                        avmood_data = []
                        for idx, row in avmood_df.iterrows():
                            v = row.get("avmood")
                            if v is not None and not (isinstance(v, float) and math.isnan(v)):
                                avmood_data.append({"time": str(idx)[:10], "value": float(v)})
        except Exception:
            pass

        return JSONResponse({
            "indexCode": code,
            "indexName": index_name,
            "totalBars": len(bars),
            "barsWithCondition": len(bars_with_condition),
            "conditionCounts": condition_counts,
            "latestBar": bars[-1] if bars else None,
            "bars": bars,
            "avmoodData": avmood_data,
        })
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


async def chart_json(request):
    """Return Plotly chart JSON for a stock."""
    strategy_name = request.path_params["name"]
    stock_code = request.path_params["code"]

    adapter = registry.get(strategy_name)
    if adapter is None:
        return JSONResponse({"error": f"Strategy not found: {strategy_name}"}, status_code=404)

    try:
        signals = adapter.load_stock_signals(stock_code)
        price_df = adapter.load_price_data(stock_code, MARKET, LEVEL)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

    closed_trades, open_pos = pairer.pair_signals(signals, price_df)

    extra_data = None
    extra_label = ""
    if adapter.has_extra_data:
        try:
            extra_data = adapter.load_extra_data(stock_code, price_df, MARKET, LEVEL)
            extra_label = adapter.get_extra_loader().get_description()
        except Exception:
            pass

    title = f"{stock_code} — {adapter.display_name}"
    fig = chart_builder.build_chart(
        price_df=price_df,
        signals=signals,
        trades=closed_trades,
        open_position=open_pos,
        extra_data=extra_data,
        extra_label=extra_label,
        title=title,
    )

    import plotly.io as pio
    chart_json_str = pio.to_json(fig)
    return JSONResponse(json.loads(chart_json_str))


# ------------------------------------------------
# App
# ------------------------------------------------
routes = [
    Route("/api/health", health),
    Route("/api/strategies", list_strategies),
    Route("/api/strategies/{name}/stocks", strategy_stocks),
    Route("/api/strategies/{name}/stocks/{code}", stock_detail),
    Route("/api/market-condition", market_condition),
    Route("/api/chart/{strategy}/{code}", chart_json),
]

app = Starlette(debug=False, routes=routes)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


if __name__ == "__main__":
    print(f"🚀 Quant-UI API Server starting on http://{config.app_host}:{config.app_port}")
    print(f"   Strategies: {registry.list_names()}")
    uvicorn.run(app, host=config.app_host, port=config.app_port, log_level="info")
