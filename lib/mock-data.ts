import { Strategy } from '@/types/strategy'
import { MarketData, TradeSignal } from '@/types/trade'

// 确定性随机数生成器（避免 SSR 和客户端不匹配）
function deterministicRandom(seed: number): number {
  const x = Math.sin(seed) * 10000
  return x - Math.floor(x)
}

// 生成时间序列数据（使用确定性随机数）
function generateTimeSeries(count: number, basePrice: number, volatility: number, seed: number = 42) {
  const data = []
  let price = basePrice
  const now = new Date()
  let randomSeed = seed

  for (let i = count - 1; i >= 0; i--) {
    const time = new Date(now.getTime() - i * 60 * 60 * 1000) // 每小时一个点

    // 使用确定性随机数
    randomSeed++
    const random1 = deterministicRandom(randomSeed)
    const random2 = deterministicRandom(randomSeed + 1)
    const random3 = deterministicRandom(randomSeed + 2)
    const random4 = deterministicRandom(randomSeed + 3)

    const change = (random1 - 0.5) * 2 * volatility
    price = price * (1 + change / 100)

    data.push({
      time: time.toISOString(),
      open: price * (1 - random2 * 0.01),
      high: price * (1 + random3 * 0.02),
      low: price * (1 - random4 * 0.02),
      close: price,
      volume: random1 * 1000000 + 500000
    })
  }

  return data
}

// 策略数据
export const strategies: Strategy[] = [
  {
    id: 'macd-divergence',
    name: 'MACD 背离策略',
    description: 'MACD 背离信号 + Triple Barrier Method + TimesNet 推理，捕捉趋势转折点的有效交易机会',
    markets: ['SSE', 'HSI'],
    pnl: 24.3,
    maxDrawdown: 8.2,
    sharpe: 2.1,
    winRate: 68.5,
    status: 'running',
    createdAt: '2024-01-15',
    updatedAt: '2025-02-27',
    totalTrades: 245,
    profitTrades: 168,
    lossTrades: 77,
    avgProfit: 1.8,
    avgLoss: 1.2,
    profitFactor: 2.4
  },
  {
    id: 'fuzzy-bayesian',
    name: '模糊贝叶斯策略',
    description: '模糊理论 + 目标导向贝叶斯寻优 + TimesNet 推理，适应复杂多变市场环境的智能策略',
    markets: ['NASDAQ', 'BTC'],
    pnl: 18.7,
    maxDrawdown: 12.5,
    sharpe: 1.8,
    winRate: 62.3,
    status: 'running',
    createdAt: '2024-02-20',
    updatedAt: '2025-02-27',
    totalTrades: 189,
    profitTrades: 118,
    lossTrades: 71,
    avgProfit: 2.1,
    avgLoss: 1.5,
    profitFactor: 1.9
  },
  {
    id: 'volatility-arbitrage',
    name: '波动率套利',
    description: '利用期权波动率偏度进行套利',
    markets: ['NIKKEI'],
    pnl: 32.5,
    maxDrawdown: 5.8,
    sharpe: 2.8,
    winRate: 75.2,
    status: 'running',
    createdAt: '2024-03-10',
    updatedAt: '2025-02-27',
    totalTrades: 156,
    profitTrades: 117,
    lossTrades: 39,
    avgProfit: 2.5,
    avgLoss: 1.8,
    profitFactor: 3.2
  },
  {
    id: 'ml-prediction',
    name: '机器学习预测',
    description: '基于LSTM神经网络的价格预测策略',
    markets: ['SSE', 'NASDAQ'],
    pnl: 15.6,
    maxDrawdown: 15.3,
    sharpe: 1.2,
    winRate: 58.7,
    status: 'paused',
    createdAt: '2024-04-05',
    updatedAt: '2025-02-26',
    totalTrades: 102,
    profitTrades: 60,
    lossTrades: 42,
    avgProfit: 2.8,
    avgLoss: 2.1,
    profitFactor: 1.6
  },
  {
    id: 'hft-market-making',
    name: '高频做市',
    description: '高频流动性提供策略',
    markets: ['BTC'],
    pnl: 42.8,
    maxDrawdown: 3.2,
    sharpe: 3.5,
    winRate: 82.1,
    status: 'running',
    createdAt: '2024-05-12',
    updatedAt: '2025-02-27',
    totalTrades: 1256,
    profitTrades: 1032,
    lossTrades: 224,
    avgProfit: 0.8,
    avgLoss: 0.6,
    profitFactor: 4.1
  },
  {
    id: 'fundamental-quant',
    name: '基本面量化',
    description: '结合基本面指标的量化选股策略',
    markets: ['SSE', 'HSI', 'NASDAQ'],
    pnl: 28.9,
    maxDrawdown: 9.7,
    sharpe: 2.4,
    winRate: 71.3,
    status: 'backtesting',
    createdAt: '2024-06-18',
    updatedAt: '2025-02-25',
    totalTrades: 87,
    profitTrades: 62,
    lossTrades: 25,
    avgProfit: 3.2,
    avgLoss: 2.4,
    profitFactor: 2.7
  }
]

