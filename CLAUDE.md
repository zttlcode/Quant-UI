# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Quant-UI is a two-layer quantitative trading strategy visualization platform:
- **Next.js 14 frontend** (root directory) — dark-themed dashboard displaying strategy performance, market charts, and index conditions
- **Python backend** (`src/`) — signal loading, trade pairing, indicator computation, and Plotly chart generation

The two layers are loosely coupled: the Python engine processes CSV data files and generates charts; the Next.js frontend renders strategy dashboards and reads market condition data via its own API route.

## Development Commands

### Frontend (Next.js)
```bash
npm run dev      # Start dev server (default port 3000)
npm run build    # Production build
npm run start    # Start production server
npm run lint     # Run ESLint
```

### Python Backend
Backend API server is started via `python api_server.py` (port 8765). Key dependencies: `pandas`, `numpy`, `plotly`, `pyyaml`, `starlette`, `uvicorn`.

**Python interpreter:** Use `D:\anaconda3\envs\Quant-UI\python.exe` (conda environment for this project). In Git Bash: `/d/anaconda3/envs/Quant-UI/python.exe`.

## Architecture

### Python Engine (`src/`)

**Data flow:** CSV files → SignalLoader/PriceLoader → TradePairer → PnLCalculator → ChartBuilder

| Layer | Module | Purpose |
|-------|--------|---------|
| Config | `config/settings.py` | YAML-based config with env var overrides, singleton `get_config()` |
| Data Model | `data_model/schemas.py` | Dataclasses: `TradeSignal`, `PriceBar`, `TradePair`, `PositionState`, `StrategySummary` |
| Data Model | `data_model/enums.py` | `SignalType` (buy/sell), `LabelType` (1=effective buy, 2=ineffective buy, 3=effective sell, 4=ineffective sell) |
| Data Loading | `data_loader/signal_loader.py` | Reads signal CSVs from `signal_root_dir/trade_point_live_inference_{strategy}/`, handles headerless files, UTF-8/GBK encoding, deduplication |
| Data Loading | `data_loader/price_loader.py` | Reads OHLCV CSVs from `price_root_dir/`, filename pattern: `live_bar_{Market}_{Code}_{Level}.csv` |
| Data Loading | `data_loader/extra_data.py` | Fuzzy MA extra indicators (avmood) computed via Kalman-filter-based fuzzy inference |
| Indicators | `indicators/ma.py` | SMA via `pd.rolling().mean()` |
| Indicators | `indicators/macd.py` | Standard MACD (DIF/DEA/histogram) via EMA |
| Indicators | `indicators/atr.py` | Average True Range, plus `compute_stop_loss()` |
| Strategy | `strategy/base.py` | `BaseStrategyAdapter` ABC — each strategy handles signal loading, price loading, extra data, and summaries |
| Strategy | `strategy/adapters.py` | Built-in adapters: `FuzzyMAAdapter`, `TeaRadicalNatureAdapter` |
| Strategy | `strategy/registry.py` | Singleton `StrategyRegistry` with `register()`/`get()` — plugin architecture for adding strategies without modifying existing code |
| Trade Engine | `trade_engine/pairer.py` | Pairs buy/sell signals into trades. Configurable rules: consecutive buy handling (`first`/`last`), consecutive sell handling (`ignore`/`warn`), duplicate signal strategy |
| Trade Engine | `trade_engine/pnl.py` | `PnLCalculator` for trade/strategy-level statistics |
| Visualization | `visualizer/chart_builder.py` | Plotly multi-panel charts: Panel 1 (candlestick + MAs + markers), Panel 2 (MACD), Panel 3 (avmood for fuzzy_ma) |
| Utils | `utils/file_utils.py` | CSV scanning, filename parsing (regex: `Market_Code_Level.csv`), directory management |

### Frontend (Next.js)

- **Framework:** Next.js 14 (App Router), React 18, TypeScript strict mode
- **Styling:** Tailwind CSS with `tailwindcss-animate`, dark theme via `next-themes`
- **UI:** Radix UI (`@radix-ui/react-tabs`, `@radix-ui/react-slot`), Lucide icons
- **Charts:** Recharts for bar/performance charts
- **Type definitions:** `types/strategy.ts` (Strategy interface), `types/trade.ts` (TradeSignal, MarketData)
- **API route:** `app/api/index-condition/route.ts` — reads index price + market condition CSVs from hardcoded Windows paths, merges by date, returns JSON with summary stats

### File Naming Conventions

- Signal files: `{Market}_{Code}_{Level}.csv` (e.g. `A_000027_d.csv`)
- Price files: `live_bar_{Market}_{Code}_{Level}.csv` (e.g. `live_bar_A_000027_d.csv`)
- Signal files live in per-strategy subdirectories: `trade_point_live_inference_{strategy}/`

### Configuration

- Python config is loaded from `config.yaml` (project root, not committed). Required fields: `signal_root_dir`, `price_root_dir`
- Env var overrides: `QUANT_UI_SIGNAL_ROOT_DIR`, `QUANT_UI_PRICE_ROOT_DIR`, `QUANT_UI_OUTPUT_DIR`, `QUANT_UI_LOG_LEVEL`, `QUANT_UI_SHOW_ONLY_EFFECTIVE`
- Frontend currently uses hardcoded CSV paths in the API route

### Adding a New Strategy

1. Create a subclass of `BaseStrategyAdapter` in `src/strategy/adapters.py`
2. Set `strategy_name` (must match the signal subdirectory name) and `display_name`
3. Optionally create a `StrategyExtraDataLoader` subclass if the strategy has extra indicators
4. Register in `src/strategy/registry.py` → `init_registry()`
