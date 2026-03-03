'use client'

import { useState } from 'react'
import { MarketData, TradeSignal } from '@/types/trade'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Scatter } from 'recharts'
import { TrendingUp, TrendingDown, DollarSign, Activity } from 'lucide-react'

interface MarketChartProps {
  market: MarketData
  signals: TradeSignal[]
}

type ChartType = 'price' | 'returns'

export default function MarketChart({ market, signals }: MarketChartProps) {
  const [chartType, setChartType] = useState<ChartType>('price')

  // 计算收益曲线数据
  const returnsData = market.data.map((item, index) => {
    const basePrice = market.data[0].close
    const returnPct = ((item.close - basePrice) / basePrice * 100)
    return {
      time: item.time,
      returns: returnPct,
      volume: item.volume
    }
  })

  const chartData = chartType === 'price' ? market.data : returnsData
  const dataKey = chartType === 'price' ? 'close' : 'returns'

  // 准备买卖点标记数据
  const signalPoints = signals.map(signal => {
    const dataPoint = market.data.find(d =>
      new Date(d.time).getTime() <= new Date(signal.time).getTime()
    )
    return dataPoint ? {
      ...signal,
      x: dataPoint.time,
      y: chartType === 'price' ? dataPoint.close :
          ((dataPoint.close - market.data[0].close) / market.data[0].close * 100)
    } : null
  }).filter(Boolean)

  const formatPrice = (value: number) => {
    if (chartType === 'price') {
      // 使用固定格式避免 SSR 不匹配
      return value.toFixed(2)
    }
    return `${value.toFixed(2)}%`
  }

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-terminal-card border border-terminal-border p-3 rounded-lg shadow-lg">
          <p className="text-sm text-terminal-muted">
            {new Date(label).toISOString().replace('T', ' ').substring(0, 16)}
          </p>
          <p className="font-bold">
            {chartType === 'price' ? '价格' : '收益率'}: {formatPrice(payload[0].value)}
          </p>
          {chartType === 'price' && (
            <>
              <p className="text-sm">
                高: {payload[0].payload.high?.toFixed(2)}
              </p>
              <p className="text-sm">
                低: {payload[0].payload.low?.toFixed(2)}
              </p>
            </>
          )}
        </div>
      )
    }
    return null
  }

  return (
    <div className="bg-terminal-card border border-terminal-border rounded-xl p-6 card-hover-glow">
      {/* 头部 */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <div className="flex items-center gap-3">
            <h3 className="text-xl font-bold">{market.name}</h3>
            <span className="text-sm font-mono">{market.symbol}</span>
            <span className={`px-2 py-1 rounded-full text-xs font-medium flex items-center gap-1 ${
              market.change >= 0 ? 'bg-profit/10 text-profit' : 'bg-loss/10 text-loss'
            }`}>
              {market.change >= 0 ? (
                <TrendingUp className="w-3 h-3" />
              ) : (
                <TrendingDown className="w-3 h-3" />
              )}
              {market.change >= 0 ? '+' : ''}{market.change.toFixed(2)}%
            </span>
          </div>
          <div className="mt-2 flex items-center gap-4 text-sm">
            <div>
              <span className="text-terminal-muted">现价: </span>
              <span className="font-bold">${market.currentPrice.toFixed(2)}</span>
            </div>
            <div>
              <span className="text-terminal-muted">涨跌: </span>
              <span className={market.change >= 0 ? 'profit-text font-bold' : 'loss-text font-bold'}>
                ${market.changeAmount.toFixed(2)}
              </span>
            </div>
            <div className="flex items-center gap-1">
              <Activity className="w-3 h-3 text-terminal-muted" />
              <span className="text-terminal-muted">
                成交量: ${(market.volume / 1_000_000).toFixed(1)}M
              </span>
            </div>
          </div>
        </div>

        {/* 图表类型切换 */}
        <div className="flex bg-terminal-bg border border-terminal-border rounded-lg p-1">
          <button
            onClick={() => setChartType('price')}
            className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
              chartType === 'price'
                ? 'bg-primary text-primary-foreground'
                : 'text-terminal-muted hover:text-terminal-text'
            }`}
          >
            价格
          </button>
          <button
            onClick={() => setChartType('returns')}
            className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
              chartType === 'returns'
                ? 'bg-primary text-primary-foreground'
                : 'text-terminal-muted hover:text-terminal-text'
            }`}
          >
            收益率
          </button>
        </div>
      </div>

      {/* 图表区域 */}
      <div className="h-[300px]">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis
              dataKey="time"
              stroke="#9CA3AF"
              fontSize={12}
              tickLine={false}
              axisLine={false}
              tickFormatter={(value) => {
                const date = new Date(value)
                const hours = date.getHours().toString().padStart(2, '0')
                const minutes = date.getMinutes().toString().padStart(2, '0')
                return `${hours}:${minutes}`
              }}
            />
            <YAxis
              stroke="#9CA3AF"
              fontSize={12}
              tickLine={false}
              axisLine={false}
              tickFormatter={formatPrice}
            />
            <Tooltip content={<CustomTooltip />} />
            <Line
              type="monotone"
              dataKey={dataKey}
              stroke={market.change >= 0 ? "#10B981" : "#EF4444"}
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4, fill: market.change >= 0 ? "#10B981" : "#EF4444" }}
            />

            {/* 买卖点标记 */}
            {signalPoints.map((point: any) => (
              <Scatter
                key={point.id}
                data={[point]}
                shape={(props: any) => {
                  const { cx, cy } = props
                  return (
                    <g>
                      <circle
                        cx={cx}
                        cy={cy}
                        r={6}
                        fill={point.action === 'buy' ? '#10B981' : '#EF4444'}
                        stroke="#FFFFFF"
                        strokeWidth={2}
                      />
                      <text
                        x={cx}
                        y={cy - 10}
                        textAnchor="middle"
                        fill={point.action === 'buy' ? '#10B981' : '#EF4444'}
                        fontSize={10}
                        fontWeight="bold"
                      >
                        {point.action === 'buy' ? 'B' : 'S'}
                      </text>
                    </g>
                  )
                }}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* 信号列表 */}
      {signals.length > 0 && (
        <div className="mt-6 pt-6 border-t border-terminal-border">
          <h4 className="font-semibold mb-3">最近交易信号</h4>
          <div className="space-y-2">
            {signals.map((signal) => (
              <div
                key={signal.id}
                className="flex items-center justify-between p-3 bg-terminal-bg rounded-lg"
              >
                <div className="flex items-center gap-3">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                    signal.action === 'buy' ? 'bg-profit/10' : 'bg-loss/10'
                  }`}>
                    {signal.action === 'buy' ? (
                      <TrendingUp className="w-4 h-4 text-profit" />
                    ) : (
                      <TrendingDown className="w-4 h-4 text-loss" />
                    )}
                  </div>
                  <div>
                    <div className="font-medium">
                      {signal.action === 'buy' ? '买入' : '卖出'} @ ${signal.price.toFixed(2)}
                    </div>
                    <div className="text-xs text-terminal-muted">
                      {new Date(signal.time).toISOString().replace('T', ' ').substring(0, 16)}
                    </div>
                  </div>
                </div>
                {signal.profitLoss !== undefined && (
                  <div className={`font-bold ${signal.profitLoss >= 0 ? 'profit-text' : 'loss-text'}`}>
                    {signal.profitLoss >= 0 ? '+' : ''}{signal.profitLoss.toFixed(1)}%
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}