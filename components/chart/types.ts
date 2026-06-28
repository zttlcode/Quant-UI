export interface PriceBar {
  time: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

export interface SignalItem {
  time: string
  type: 'buy' | 'sell'
  price: number
  label: number | null
}

export interface TradeItem {
  entryTime: string
  exitTime: string | null
  entryPrice: number
  exitPrice: number | null
  pnlPct: number | null
  isHolding: boolean
}

/** One data point for the combined chart. */
export interface ChartDataPoint {
  time: string
  open: number
  high: number
  low: number
  close: number
  range: number       // high - low (for candlestick)
  volume: number
  isUp: boolean
  ma5: number | null
  ma10: number | null
  ma20: number | null
  dif: number | null
  dea: number | null
  macd: number | null
  avmood: number | null
}
