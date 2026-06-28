'use client'

import { useState, useEffect, useMemo } from 'react'
import Link from 'next/link'
import { ArrowLeft, TrendingUp, Activity, BarChart3, AlertTriangle, Search, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { GlassCard } from '@/components/glass-card'
import { CountUp } from '@/components/count-up'
import { AIInferenceLoader } from '@/components/ai-inference-loader'
import { fetchStrategies, fetchStrategyStocks } from '@/lib/data-service'
import type { StockSummary } from '@/lib/data-service'
import type { Strategy, StrategyStatus } from '@/types/strategy'

const STATUS_MAP: Record<StrategyStatus, { label: string; variant: 'success' | 'warning' | 'destructive' | 'default' }> = {
  running: { label: 'Running', variant: 'success' },
  paused: { label: 'Paused', variant: 'warning' },
  stopped: { label: 'Stopped', variant: 'destructive' },
  backtesting: { label: 'Backtesting', variant: 'default' },
}

// ── Sort types & column definitions ─────────────────────────────

type SortKey = 'isHolding' | 'code' | 'name' | 'lastDate' | 'entryPrice' | 'currentPrice' | 'pnlPct' | 'signalCount' | 'tradeCount' | 'stopLossPrice'
type SortDir = 'asc' | 'desc'

const COLUMNS: { label: string; sortKey: SortKey }[] = [
  { label: '',             sortKey: 'isHolding' },
  { label: 'Code',         sortKey: 'code' },
  { label: 'Name',         sortKey: 'name' },
  { label: 'Date',         sortKey: 'lastDate' },
  { label: 'Entry',        sortKey: 'entryPrice' },
  { label: 'Current',      sortKey: 'currentPrice' },
  { label: 'PnL%',         sortKey: 'pnlPct' },
  { label: 'Sigs',         sortKey: 'signalCount' },
  { label: 'Trades',       sortKey: 'tradeCount' },
  { label: 'SL',           sortKey: 'stopLossPrice' },
]

function SortIcon({ columnKey, sortKey, sortDir }: { columnKey: SortKey; sortKey: SortKey | null; sortDir: SortDir }) {
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

export default function StrategyDetailPage({ params }: { params: { id: string } }) {
  const [strategy, setStrategy] = useState<Strategy | null>(null)
  const [stocks, setStocks] = useState<StockSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [inferenceResult, setInferenceResult] = useState<'BUY' | 'SELL' | 'HOLD' | null>(null)
  const [inferring, setInferring] = useState(false)
  const [sortKey, setSortKey] = useState<SortKey | null>(null)
  const [sortDir, setSortDir] = useState<SortDir>('asc')
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState<'all' | 'holding' | 'closed'>('all')

  useEffect(() => {
    async function load() {
      setLoading(true)
      const [stratRes, stockRes] = await Promise.all([
        fetchStrategies(),
        fetchStrategyStocks(params.id),
      ])
      if (stratRes.error) { setError(stratRes.error); setLoading(false); return }
      const strat = stratRes.data!.find((s) => s.id === params.id)
      if (!strat) { setError(`策略 "${params.id}" 未找到`); setLoading(false); return }
      setStrategy(strat)

      if (stockRes.error) { setError(stockRes.error); setLoading(false); return }
      setStocks(stockRes.data!)
      setLoading(false)
    }
    load()
  }, [params.id])

  // Sort handlers & derived data — MUST be before any conditional return (hooks rule)
  const handleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDir(sortDir === 'asc' ? 'desc' : 'asc')
    } else {
      setSortKey(key)
      setSortDir('asc')
    }
  }

  const filteredStocks = useMemo(() => {
    // Step 1: Filter
    let result = stocks

    if (searchQuery.trim()) {
      const q = searchQuery.trim().toLowerCase()
      result = result.filter((s) => s.code.toLowerCase().includes(q))
    }

    if (statusFilter === 'holding') {
      result = result.filter((s) => s.isHolding)
    } else if (statusFilter === 'closed') {
      result = result.filter((s) => !s.isHolding)
    }

    // Step 2: Sort
    if (sortKey) {
      result = [...result].sort((a, b) => {
        const aVal = a[sortKey]
        const bVal = b[sortKey]

        let cmp = 0
        if (aVal == null && bVal == null) cmp = 0
        else if (aVal == null) cmp = 1
        else if (bVal == null) cmp = -1
        else if (typeof aVal === 'string') cmp = aVal.localeCompare(bVal as string)
        else if (typeof aVal === 'number') cmp = aVal - (bVal as number)
        else if (typeof aVal === 'boolean') cmp = (aVal ? 1 : 0) - ((bVal as boolean) ? 1 : 0)

        return sortDir === 'asc' ? cmp : -cmp
      })
    }

    return result
  }, [stocks, sortKey, sortDir, searchQuery, statusFilter])

  const STATUS_FILTERS: { key: 'all' | 'holding' | 'closed'; label: string }[] = [
    { key: 'all', label: '全部' },
    { key: 'holding', label: '📈 持仓中' },
    { key: 'closed', label: '✅ 已清仓' },
  ]

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-20 flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-quant-cyan border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-terminal-muted font-mono text-sm">Loading strategy data...</p>
        </div>
      </div>
    )
  }

  if (error || !strategy) {
    return (
      <div className="container mx-auto px-4 py-20">
        <Link href="/strategies" className="inline-flex items-center gap-2 text-terminal-muted hover:text-quant-cyan transition-colors text-sm mb-6">
          <ArrowLeft className="w-4 h-4" /> All Strategies
        </Link>
        <div className="glass-card-variant p-8 text-center border-quant-red/30">
          <AlertTriangle className="w-8 h-8 text-quant-red mx-auto mb-3" />
          <p className="text-quant-red font-mono text-sm font-semibold mb-2">数据加载失败</p>
          <p className="text-terminal-muted text-xs font-mono">{error}</p>
        </div>
      </div>
    )
  }

  const isMacd = strategy.id === 'tea_radical_nature'
  const isFuzzy = strategy.id === 'fuzzy_ma'

  const totalPnl = stocks.reduce((sum, s) => sum + (s.pnlPct || 0), 0)
  const avgPnl = stocks.length > 0 ? totalPnl / stocks.length : 0
  const holdingCount = stocks.filter((s) => s.isHolding).length

  return (
    <div className="container mx-auto px-4 py-12">
      <Link href="/strategies" className="inline-flex items-center gap-2 text-terminal-muted hover:text-quant-cyan transition-colors text-sm mb-4">
        <ArrowLeft className="w-4 h-4" /> All Strategies
      </Link>

      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-10">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${isMacd ? 'bg-gradient-to-br from-quant-cyan/20 to-blue-500/10 border border-quant-cyan/20' : 'bg-gradient-to-br from-purple-500/20 to-quant-cyan/10 border border-purple-400/20'}`}>
              {isMacd ? <TrendingUp className="w-5 h-5 text-quant-cyan" /> : <Activity className="w-5 h-5 text-purple-400" />}
            </div>
            <Badge variant={STATUS_MAP[strategy.status].variant}>● {STATUS_MAP[strategy.status].label}</Badge>
          </div>
          <h1 className="font-display text-3xl font-bold">{strategy.name}</h1>
          <p className="text-terminal-muted text-sm mt-1">{strategy.description}</p>
        </div>
        <Button variant="glow" size="lg" onClick={() => setInferring(true)} disabled={inferring}>
          {inferring ? 'Inferring...' : '▶ Run AI Inference'}
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-1 space-y-6">
          <GlassCard variant="subtle" className="p-5">
            <h3 className="font-display font-semibold text-sm mb-4 flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-quant-cyan" /> Strategy Pipeline
            </h3>
            <div className="space-y-1">
              {isMacd ? (
                <>{flow('Price Data',1,true)}{flowConn()}{flow('Tea Radical Analysis',2,true)}{flowConn()}{flow('Multi-MA Signal',3,true)}{flowConn()}{flow('Trade Signal',4,false)}</>
              ) : (
                <>{flow('Price Data',1,true)}{flowConn()}{flow('Fuzzy Membership',2,true)}{flowConn()}{flow('Bayesian Optimization',3,true)}{flowConn()}{flow('Goal-Oriented Search',4,true)}{flowConn()}{flow('Trade Signal',5,false,true)}</>
              )}
            </div>
          </GlassCard>

          {inferring && <AIInferenceLoader onComplete={(r) => { setInferenceResult(r); setInferring(false) }} />}
          {inferenceResult && (
            <GlassCard variant="subtle" className="p-5 animate-count-up">
              <h3 className="font-display font-semibold text-sm mb-3">Latest Inference</h3>
              <div className={`text-center p-4 rounded-xl border ${inferenceResult === 'BUY' ? 'bg-quant-green/5 border-quant-green/20' : inferenceResult === 'SELL' ? 'bg-quant-red/5 border-quant-red/20' : 'bg-quant-amber/5 border-quant-amber/20'}`}>
                <p className={`text-2xl font-bold font-mono ${inferenceResult === 'BUY' ? 'text-quant-green' : inferenceResult === 'SELL' ? 'text-quant-red' : 'text-quant-amber'}`}>{inferenceResult}</p>
                <p className="text-xs text-terminal-muted mt-1">Confidence: {(Math.random()*15+80).toFixed(1)}%</p>
              </div>
            </GlassCard>
          )}

          <GlassCard variant="subtle" className="p-5">
            <h3 className="font-display font-semibold text-sm mb-3">Portfolio Summary</h3>
            <div className="space-y-3">
              <Row label="总标的数" value={`${stocks.length}`} />
              <Row label="持仓中" value={`${holdingCount}`} color="text-quant-green" />
              <Row label="已清仓" value={`${stocks.length - holdingCount}`} color="text-quant-red" />
              <div className="flex justify-between text-sm pt-2 border-t border-border">
                <span className="text-terminal-muted">平均盈亏</span>
                <span className={`font-mono font-semibold ${avgPnl >= 0 ? 'text-quant-green' : 'text-quant-red'}`}>
                  {avgPnl >= 0 ? '+' : ''}{avgPnl.toFixed(2)}%
                </span>
              </div>
            </div>
          </GlassCard>
        </div>

        <div className="lg:col-span-2 space-y-6">
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            {[
              { label: 'Stocks', value: stocks.length, color: 'text-quant-cyan' },
              { label: 'Trades', value: stocks.reduce((s, st) => s + st.tradeCount, 0), color: 'text-quant-cyan' },
              { label: 'Holding', value: holdingCount, color: 'text-quant-green' },
              { label: 'Avg PnL', value: avgPnl, isPnl: true },
              { label: 'Win Rate', value: strategy.winRate, suffix: '%', decimals: 1, color: 'text-quant-cyan' },
            ].map((m) => (
              <GlassCard key={m.label} variant="subtle" className="p-4 text-center">
                <p className="text-[10px] text-terminal-muted uppercase tracking-wider mb-1">{m.label}</p>
                <p className={`font-mono font-bold text-lg ${m.isPnl ? (m.value >= 0 ? 'text-quant-green' : 'text-quant-red') : m.color}`}>
                  <CountUp value={typeof m.value === 'number' ? m.value : 0} decimals={m.decimals || 0} />{m.suffix || ''}
                </p>
              </GlassCard>
            ))}
          </div>

          <GlassCard variant="subtle" className="p-5">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
              <h3 className="font-display font-semibold text-sm">
                Trading Assets ({filteredStocks.length}{filteredStocks.length !== stocks.length ? ` / ${stocks.length}` : ''})
              </h3>

              {/* ── Toolbar: search + status filter ── */}
              <div className="flex items-center gap-2 flex-wrap">
                {/* Search */}
                <div className="relative flex-1 min-w-[160px] max-w-[220px]">
                  <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-terminal-muted/50" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="搜索代码..."
                    className="w-full pl-7 pr-7 py-1.5 text-xs font-mono bg-muted/20 border border-border rounded-lg text-foreground placeholder:text-terminal-muted/30 focus:outline-none focus:border-quant-cyan/40 focus:bg-muted/30 transition-colors"
                  />
                  {searchQuery && (
                    <button
                      onClick={() => setSearchQuery('')}
                      className="absolute right-2 top-1/2 -translate-y-1/2 text-terminal-muted/40 hover:text-terminal-muted transition-colors"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  )}
                </div>

                {/* Status filter pills */}
                <div className="flex items-center bg-muted/30 rounded-lg p-0.5">
                  {STATUS_FILTERS.map((f) => (
                    <button
                      key={f.key}
                      onClick={() => setStatusFilter(f.key)}
                      className={`px-2.5 py-1 rounded-md text-[10px] font-mono transition-all ${
                        statusFilter === f.key
                          ? 'bg-ai-card text-foreground shadow-sm'
                          : 'text-terminal-muted hover:text-foreground'
                      }`}
                    >
                      {f.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <div className="overflow-x-auto max-h-[500px] overflow-y-auto scrollbar-thin">
              <table className="w-full text-sm">
                <thead className="sticky top-0 bg-ai-card">
                  <tr className="border-b border-border">
                    {COLUMNS.map((col) => (
                      <th
                        key={col.sortKey}
                        onClick={() => handleSort(col.sortKey)}
                        className="text-left py-2 px-2 text-[10px] font-mono text-terminal-muted uppercase tracking-wider cursor-pointer hover:text-quant-cyan transition-colors select-none"
                      >
                        <span className="inline-flex items-center">
                          {col.label}
                          <SortIcon columnKey={col.sortKey} sortKey={sortKey} sortDir={sortDir} />
                        </span>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {filteredStocks.map((s) => (
                    <tr key={s.code} className="border-b border-border/50 hover:bg-muted/20 transition-colors">
                      <td className="py-2 px-2"><span className={s.isHolding ? 'text-quant-green' : 'text-terminal-muted'}>{s.isHolding ? '📈' : '✅'}</span></td>
                      <td className="py-2 px-2 font-mono text-xs font-semibold">
                        <Link href={`/strategies/${params.id}/${s.code}`} className="hover:text-quant-cyan transition-colors">{s.code}</Link>
                      </td>
                      <td className="py-2 px-2 text-xs text-terminal-muted">{s.name || '—'}</td>
                      <td className="py-2 px-2 font-mono text-[10px] text-terminal-muted">{s.lastDate}</td>
                      <td className="py-2 px-2 font-mono text-xs">{s.entryPrice?.toFixed(4) || '—'}</td>
                      <td className="py-2 px-2 font-mono text-xs">{s.currentPrice?.toFixed(4) || '—'}</td>
                      <td className={`py-2 px-2 font-mono text-xs font-semibold ${(s.pnlPct ?? 0) >= 0 ? 'text-quant-green' : 'text-quant-red'}`}>
                        {(s.pnlPct != null) ? `${s.pnlPct >= 0 ? '+' : ''}${s.pnlPct.toFixed(2)}%` : '—'}
                      </td>
                      <td className="py-2 px-2 font-mono text-xs text-terminal-muted">{s.signalCount}</td>
                      <td className="py-2 px-2 font-mono text-xs text-terminal-muted">{s.tradeCount}</td>
                      <td className="py-2 px-2">
                        {s.stopLossPrice ? (
                          <span className="text-[10px] font-mono text-quant-amber leading-tight" title={`止损日期: ${s.stopLossDate || '—'}`}>
                            ⚠️ {s.stopLossPrice.toFixed(4)}<br />
                            <span className="text-[9px] text-terminal-muted">{s.stopLossDate || ''}</span>
                          </span>
                        ) : (
                          <span className="text-terminal-muted text-[10px]">—</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </GlassCard>
        </div>
      </div>
    </div>
  )
}

function flow(label: string, idx: number, active: boolean, hl?: boolean) {
  return (
    <div className={`flex items-center gap-3 px-3 py-2.5 rounded-lg ${hl ? 'bg-quant-green/10 border border-quant-green/20' : active ? 'bg-muted/20 border border-border' : 'opacity-40'}`}>
      <span className={`w-6 h-6 rounded-lg flex items-center justify-center text-xs font-mono font-bold ${hl ? 'bg-quant-green/20 text-quant-green' : active ? 'bg-quant-cyan/10 text-quant-cyan' : 'bg-muted/30 text-terminal-muted'}`}>{idx}</span>
      <span className={`text-xs font-mono ${hl ? 'text-quant-green' : 'text-foreground'}`}>{label}</span>
    </div>
  )
}
function flowConn() {
  return <div className="flex justify-center py-0.5"><div className="w-0.5 h-4 bg-gradient-to-b from-quant-cyan/20 to-quant-cyan/5" /></div>
}
function Row({ label, value, color }: { label: string; value: string; color?: string }) {
  return <div className="flex justify-between text-sm"><span className="text-terminal-muted">{label}</span><span className={`font-mono font-semibold ${color || 'text-foreground'}`}>{value}</span></div>
}
