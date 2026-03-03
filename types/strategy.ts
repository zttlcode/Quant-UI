export type StrategyStatus = 'running' | 'stopped' | 'paused' | 'backtesting'

export interface Strategy {
  id: string
  name: string
  description: string
  markets: string[]
  pnl: number  // 总收益百分比
  maxDrawdown: number  // 最大回撤百分比
  sharpe: number  // 夏普比率
  winRate: number  // 胜率百分比
  status: StrategyStatus
  createdAt: string
  updatedAt: string
  totalTrades: number
  profitTrades: number
  lossTrades: number
  avgProfit: number
  avgLoss: number
  profitFactor: number
}