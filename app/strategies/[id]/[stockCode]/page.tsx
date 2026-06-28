'use client'

import { useState, useEffect, useMemo } from 'react'
import Link from 'next/link'
import { ArrowLeft, Activity, BarChart3, AlertTriangle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { GlassCard, GlassCardHeader, GlassCardContent } from '@/components/glass-card'
import { AssetChart } from '@/components/asset-chart'
import { fetchStrategies, fetchStockDetail } from '@/lib/data-service'
import type { StockDetailResponse } from '@/lib/data-service'
import type { Strategy } from '@/types/strategy'

// ── Sort types & column definitions ─────────────────────────────

type TradeSortKey = 'entryTime' | 'exitTime' | 'entryPrice' | 'exitPrice' | 'pnlPct' | 'isHolding'
type TradeSortDir = 'asc' | 'desc'

const TRADE_COLUMNS: { label: string; sortKey: TradeSortKey }[] = [
  { label: 'Entry',       sortKey: 'entryTime' },
  { label: 'Exit',        sortKey: 'exitTime' },
  { label: 'Entry Price', sortKey: 'entryPrice' },
  { label: 'Exit Price',  sortKey: 'exitPrice' },
  { label: 'PnL%',        sortKey: 'pnlPct' },
  { label: 'Status',      sortKey: 'isHolding' },
]

function TradeSortIcon({ columnKey, sortKey, sortDir }: { columnKey: TradeSortKey; sortKey: TradeSortKey | null; sortDir: TradeSortDir }) {
  if (sortKey !== columnKey) {
    return (
      <span className="inline-flex flex-col ml-1 leading-[0.35] text-[7px] text-terminal-muted/20">
        <span>▲</span>
        <span>▼</span>
      </span>
    )
  }
  return (
    <span className="inline-block ml-1 text-[8px] text-quant-cyan">
      {sortDir === 'asc' ? '▲' : '▼'}
    </span>
  )
}

export default function StockDetailPage({ params }: { params: { id: string; stockCode: string } }) {
  const [strategy, setStrategy] = useState<Strategy | null>(null)
  const [detail, setDetail] = useState<StockDetailResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [showMA5, setShowMA5] = useState(true)
  const [showMA10, setShowMA10] = useState(true)
  const [showMA20, setShowMA20] = useState(true)
  const [showMACD, setShowMACD] = useState(true)
  const [tradeSortKey, setTradeSortKey] = useState<TradeSortKey | null>(null)
  const [tradeSortDir, setTradeSortDir] = useState<TradeSortDir>('asc')

  const isFuzzy = params.id === 'fuzzy_ma' || params.id === 'fuzzy-bayesian'

  useEffect(() => {
    async function load() {
      setLoading(true)
      const [stratRes, detailRes] = await Promise.all([
        fetchStrategies(),
        fetchStockDetail(params.id, params.stockCode),
      ])
      if (stratRes.error) { setError(stratRes.error); setLoading(false); return }
      setStrategy(stratRes.data!.find((s) => s.id === params.id) || null)

      if (detailRes.error) { setError(detailRes.error); setLoading(false); return }
      setDetail(detailRes.data!)
      setLoading(false)
    }
    load()
  }, [params.id, params.stockCode])

  // avmood: use real data from API only (no mock)
  const avmoodData = useMemo(() => {
    if (!isFuzzy || !detail) return null
    return detail.avmoodData?.length ? detail.avmoodData : null
  }, [isFuzzy, detail])

  const stopLossPrice = useMemo(() => {
    if (!detail?.priceData?.length) return null
    const openPos = detail.trades.find((t) => t.isHolding)
    if (!openPos?.entryPrice) return null
    const bars = detail.priceData.slice(-14)
    let sumTR = 0
    for (let i = 1; i < bars.length; i++) {
      sumTR += Math.max(bars[i].high - bars[i].low, Math.abs(bars[i].high - bars[i-1].close), Math.abs(bars[i].low - bars[i-1].close))
    }
    const atr = bars.length > 1 ? sumTR / (bars.length - 1) : 0.01
    return openPos.entryPrice - atr * 1.0
  }, [detail])

  const handleTradeSort = (key: TradeSortKey) => {
    if (tradeSortKey === key) {
      setTradeSortDir(tradeSortDir === 'asc' ? 'desc' : 'asc')
    } else {
      setTradeSortKey(key)
      setTradeSortDir('asc')
    }
  }

  const sortedTrades = useMemo(() => {
    if (!detail || !tradeSortKey) return detail?.trades ?? []
    return [...detail.trades].sort((a, b) => {
      const aVal = a[tradeSortKey]
      const bVal = b[tradeSortKey]

      let cmp = 0
      if (aVal == null && bVal == null) cmp = 0
      else if (aVal == null) cmp = 1
      else if (bVal == null) cmp = -1
      else if (typeof aVal === 'string') cmp = aVal.localeCompare(bVal as string)
      else if (typeof aVal === 'number') cmp = aVal - (bVal as number)
      else if (typeof aVal === 'boolean') cmp = (aVal ? 1 : 0) - ((bVal as boolean) ? 1 : 0)

      return tradeSortDir === 'asc' ? cmp : -cmp
    })
  }, [detail, tradeSortKey, tradeSortDir])

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-20 flex items-center justify-center min-h-[60vh]">
        <div className="text-center"><div className="w-8 h-8 border-2 border-quant-cyan border-t-transparent rounded-full animate-spin mx-auto mb-4" /><p className="text-terminal-muted font-mono text-sm">Loading...</p></div>
      </div>
    )
  }

  if (error || !detail) {
    return (
      <div className="container mx-auto px-4 py-20">
        <Link href={`/strategies/${params.id}`} className="inline-flex items-center gap-2 text-terminal-muted hover:text-quant-cyan transition-colors text-sm mb-6">
          <ArrowLeft className="w-4 h-4" /> Back to Strategy
        </Link>
        <div className="glass-card-variant p-8 text-center border-quant-red/30">
          <AlertTriangle className="w-8 h-8 text-quant-red mx-auto mb-3" />
          <p className="text-quant-red font-mono text-sm font-semibold mb-2">数据加载失败</p>
          <p className="text-terminal-muted text-xs font-mono">{error}</p>
        </div>
      </div>
    )
  }

  const latestPrice = detail.priceData.length > 0 ? detail.priceData[detail.priceData.length - 1].close : 0
  const openPosition = detail.trades.find((t) => t.isHolding)
  const latestPnl = openPosition?.pnlPct ?? detail.trades.filter(t => !t.isHolding && t.pnlPct != null).pop()?.pnlPct ?? null

  // pnlPct from API is decimal (0.05 = 5%) — multiply by 100 for display
  const pct = (v: number | null | undefined): string => {
    if (v == null) return '—'
    return `${v >= 0 ? '+' : ''}${(v * 100).toFixed(2)}%`
  }

  return (
    <div className="container mx-auto px-4 py-12">
      <div className="flex items-center justify-between mb-4">
        <Link href={`/strategies/${params.id}`} className="inline-flex items-center gap-2 text-terminal-muted hover:text-quant-cyan transition-colors text-sm">
          <ArrowLeft className="w-4 h-4" /> Back to {strategy?.name || 'Strategy'}
        </Link>
      </div>

      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <h1 className="text-3xl font-display font-bold">{params.stockCode}</h1>
            <Badge variant={openPosition ? 'success' : 'outline'}>{openPosition ? '📈 持仓中' : '✅ 已清仓'}</Badge>
          </div>
          <p className="text-terminal-muted text-sm">{strategy?.name || params.id} · {detail.stockCode}</p>
        </div>
        {openPosition && <Button variant="glow" size="lg" className="gap-2"><Activity className="w-4 h-4" />Run AI Inference</Button>}
      </div>

      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
        {[
          { label: 'Latest Price', value: latestPrice.toFixed(4) },
          { label: openPosition ? 'Float PnL' : 'Last Trade', value: pct(latestPnl), color: (latestPnl ?? 0) >= 0 ? 'text-quant-green' : 'text-quant-red' },
          { label: 'Total PnL', value: `${detail.stats.totalPnlPct >= 0 ? '+' : ''}${detail.stats.totalPnlPct.toFixed(2)}%`, color: detail.stats.totalPnlPct >= 0 ? 'text-quant-green' : 'text-quant-red' },
          { label: 'Win Rate', value: `${detail.stats.winRate.toFixed(1)}%`, color: 'text-quant-cyan' },
          { label: 'Trades', value: `${detail.stats.totalTrades}/${detail.stats.winCount}` },
        ].map((m) => (
          <GlassCard key={m.label} variant="subtle" className="p-4 text-center">
            <p className="text-[10px] text-terminal-muted uppercase tracking-wider mb-1">{m.label}</p>
            <p className={`font-mono font-bold text-lg ${m.color || 'text-foreground'}`}>{m.value}</p>
          </GlassCard>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 mb-8">
        <div className="lg:col-span-3">
          <GlassCard variant="subtle" className="p-5">
            <GlassCardHeader>
              <BarChart3 className="w-4 h-4 text-quant-cyan" />
              <span className="text-sm font-display font-semibold">{params.stockCode} — K线图</span>
            </GlassCardHeader>
            <GlassCardContent>
              <div className="flex items-center gap-2 mb-3 flex-wrap">
                <span className="text-[10px] font-mono text-terminal-muted mr-1">Indicators:</span>
                <Tgl label="MA5" color="#636EFA" on={showMA5} toggle={() => setShowMA5(!showMA5)} />
                <Tgl label="MA10" color="#FFA15A" on={showMA10} toggle={() => setShowMA10(!showMA10)} />
                <Tgl label="MA20" color="#B6E880" on={showMA20} toggle={() => setShowMA20(!showMA20)} />
                <Tgl label="MACD" on={showMACD} toggle={() => setShowMACD(!showMACD)} />
              </div>
              <AssetChart priceData={detail.priceData} trades={detail.trades}
                isFuzzy={isFuzzy} avmoodData={avmoodData} stopLossPrice={stopLossPrice}
                showMA5={showMA5} showMA10={showMA10} showMA20={showMA20} showMACD={showMACD} />
            </GlassCardContent>
          </GlassCard>
        </div>

        <div className="lg:col-span-1 space-y-4">
          <GlassCard variant="subtle" className="p-5">
            <h3 className="font-display font-semibold text-sm mb-3">持仓状态</h3>
            {openPosition ? (
              <div className="space-y-3">
                <R label="入场价" v={openPosition.entryPrice?.toFixed(4)} />
                <R label="当前价" v={latestPrice.toFixed(4)} />
                <R label="入场时间" v={openPosition.entryTime?.substring(0, 10)} mono />
                <div className="flex justify-between text-sm pt-2 border-t border-border">
                  <span className="text-terminal-muted">浮动盈亏</span>
                  <span className={`font-mono font-bold ${(openPosition.pnlPct ?? 0) >= 0 ? 'text-quant-green' : 'text-quant-red'}`}>
                    {pct(openPosition?.pnlPct)}
                  </span>
                </div>
                {stopLossPrice && (
                  <div className="mt-2 p-2 rounded-lg bg-quant-amber/5 border border-quant-amber/20">
                    <div className="flex items-center gap-1.5 text-quant-amber text-xs"><AlertTriangle className="w-3 h-3" /><span className="font-mono">ATR 止损位</span></div>
                    <p className="font-mono text-sm font-bold text-quant-amber mt-1">{stopLossPrice.toFixed(4)}</p>
                  </div>
                )}
              </div>
            ) : (
              <div className="space-y-2">
                <R label="累计交易" v={`${detail.stats.totalTrades} 笔`} />
                <R label="盈利" v={`${detail.stats.winCount} 笔`} c="text-quant-green" />
                <R label="亏损" v={`${detail.stats.totalTrades - detail.stats.winCount} 笔`} c="text-quant-red" />
              </div>
            )}
          </GlassCard>

          <GlassCard variant="subtle" className="p-5">
            <h3 className="font-display font-semibold text-sm mb-3">信号摘要</h3>
            <R label="总信号" v={`${detail.signals.length}`} />
            <R label="买入" v={`${detail.signals.filter((s) => s.type === 'buy').length}`} c="text-quant-green" />
            <R label="卖出" v={`${detail.signals.filter((s) => s.type === 'sell').length}`} c="text-quant-red" />
            <div className="mt-3 pt-3 border-t border-border text-[10px] font-mono grid grid-cols-2 gap-1">
              <span className="text-quant-green">1=有效买入</span><span className="text-quant-amber">2=无效买入</span>
              <span className="text-quant-red">3=有效卖出</span><span className="text-terminal-muted">4=无效卖出</span>
            </div>
          </GlassCard>
        </div>
      </div>

      <GlassCard variant="subtle" className="p-5">
        <h3 className="font-display font-semibold text-sm mb-4">交易明细 ({detail.trades.length})</h3>
        <div className="overflow-x-auto max-h-[400px] overflow-y-auto scrollbar-thin">
          <table className="w-full text-sm">
            <thead className="sticky top-0 bg-ai-card">
              <tr className="border-b border-border">
                {TRADE_COLUMNS.map((col) => (
                  <th
                    key={col.sortKey}
                    onClick={() => handleTradeSort(col.sortKey)}
                    className="text-left py-2 px-3 text-[10px] font-mono text-terminal-muted uppercase tracking-wider cursor-pointer hover:text-quant-cyan transition-colors select-none"
                  >
                    <span className="inline-flex items-center">
                      {col.label}
                      <TradeSortIcon columnKey={col.sortKey} sortKey={tradeSortKey} sortDir={tradeSortDir} />
                    </span>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {sortedTrades.map((t, i) => (
                <tr key={i} className="border-b border-border/50 hover:bg-muted/20 transition-colors">
                  <td className="py-2.5 px-3 font-mono text-xs">{t.entryTime?.substring(0, 10)}</td>
                  <td className="py-2.5 px-3 font-mono text-xs">{t.isHolding ? '—' : t.exitTime?.substring(0, 10)}</td>
                  <td className="py-2.5 px-3 font-mono text-xs">{t.entryPrice?.toFixed(4)}</td>
                  <td className="py-2.5 px-3 font-mono text-xs">{t.isHolding ? latestPrice.toFixed(4) : t.exitPrice?.toFixed(4)}</td>
                  <td className={`py-2.5 px-3 font-mono text-xs font-semibold ${(t.pnlPct ?? 0) >= 0 ? 'text-quant-green' : 'text-quant-red'}`}>
                    {pct(t.pnlPct)}
                  </td>
                  <td className="py-2.5 px-3">{t.isHolding ? <span className="px-2 py-0.5 rounded-full bg-quant-green/10 text-quant-green text-[10px] font-mono">Holding</span> : <span className="px-2 py-0.5 rounded-full bg-muted/30 text-terminal-muted text-[10px] font-mono">Closed</span>}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </GlassCard>
    </div>
  )
}

function R({ label: l, v, c, mono }: { label: string; v: string; c?: string; mono?: boolean }) {
  return <div className="flex justify-between text-sm py-0.5"><span className="text-terminal-muted">{l}</span><span className={`${mono ? 'font-mono text-xs' : 'font-mono'} font-semibold ${c || 'text-foreground'}`}>{v}</span></div>
}
function Tgl({ label, color, on, toggle }: { label: string; color?: string; on: boolean; toggle: () => void }) {
  return <button onClick={toggle} className={`px-2.5 py-1 rounded-md text-[10px] font-mono border transition-all ${on ? 'bg-muted/50 border-border text-foreground' : 'bg-transparent border-transparent text-terminal-muted opacity-50'}`} style={on && color ? { borderColor: color, color } : undefined}>{label}</button>
}
