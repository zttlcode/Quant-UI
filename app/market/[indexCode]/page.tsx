'use client'

import { useState, useEffect, useMemo } from 'react'
import Link from 'next/link'
import { useT } from '@/lib/i18n'
import { ArrowLeft, TrendingUp, TrendingDown, ArrowLeftRight, AlertTriangle, BarChart3 } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { GlassCard } from '@/components/glass-card'
import { fetchMarketConditionByCode, MARKET_INDICES } from '@/lib/data-service'
import type { IndexBar, MarketConditionResponse } from '@/lib/data-service'
import {
  ComposedChart, Bar, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell, ReferenceLine, ReferenceDot,
} from 'recharts'

// ── Condition config ────────────────────────────────────────────

const COND_MAP: Record<string, { label: string; color: string; upFill: string; downFill: string; icon: typeof TrendingUp }> = {
  trend_up:   { label: 'Trend Up',   color: '#10B981', upFill: '#10B981', downFill: 'rgba(16,185,129,0.25)', icon: TrendingUp },
  trend_down: { label: 'Trend Down', color: '#EF4444', upFill: '#EF4444', downFill: 'rgba(239,68,68,0.25)',   icon: TrendingDown },
  range:      { label: 'Range',      color: '#F59E0B', upFill: '#F59E0B', downFill: 'rgba(245,158,11,0.25)', icon: ArrowLeftRight },
}
const NO_COND = { upFill: '#9CA3AF', downFill: 'rgba(156,163,175,0.2)' }

// ── Candlestick Shape (condition-colored) ────────────────────────

function CandleShape(props: any) {
  const { x, y, width, height, payload } = props
  if (!payload || !height) return <g />
  const range = payload.high - payload.low
  if (range <= 0) return <g />
  const cx = x + width / 2
  const scale = height / range
  const isUp = payload.close >= payload.open
  const cfg = COND_MAP[payload.marketCondition] || null
  const bodyColor = isUp ? (cfg?.upFill || NO_COND.upFill) : (cfg?.downFill || NO_COND.downFill)
  const bodyTop = y + (payload.high - Math.max(payload.open, payload.close)) * scale
  const bodyBottom = y + (payload.high - Math.min(payload.open, payload.close)) * scale
  const bodyH = Math.max(bodyBottom - bodyTop, 0.5)
  const bodyW = Math.max(width * 0.8, 2)
  return (
    <g>
      <line x1={cx} y1={y} x2={cx} y2={bodyTop} stroke={bodyColor} strokeWidth={1} opacity={0.7} />
      <line x1={cx} y1={bodyBottom} x2={cx} y2={y + height} stroke={bodyColor} strokeWidth={1} opacity={0.7} />
      <rect x={cx - bodyW / 2} y={bodyTop} width={bodyW} height={bodyH} fill={bodyColor} rx={0.5} />
      {!isUp && <rect x={cx - bodyW / 2} y={bodyTop} width={bodyW} height={bodyH} fill="none" stroke={bodyColor} strokeWidth={0.8} rx={0.5} />}
    </g>
  )
}

// ── Avmood zero-cross markers ────────────────────────────────────

function AvmoodCrossMarkers({ data }: { data: any[] }) {
  const crosses = useMemo(() => {
    const up: any[] = [], down: any[] = []
    for (let i = 1; i < data.length; i++) {
      const p = data[i - 1]?.avmood, c = data[i]?.avmood
      if (p == null || c == null) continue
      if (p <= 0 && c > 0) up.push(data[i])
      else if (p >= 0 && c < 0) down.push(data[i])
    }
    return { up, down }
  }, [data])
  return (
    <>
      {crosses.up.map((d: any, i: number) => (
        <ReferenceDot key={`au-${i}`} x={d.time} y={0} r={5} fill="#10B981" stroke="#059669" strokeWidth={1}
          shape={(p: any) => (<g transform={`translate(${p.cx},${p.cy})`}><polygon points="0,-7 6,4 -6,4" fill="#10B981" stroke="#059669" strokeWidth={0.8} /></g>)} />
      ))}
      {crosses.down.map((d: any, i: number) => (
        <ReferenceDot key={`ad-${i}`} x={d.time} y={0} r={5} fill="#EF4444" stroke="#DC2626" strokeWidth={1}
          shape={(p: any) => (<g transform={`translate(${p.cx},${p.cy})`}><polygon points="0,7 6,-4 -6,-4" fill="#EF4444" stroke="#DC2626" strokeWidth={0.8} /></g>)} />
      ))}
    </>
  )
}

