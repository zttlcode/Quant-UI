"""Quant-UI: Stock Strategy Visualization Platform

Main Streamlit application entry point.

Usage:
    streamlit run app.py

Pages:
- 首页: Platform introduction (strategies & AI market condition)
- 策略详情: Browse traded assets for a strategy, click row to enter asset detail
- 资产详情: Interactive K-line chart with signals, MAs, MACD, and trade history
- 行情分类: AI market condition classification (trend up / down / range)
"""

import sys
from pathlib import Path

# Ensure src is importable
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.logger import setup_logging
from src.config.settings import get_config
from src.strategy.registry import init_registry, get_registry
from src.data_loader.price_loader import PriceLoader
from src.trade_engine.pairer import TradePairer
from src.trade_engine.pnl import PnLCalculator
from src.visualizer.chart_builder import ChartBuilder
from src.visualizer.components import (
    render_label_legend,
    render_position_status,
    render_trade_table,
    render_strategy_card,
    render_data_warnings,
    render_signal_filter_ui,
)
from src.visualizer.index_condition_ui import render_index_condition_section
from src.indicators.risk import (
    compute_risk_indicators,
    get_indicator_at_entry,
    classify_risk_level,
)

import streamlit as st
import pandas as pd

# ============================================================
# Page Configuration
# ============================================================
st.set_page_config(
    page_title="Quant-UI | 策略可视化平台",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# Initialize Application
# ============================================================
@st.cache_resource
def init_app():
    """Initialize application: config, logging, strategy registry."""
    cfg = get_config()
    logger = setup_logging(cfg.log_level, cfg.log_file, "quant_ui")
    logger.info("Quant-UI starting...")
    registry = init_registry(cfg)
    logger.info("Application initialized with %d strategies", len(registry))
    return cfg, registry


config, registry = init_app()


# ============================================================
# Stock Name Mapping
# ============================================================
@st.cache_data
def load_stock_name_map() -> dict:
    """Load stock code → stock name mapping from the configured CSV.

    The CSV is expected to have columns: ipodate, code, code_name.
    The 'code' column uses format like 'sh.600000' — the prefix is
    stripped so the returned dict maps bare numeric codes to names.
    """
    csv_path = config.stock_name_csv_path
    if not csv_path or not Path(csv_path).exists():
        return {}

    try:
        df = pd.read_csv(csv_path)
        mapping: dict[str, str] = {}
        for _, row in df.iterrows():
            raw_code = str(row["code"]).strip()
            # Strip market prefix: "sh.600000" → "600000"
            if "." in raw_code:
                raw_code = raw_code.split(".", 1)[1]
            mapping[raw_code] = str(row["code_name"]).strip()
        return mapping
    except Exception:
        return {}


def get_stock_display(code: str, name_map: dict) -> str:
    """Return display string for a stock code, with name if available."""
    name = name_map.get(code, "")
    if not name:
        name = _FALLBACK_STOCK_NAMES.get(code, "")
    if name:
        return f"{code}  {name}"
    return code


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

# ============================================================
# Sidebar Navigation
# ============================================================
st.sidebar.title("📊 Quant-UI")
st.sidebar.caption("策略可视化平台")

# --- Navigation buttons ---
if st.sidebar.button("🏠 首页", use_container_width=True, key="nav_home"):
    st.session_state["page"] = "🏠 首页"
    st.rerun()

# Strategy selector
strategy_names = registry.list_names()
strategy_displays = {
    name: registry.get(name).display_name for name in strategy_names
}

if strategy_names:
    selected_strategy = st.sidebar.selectbox(
        "📈 策略选择",
        options=strategy_names,
        format_func=lambda x: strategy_displays.get(x, x),
        key="sidebar_strategy",
    )

    # Auto-navigate to strategy detail when the dropdown changes
    if "prev_sidebar_strategy" not in st.session_state:
        st.session_state["prev_sidebar_strategy"] = selected_strategy

    if selected_strategy != st.session_state["prev_sidebar_strategy"]:
        st.session_state["prev_sidebar_strategy"] = selected_strategy
        st.session_state["page"] = "📈 策略详情"
        st.rerun()
else:
    st.sidebar.warning("没有已注册的策略")
    selected_strategy = None

if st.sidebar.button("🤖 行情分类", use_container_width=True, key="nav_condition"):
    st.session_state["page"] = "🤖 行情分类"
    st.rerun()


# Market & Level filter
st.sidebar.markdown("---")
market_filter = st.sidebar.selectbox("市场", ["A"], disabled=True)
level_filter = st.sidebar.selectbox("级别", ["d", "w", "15", "30", "60"], index=0)

st.sidebar.markdown("---")
st.sidebar.caption("Quant-UI v1.0.0")
if st.sidebar.button("🔄 刷新数据"):
    st.cache_data.clear()
    st.rerun()


# ============================================================
# Page: Home
# ============================================================
def render_home():
    """Render the home page — platform introduction."""
    st.title("🏠 欢迎使用 Quant-UI")
    st.markdown("### 量化交易策略可视化平台")

    st.markdown("---")

    col1, col2 = st.columns(2, gap="large")

    with col1:
        with st.container(border=True):
            st.subheader("📈 策略交易")
            st.markdown(
                "基于**深度时间序列模型**（Transformer / TCN / NBeats 等）"
                "对金融资产价格进行推理，生成高胜率买卖信号。"
            )
            st.markdown("- 多策略并行，插件化架构，轻松扩展")
            st.markdown("- 完整买卖信号配对与收益归因分析")
            st.markdown("- 交互式 K 线图表，集成 MA / MACD / ATR 等技术指标")
            st.markdown("- 实时持仓管理与 ATR 动态止损监控")
            if strategy_names:
                st.caption(
                    f"已注册策略: **{', '.join(strategy_displays.values())}**"
                )

    with col2:
        with st.container(border=True):
            st.subheader("🤖 AI 行情分类")
            st.markdown(
                "基于**深度学习模型**实时识别指数行情状态，"
                "将市场划分为趋势上涨、趋势下跌、震荡三种模式。"
            )
            st.markdown("- 端到端深度分类模型，每日自动推理")
            st.markdown("- 分类结果叠加 K 线蜡烛图，直观展示市场结构")
            st.markdown("- 模型分类概率与置信度量化评估")
            st.markdown("- 支持收盘价走势与 AI 分类标注叠加分析")
            st.caption("标的: **上证指数 (000001)**")

    st.markdown("---")

    st.markdown("### 🚀 快速开始")
    st.markdown(
        "在左侧边栏选择 **策略** 查看交易资产列表，"
        "或点击 **行情分类** 查看 AI 市场状态识别结果。"
    )


# ============================================================
# Page: Strategy Detail
# ============================================================
def render_strategy_detail():
    """Render the strategy detail page with a clickable asset list."""
    st.title("📈 策略详情")

    if selected_strategy is None:
        st.warning("请从侧边栏选择一个策略。")
        return

    adapter = registry.get(selected_strategy)
    if adapter is None:
        st.error(f"策略 '{selected_strategy}' 未注册。")
        return

    st.subheader(adapter.display_name)
    st.caption(adapter.description)

    st.markdown("---")

    # Load data
    with st.spinner(f"加载 {adapter.display_name} 的信号数据..."):
        try:
            signals = adapter.load_signals()
        except Exception as e:
            st.error(f"加载信号数据失败: {e}")
            return

    if not signals:
        st.warning("该策略没有交易信号数据。")
        return

    # Load ALL signals (incl. ineffective) for stop-loss display
    try:
        all_signals = adapter.load_all_signals()
    except Exception:
        all_signals = []  # Graceful fallback if all-signals loading fails

    # Build stock summary
    price_loader = PriceLoader(config)

    stocks = sorted(set(s.stock_code for s in signals))

    # Search and filter
    col1, col2, col3 = st.columns(3)
    with col1:
        search_term = st.text_input(
            "🔍 搜索股票代码",
            placeholder="输入代码如 000027",
            key="strategy_search",
        )
    with col2:
        status_filter = st.selectbox(
            "持仓状态",
            ["全部", "持仓中", "已清仓"],
            key="strategy_status",
        )
    with col3:
        st.caption(f"共 {len(stocks)} 只股票")

    # Filter stocks by search
    if search_term:
        stocks = [s for s in stocks if search_term.strip() in s]
        st.caption(f"搜索 '{search_term}': 匹配 {len(stocks)} 只股票")

    st.markdown("---")

    # Display stock list
    if not stocks:
        st.info("没有匹配的股票。")
        return

    # Build summaries for each stock
    pairer = TradePairer(config)
    pnl_calc = PnLCalculator(config.commission, config.slippage)

    stock_data = []
    for stock_code in stocks:
        stock_signals = [s for s in signals if s.stock_code == stock_code]
        stock_signals.sort(key=lambda s: s.time)

        # Try to load price data
        try:
            price_df = adapter.load_price_data(stock_code, market_filter, level_filter)
        except Exception:
            price_df = pd.DataFrame()

        # Pair trades
        closed_trades, open_pos = pairer.pair_signals(stock_signals, price_df)

        is_holding = open_pos is not None
        pnl = open_pos.pnl_pct if is_holding else (
            closed_trades[-1].pnl_pct if closed_trades else None
        )
        entry_price = open_pos.entry_price if is_holding else (
            closed_trades[-1].entry_price if closed_trades else None
        )
        current_price = open_pos.exit_price if is_holding else (
            closed_trades[-1].exit_price if closed_trades else None
        )

        # Latest trade date
        last_date = stock_signals[-1].time.strftime("%Y-%m-%d") if stock_signals else "—"

        # ---- Compute risk indicators ----
        ret_5d = None
        atr_pct = None
        ma_bullish = None
        avmood_val = None
        risk_level = "—"
        risk_warnings = []

        if not price_df.empty and is_holding:
            # Get entry time of the current position
            entry_sig = open_pos.entry_signal if open_pos else (
                stock_signals[-1] if stock_signals else None
            )
            if entry_sig is not None:
                risk_indicators = get_indicator_at_entry(price_df, entry_sig.time)
                ret_5d = risk_indicators.get("ret_5d")
                atr_pct = risk_indicators.get("atr_pct")
                ma_bullish = risk_indicators.get("ma_bullish")
                avmood_val = risk_indicators.get("avmood")
                risk_level, _, risk_warnings = classify_risk_level(risk_indicators)

        # ---- Detect stop-loss (ineffective sell signals) ----
        stop_loss_price = None
        stop_loss_date = None
        if all_signals:
            all_stock_signals = [s for s in all_signals if s.stock_code == stock_code]
            # Find sell signals whose label is not 3 (有效卖出)
            # These represent stop-loss / ineffective exits
            ineffective_sells = [
                s for s in all_stock_signals
                if s.is_sell and s.label is not None and s.label != 3
            ]
            if ineffective_sells:
                # Use the most recent ineffective sell as the stop-loss marker
                ineffective_sells.sort(key=lambda s: s.time)
                latest_sl = ineffective_sells[-1]
                stop_loss_price = latest_sl.price
                stop_loss_date = latest_sl.date_str

        stock_data.append({
            "code": stock_code,
            "is_holding": is_holding,
            "pnl_pct": pnl,
            "entry_price": entry_price,
            "current_price": current_price,
            "signal_count": len(stock_signals),
            "trade_count": len(closed_trades) + (1 if is_holding else 0),
            "last_date": last_date,
            # Risk indicators
            "ret_5d": ret_5d,
            "atr_pct": atr_pct,
            "ma_bullish": ma_bullish,
            "avmood": avmood_val,
            "risk_level": risk_level,
            "risk_warnings": risk_warnings,
            # Stop-loss info (from ineffective sell signals)
            "stop_loss_price": stop_loss_price,
            "stop_loss_date": stop_loss_date,
        })

    # Apply status filter
    if status_filter == "持仓中":
        stock_data = [s for s in stock_data if s["is_holding"]]
    elif status_filter == "已清仓":
        stock_data = [s for s in stock_data if not s["is_holding"]]

    # ---- Sort state ----
    sort_key = f"sort_{selected_strategy}"
    if sort_key not in st.session_state:
        st.session_state[sort_key] = {"col": None, "asc": True}

    def _toggle_sort(col: str):
        s = st.session_state[sort_key]
        if s["col"] == col:
            s["asc"] = not s["asc"]
        else:
            s["col"] = col
            s["asc"] = True

    def _sort_arrow(col: str) -> str:
        s = st.session_state[sort_key]
        if s["col"] != col:
            return "  ↕"
        return "  ▲" if s["asc"] else "  ▼"

    # Apply sort
    s = st.session_state[sort_key]
    if s["col"]:
        reverse = not s["asc"]
        key_map = {
            "code":    lambda d: d["code"],
            "date":    lambda d: d["last_date"] or "0000-00-00",
            "entry":   lambda d: d["entry_price"] or -1e9,
            "current": lambda d: d["current_price"] or -1e9,
            "pnl":     lambda d: d["pnl_pct"] if d["pnl_pct"] is not None else -1e9,
            "ret5d":   lambda d: d["ret_5d"] if d["ret_5d"] is not None else -1e9,
            "atr":     lambda d: d["atr_pct"] if d["atr_pct"] is not None else -1e9,
            "avmood":  lambda d: d["avmood"] if d["avmood"] is not None else -1e9,
        }
        sort_fn = key_map.get(s["col"])
        if sort_fn:
            stock_data.sort(key=sort_fn, reverse=reverse)

    # ---- Render table ----
    stock_name_map = load_stock_name_map()

    st.caption("💡 点击 **股票代码** 进入资产详情 | 点击带 ↕ 的列名排序 | 🔴=高风险 ⚡=中风险 | ⚠️=已止损")

    col_weights = [0.2, 0.45, 0.55, 0.6, 0.35, 0.35, 0.5, 0.5, 0.5, 0.5, 0.45, 0.4, 0.35, 0.4]

    # Header
    hdr = st.columns(col_weights)
    hdr[0].markdown("**状态**")
    if hdr[1].button(f"**代码**{_sort_arrow('code')}", key="sort_code", type="tertiary"):
        _toggle_sort("code"); st.rerun()
    hdr[2].markdown("**名称**")
    if hdr[3].button(f"**日期**{_sort_arrow('date')}", key="sort_date", type="tertiary"):
        _toggle_sort("date"); st.rerun()
    if hdr[4].button(f"**入场价**{_sort_arrow('entry')}", key="sort_entry", type="tertiary"):
        _toggle_sort("entry"); st.rerun()
    if hdr[5].button(f"**当前价**{_sort_arrow('current')}", key="sort_current", type="tertiary"):
        _toggle_sort("current"); st.rerun()
    hdr[6].markdown("**止损**")
    if hdr[7].button(f"**收益**{_sort_arrow('pnl')}", key="sort_pnl", type="tertiary"):
        _toggle_sort("pnl"); st.rerun()
    # Risk columns
    if hdr[8].button(f"**前5日%**{_sort_arrow('ret5d')}", key="sort_ret5d", type="tertiary"):
        _toggle_sort("ret5d"); st.rerun()
    if hdr[9].button(f"**ATR%**{_sort_arrow('atr')}", key="sort_atr", type="tertiary"):
        _toggle_sort("atr"); st.rerun()
    hdr[10].markdown("**MA排列**")
    if hdr[11].button(f"**avmood**{_sort_arrow('avmood')}", key="sort_avmood", type="tertiary"):
        _toggle_sort("avmood"); st.rerun()
    hdr[12].markdown("**风险**")
    hdr[13].markdown("**信号/交易**")

    st.markdown("---")

    # Rows
    for sd in stock_data:
        code = sd["code"]
        stock_name = stock_name_map.get(code, "") or _FALLBACK_STOCK_NAMES.get(code, "")
        holding_icon = "📈" if sd["is_holding"] else "✅"
        pnl_val = sd["pnl_pct"]
        pnl_str = f"{pnl_val * 100:.2f}%" if pnl_val is not None else "—"
        entry_str = f"{sd['entry_price']:.4f}" if sd["entry_price"] else "—"
        current_str = f"{sd['current_price']:.4f}" if sd["current_price"] else "—"

        pnl_display = pnl_str
        if pnl_val is not None:
            if pnl_val > 0:
                pnl_display = f"🟢 {pnl_str}"
            elif pnl_val < 0:
                pnl_display = f"🔴 {pnl_str}"

        # Risk indicator display strings with color coding
        ret_5d_val = sd.get("ret_5d")
        if ret_5d_val is not None:
            if ret_5d_val > 15:
                ret_5d_str = f"🔴 {ret_5d_val:+.1f}%"
            elif ret_5d_val > 10:
                ret_5d_str = f"🟡 {ret_5d_val:+.1f}%"
            else:
                ret_5d_str = f"{ret_5d_val:+.1f}%"
        else:
            ret_5d_str = "—"

        atr_val = sd.get("atr_pct")
        if atr_val is not None:
            if atr_val > 6:
                atr_str = f"🔴 {atr_val:.1f}%"
            elif atr_val > 4:
                atr_str = f"🟡 {atr_val:.1f}%"
            else:
                atr_str = f"{atr_val:.1f}%"
        else:
            atr_str = "—"

        ma_val = sd.get("ma_bullish")
        if ma_val is not None:
            if ma_val == 1:
                ma_str = "✅ 多头"
            else:
                ma_str = "🔴 空头"
        else:
            ma_str = "—"

        avmood_val = sd.get("avmood")
        if avmood_val is not None:
            if avmood_val > 0.03:
                avmood_str = f"🟢 {avmood_val:.4f}"
            elif avmood_val > 0:
                avmood_str = f"🟡 {avmood_val:.4f}"
            else:
                avmood_str = f"🔴 {avmood_val:.4f}"
        else:
            avmood_str = "—"

        risk_level = sd.get("risk_level", "—")
        if risk_level == "高风险":
            risk_display = "🔴 高"
        elif risk_level == "中风险":
            risk_display = "🟡 中"
        elif risk_level == "低风险":
            risk_display = "🟢 低"
        else:
            risk_display = "—"

        sig_trade_str = f"{sd['signal_count']}/{sd['trade_count']}"

        # Stop-loss display
        sl_price = sd.get("stop_loss_price")
        sl_date = sd.get("stop_loss_date")
        if sl_price is not None:
            sl_display = f"⚠️ 已止损\n{sl_price:.4f}\n{sl_date}"
        else:
            sl_display = "—"

        row = st.columns(col_weights)
        row[0].write(holding_icon)
        if row[1].button(code, key=f"goto_{selected_strategy}_{code}", type="tertiary"):
            st.session_state["page"] = "📋 资产详情"
            st.session_state["detail_stock"] = code
            st.rerun()
        row[2].write(stock_name or "—")
        row[3].write(sd["last_date"])
        row[4].write(entry_str)
        row[5].write(current_str)
        row[6].write(sl_display)
        row[7].write(pnl_display)
        row[8].write(ret_5d_str)
        row[9].write(atr_str)
        row[10].write(ma_str)
        row[11].write(avmood_str)
        row[12].write(risk_display)
        row[13].write(sig_trade_str)

        # Show risk warnings as tooltip/expandable if any
        if sd.get("risk_warnings"):
            with row[12]:
                with st.expander("详", expanded=False):
                    for w in sd["risk_warnings"]:
                        st.caption(w)


# ============================================================
# Page: Asset Detail
# ============================================================
def render_stock_detail():
    """Render the detailed asset chart page with signals, indicators, and trades."""
    # Back to strategy detail
    if st.button("← 返回策略详情", key="back_to_strategy"):
        st.session_state["page"] = "📈 策略详情"
        st.rerun()

    st.title("📋 资产详情")

    if selected_strategy is None:
        st.warning("请从侧边栏选择一个策略。")
        return

    adapter = registry.get(selected_strategy)
    if adapter is None:
        st.error(f"策略 '{selected_strategy}' 未注册。")
        return

    # Stock selection
    stocks = adapter.get_stock_list()
    if not stocks:
        st.warning(f"策略 '{selected_strategy}' 没有信号数据。")
        return

    stock_name_map = load_stock_name_map()

    # Use session state for stock selection
    default_stock = st.session_state.get("detail_stock", stocks[0] if stocks else "")

    col1, col2 = st.columns([1, 3])
    with col1:
        # Show code + name in selectbox
        stock_options = {s: get_stock_display(s, stock_name_map) for s in stocks}
        selected_stock = st.selectbox(
            "选择资产",
            options=stocks,
            format_func=lambda x: stock_options.get(x, x),
            index=stocks.index(default_stock) if default_stock in stocks else 0,
            key="stock_detail_selector",
        )

    if not selected_stock:
        st.info("请选择一只股票。")
        return

    # Load data
    with st.spinner(f"加载 {selected_stock} 数据..."):
        # Load signals
        signals = adapter.load_stock_signals(selected_stock)
        if not signals:
            st.warning(f"股票 {selected_stock} 没有信号数据。")
            return

        # Load price data
        try:
            price_df = adapter.load_price_data(selected_stock, market_filter, level_filter)
        except FileNotFoundError as e:
            st.error(f"找不到行情数据: {e}")
            return
        except Exception as e:
            st.error(f"加载行情数据失败: {e}")
            return

        if price_df.empty:
            st.error(f"股票 {selected_stock} 没有行情数据。")
            return

        # Validate signal dates
        price_loader = PriceLoader(config)
        signal_dates = {s.date_str for s in signals}
        warnings = price_loader.validate_signal_dates(selected_stock, signal_dates, market_filter, level_filter)
        if warnings:
            render_data_warnings(warnings)

        # Pair trades
        pairer = TradePairer(config)
        closed_trades, open_position = pairer.pair_signals(signals, price_df)

        # Compute PnL stats
        pnl_calc = PnLCalculator(config.commission, config.slippage)
        closed_stats = pnl_calc.get_closed_trade_stats(closed_trades, selected_stock)

        # Load extra data for fuzzy_ma
        extra_data = None
        extra_label = ""
        if adapter.has_extra_data:
            with st.spinner("计算 Fuzzy MA 辅助指标..."):
                extra_data = adapter.load_extra_data(selected_stock, price_df, market_filter, level_filter)
                if extra_data is not None:
                    extra_label = adapter.get_extra_loader().get_description()

    # ============================================================
    # Header: Stock info and position status
    # ============================================================
    st.markdown("---")

    # Top metrics row
    latest_price = float(price_df["close"].iloc[-1]) if not price_df.empty else 0.0

    stock_display_name = get_stock_display(selected_stock, stock_name_map)

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("资产", stock_display_name)
    with col2:
        st.metric("策略", adapter.display_name)
    with col3:
        st.metric("最新价格", f"{latest_price:.4f}")
    with col4:
        if open_position:
            pnl_pct = open_position.pnl_pct
            st.metric(
                "浮动收益率",
                f"{pnl_pct * 100:.2f}%" if pnl_pct is not None else "N/A",
                delta_color="normal",
            )
        else:
            last_pnl = closed_stats.get("last_trade_pnl")
            st.metric(
                "最近交易收益",
                f"{last_pnl:.2f}%" if last_pnl is not None else "N/A",
            )
    with col5:
        if open_position:
            stop_str = f"{open_position.stop_loss:.4f}" if open_position.stop_loss else "⚠️ N/A"
            st.metric("止损位", stop_str)
        else:
            st.metric("累计收益", f"{closed_stats.get('total_pnl_pct', 0):.2f}%")

    # Position status
    st.markdown("---")

    if open_position:
        position_state = pnl_calc.get_position_state(
            [open_position], selected_stock, selected_strategy, latest_price
        )
        render_position_status(position_state)
    else:
        st.markdown("### ✅ 已清仓")
        if closed_stats.get("total_trades", 0) > 0:
            col_a, col_b, col_c, col_d = st.columns(4)
            with col_a:
                st.metric("历史交易数", closed_stats["total_trades"])
            with col_b:
                st.metric("盈利次数", closed_stats["win_count"])
            with col_c:
                st.metric("胜率", f"{closed_stats['win_rate'] * 100:.1f}%")
            with col_d:
                st.metric("累计收益", f"{closed_stats['total_pnl_pct']:.2f}%")

    # Label legend
    render_label_legend()

    st.markdown("---")

    # ============================================================
    # Chart
    # ============================================================
    st.subheader("📊 交易图表")

    # Filter controls
    filter_opts = render_signal_filter_ui("detail")

    # Build chart
    chart_builder = ChartBuilder(ma_periods=config.ma_periods)

    title = f"{selected_stock} — {adapter.display_name} ({market_filter}_{level_filter})"

    fig = chart_builder.build_chart(
        price_df=price_df,
        signals=signals,
        trades=closed_trades,
        open_position=open_position if filter_opts["show_unclosed"] else None,
        extra_data=extra_data,
        extra_label=extra_label,
        title=title,
    )

    st.plotly_chart(fig, width="stretch")

    # ============================================================
    # Trade History Table
    # ============================================================
    st.markdown("---")
    st.subheader("📝 交易明细")

    render_trade_table(
        closed_trades,
        stock_code=selected_stock,
        open_position=open_position if filter_opts["show_unclosed"] else None,
    )

    # ============================================================
    # Export
    # ============================================================
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📥 导出 HTML 报表"):
            export_path = Path(config.output_dir) / f"{selected_strategy}_{selected_stock}.html"
            export_path.parent.mkdir(parents=True, exist_ok=True)
            fig.write_html(str(export_path))
            st.success(f"报表已导出到: {export_path}")
    with col2:
        st.caption("💡 提示: 使用鼠标滚轮缩放图表，拖拽平移。")


# ============================================================
# Page: Market Condition
# ============================================================
def render_market_condition():
    """Render the AI market condition classification page."""
    render_index_condition_section()


# ============================================================
# Route to Page
# ============================================================
if "page" not in st.session_state:
    st.session_state["page"] = "🏠 首页"

current_page = st.session_state["page"]

if current_page == "🏠 首页":
    render_home()
elif current_page == "📈 策略详情":
    render_strategy_detail()
elif current_page == "📋 资产详情":
    render_stock_detail()
elif current_page == "🤖 行情分类":
    render_market_condition()
else:
    render_home()
