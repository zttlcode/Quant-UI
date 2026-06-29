'use client'

import { useMemo } from 'react'
import { CandlestickPanel } from './chart/candlestick-panel'
import { MACDPanel } from './chart/macd-panel'
import { AvmoodPanel } from './chart/avmood-panel'
import { buildChartData } from './chart/indicators'
import { useT } from '@/lib/i18n'
import type { PriceBar, TradeItem } from './chart/types'

interface AssetChartProps {
  priceData: PriceBar[]
  trades: TradeItem[]
  isFuzzy?: boolean
  avmoodData?: { time: string; value: number }[] | null
  stopLossPrice?: number | null
  showMA5?: boolean
  showMA10?: boolean
  showMA20?: boolean
  showMACD?: boolean
}

export function AssetChart({
  priceData, trades, isFuzzy, avmoodData, stopLossPrice,
  showMA5 = true, showMA10 = true, showMA20 = true,
  showMACD = true,
}: AssetChartProps) {
  const t = useT('common')

  const chartData = useMemo(
    () => buildChartData(priceData, [], isFuzzy ? avmoodData : null),
    [priceData, isFuzzy, avmoodData],
  )

  if (!priceData.length) {
    return <div className="flex items-center justify-center h-64 text-terminal-muted text-sm">{t('noData')}</div>
  }

  return (
    <div className="space-y-1">
      {/* Panel 1 — Candlestick */}
      <div>
        <CandlestickPanel
          data={chartData}
          trades={trades}
          priceData={priceData}
          stopLossPrice={stopLossPrice}
          showMA5={showMA5}
          showMA10={showMA10}
          showMA20={showMA20}
          height={380}
        />
      </div>

      {/* Panel 2 — MACD */}
      {showMACD && (
        <div className="border-t border-border pt-1">
          <MACDPanel data={chartData} height={140} />
        </div>
      )}

      {/* Panel 3 — avmood (fuzzy only) */}
      {isFuzzy && (
        <div className="border-t border-border pt-1">
          <AvmoodPanel data={chartData} height={120} />
        </div>
      )}
    </div>
  )
}