// ── Normalize helper ─────────────────────────────────────────────

function normalizeBars(bars: IndexBar[]) {
  let minL = Infinity, maxH = -Infinity
  bars.forEach(b => { if (b.low < minL) minL = b.low; if (b.high > maxH) maxH = b.high })
  const base = minL - (maxH - minL) * 0.02
  return {
    norm: bars.map(b => ({
      ...b, range: b.high - b.low,
      _o: b.open, _h: b.high, _l: b.low, _c: b.close,
      open: b.open - base, high: b.high - base, low: b.low - base, close: b.close - base,
    })),
    base,
    domain: [0, (maxH + (maxH - minL) * 0.02) - base] as [number, number],
  }
}

// ── Page ─────────────────────────────────────────────────────────

export default function MarketDetailPage({ params }: { params: { indexCode: string } }) {
  const t = useT('marketDetail')
  const { indexCode } = params
  const indexMeta = MARKET_INDICES.find(i => i.code === indexCode)
  const indexName = indexMeta?.name || indexCode

  const [data, setData] = useState<MarketConditionResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [visibleBars, setVisibleBars] = useState(60)

  useEffect(() => {
    setLoading(true)
    fetchMarketConditionByCode(indexCode).then(r => {
      if (r.error) { setError(r.error); setLoading(false); return }
      setData(r.data!)
      setLoading(false)
    })
  }, [indexCode])

  const bars = data?.bars || []
  const latest = data?.latestBar
  const avmoodRaw = data?.avmoodData

  // Slice to visible bars
  const visible = useMemo(() => bars.slice(-visibleBars), [bars, visibleBars])
  const { norm, base, domain } = useMemo(() => normalizeBars(visible), [visible])

  // Translated condition labels
  const condLabel: Record<string, string> = useMemo(() => ({
    trend_up: t('trendUp'),
    trend_down: t('trendDown'),
    range: t('range'),
  }), [t])

  // Process avmood for chart
  const avmoodChartData = useMemo(() => {
    if (!avmoodRaw?.length) return []
    const seen = visible.map(b => b.time?.substring(0, 10))
    const m = new Map(avmoodRaw.map(a => [a.time, a.value]))
    return visible.map(b => {
      const key = b.time?.substring(0, 10)
      return { time: b.time, avmood: m.get(key) ?? null }
    })
  }, [avmoodRaw, visible])

  // ── Loading ──
  if (loading) {
    return (
      <div className="container mx-auto px-4 py-20 flex justify-center">
        <div className="w-8 h-8 border-2 border-quant-cyan border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  // ── Error ──
  if (error) {
    return (
      <div className="container mx-auto px-4 py-20">
        <Link href="/market" className="inline-flex items-center gap-2 text-terminal-muted hover:text-quant-cyan text-sm mb-6">
          <ArrowLeft className="w-4 h-4" /> {t('backTo')}
        </Link>
        <div className="glass-card-variant p-8 text-center border-quant-red/30">
          <AlertTriangle className="w-8 h-8 text-quant-red mx-auto mb-3" />
          <p className="text-quant-red font-mono text-sm">{error}</p>
        </div>
      </div>
    )
  }

  // ── Detail Page ──
  return (
    <div className="container mx-auto px-4 py-12">
      {/* Back link */}
      <Link href="/market" className="inline-flex items-center gap-2 text-terminal-muted hover:text-quant-cyan transition-colors text-sm mb-4">
        <ArrowLeft className="w-4 h-4" /> {t('backToOverview')}
      </Link>

      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="font-display text-2xl font-bold">{indexName}</h1>
          <p className="text-xs font-mono text-terminal-muted mt-0.5">{indexCode}{t('subtitle')}</p>
        </div>
        <Badge variant="default" className="gap-2 h-8">
          <span className="w-2 h-2 bg-quant-cyan rounded-full animate-pulse" />
          <span className="font-mono text-xs">{t('aiLive')}</span>
        </Badge>
      </div>

      {/* ── Latest Condition Card ── */}
      {latest && (
        <GlassCard variant="subtle" className="p-6 mb-8 relative overflow-hidden">
          {latest.marketCondition && (
            <div className="absolute left-0 top-0 bottom-0 w-1" style={{ backgroundColor: COND_MAP[latest.marketCondition]?.color || '#6B7280' }} />
          )}
          <div className="flex items-center justify-between mb-4">
            <div>
              <p className="text-xs text-terminal-muted uppercase tracking-wider mb-1">{t('latestClassification')}</p>
              <p className="text-lg font-display font-bold">{latest.time?.substring(0, 10)}</p>
            </div>
            {latest.marketCondition && COND_MAP[latest.marketCondition] ? (() => {
              const c = COND_MAP[latest.marketCondition]
              return (
                <div className="px-4 py-2.5 rounded-full text-white font-bold text-sm flex items-center gap-2" style={{ backgroundColor: c.color }}>
                  <c.icon className="w-4 h-4" />{condLabel[latest.marketCondition]}
                </div>
              )
            })() : <Badge variant="outline">{t('noData')}</Badge>}
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <p className="text-[10px] text-terminal-muted uppercase">{t('close')}</p>
              <p className="font-mono font-semibold">{latest.close.toFixed(2)}</p>
            </div>
            <div>
              <p className="text-[10px] text-terminal-muted uppercase">{t('change')}</p>
              <p className={`font-mono font-semibold ${latest.close >= latest.open ? 'text-quant-green' : 'text-quant-red'}`}>
                {((latest.close - latest.open) / latest.open * 100).toFixed(2)}%
              </p>
            </div>
            <div>
              <p className="text-[10px] text-terminal-muted uppercase">{t('volume')}</p>
              <p className="font-mono text-sm">{(latest.volume / 1e8).toFixed(2)}{t('volumeUnit')}</p>
            </div>
            <div>
              <p className="text-[10px] text-terminal-muted uppercase">{t('probability')}</p>
              {latest.probability != null ? (
                <div>
                  <p className="font-mono font-bold text-lg" style={{ color: latest.marketCondition ? COND_MAP[latest.marketCondition]?.color : '#9CA3AF' }}>
                    {((latest.probability > 1 ? latest.probability : latest.probability * 100)).toFixed(0)}%
                  </p>
                  <div className="h-1.5 bg-muted rounded-full mt-1 overflow-hidden">
                    <div className="h-full rounded-full transition-all" style={{
                      width: `${Math.min((latest.probability > 1 ? latest.probability : latest.probability * 100), 100)}%`,
                      backgroundColor: latest.marketCondition ? COND_MAP[latest.marketCondition]?.color : '#9CA3AF'
                    }} />
                  </div>
                </div>
              ) : <span className="text-terminal-muted">—</span>}
            </div>
          </div>
        </GlassCard>
      )}

      {/* ── Classification Statistics ── */}
      <div className="grid grid-cols-3 gap-4 mb-8">
        {Object.entries(COND_MAP).map(([key, cfg]) => {
          const count = data?.conditionCounts?.[key] || 0
          const total = data?.barsWithCondition || 1
          return (
            <GlassCard key={key} variant="subtle" className="p-4 text-center">
              <cfg.icon className="w-6 h-6 mx-auto mb-2" style={{ color: cfg.color }} />
              <p className="font-mono text-2xl font-bold" style={{ color: cfg.color }}>{count}</p>
              <p className="text-[10px] text-terminal-muted">({(count / total * 100).toFixed(1)}%)</p>
              <p className="text-xs font-display font-semibold mt-1">{condLabel[key]}</p>
            </GlassCard>
          )
        })}
      </div>

      {/* ── Bar count selector ── */}
      <div className="flex items-center gap-2 mb-4">
        <span className="text-[10px] font-mono text-terminal-muted">{t('bars')}</span>
        {[20, 40, 60, 90, 120, 180].map(n => (
          <button key={n} onClick={() => setVisibleBars(n)}
            className={`px-2.5 py-1 rounded-md text-[10px] font-mono border transition-all ${visibleBars === n ? 'bg-quant-cyan/10 border-quant-cyan/30 text-quant-cyan' : 'border-transparent text-terminal-muted hover:text-foreground'}`}
          >{n}</button>
        ))}
        <span className="text-[10px] font-mono text-terminal-muted ml-auto">Total: {bars.length} bars</span>
      </div>

      {/* ── Candlestick Chart ── */}
      <GlassCard variant="subtle" className="p-5 mb-8">
        <h3 className="font-display font-semibold text-sm mb-2 flex items-center gap-2">
          <BarChart3 className="w-4 h-4 text-quant-cyan" /> {indexName}{t('chartHeading')}
        </h3>
        <div className="flex gap-4 mb-2 flex-wrap">
          {Object.entries(COND_MAP).map(([k, c]) => (
            <div key={k} className="flex items-center gap-1">
              <span className="w-3 h-3 rounded-sm" style={{ backgroundColor: c.upFill }} />
              <span className="text-[10px] font-mono text-terminal-muted">{condLabel[k]}</span>
            </div>
          ))}
          <div className="flex items-center gap-1">
            <span className="w-3 h-3 rounded-sm" style={{ backgroundColor: NO_COND.upFill }} />
            <span className="text-[10px] font-mono text-terminal-muted">{t('noData')}</span>
          </div>
        </div>
        <ResponsiveContainer width="100%" height={400}>
          <ComposedChart data={norm} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.4} />
            <XAxis dataKey="time" tickFormatter={(t: string) => { try { return `${new Date(t).getMonth()+1}/${new Date(t).getDate()}` } catch { return t.substring(5,10) } }}
              tick={{ fontSize: 10, fontFamily: 'JetBrains Mono', fill: 'hsl(var(--muted-foreground))' }} axisLine={{ stroke: 'hsl(var(--border))' }} tickLine={false} interval="preserveStartEnd" />
            <YAxis domain={domain} tickFormatter={(v: number) => (v + base).toFixed(0)}
              tick={{ fontSize: 10, fontFamily: 'JetBrains Mono', fill: 'hsl(var(--muted-foreground))' }} axisLine={false} tickLine={false} width={60} />
            <Tooltip content={({ active, payload }: any) => {
              if (!active || !payload?.length) return null
              const d = payload[0]?.payload
              if (!d) return null
              const o = d._o ?? d.open + base, h = d._h ?? d.high + base, l = d._l ?? d.low + base, c = d._c ?? d.close + base
              const cond = d.marketCondition ? COND_MAP[d.marketCondition] : null
              return (
                <div className="glass-card-variant p-3 text-xs font-mono">
                  <p className="text-terminal-muted mb-1">{d.time?.substring(0, 10)}</p>
                  <p>{t('openLabel')}: {o?.toFixed(2)} {t('highLabel')}: <span className="text-quant-red">{h?.toFixed(2)}</span></p>
                  <p>{t('lowLabel')}: <span className="text-quant-green">{l?.toFixed(2)}</span> {t('closeLabel')}: <span className={c >= o ? 'text-quant-red' : 'text-quant-green'}>{c?.toFixed(2)}</span></p>
                  {cond && <p style={{ color: cond.color }}>{t('aiClassLabel')}: {condLabel[d.marketCondition]}</p>}
                  {d.probability != null && <p className="text-terminal-muted">{t('probLabel')}: {((d.probability > 1 ? d.probability : d.probability * 100)).toFixed(0)}%</p>}
                </div>
              )
            }} />
            <Bar dataKey="low" stackId="candle" fill="transparent" isAnimationActive={false} />
            <Bar dataKey="range" stackId="candle" shape={<CandleShape />} isAnimationActive={false} />
          </ComposedChart>
        </ResponsiveContainer>
        <p className="text-[10px] text-terminal-muted mt-2">{t('chartFooter', { total: bars.length, visible: visibleBars })}</p>
      </GlassCard>

      {/* ── avmood Trend Chart (only when Python API provides data) ── */}
      {avmoodRaw && avmoodRaw.length > 0 && (
        <GlassCard variant="subtle" className="p-5 mb-8">
          <h3 className="font-display font-semibold text-sm mb-2">{t('avmoodChartTitle', { name: indexName })}</h3>
          <ResponsiveContainer width="100%" height={280}>
            <ComposedChart data={avmoodChartData} margin={{ top: 4, right: 10, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.4} />
              <XAxis dataKey="time" tickFormatter={(t: string) => { try { return `${new Date(t).getMonth()+1}/${new Date(t).getDate()}` } catch { return t.substring(5,10) } }}
                tick={{ fontSize: 10, fontFamily: 'JetBrains Mono', fill: 'hsl(var(--muted-foreground))' }} axisLine={{ stroke: 'hsl(var(--border))' }} tickLine={false} interval="preserveStartEnd" />
              <YAxis domain={['auto', 'auto']} tick={{ fontSize: 10, fontFamily: 'JetBrains Mono', fill: 'hsl(var(--muted-foreground))' }} axisLine={false} tickLine={false} width={55} />
              <Tooltip content={({ active, payload }: any) => {
                if (!active || !payload?.length) return null
                const d = payload[0]?.payload; if (!d) return null
                return <div className="glass-card-variant p-2 text-[10px] font-mono"><p className="text-terminal-muted">{d.time?.substring(0, 10)}</p>{d.avmood != null && <p className="text-[#AB63FA]">{t('avmood')}: {d.avmood.toFixed(6)}</p>}</div>
              }} />
              <Line type="monotone" dataKey="avmood" stroke="#AB63FA" dot={false} strokeWidth={1.5} connectNulls />
              <ReferenceLine y={0} stroke="#F59E0B" strokeWidth={0.8} strokeDasharray="4 3" />
              <AvmoodCrossMarkers data={avmoodChartData} />
            </ComposedChart>
          </ResponsiveContainer>
          <p className="text-[10px] text-terminal-muted mt-2">{t('avmoodLegend')}</p>
        </GlassCard>
      )}

      {/* ── avmood Indicator Card ── */}
      {avmoodRaw && avmoodRaw.length > 0 && (() => {
        const vals = avmoodRaw.filter(a => a.value != null).map(a => a.value)
        const latestVal = vals[vals.length - 1]
        const prev3 = vals.length > 3 ? vals[vals.length - 4] : latestVal
        const slope = latestVal != null && prev3 != null ? latestVal - prev3 : 0
        const isBull = latestVal > 0
        const absV = Math.abs(latestVal)
        const strength = absV > 0.05 ? t('strong') : absV > 0.02 ? t('medium') : t('weak')
        const dirColor = isBull ? '#10B981' : '#EF4444'
        const trendText = slope > 0.005 ? t('strengthening') : slope < -0.005 ? t('weakening') : t('flat')
        const trendColor = slope > 0.005 ? '#10B981' : slope < -0.005 ? '#EF4444' : '#9CA3AF'
        return (
          <GlassCard variant="subtle" className="p-5">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="font-display font-semibold text-sm">{t('avmoodCardTitle')}</h3>
                <p className="text-[10px] text-terminal-muted">{t('avmoodCardSubtitle')}</p>
              </div>
              <div className="px-4 py-2 rounded-full text-white font-bold text-sm" style={{ backgroundColor: dirColor }}>
                {isBull ? t('longUp') : t('shortDown')}
              </div>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <GlassCard variant="subtle" className="p-3 text-center">
                <p className="text-[10px] text-terminal-muted uppercase mb-1">{t('avmood')}</p>
                <p className="font-mono text-xl font-bold" style={{ color: dirColor }}>{latestVal?.toFixed(6)}</p>
                <p className={`text-[10px] font-mono ${slope >= 0 ? 'text-quant-green' : 'text-quant-red'}`}>{slope >= 0 ? '+' : ''}{slope.toFixed(4)}</p>
              </GlassCard>
              <GlassCard variant="subtle" className="p-3 text-center">
                <p className="text-[10px] text-terminal-muted uppercase mb-1">{t('strength')}</p>
                <p className="font-mono text-xl font-bold" style={{ color: dirColor }}>{strength}</p>
              </GlassCard>
              <GlassCard variant="subtle" className="p-3 text-center">
                <p className="text-[10px] text-terminal-muted uppercase mb-1">{t('trend')}</p>
                <p className="font-mono text-xl font-bold" style={{ color: trendColor }}>{trendText}</p>
              </GlassCard>
              <GlassCard variant="subtle" className="p-3 text-center">
                <p className="text-[10px] text-terminal-muted uppercase mb-1">{t('rangeLabel')}</p>
                <p className="font-mono text-xs text-terminal-muted">[-0.10, +0.10]</p>
                <div className="h-3 bg-gradient-to-r from-red-500/30 via-gray-400/20 to-green-500/30 rounded-full mt-2 relative">
                  <div className="absolute top-0 w-2 h-3 rounded-full -translate-x-1/2" style={{ left: `${Math.min(Math.max((latestVal + 0.1) / 0.2 * 100, 5), 95)}%`, backgroundColor: dirColor }} />
                </div>
              </GlassCard>
            </div>
          </GlassCard>
        )
      })()}

      {/* ── Legend ── */}
      <details className="mt-8">
        <summary className="text-sm font-display font-semibold cursor-pointer text-terminal-muted hover:text-foreground">{t('legend')}</summary>
        <div className="grid grid-cols-3 gap-4 mt-4">
          {Object.entries(COND_MAP).map(([k, c]) => (
            <div key={k} className="flex gap-2">
              <div className="w-1 rounded-full" style={{ backgroundColor: c.color }} />
              <div><p className="text-xs font-semibold" style={{ color: c.color }}>■ {condLabel[k]}</p><p className="text-[10px] text-terminal-muted">{t('candleLegend')} {condLabel[k]}{t('classification')}</p></div>
            </div>
          ))}
        </div>
      </details>
    </div>
  )
}
