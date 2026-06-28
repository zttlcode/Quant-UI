'use client'

import React, { useMemo } from 'react'
import {
  ComposedChart, Bar, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, ReferenceLine, ReferenceDot,
} from 'recharts'
import type { ChartDataPoint, TradeItem, PriceBar } from './types'

const C_UP = '#EF553B'
const C_DOWN = '#00CC96'
const C_MA5 = '#636EFA'
const C_MA10 = '#FFA15A'
const C_MA20 = '#B6E880'

/** Custom candlestick shape — renders wick + body from normalized OHLC prices. */
function CandlestickShape(props: any) {
  const { x, y, width, height, payload } = props
  if (!payload || !height) return <g />

  const range = payload._high - payload._low
  if (range <= 0) return <g />

  const centerX = x + width / 2
  const scale = height / range
  const isUp = payload._close >= payload._open
  const bodyColor = isUp ? C_UP : C_DOWN

  const bodyTop = y + (payload._high - Math.max(payload._open, payload._close)) * scale
  const bodyBottom = y + (payload._high - Math.min(payload._open, payload._close)) * scale
  const bodyH = Math.max(bodyBottom - bodyTop, 0.5)
  const bodyW = Math.max(width * 0.8, 2)

  return (
    <g>
      <line x1={centerX} y1={y} x2={centerX} y2={bodyTop} stroke={bodyColor} strokeWidth={1} opacity={0.7} />
      <line x1={centerX} y1={bodyBottom} x2={centerX} y2={y + height} stroke={bodyColor} strokeWidth={1} opacity={0.7} />
      <rect x={centerX - bodyW / 2} y={bodyTop} width={bodyW} height={bodyH} fill={bodyColor} rx={0.5} />
      {!isUp && <rect x={centerX - bodyW / 2} y={bodyTop} width={bodyW} height={bodyH} fill="none" stroke={bodyColor} strokeWidth={0.8} opacity={0.8} rx={0.5} />}
    </g>
  )
}

interface CandlestickPanelProps {
  data: ChartDataPoint[]
  trades: TradeItem[]
  priceData: PriceBar[]
  stopLossPrice?: number | null
  showMA5?: boolean
  showMA10?: boolean
  showMA20?: boolean
  height?: number
}

