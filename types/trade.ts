export type TradeAction = 'buy' | 'sell'

export interface TradeSignal {
  id: string
  time: string
  action: TradeAction
  price: number
  marketId: string
  strategyId: string
  profitLoss?: number  // 盈亏百分比
}

export interface MarketData {
  id: string
  name: string
  symbol: string
  currentPrice: number
  change: number  // 涨跌幅百分比
  changeAmount: number
  volume: number
  data: {
    time: string
    open: number
    high: number
    low: number
    close: number
    volume: number
  }[]
}