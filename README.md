# Quant UI - 量化交易策略实盘展示平台

专业的量化交易策略实盘展示平台，实时监控策略表现与市场行情。采用深色量化交易终端风格设计，类似 TradingView Dashboard。

## 特性

- 📊 **策略总览**：实时展示总收益率、今日收益、胜率、运行中策略数量
- 📈 **资金曲线图**：可视化策略资金增长曲线
- 🃏 **策略卡片**：详细展示每个策略的绩效指标（PNL、Sharpe、最大回撤、胜率等）
- 🌍 **全球市场行情**：SSE、HSI、NASDAQ、NIKKEI、BTC 实时K线图
- 🎯 **交易信号标记**：在图表上标记买卖点
- 📊 **策略对比仪表盘**：收益排行榜、Sharpe对比条形图、最大回撤对比
- 🌙 **深色模式**：专为量化交易设计的深色主题
- 📱 **响应式布局**：适配桌面、平板和手机
- ✨ **交互效果**：数字增长动画、卡片hover发光效果

## 技术栈

- **Next.js 14** (App Router)
- **TypeScript**
- **Tailwind CSS**
- **shadcn/ui** (基于 Radix UI)
- **Recharts** (数据可视化)
- **next-themes** (主题切换)

## 快速开始

### 安装依赖

```bash
npm install
```

### 开发环境

```bash
npm run dev
```

然后在浏览器中打开 [http://localhost:3000](http://localhost:3000)

### 生产构建

```bash
npm run build
npm start
```

## 项目结构

```
quant-ui/
├── app/                    # Next.js App Router
│   ├── layout.tsx         # 根布局
│   ├── page.tsx          # 主页
│   └── globals.css       # 全局样式
├── components/            # React组件
│   ├── navbar.tsx        # 导航栏
│   ├── hero-stats.tsx    # 英雄统计区
│   ├── strategy-card.tsx # 策略卡片
│   ├── market-chart.tsx  # 市场图表
│   └── performance-dashboard.tsx # 性能仪表盘
├── lib/                   # 工具函数和数据
│   └── mock-data.ts      # 模拟数据
├── types/                 # TypeScript类型定义
│   ├── strategy.ts       # 策略类型
│   └── trade.ts          # 交易类型
└── public/               # 静态资源
```

## 数据说明

平台使用模拟数据驱动UI，包含：

- 6个量化交易策略
- 5个全球市场（SSE、HSI、NASDAQ、NIKKEI、BTC）
- 实时交易信号
- 30天资金曲线历史数据

所有数据均为模拟生成，仅用于展示UI功能。

## 设计特色

### 颜色系统
- **盈利**：绿色 (`#10b981`)
- **亏损**：红色 (`#ef4444`)
- **背景**：深色终端 (`#0a0e17`)
- **卡片**：深灰 (`#111827`)
- **边框**：灰蓝 (`#1f2937`)

### 动画效果
- 数字增长动画
- 卡片hover发光效果
- 实时状态脉冲动画
- 平滑过渡效果

## 许可证

MIT

## 联系方式

- Twitter: [@quant_trader](https://twitter.com/quant_trader)
- 微信: quant_trader
- 知识星球: [量化交易社区](https://knowledge-planet.com/quant)