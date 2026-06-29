'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { ArrowLeft, Search, SlidersHorizontal, AlertTriangle } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { GlassCard } from '@/components/glass-card'
import { SectionHeading } from '@/components/section-heading'
import { fetchStrategies } from '@/lib/data-service'
import { useT, useStrategyName, useStrategyDesc } from '@/lib/i18n'
import type { Strategy, StrategyStatus } from '@/types/strategy'

const STATUS_MAP: Record<StrategyStatus, { label: string; variant: 'success' | 'warning' | 'destructive' | 'default' }> = {
  running: { label: 'Running', variant: 'success' },
  paused: { label: 'Paused', variant: 'warning' },
  stopped: { label: 'Stopped', variant: 'destructive' },
  backtesting: { label: 'Backtesting', variant: 'default' },
}

export default function StrategiesPage() {
  const [strategies, setStrategies] = useState<Strategy[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState<StrategyStatus | 'all'>('all')
  const t = useT('strategies')
  const sn = useStrategyName()
  const sd = useStrategyDesc()

  useEffect(() => {
    fetchStrategies().then((result) => {
      if (result.error) { setError(result.error); setLoading(false); return }
      setStrategies(result.data!)
      setLoading(false)
    })
  }, [])

  const filtered = strategies.filter((s) => {
    if (statusFilter !== 'all' && s.status !== statusFilter) return false
    if (search && !s.name.includes(search) && !s.description.includes(search)) return false
    return true
  })

  return (
    <div className="container mx-auto px-4 py-12">
      <Link href="/" className="inline-flex items-center gap-2 text-terminal-muted hover:text-quant-cyan transition-colors text-sm mb-4">
        <ArrowLeft className="w-4 h-4" /> {t('backToResearch')}
      </Link>
      <SectionHeading label={t('label')} title={t('pageTitle')} align="left"
        subtitle={t('pageSubtitle')} />

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div className="w-8 h-8 border-2 border-quant-cyan border-t-transparent rounded-full animate-spin" />
        </div>
      ) : error ? (
        <div className="glass-card-variant p-8 text-center border-quant-red/30">
          <AlertTriangle className="w-8 h-8 text-quant-red mx-auto mb-3" />
          <p className="text-quant-red font-mono text-sm font-semibold mb-2">{t('loadError')}</p>
          <p className="text-terminal-muted text-xs font-mono max-w-lg mx-auto">{error}</p>
        </div>
      ) : (
        <>
          <div className="flex flex-col sm:flex-row gap-4 mb-8">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-terminal-muted" />
              <input type="text" placeholder={t('searchPlaceholder')} value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-muted/30 border border-border text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-quant-cyan/40 transition-all" />
            </div>
            <div className="flex items-center gap-1">
              <SlidersHorizontal className="w-4 h-4 text-terminal-muted mr-2" />
              {(['all', 'running', 'paused', 'stopped', 'backtesting'] as const).map((f) => (
                <button key={f} onClick={() => setStatusFilter(f)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-mono transition-all ${statusFilter === f ? 'bg-quant-cyan/10 text-quant-cyan border border-quant-cyan/30' : 'text-terminal-muted hover:text-foreground border border-transparent'}`}>
                  {f === 'all' ? t('filterAll') : STATUS_MAP[f].label}
                </button>
              ))}
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filtered.map((s) => (
              <Link key={s.id} href={`/strategies/${s.id}`}>
                <GlassCard className="group h-full">
                  <div className="flex items-start justify-between mb-4">
                    <div><h3 className="font-display font-semibold group-hover:text-quant-cyan transition-colors">{sn(s.id, s.name)}</h3>
                      <p className="text-xs text-terminal-muted mt-1 line-clamp-2">{sd(s.id, s.description)}</p></div>
                    <Badge variant={STATUS_MAP[s.status].variant}>● {STATUS_MAP[s.status].label}</Badge>
                  </div>
                  <div className="flex flex-wrap gap-1 mb-4">
                    {s.markets.map((m) => <span key={m} className="px-2 py-0.5 rounded-md bg-muted/30 border border-border text-[10px] font-mono text-terminal-muted">{m}</span>)}
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    {[{ label: t('returnRate'), value: `${s.pnl > 0 ? '+' : ''}${s.pnl.toFixed(1)}%`, color: s.pnl >= 0 ? 'text-quant-green' : 'text-quant-red' },
                      { label: 'Sharpe', value: s.sharpe.toFixed(2), color: s.sharpe >= 2 ? 'text-quant-green' : 'text-quant-amber' },
                      { label: t('maxDrawdown'), value: `${s.maxDrawdown.toFixed(1)}%`, color: 'text-quant-red' },
                      { label: t('winRate'), value: `${s.winRate.toFixed(1)}%`, color: 'text-quant-cyan' }].map((m) => (
                      <div key={m.label}><p className="text-[10px] text-terminal-muted uppercase tracking-wider mb-0.5">{m.label}</p><p className={`font-mono font-semibold text-sm ${m.color}`}>{m.value}</p></div>
                    ))}
                  </div>
                  <div className="mt-4 pt-4 border-t border-border flex items-center justify-between text-xs text-terminal-muted">
                    <span>{t('totalTrades', { count: s.totalTrades })}</span><span>{t('profitFactor')} {s.profitFactor.toFixed(1)}</span>
                  </div>
                </GlassCard>
              </Link>
            ))}
          </div>
          {filtered.length === 0 && <p className="text-center py-20 text-terminal-muted">{t('noResults')}</p>}
        </>
      )}
    </div>
  )
}
