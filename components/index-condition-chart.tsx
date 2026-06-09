'use client'

import { useState, useEffect, useMemo, useCallback } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell, ReferenceLine,
} from 'recharts'
import {
  TrendingUp, TrendingDown, Minus, BarChart3,
  AlertCircle, Loader2, ChevronLeft, ChevronRight,
} from 'lucide-react'

// ---------- 类型定义 ----------
interface IndexBar {
  time: string
  open: number
  high: number
  low: number
  close: number
  volume: number
  marketCondition: 'trend_up' | 'trend_down' | 'range' | null
  probability: number | null
}

interface ApiResponse {
  indexCode: string
  indexName: string
  totalBars: number
  barsWithCondition: number
  conditionCounts: {
    trend_up: number
    trend_down: number
    range: number
  }
  latestBar: IndexBar | null
  bars: IndexBar[]
}

// 用于 Recharts 的数据结构（包含 range 字段用于 stacking）
interface ChartDataPoint extends IndexBar {
  range: number  // high - low，用于 stacking 计算
}

// ---------- 常数 ----------
const CONDITION_CONFIG: Record<string, { label: string; color: string; bgColor: string; icon: typeof TrendingUp }> = {
  trend_up:    { label: '上涨', color: '#10B981', bgColor: 'rgba(16,185,129,0.15)', icon: TrendingUp },
  trend_down:  { label: '下跌', color: '#EF4444', bgColor: 'rgba(239,68,68,0.15)',   icon: TrendingDown },
  range:       { label: '震荡', color: '#F59E0B', bgColor: 'rgba(245,158,11,0.15)',  icon: Minus },
}

const DEFAULT_BARS = 60 // 默认显示最近60个 bar

// ---------- 自定义蜡烛图形状 ----------
interface CandlestickShapeProps {
  x: number
  y: number
  width: number
  height: number
  index: number
  payload: ChartDataPoint
}

function CandlestickShape(props: any) {
  const { x, y, width, height, payload } = props as CandlestickShapeProps
  const { open, high, low, close, marketCondition } = payload

  const dataRange = high - low
  if (dataRange <= 0 || height <= 0) {
    // 退化情况：画一条水平线
    const cx = x + width / 2
    return (
      <line
        x1={cx} y1={y}
        x2={cx} y2={y + Math.max(height, 1)}
        stroke="#6B7280" strokeWidth={1}
      />
    )
  }

  const pixelPerUnit = height / dataRange
  const centerX = x + width / 2

  // 计算各价格在像素空间中的 Y 坐标
  const highY = y
  const lowY = y + height
  const openY = y + (high - open) * pixelPerUnit
  const closeY = y + (high - close) * pixelPerUnit

  const bodyTop = Math.min(openY, closeY)
  const bodyBottom = Math.max(openY, closeY)
  const bodyHeight = Math.max(bodyBottom - bodyTop, 0.5)

  // 判断是阳线 (close >= open) 还是阴线
  const isBullish = close >= open

  // 选择蜡烛颜色：优先用行情分类颜色，无分类则用阴阳线颜色
  let bodyColor: string
  let bodyOpacity: number
  if (marketCondition && CONDITION_CONFIG[marketCondition]) {
    bodyColor = CONDITION_CONFIG[marketCondition].color
    bodyOpacity = isBullish ? 0.85 : 0.45
  } else {
    bodyColor = isBullish ? '#10B981' : '#EF4444'
    bodyOpacity = isBullish ? 0.8 : 0.7
  }

  const bodyWidth = Math.max(width * 0.65, 1.5)

  return (
    <g>
      {/* 上影线 (high → body top) */}
      <line
        x1={centerX} y1={highY}
        x2={centerX} y2={bodyTop}
        stroke={bodyColor}
        strokeWidth={1}
        opacity={0.7}
      />
      {/* 下影线 (body bottom → low) */}
      <line
        x1={centerX} y1={bodyBottom}
        x2={centerX} y2={lowY}
        stroke={bodyColor}
        strokeWidth={1}
        opacity={0.7}
      />
      {/* 蜡烛实体 (open ↔ close) */}
      <rect
        x={centerX - bodyWidth / 2}
        y={bodyTop}
        width={bodyWidth}
        height={bodyHeight}
        fill={bodyColor}
        opacity={bodyOpacity}
        rx={0.5}
      />
      {/* 阴线加边框 */}
      {!isBullish && (
        <rect
          x={centerX - bodyWidth / 2}
          y={bodyTop}
          width={bodyWidth}
          height={bodyHeight}
          fill="none"
          stroke={bodyColor}
          strokeWidth={0.8}
          opacity={0.8}
          rx={0.5}
        />
      )}
    </g>
  )
}

