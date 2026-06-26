# Quant-UI: Stock Strategy Visualization Platform

股票策略可视化平台 — 基于 Streamlit + Plotly 的交互式量化交易信号可视化系统。

## 功能特性

- 📊 **多策略支持**: 插件化策略架构，轻松扩展新策略
- 📈 **交互式图表**: K线图 + MA均线 + MACD + 买卖点标记
- 🔍 **资产搜索**: 按股票代码搜索、按持仓状态筛选
- 📋 **交易明细**: 完整的交易记录表，含收益率、标签、概率
- 💰 **持仓管理**: 实时显示持仓收益、入场价、止损位
- 🤖 **AI 行情分类**: 深度学习模型实时识别指数行情状态（上涨/下跌/震荡）
- 📥 **报表导出**: 一键导出 HTML 交互式报表
- 🎨 **深色主题**: 现代化深色主题，清晰区分买卖点

## 页面结构

| 页面 | 说明 |
|------|------|
| 🏠 首页 | 平台功能介绍：策略交易 + AI 行情分类 |
| 📈 策略详情 | 选择策略后查看交易资产列表，点击行进入资产详情 |
| 📋 资产详情 | K线图 + 技术指标 + 买卖信号 + 交易明细 |
| 🤖 行情分类 | AI 模型对指数行情的实时分类（趋势上涨/下跌/震荡） |

## 目录结构

```
Quant-UI/
├── app.py                      # Streamlit 主入口
├── config.yaml                 # 配置文件
├── requirements.txt            # Python 依赖
├── README.md                   # 本文件
├── output/                     # 导出报表目录
└── src/
    ├── config/                 # 配置加载
    │   └── settings.py         # AppConfig, 环境变量覆盖
    ├── data_loader/            # 数据加载层
    │   ├── signal_loader.py    # 策略信号 CSV 读取
    │   ├── price_loader.py     # 历史行情 CSV 读取
    │   └── extra_data.py       # 策略额外数据接口
    ├── data_model/             # 数据模型
    │   ├── enums.py            # SignalType, LabelType 枚举
    │   └── schemas.py          # TradeSignal, PriceBar, TradePair 等
    ├── indicators/             # 技术指标
    │   ├── ma.py               # 移动平均线 (MA5/10/20)
    │   ├── macd.py             # MACD (DIF/DEA/柱)
    │   └── atr.py              # ATR 及止损计算
    ├── strategy/               # 策略适配层
    │   ├── base.py             # 策略基类
    │   ├── adapters.py         # 具体策略实现
    │   └── registry.py         # 策略注册中心
    ├── trade_engine/           # 交易引擎
    │   ├── pairer.py           # 买卖配对
    │   └── pnl.py              # 收益计算
    ├── visualizer/             # 可视化
    │   ├── chart_builder.py    # Plotly 图表构建
    │   └── components.py       # UI 组件
    └── utils/                  # 工具
        ├── date_utils.py       # 日期解析
        ├── file_utils.py       # 文件扫描
        └── logger.py           # 日志配置
```

## 快速启动

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置数据路径

编辑 `config.yaml`，设置你的数据目录：

```yaml
signal_root_dir: "D:/github/RobotMeQ_Dataset/QuantData"
price_root_dir: "D:/github/RobotMeQ_Dataset/QuantData/live"
index_price_csv_path: "D:/github/RobotMeQ_Dataset/QuantData/live_index/live_bar_A_000001_d.csv"
index_condition_csv_path: "D:/github/RobotMeQ_Dataset/QuantData/market_condition_live/A_000001_d.csv"
stock_name_csv_path: "D:/github/RobotMeQ_Dataset/QuantData/asset_code/a800_stocks.csv"
```

也可通过环境变量覆盖：
- `QUANT_UI_SIGNAL_ROOT_DIR`
- `QUANT_UI_PRICE_ROOT_DIR`

### 3. 启动应用

```bash
streamlit run app.py
```

浏览器会自动打开 `http://localhost:8501`。

## 数据约定

### 策略信号数据

信号文件放在 `{signal_root_dir}/trade_point_live_inference_{策略名}/` 目录下。

文件名格式: `{市场}_{股票代码}_{级别}.csv`
- 例如: `A_000027_d.csv` (A股, 000027, 日线)

