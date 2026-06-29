'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { TrendingUp, TrendingDown, Activity, AlertTriangle, BarChart3 } from 'lucide-react'
import { GlassCard } from '@/components/glass-card'
import { fetchMarketOverview } from '@/lib/data-service'
import { useT } from '@/lib/i18n'
import type { IndexOverviewItem } from '@/lib/data-service'

export default function MarketOverviewPage() {
  const [indices, setIndices] = useState<IndexOverviewItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const t = useT('market')

  useEffect(() => {
    async function load() {
      setLoading(true)
      const res = await fetchMarketOverview()
      if (res.error) { setError(res.error); setLoading(false); return }
      setIndices(res.data!)
      setLoading(false)
    }
    load()
  }, [])

  const CONDITION_META: Record<string, { label: string; color: string; bg: string; border: string; icon: typeof TrendingUp }> = {
    trend_up:   { label: t('trendUp'), color: 'text-quant-green', bg: 'bg-quant-green/5',  border: 'border-quant-green/20',  icon: TrendingUp },
    trend_down: { label: t('trendDown'), color: 'text-quant-red',   bg: 'bg-quant-red/5',    border: 'border-quant-red/20',    icon: TrendingDown },
    range:      { label: t('range'), color: 'text-quant-amber', bg: 'bg-quant-amber/5',  border: 'border-quant-amber/20',  icon: Activity },
  }

  // ── Loading ──
  if (loading) {
    return (
      <div className="container mx-auto px-4 py-20 flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-quant-cyan border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-terminal-muted font-mono text-sm">{t('loading')}</p>
        </div>
      </div>
    )
  }

  // ── Error ──
  if (error) {
    return (
      <div className="container mx-auto px-4 py-20">
        <div className="glass-card-variant p-8 text-center border-quant-red/30 max-w-lg mx-auto">
          <AlertTriangle className="w-8 h-8 text-quant-red mx-auto mb-3" />
          <p className="text-quant-red font-mono text-sm font-semibold mb-2">{t('dataLoadFailed')}</p>
          <p className="text-terminal-muted text-xs font-mono break-all">{error}</p>
        </div>
      </div>
    )
  }

  // ── Empty ──
  if (indices.length === 0) {
    return (
      <div className="container mx-auto px-4 py-20">
        <div className="glass-card-variant p-8 text-center border-quant-amber/20 max-w-lg mx-auto">
          <BarChart3 className="w-8 h-8 text-quant-amber mx-auto mb-3" />
          <p className="text-terminal-muted font-mono text-sm">{t('noData')}</p>
          <p className="text-terminal-muted text-xs font-mono mt-1">{t('noDataHint')}</p>
        </div>
      </div>
    )
  }

  // ── Overview ──
  return (
    <div className="container mx-auto px-4 py-12">
      {/* Header */}
      <div className="mb-10">
        <h1 className="font-display text-3xl font-bold mb-2">{t('pageTitle')}</h1>
        <p className="text-terminal-muted text-sm">
          {t('pageSubtitle')}
        </p>
      </div>

      {/* Index cards grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {indices.map((idx) => {
          const meta = idx.marketCondition ? CONDITION_META[idx.marketCondition] : null
          const ConditionIcon = meta?.icon

          return (
            <Link key={idx.code} href={`/market/${idx.code}`} className="group block">
              <GlassCard variant="subtle" className="p-5 h-full hover:border-quant-cyan/20 transition-all duration-300">
                {/* Header: name + code + date */}
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h3 className="font-display font-semibold text-base group-hover:text-quant-cyan transition-colors">
                      {idx.name}
                    </h3>
                    <p className="text-[11px] font-mono text-terminal-muted mt-0.5">{idx.code}</p>
                  </div>
                  <span className="text-[10px] font-mono text-terminal-muted/50 shrink-0">{idx.latestDate}</span>
                </div>

                {/* Price + change */}
                <div className="flex items-baseline gap-3 mb-4">
                  <span className="font-mono text-2xl font-bold text-foreground">
                    {idx.latestClose.toFixed(2)}
                  </span>
                  <span className={`font-mono text-sm font-semibold ${idx.change >= 0 ? 'text-quant-green' : 'text-quant-red'}`}>
                    {idx.change >= 0 ? '+' : ''}{idx.change.toFixed(2)}
                    <span className="ml-0.5">
                      ({idx.changePct >= 0 ? '+' : ''}{idx.changePct.toFixed(2)}%)
                    </span>
                  </span>
                </div>

                {/* Classification result */}
                {meta ? (
                  <div className={`rounded-xl p-4 ${meta.bg} border ${meta.border}`}>
                    <div className="flex items-center gap-3 mb-2">
                      {ConditionIcon && <ConditionIcon className={`w-5 h-5 ${meta.color}`} />}
                      <p className={`font-mono text-sm font-bold ${meta.color}`}>{meta.label}</p>
                    </div>
                    {idx.probability != null && (
                      <div className="flex items-center gap-2">
                        <div className="flex-1 h-1.5 bg-muted/40 rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full transition-all duration-700 ${
                              idx.marketCondition === 'trend_up'
                                ? 'bg-quant-green'
                                : idx.marketCondition === 'trend_down'
                                  ? 'bg-quant-red'
                                  : 'bg-quant-amber'
                            }`}
                            style={{ width: `${Math.min((idx.probability > 1 ? idx.probability : idx.probability * 100), 100)}%` }}
                          />
                        </div>
                        <span className={`text-[10px] font-mono font-semibold ${meta.color}`}>
                          {(idx.probability > 1 ? idx.probability : idx.probability * 100).toFixed(1)}%
                        </span>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="rounded-xl p-4 bg-muted/10 border border-border flex items-center gap-3">
                    <Activity className="w-5 h-5 text-terminal-muted/30" />
                    <p className="text-xs font-mono text-terminal-muted">{t('noClassification')}</p>
                  </div>
                )}

                {/* Footer */}
                <div className="mt-4 pt-3 border-t border-border/50 flex items-center justify-between">
                  <span className="text-[10px] text-terminal-muted/50 font-mono group-hover:text-quant-cyan transition-colors">
                    {t('viewDetails')}
                  </span>
                  {idx.avmoodTrend ? (
                    (() => {
                      const trendColor = idx.avmoodTrend.startsWith('↑') ? 'text-quant-green' :
                                         idx.avmoodTrend.startsWith('↓') ? 'text-quant-red' : 'text-quant-amber'
                      return (
                        <span className={`text-[10px] font-mono font-semibold ${trendColor}`}>
                          {t('fuzzyLabel')}{idx.avmoodTrend}
                        </span>
                      )
                    })()
                  ) : meta ? (
                    <span className={`text-[10px] font-mono font-semibold ${meta.color}`}>
                      {t('fuzzyVerdict')}{meta.label}
                    </span>
                  ) : null}
                </div>
              </GlassCard>
            </Link>
          )
        })}
      </div>
    </div>
  )
}