export function CandlestickPanel({
  data, trades, priceData, stopLossPrice,
  showMA5 = true, showMA10 = true, showMA20 = true,
  height = 380,
}: CandlestickPanelProps) {
  // ── Normalize prices: shift by basePrice so Y-axis starts near 0 ──
  const { normData, normStop, normBuy, normSell, basePrice, yDomainNorm } = useMemo(() => {
    const buy: { time: string; price: number }[] = []
    const sell: { time: string; price: number }[] = []

    // Find actual min/max from visible data
    let minVal = Infinity, maxVal = -Infinity
    data.forEach((d) => {
      if (d.low < minVal) minVal = d.low
      if (d.high > maxVal) maxVal = d.high
    })

    trades.forEach((t) => {
      const d = t.entryTime.substring(0, 10)
      const bar = priceData.find((p) => p.time.substring(0, 10) === d)
      if (bar) buy.push({ time: bar.time, price: bar.low })
      if (!t.isHolding && t.exitTime) {
        const ed = t.exitTime.substring(0, 10)
        const ebar = priceData.find((p) => p.time.substring(0, 10) === ed)
        if (ebar) sell.push({ time: ebar.time, price: ebar.high })
      }
    })

    const base = minVal - (maxVal - minVal) * 0.02   // 2% padding below the lowest low
    const pad = (maxVal - minVal) * 0.02 || 0.1       // 2% padding above

    // Normalize each data point
    const norm = data.map((d) => ({
      ...d,
      // Keep original OHLC for tooltip
      _open: d.open,
      _high: d.high,
      _low: d.low,
      _close: d.close,
      // Normalized values for chart rendering
      open: d.open - base,
      high: d.high - base,
      low: d.low - base,
      close: d.close - base,
      range: d.range, // invariant to shift
      ma5: d.ma5 != null ? d.ma5 - base : null,
      ma10: d.ma10 != null ? d.ma10 - base : null,
      ma20: d.ma20 != null ? d.ma20 - base : null,
    }))

    const normStopLoss = stopLossPrice ? stopLossPrice - base : null
    const normBuy = buy.map((m) => ({ ...m, price: m.price - base }))
    const normSell = sell.map((m) => ({ ...m, price: m.price - base }))

    return {
      normData: norm,
      normStop: normStopLoss,
      normBuy,
      normSell,
      basePrice: base,
      yDomainNorm: [0, (maxVal + pad) - base] as [number, number],
    }
  }, [data, trades, priceData, stopLossPrice])

  const formatDate = (t: string) => {
    try { return `${new Date(t).getMonth() + 1}/${new Date(t).getDate()}` }
    catch { return t.substring(5, 10) }
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <ComposedChart data={normData} margin={{ top: 8, right: 10, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.4} />
        <XAxis dataKey="time" tickFormatter={formatDate} hide />

        {/* Y-axis: shows REAL price (base + normalized value) */}
        <YAxis
          domain={yDomainNorm}
          tickFormatter={(v: number) => (v + basePrice).toFixed(2)}
          tick={{ fontSize: 10, fontFamily: 'JetBrains Mono', fill: 'hsl(var(--muted-foreground))' }}
          axisLine={false} tickLine={false} width={60}
        />

        <Tooltip
          content={({ active, payload }: any) => {
            if (!active || !payload?.length) return null
            const d = payload[0]?.payload as any
            if (!d) return null
            const o = d._open ?? d.open + basePrice
            const h = d._high ?? d.high + basePrice
            const l = d._low ?? d.low + basePrice
            const c = d._close ?? d.close + basePrice
            return (
              <div className="glass-card-variant p-3 text-xs font-mono">
                <p className="text-terminal-muted mb-1">{d.time?.substring(0, 10)}</p>
                <p>O: {o?.toFixed(2)}  H: <span className="text-quant-red">{h?.toFixed(2)}</span></p>
                <p>L: <span className="text-quant-green">{l?.toFixed(2)}</span>  C: <span className={(c >= o) ? 'text-quant-red' : 'text-quant-green'}>{c?.toFixed(2)}</span></p>
              </div>
            )
          }}
        />

        {/* Candlestick bars */}
        <Bar dataKey="low" stackId="candle" fill="transparent" isAnimationActive={false} />
        <Bar dataKey="range" stackId="candle" shape={<CandlestickShape />} isAnimationActive={false} />

        {/* MA lines */}
        {showMA5 && <Line type="monotone" dataKey="ma5" stroke={C_MA5} dot={false} strokeWidth={1} />}
        {showMA10 && <Line type="monotone" dataKey="ma10" stroke={C_MA10} dot={false} strokeWidth={1} />}
        {showMA20 && <Line type="monotone" dataKey="ma20" stroke={C_MA20} dot={false} strokeWidth={1} />}

        {/* Buy markers */}
        {normBuy.map((m, i) => (
          <ReferenceDot key={`b-${i}`} x={m.time} y={m.price} r={5} fill={C_DOWN} stroke="#059669" strokeWidth={1}
            shape={(p: any) => (<g transform={`translate(${p.cx},${p.cy})`}><polygon points="0,-7 6,4 -6,4" fill={C_DOWN} stroke="#059669" strokeWidth={0.8} /></g>)} />
        ))}

        {/* Sell markers */}
        {normSell.map((m, i) => (
          <ReferenceDot key={`s-${i}`} x={m.time} y={m.price} r={5} fill={C_UP} stroke="#991B1B" strokeWidth={1}
            shape={(p: any) => (<g transform={`translate(${p.cx},${p.cy})`}><polygon points="0,7 6,-4 -6,-4" fill={C_UP} stroke="#991B1B" strokeWidth={0.8} /></g>)} />
        ))}

        {/* Stop loss */}
        {normStop && normStop > 0 && (
          <ReferenceLine y={normStop} stroke="#FF0000" strokeDasharray="6 3" strokeWidth={1}
            label={{ value: `止损 ${stopLossPrice?.toFixed(2)}`, position: 'right', fontSize: 10, fontFamily: 'JetBrains Mono', fill: '#FF0000' }} />
        )}
      </ComposedChart>
    </ResponsiveContainer>
  )
}