CSV 列:
- `time`: 交易时间 (YYYY-MM-DD HH:MM:SS)
- `price`: 交易价格
- `signal`: buy / sell
- `label` (可选): 1=有效买入, 2=无效买入, 3=有效卖出, 4=无效卖出
- `prob` (可选): 模型分类概率

### 历史行情数据

行情文件放在 `{price_root_dir}/` 目录下。

文件名格式: `live_bar_{市场}_{股票代码}_{级别}.csv`
- 例如: `live_bar_A_000027_d.csv`

CSV 列: `time, open, high, low, close, volume`

### Fuzzy MA 额外数据 (avmood)

平台通过内置 `fuzzy()` 算法实时从行情数据计算 avmood 指标，无需额外配置文件。

### 股票代码-名称映射

股票名称映射文件配置在 `stock_name_csv_path`，CSV 包含以下列：
- `ipodate`: 上市日期
- `code`: 股票代码（带市场前缀，如 `sh.600000`、`sz.000027`）
- `code_name`: 股票中文名称（如 `浦发银行`、`深圳能源`）

平台会自动去除市场前缀并建立代码→名称的映射，在前端表格和详情页中同时显示代码与名称。

## 如何新增策略

1. 创建策略信号 CSV 目录: `{signal_root_dir}/trade_point_live_inference_{新策略名}/`
2. 在 `src/strategy/adapters.py` 中创建适配器:

```python
class MyNewAdapter(BaseStrategyAdapter):
    strategy_name = "my_new_strategy"
    display_name = "我的新策略"

    @property
    def description(self) -> str:
        return "策略描述"
```

3. 在 `src/strategy/registry.py` 的 `init_registry()` 中注册:

```python
from .adapters import MyNewAdapter
registry.register(MyNewAdapter(config))
```

4. 在 `config.yaml` 的 `default_strategy_list` 中添加策略名。

5. （可选）如果需要额外数据，继承 `StrategyExtraDataLoader` 并设置到适配器的 `_extra_loader`。

## 配置项说明

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| signal_root_dir | (必填) | 策略信号数据根目录 |
| price_root_dir | (必填) | 历史行情数据根目录 |
| index_price_csv_path | (必填) | 指数行情 CSV 文件路径（用于市场行情分类页面） |
| index_condition_csv_path | (必填) | 指数行情分类 CSV 文件路径（用于市场行情分类页面） |
| stock_name_csv_path | (必填) | 股票代码-名称映射 CSV（用于前端显示股票名称） |
| output_dir | ./output | 报表导出目录 |
| default_strategy_list | [] | 默认加载的策略列表 |
| default_market | A | 默认市场 |
| default_level | d | 默认时间级别 |
| show_only_effective_signal | false | 已废弃：label=2/4 信号在加载时自动过滤 |
| hold_stop_atr_multiplier | 1.0 | 止损 ATR 倍数 |
| commission | 0.0 | 手续费 |
| slippage | 0.0 | 滑点 |
| macd_fast | 12 | MACD 快线周期 |
| macd_slow | 26 | MACD 慢线周期 |
| macd_signal | 9 | MACD 信号线周期 |
| ma_periods | [5, 10, 20] | 均线周期列表 |
| atr_period | 14 | ATR 计算周期 |
| duplicate_signal_strategy | first | 同日多信号处理策略 |

## 边界情况处理

| 场景 | 处理方式 |
|------|----------|
| 只有买点没有卖点 | 标记为未平仓，按当前价计算浮动收益 |
| 只有卖点没有买点 | 根据配置忽略或警告 |
| 买卖点时间与行情不一致 | 明确提示警告信息 |
| 同一天多个信号 | 按配置保留第一条或最后一条 |
| 连续买入信号 | 按配置保留第一条或替换为最新 |
| 信号文件存在但行情缺失 | 明确报错提示 |
| 行情文件存在但信号缺失 | 正常显示，无信号标记 |
| fuzzy_ma 无 aa 数据 | 自动从行情计算 avmood |
| ATR/MACD 窗口不足 | 返回 NaN，页面提示 |
| 股票停牌或数据断档 | 图中自然显示空白段 |

## 技术栈

- **Web 框架**: Streamlit
- **图表**: Plotly
- **数据处理**: pandas, numpy
- **配置**: YAML + dataclasses

## 许可证

MIT
ps://twitter.com/quant_trader)
- 微信: quant_trader
- 知识星球: [量化交易社区](https://knowledge-planet.com/quant)