// 市场数据
export const marketData: MarketData[] = [
  {
    id: 'sse',
    name: '上证指数',
    symbol: 'SSE',
    currentPrice: 3250.42,
    change: 1.25,
    changeAmount: 40.18,
    volume: 45230000000,
    data: generateTimeSeries(24, 3200, 0.8, 1001)
  },
  {
    id: 'hsi',
    name: '恒生指数',
    symbol: 'HSI',
    currentPrice: 16845.32,
    change: -0.42,
    changeAmount: -71.25,
    volume: 12580000000,
    data: generateTimeSeries(24, 16900, 1.2, 1002)
  },
  {
    id: 'nasdaq',
    name: '纳斯达克',
    symbol: 'NASDAQ',
    currentPrice: 16235.78,
    change: 0.85,
    changeAmount: 137.42,
    volume: 78250000000,
    data: generateTimeSeries(24, 16100, 1.5, 1003)
  },
  {
    id: 'nikkei',
    name: '日经指数',
    symbol: 'NIKKEI',
    currentPrice: 38542.18,
    change: 2.12,
    changeAmount: 800.25,
    volume: 4521000000,
    data: generateTimeSeries(24, 37700, 1.0, 1004)
  },
  {
    id: 'btc',
    name: '比特币',
    symbol: 'BTC',
    currentPrice: 68250.75,
    change: 3.82,
    changeAmount: 2510.32,
    volume: 38542000000,
    data: generateTimeSeries(24, 65700, 3.5, 1005)
  }
]

// 交易信号
export const tradeSignals: TradeSignal[] = [
  {
    id: '1',
    time: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
    action: 'buy',
    price: 3220.15,
    marketId: 'sse',
    strategyId: '1',
    profitLoss: 1.8
  },
  {
    id: '2',
    time: new Date(Date.now() - 1 * 60 * 60 * 1000).toISOString(),
    action: 'sell',
    price: 3260.42,
    marketId: 'sse',
    strategyId: '1',
    profitLoss: 1.2
  },
  {
    id: '3',
    time: new Date(Date.now() - 3 * 60 * 60 * 1000).toISOString(),
    action: 'buy',
    price: 16750.42,
    marketId: 'hsi',
    strategyId: '2',
    profitLoss: 0.8
  },
  {
    id: '4',
    time: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
    action: 'sell',
    price: 16820.15,
    marketId: 'hsi',
    strategyId: '2',
    profitLoss: 0.4
  },
  {
    id: '5',
    time: new Date(Date.now() - 45 * 60 * 1000).toISOString(),
    action: 'buy',
    price: 67500.25,
    marketId: 'btc',
    strategyId: '5',
    profitLoss: 1.1
  }
]

// 计算总览统计数据
export function getOverviewStats() {
  const runningStrategies = strategies.filter(s => s.status === 'running')
  const totalPnl = runningStrategies.reduce((sum, s) => sum + s.pnl, 0)
  const avgPnl = runningStrategies.length > 0 ? totalPnl / runningStrategies.length : 0
  const totalWinRate = runningStrategies.reduce((sum, s) => sum + s.winRate, 0)
  const avgWinRate = runningStrategies.length > 0 ? totalWinRate / runningStrategies.length : 0
  const todayProfit = runningStrategies.reduce((sum, s) => sum + (s.pnl * 0.01), 0) // 模拟今日收益

  return {
    totalPnl: avgPnl,
    todayProfit: todayProfit,
    winRate: avgWinRate,
    runningStrategies: runningStrategies.length,
    totalStrategies: strategies.length
  }
}