// ---------- 自定义 Tooltip ----------
function CustomTooltip({ active, payload }: any) {
  if (!active || !payload || !payload.length) return null

  const data: ChartDataPoint = payload[0]?.payload
  if (!data) return null

  const condition = data.marketCondition
  const config = condition ? CONDITION_CONFIG[condition] : null
  const isBullish = data.close >= data.open
  const changePct = ((data.close - data.open) / data.open * 100)

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-lg p-3 shadow-xl min-w-[200px]">
      {/* 日期 */}
      <p className="text-xs text-gray-400 mb-2">{data.time}</p>

      {/* OHLC */}
      <div className="grid grid-cols-2 gap-x-4 gap-y-0.5 text-sm">
        <span className="text-gray-400">开盘:</span>
        <span className="text-right font-mono">{data.open.toFixed(2)}</span>
        <span className="text-gray-400">最高:</span>
        <span className="text-right font-mono text-green-400">{data.high.toFixed(2)}</span>
        <span className="text-gray-400">最低:</span>
        <span className="text-right font-mono text-red-400">{data.low.toFixed(2)}</span>
        <span className="text-gray-400">收盘:</span>
        <span className={`text-right font-mono ${isBullish ? 'text-green-400' : 'text-red-400'}`}>
          {data.close.toFixed(2)}
        </span>
      </div>

      {/* 涨跌幅 */}
      <div className={`mt-1 text-xs ${changePct >= 0 ? 'text-green-400' : 'text-red-400'}`}>
        {changePct >= 0 ? '+' : ''}{changePct.toFixed(2)}%
      </div>

      {/* 行情分类 */}
      {config && (
        <div
          className="mt-2 pt-2 border-t border-gray-700 flex items-center justify-between"
        >
          <span className="text-xs text-gray-400">AI 行情分类:</span>
          <span
            className="px-2 py-0.5 rounded text-xs font-semibold"
            style={{ backgroundColor: config.bgColor, color: config.color }}
          >
            {config.label}
          </span>
        </div>
      )}

      {/* 预测概率 */}
      {data.probability !== null && (
        <div className="mt-1 flex items-center justify-between">
          <span className="text-xs text-gray-400">分类概率:</span>
          <span className="text-xs font-mono font-semibold" style={{ color: config?.color ?? '#9CA3AF' }}>
            {(data.probability * 100).toFixed(0)}%
          </span>
        </div>
      )}

      {/* 成交量 */}
      <div className="mt-1 flex items-center justify-between">
        <span className="text-xs text-gray-400">成交量:</span>
        <span className="text-xs font-mono">
          {(data.volume / 1_0000_0000).toFixed(2)}亿
        </span>
      </div>
    </div>
  )
}

// ---------- 行情分类图例 ----------
type ConditionKey = keyof typeof CONDITION_CONFIG

