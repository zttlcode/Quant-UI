import type { PriceBar, SignalItem, TradeItem, ChartDataPoint } from './types'

// ── Simple Moving Average ──
function sma(data: number[], period: number): (number | null)[] {
  const out: (number | null)[] = []
  for (let i = 0; i < data.length; i++) {
    if (i < period - 1) { out.push(null); continue }
    let s = 0
    for (let j = i - period + 1; j <= i; j++) s += data[j]
    out.push(s / period)
  }
  return out
}

// ── EMA (for MACD) ──
function ema(data: number[], period: number): (number | null)[] {
  const out: (number | null)[] = []
  const k = 2 / (period + 1)
  let prev: number | null = null
  for (let i = 0; i < data.length; i++) {
    if (i < period - 1) {
      out.push(null)
      // accumulate SMA seed
      if (i === period - 2) {
        let s = 0
        for (let j = 0; j < period; j++) s += data[j]
        prev = s / period
      }
      continue
    }
    const val: number = data[i] * k + (prev ?? data[i]) * (1 - k)
    out.push(val)
    prev = val
  }
  return out
}

// ── MACD ──
function macd(data: number[], fast = 12, slow = 26, signal = 9) {
  const emaFast = ema(data, fast)
  const emaSlow = ema(data, slow)
  const dif: (number | null)[] = []
  for (let i = 0; i < data.length; i++) {
    if (emaFast[i] == null || emaSlow[i] == null) { dif.push(null); continue }
    dif.push(emaFast[i]! - emaSlow[i]!)
  }
  const difVals = dif.map((v) => v ?? 0)
  const deaArr = ema(difVals, signal)
  // DEA only valid after signal-1 bars of DIF
  const dea: (number | null)[] = difVals.map((_, i) => (i < signal - 1 ? null : deaArr[i]))
  const macdHist: (number | null)[] = dif.map((d, i) => {
    if (d == null || dea[i] == null) return null
    return (d - dea[i]!) * 2  // ×2 as common convention
  })
  return { dif, dea, macd: macdHist }
}

/** Build unified ChartDataPoint array from raw price + signals + optional avmood. */
export function buildChartData(
  priceData: PriceBar[],
  signals: SignalItem[],
  avmoodData?: { time: string; value: number }[] | null,
): ChartDataPoint[] {
  if (!priceData.length) return []

  const closes = priceData.map((d) => d.close)
  const ma5 = sma(closes, 5)
  const ma10 = sma(closes, 10)
  const ma20 = sma(closes, 20)
  const { dif, dea, macd: macdHist } = macd(closes)

  const avmoodMap = new Map<string, number>()
  avmoodData?.forEach((a) => avmoodMap.set(a.time.substring(0, 10), a.value))

  return priceData.map((d, i) => ({
    time: d.time,
    open: d.open,
    high: d.high,
    low: d.low,
    close: d.close,
    range: d.high - d.low,
    volume: d.volume,
    isUp: d.close >= d.open,
    ma5: ma5[i] ?? null,
    ma10: ma10[i] ?? null,
    ma20: ma20[i] ?? null,
    dif: dif[i] ?? null,
    dea: dea[i] ?? null,
    macd: macdHist[i] ?? null,
    avmood: avmoodMap.get(d.time.substring(0, 10)) ?? null,
  }))
}

/** Find buy/sell signal markers from trades, matching to chart data points. */
export function buildSignalMarkers(
  priceData: PriceBar[],
  trades: TradeItem[],
): { time: string; type: 'buy' | 'sell'; price: number }[] {
  const markers: { time: string; type: 'buy' | 'sell'; price: number }[] = []
  const priceByIdx = new Map<number, PriceBar>()
  priceData.forEach((p, i) => priceByIdx.set(i, p))

  trades.forEach((trade) => {
    // Entry → buy marker
    const entryDate = trade.entryTime.substring(0, 10)
    const entryMatch = priceData.find((p) => p.time.substring(0, 10) === entryDate)
    if (entryMatch) {
      markers.push({ time: entryMatch.time, type: 'buy', price: entryMatch.low * 0.995 })
    }
    // Exit → sell marker (only closed trades)
    if (!trade.isHolding && trade.exitTime) {
      const exitDate = trade.exitTime.substring(0, 10)
      const exitMatch = priceData.find((p) => p.time.substring(0, 10) === exitDate)
      if (exitMatch) {
        markers.push({ time: exitMatch.time, type: 'sell', price: exitMatch.high * 1.005 })
      }
    }
  })

  return markers
}
