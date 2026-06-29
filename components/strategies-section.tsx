'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { useT, useStrategyName, useStrategyDesc } from '@/lib/i18n'
import { ArrowRight, TrendingUp, Activity, Loader2 } from 'lucide-react'
import { SectionHeading } from '@/components/section-heading'
import { GlassCard } from '@/components/glass-card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { fetchStrategyStocks, type StockSummary } from '@/lib/data-service'
import type { Strategy } from '@/types/strategy'

interface ComputedMetrics {
  totalAssets: number
  profitableAssets: number
  avgPnl: number
  winRate: number
}

function computeMetrics(stocks: StockSummary[]): ComputedMetrics {
  const withPnl = stocks.filter(s => s.pnlPct !== null)
  const totalAssets = stocks.length
  const profitableAssets = stocks.filter(s => (s.pnlPct ?? 0) > 0).length
  const avgPnl = withPnl.length > 0
    ? withPnl.reduce((sum, s) => sum + (s.pnlPct ?? 0), 0) / withPnl.length
    : 0
  const winRate = withPnl.length > 0
    ? (profitableAssets / withPnl.length) * 100
    : 0
  return { totalAssets, profitableAssets, avgPnl, winRate }
}

export function StrategiesSection({ strategies }: { strategies: Strategy[] }) {
  const t = useT('strategies')
  const sn = useStrategyName()
  const sd = useStrategyDesc()

  const featured = strategies
    .filter(s => s.status === 'running')
    .slice(0, 2)

  // Fetch stock-level data for each featured strategy
  const [stocksMap, setStocksMap] = useState<Record<string, StockSummary[]>>({})
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    async function load() {
      setLoading(true)
      const map: Record<string, StockSummary[]> = {}
      await Promise.all(
        featured.map(async (s) => {
          const result = await fetchStrategyStocks(s.id)
          if (!cancelled) {
            map[s.id] = result.data ?? []
          }
        })
      )
      if (!cancelled) {
        setStocksMap(map)
        setLoading(false)
      }
    }
    if (featured.length >= 2) {
      load()
    }
    return () => { cancelled = true }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [JSON.stringify(strategies.map(s => s.id))])

  if (featured.length < 2) return null

  // Helper to determine if a strategy is tea_radical_nature (MACD-based)
  const isTea = (id: string) => id.includes('tea') || id.includes('radical')

  const metricLabels = [t('returnRate'), t('sharpe'), t('maxDrawdown'), t('winRate')]

  return (
    <section className="py-24 relative">
      <div className="container mx-auto px-4">
        <SectionHeading
          label={t('label')}
          title={t('title')}
          subtitle={t('subtitle')}
        />

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mt-12">
          {featured.map((strategy) => {
            const tea = isTea(strategy.id)
            const stocks = stocksMap[strategy.id]
            const metrics = stocks ? computeMetrics(stocks) : null
            const isLoading = loading && !stocks

            return (
            <Link key={strategy.id} href={`/strategies/${strategy.id}`}>
              <GlassCard className="group h-full p-8 transform transition-all duration-500 hover:rotate-y-2 hover:scale-[1.02]">
                {/* Header */}
                <div className="flex items-start justify-between mb-6">
                  <div className="flex items-center gap-3">
                    <div className={`w-12 h-12 rounded-2xl flex items-center justify-center ${
                      tea
                        ? 'bg-gradient-to-br from-quant-cyan/20 to-blue-500/10 border border-quant-cyan/20'
                        : 'bg-gradient-to-br from-purple-500/20 to-quant-cyan/10 border border-purple-400/20'
                    }`}>
                      {tea ? (
                        <TrendingUp className="w-6 h-6 text-quant-cyan" />
                      ) : (
                        <Activity className="w-6 h-6 text-purple-400" />
                      )}
                    </div>
                    <div>
                      <h3 className="font-display font-bold text-lg text-foreground">{sn(strategy.id, strategy.name)}</h3>
                      <p className="text-xs text-terminal-muted font-mono">
                        {tea ? t('macdSubtitle') : t('fuzzySubtitle')}
                      </p>
                    </div>
                  </div>
                  <Badge variant="success">● {t('running')}</Badge>
                </div>

                {/* Key Metrics */}
                {isLoading ? (
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                    {metricLabels.map(label => (
                      <div key={label}>
                        <p className="text-[10px] text-terminal-muted uppercase tracking-wider mb-1">{label}</p>
                        <div className="flex items-center gap-1.5 h-5">
                          <Loader2 className="w-3 h-3 animate-spin text-terminal-muted" />
                          <span className="text-xs text-terminal-muted">...</span>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : metrics ? (
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                    {[
                      { label: t('returnRate'), value: `${metrics.avgPnl > 0 ? '+' : ''}${metrics.avgPnl.toFixed(1)}%`, color: metrics.avgPnl >= 0 ? 'text-quant-green' : 'text-quant-red' },
                      { label: t('sharpe'), value: strategy.sharpe.toFixed(2), color: strategy.sharpe >= 2 ? 'text-quant-green' : 'text-quant-amber' },
                      { label: t('maxDrawdown'), value: `${strategy.maxDrawdown.toFixed(1)}%`, color: 'text-quant-red' },
                      { label: t('winRate'), value: `${metrics.winRate.toFixed(1)}%`, color: 'text-quant-cyan' },
                    ].map((metric) => (
                      <div key={metric.label}>
                        <p className="text-[10px] text-terminal-muted uppercase tracking-wider mb-1">{metric.label}</p>
                        <p className={`font-mono font-semibold text-sm ${metric.color}`}>{metric.value}</p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                    {metricLabels.map(label => (
                      <div key={label}>
                        <p className="text-[10px] text-terminal-muted uppercase tracking-wider mb-1">{label}</p>
                        <p className="text-xs text-quant-red font-mono">{t('loadFailed')}</p>
                      </div>
                    ))}
                  </div>
                )}

                {/* Flow diagram placeholder */}
                <div className="mb-6 p-4 rounded-xl bg-muted/30 border border-border">
                  <div className="flex items-center justify-between gap-2">
                    {tea ? (
                      <>
                        <FlowStep label={t('flowPrice')} />
                        <FlowArrow />
                        <FlowStep label={t('flowMACD')} />
                        <FlowArrow />
                        <FlowStep label={t('flowDivergence')} color="cyan" />
                        <FlowArrow />
                        <FlowStep label={t('flowBarrier')} />
                        <FlowArrow />
                        <FlowStep label={t('flowDeepTS')} color="green" highlight />
                      </>
                    ) : (
                      <>
                        <FlowStep label={t('flowFuzzify')} />
                        <FlowArrow />
                        <FlowStep label={t('flowMembership')} color="cyan" />
                        <FlowArrow />
                        <FlowStep label={t('flowBayesian')} />
                        <FlowArrow />
                        <FlowStep label={t('flowOptimization')} />
                        <FlowArrow />
                        <FlowStep label={t('flowDeepTS')} color="green" highlight />
                      </>
                    )}
                  </div>
                </div>

                {/* CTA */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-sm text-terminal-muted">
                    {metrics ? (
                      <>
                        <span>{t('assetsCount', { count: metrics.totalAssets })}</span>
                        <span>·</span>
                        <span className="profit-text">{t('profitable', { count: metrics.profitableAssets })}</span>
                      </>
                    ) : (
                      <span className="text-terminal-muted">{t('loading')}</span>
                    )}
                  </div>
                  <div className="flex items-center gap-1 text-quant-cyan text-sm font-medium group-hover:gap-2 transition-all">
                    {t('viewDetails')}
                    <ArrowRight className="w-4 h-4" />
                  </div>
                </div>
              </GlassCard>
            </Link>
          )})}
        </div>

        {/* View all link */}
        <div className="text-center mt-10">
          <Link href="/strategies">
            <Button variant="ghost" className="text-terminal-muted hover:text-quant-cyan">
              {t('viewAllStrategies')}
            </Button>
          </Link>
        </div>
      </div>
    </section>
  )
}

function FlowStep({ label, color, highlight }: { label: string; color?: string; highlight?: boolean }) {
  const textColor =
    color === 'cyan' ? 'text-quant-cyan' :
    color === 'green' ? 'text-quant-green' :
    'text-terminal-muted'
  return (
    <span className={`text-[10px] md:text-xs font-mono whitespace-nowrap px-2 py-1 rounded-md ${
      highlight ? 'bg-quant-green/10 border border-quant-green/20 text-quant-green' :
      'bg-muted/30 border border-border'
    } ${textColor}`}>
      {label}
    </span>
  )
}

function FlowArrow() {
  return (
    <span className="text-terminal-muted text-[10px]">→</span>
  )
}