function ConditionLegend({ counts }: { counts: Record<ConditionKey, number> }) {
  return (
    <div className="flex items-center gap-4 text-xs">
      {(Object.keys(CONDITION_CONFIG) as ConditionKey[]).map((key) => {
        const config = CONDITION_CONFIG[key]
        const Icon = config.icon
        return (
          <div key={key} className="flex items-center gap-1.5">
            <div
              className="w-3 h-3 rounded-sm flex items-center justify-center"
              style={{ backgroundColor: config.bgColor }}
            >
              <Icon className="w-2 h-2" style={{ color: config.color }} />
            </div>
            <span className="text-terminal-muted">{config.label}</span>
            <span className="font-mono font-medium" style={{ color: config.color }}>
              {counts[key]}
            </span>
          </div>
        )
      })}
    </div>
  )
}

// ---------- 最新分类指示器 ----------
function LatestConditionCard({ bar }: { bar: IndexBar }) {
  const condition = bar.marketCondition
  const config = condition ? CONDITION_CONFIG[condition] : null
  const Icon = config?.icon ?? AlertCircle
  const isBullish = bar.close >= bar.open
  const changePct = ((bar.close - bar.open) / bar.open * 100)

  return (
    <div
      className="relative overflow-hidden rounded-xl border-2 p-5"
      style={{
        borderColor: config?.color ?? '#6B7280',
        backgroundColor: config?.bgColor ?? 'rgba(107,114,128,0.1)',
      }}
    >
      {/* 背景装饰 */}
      <div className="absolute top-0 right-0 opacity-10">
        <Icon className="w-24 h-24 -mr-4 -mt-4" style={{ color: config?.color }} />
      </div>

      <div className="relative">
        {/* 标题行 */}
        <div className="flex items-center justify-between mb-4">
          <div>
            <p className="text-xs text-terminal-muted uppercase tracking-wider">
              最新 AI 行情分类
            </p>
            <p className="text-lg font-bold mt-0.5">
              {bar.time}
            </p>
          </div>
          {config ? (
            <div
              className="flex items-center gap-2 px-4 py-2.5 rounded-full"
              style={{ backgroundColor: config.color, color: '#fff' }}
            >
              <Icon className="w-5 h-5" />
              <span className="text-lg font-bold">{config.label}</span>
            </div>
          ) : (
            <div className="flex items-center gap-2 px-4 py-2.5 rounded-full bg-gray-600 text-white">
              <AlertCircle className="w-5 h-5" />
              <span className="text-lg font-bold">无数据</span>
            </div>
          )}
        </div>

        {/* 详情行 */}
        <div className="grid grid-cols-2 gap-4">
          {/* 价格信息 */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <span className="text-xs text-terminal-muted">收盘价</span>
              <span className="font-mono font-semibold">{bar.close.toFixed(2)}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-xs text-terminal-muted">涨跌</span>
              <span className={`font-mono font-semibold ${changePct >= 0 ? 'profit-text' : 'loss-text'}`}>
                {changePct >= 0 ? '+' : ''}{changePct.toFixed(2)}%
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-xs text-terminal-muted">成交量</span>
              <span className="font-mono text-sm">{(bar.volume / 1_0000_0000).toFixed(2)}亿</span>
            </div>
          </div>

          {/* 分类概率 */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <span className="text-xs text-terminal-muted">分类概率</span>
              <span
                className="text-3xl font-bold font-mono"
                style={{ color: config?.color }}
              >
                {bar.probability !== null
                  ? `${(bar.probability * 100).toFixed(0)}%`
                  : '--'}
              </span>
            </div>
            {bar.probability !== null && (
              <div className="mt-1 h-2 bg-black/20 rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full transition-all duration-700"
                  style={{
                    width: `${(bar.probability * 100).toFixed(0)}%`,
                    backgroundColor: config?.color,
                  }}
                />
              </div>
            )}
            <p className="text-xs text-terminal-muted mt-1">
              {bar.probability !== null && bar.probability >= 0.7
                ? '模型置信度较高'
                : bar.probability !== null && bar.probability >= 0.5
                  ? '模型置信度中等'
                  : bar.probability !== null
                    ? '模型置信度较低'
                    : ''}
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

// ---------- 主组件 ----------
export default function IndexConditionChart() {
  const [data, setData] = useState<ApiResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [visibleStart, setVisibleStart] = useState(0) // 可见范围起点索引
  const [visibleBars, setVisibleBars] = useState(DEFAULT_BARS) // 可见 bar 数量

  // 加载数据
  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true)
        setError(null)
        const res = await fetch('/api/index-condition')
        if (!res.ok) {
          const errData = await res.json().catch(() => ({}))
          throw new Error(errData.error || `HTTP ${res.status}`)
        }
        const json = await res.json()
        setData(json)
        // 默认显示最后 N 个 bar
        setVisibleStart(Math.max(0, json.bars.length - DEFAULT_BARS))
      } catch (err: any) {
        setError(err.message || '加载数据失败')
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [])

  // 构建图表数据（添加 range 字段）
  const chartData: ChartDataPoint[] = useMemo(() => {
    if (!data) return []
    return data.bars.map(bar => ({
      ...bar,
      range: bar.high - bar.low,
    }))
  }, [data])

  // 当前可见的数据
  const visibleData = useMemo(() => {
    return chartData.slice(visibleStart, visibleStart + visibleBars)
  }, [chartData, visibleStart, visibleBars])

  // 翻页控制
  const canGoBack = visibleStart > 0
  const canGoForward = visibleStart + visibleBars < chartData.length

  const goBack = useCallback(() => {
    setVisibleStart(prev => Math.max(0, prev - Math.floor(visibleBars / 2)))
  }, [visibleBars])

  const goForward = useCallback(() => {
    setVisibleStart(prev => Math.min(
      chartData.length - visibleBars,
      prev + Math.floor(visibleBars / 2)
    ))
  }, [chartData.length, visibleBars])

  const goToLatest = useCallback(() => {
    setVisibleStart(Math.max(0, chartData.length - visibleBars))
  }, [chartData.length, visibleBars])

  // 计算 Y 轴范围
  const yDomain = useMemo(() => {
    if (visibleData.length === 0) return [0, 100]
    const lows = visibleData.map(d => d.low)
    const highs = visibleData.map(d => d.high)
    const min = Math.min(...lows)
    const max = Math.max(...highs)
    const padding = (max - min) * 0.05
    return [min - padding, max + padding]
  }, [visibleData])

  // 格式化日期标签
  const formatDateLabel = (timeStr: string) => {
    const parts = timeStr.split('-')
    if (parts.length >= 3) {
      return `${parts[1]}/${parts[2]}` // MM/DD
    }
    return timeStr
  }

  // ---------- 加载状态 ----------
  if (loading) {
    return (
      <div className="bg-terminal-card border border-terminal-border rounded-xl p-6 card-hover-glow">
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-8 h-8 text-primary animate-spin" />
          <span className="ml-3 text-terminal-muted">正在加载指数数据...</span>
        </div>
      </div>
    )
  }

  // ---------- 错误状态 ----------
  if (error) {
    return (
      <div className="bg-terminal-card border border-terminal-border rounded-xl p-6 card-hover-glow">
        <div className="flex items-center justify-center py-20 text-loss">
          <AlertCircle className="w-6 h-6 mr-2" />
          <span>数据加载失败: {error}</span>
        </div>
      </div>
    )
  }

  // ---------- 空数据 ----------
  if (!data || data.bars.length === 0) {
    return (
      <div className="bg-terminal-card border border-terminal-border rounded-xl p-6 card-hover-glow">
        <div className="flex items-center justify-center py-20 text-terminal-muted">
          <BarChart3 className="w-6 h-6 mr-2" />
          <span>暂无指数数据</span>
        </div>
      </div>
    )
  }

  const latestBar = data.bars[data.bars.length - 1]

  return (
    <div className="space-y-6">
      {/* ========== 最新行情分类卡片 ========== */}
      {latestBar && <LatestConditionCard bar={latestBar} />}

      {/* ========== 蜡烛图卡片 ========== */}
      <div className="bg-terminal-card border border-terminal-border rounded-xl p-6 card-hover-glow">
        {/* 头部 */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <h3 className="text-xl font-bold">
              {data.indexName}
            </h3>
            <span className="text-sm font-mono text-terminal-muted">
              {data.indexCode}
            </span>
          </div>
          <ConditionLegend counts={data.conditionCounts} />
        </div>

        {/* 工具栏 */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2 text-xs text-terminal-muted">
            <span>
              共 {data.totalBars} 个 Bar，{data.barsWithCondition} 个有行情分类
            </span>
          </div>
          <div className="flex items-center gap-1">
            <button
              onClick={goBack}
              disabled={!canGoBack}
              className="p-1.5 rounded hover:bg-terminal-bg disabled:opacity-30 transition-colors"
              title="向前翻页"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button
              onClick={goToLatest}
              className="px-2.5 py-1 text-xs rounded bg-primary/20 text-primary hover:bg-primary/30 transition-colors"
            >
              最新
            </button>
            <button
              onClick={goForward}
              disabled={!canGoForward}
              className="p-1.5 rounded hover:bg-terminal-bg disabled:opacity-30 transition-colors"
              title="向后翻页"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
            <span className="text-xs text-terminal-muted ml-2">
              {visibleStart + 1}–{Math.min(visibleStart + visibleBars, chartData.length)} / {chartData.length}
            </span>
          </div>
        </div>

        {/* 图表 */}
        <div className="h-[420px]">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={visibleData}
              margin={{ top: 10, right: 10, left: 0, bottom: 0 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.5} />
              <XAxis
                dataKey="time"
                stroke="#9CA3AF"
                fontSize={11}
                tickLine={false}
                axisLine={false}
                tickFormatter={formatDateLabel}
                interval="preserveStartEnd"
              />
              <YAxis
                stroke="#9CA3AF"
                fontSize={11}
                tickLine={false}
                axisLine={false}
                domain={yDomain}
                tickFormatter={(v: number) => v.toFixed(0)}
                width={55}
              />
              <Tooltip
                content={<CustomTooltip />}
                cursor={{ fill: 'rgba(255,255,255,0.03)' }}
              />
              {/* 隐藏的基底 Bar（stack 的底部，定位到 low） */}
              <Bar
                dataKey="low"
                stackId="candle"
                fill="transparent"
                isAnimationActive={false}
              />
              {/* 蜡烛图 Bar（stack 在 low 之上，范围 = high - low） */}
              <Bar
                dataKey="range"
                stackId="candle"
                shape={<CandlestickShape />}
                isAnimationActive={false}
              >
                {visibleData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill="transparent" />
                ))}
              </Bar>
              {/* 最新 bar 的分隔线 */}
              {visibleData.length > 0 && visibleData[visibleData.length - 1].time === latestBar?.time && (
                <ReferenceLine
                  x={visibleData[visibleData.length - 1].time}
                  stroke="#6B7280"
                  strokeDasharray="4 4"
                  strokeWidth={1}
                />
              )}
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* 底部提示 */}
        <div className="mt-4 pt-3 border-t border-terminal-border text-xs text-terminal-muted flex items-center gap-4">
          <span>实体颜色 = AI 行情分类</span>
          <span className="flex items-center gap-1">
            <span className="w-3 h-2 rounded-sm" style={{ backgroundColor: '#10B981', opacity: 0.85 }} />
            上涨
          </span>
          <span className="flex items-center gap-1">
            <span className="w-3 h-2 rounded-sm" style={{ backgroundColor: '#EF4444', opacity: 0.85 }} />
            下跌
          </span>
          <span className="flex items-center gap-1">
            <span className="w-3 h-2 rounded-sm" style={{ backgroundColor: '#F59E0B', opacity: 0.85 }} />
            震荡
          </span>
          <span className="ml-auto">悬停查看详细数据和分类概率</span>
        </div>
      </div>
    </div>
  )
}
