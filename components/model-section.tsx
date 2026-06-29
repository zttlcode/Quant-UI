'use client'

import { useState } from 'react'
import { useT } from '@/lib/i18n'
import { SectionHeading } from '@/components/section-heading'
import { GlassCard } from '@/components/glass-card'
import { cn } from '@/lib/utils'

const MODELS = [
  {
    id: 'cnn',
    name: 'CNN',
    fullName: 'Convolutional Neural Network',
    color: 'border-blue-400/30',
    glow: 'shadow-blue-500/10',
  },
  {
    id: 'rnn',
    name: 'RNN',
    fullName: 'Recurrent Neural Network',
    color: 'border-purple-400/30',
    glow: 'shadow-purple-500/10',
  },
  {
    id: 'transformer',
    name: 'Transformer',
    fullName: 'Self-Attention Architecture',
    color: 'border-amber-400/30',
    glow: 'shadow-amber-500/10',
  },
  {
    id: 'timesnet',
    name: 'TimesNet',
    fullName: 'TimesBlock Architecture',
    color: 'border-quant-green/40',
    glow: 'shadow-quant-green/20',
    highlight: true,
  },
  {
    id: 'autoformer',
    name: 'Autoformer',
    fullName: 'Auto-Correlation Mechanism',
    color: 'border-orange-400/30',
    glow: 'shadow-orange-500/10',
  },
  {
    id: 'nonstationary',
    name: 'Nonstationary Transformer',
    fullName: 'Series Stationarization',
    color: 'border-pink-400/30',
    glow: 'shadow-pink-500/10',
  },
  {
    id: 'dlinear',
    name: 'DLinear',
    fullName: 'Simple Linear Layers',
    color: 'border-cyan-400/30',
    glow: 'shadow-cyan-500/10',
  },
  {
    id: 'informer',
    name: 'Informer',
    fullName: 'ProbSparse Self-Attention',
    color: 'border-yellow-400/30',
    glow: 'shadow-yellow-500/10',
  },
  {
    id: 'patchtst',
    name: 'PatchTST',
    fullName: 'Patch-based Forecasting',
    color: 'border-indigo-400/30',
    glow: 'shadow-indigo-500/10',
  },
  {
    id: 'itransformer',
    name: 'iTransformer',
    fullName: 'Inverted Transformer',
    color: 'border-teal-400/30',
    glow: 'shadow-teal-500/10',
  },
  {
    id: 'xgb',
    name: 'XGBoost',
    fullName: 'Gradient Boosting Ensemble',
    color: 'border-red-400/30',
    glow: 'shadow-red-500/10',
  },
]

export function ModelSection() {
  const t = useT('models')
  const [activeModel, setActiveModel] = useState<string | null>(null)

  return (
    <section className="py-24 relative">
      <div className="container mx-auto px-4">
        <SectionHeading
          label={t('label')}
          title={t('title')}
          subtitle={t('subtitle')}
        />

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mt-12">
          {MODELS.map((model) => (
            <GlassCard
              key={model.id}
              variant="subtle"
              className={cn(
                'group text-center cursor-pointer transition-all duration-500',
                activeModel === model.id && 'border-quant-cyan/40 shadow-cyan-glow',
                !activeModel && model.highlight && 'border-quant-green/20'
              )}
              onClick={() => setActiveModel(activeModel === model.id ? null : model.id)}
            >
              {/* Icon / Animation area */}
              <div className={cn(
                'w-full h-32 rounded-xl mb-4 flex items-center justify-center border transition-all duration-500',
                model.color,
                activeModel === model.id ? 'bg-quant-cyan/5' : 'bg-muted/20'
              )}>
                <ModelAnimation model={model.id} active={activeModel === model.id} />
              </div>

              <h3 className={cn(
                'font-display font-bold text-lg mb-1',
                model.highlight ? 'text-quant-green' : 'text-foreground'
              )}>
                {model.name}
                {model.highlight && <span className="ml-2 text-[10px] bg-quant-green/10 text-quant-green px-1.5 py-0.5 rounded-full">{t('core')}</span>}
              </h3>
              <p className="text-xs text-terminal-muted mb-2">{model.fullName}</p>
              <p className="text-xs text-terminal-muted leading-relaxed opacity-70">{t(`${model.id}.desc`)}</p>
            </GlassCard>
          ))}
        </div>

        {activeModel && (
          <div className="mt-8 glass-card p-6 animate-count-up">
            <div className="flex items-center gap-2 mb-3">
              <div className="w-2 h-2 bg-quant-cyan rounded-full animate-pulse" />
              <span className="text-xs font-mono text-quant-cyan tracking-wider">
                {MODELS.find(m => m.id === activeModel)?.name} {t('structureDemo')}
              </span>
            </div>
            <p className="text-sm text-terminal-muted">
              {t(`${activeModel}.detail`)}
            </p>
          </div>
        )}
      </div>
    </section>
  )
}

function ModelAnimation({ model, active }: { model: string; active: boolean }) {
  return (
    <div className="relative w-full h-full flex items-center justify-center">
      {model === 'cnn' && (
        <div className="flex gap-1">
          {Array.from({ length: 8 }).map((_, i) => (
            <div
              key={i}
              className={cn(
                'w-2 rounded-full transition-all duration-300',
                active ? 'animate-pulse' : 'opacity-30'
              )}
              style={{
                height: `${Math.sin(i * 0.5) * 20 + 40}px`,
                backgroundColor: active
                  ? `hsl(${180 + i * 15}, 100%, ${50 + Math.sin(i) * 20}%)`
                  : '#374151',
                animationDelay: `${i * 0.1}s`,
              }}
            />
          ))}
          <div
            className={cn(
              'absolute h-16 w-6 border-2 border-quant-cyan/50 rounded transition-all duration-500',
              active ? 'opacity-100 translate-x-0' : 'opacity-0 -translate-x-4'
            )}
            style={{ animation: active ? 'flow-right 2s linear infinite' : 'none' }}
          />
        </div>
      )}

      {model === 'rnn' && (
        <div className="flex items-center gap-1">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="flex flex-col items-center gap-1">
              <div
                className={cn(
                  'w-5 h-5 rounded-full border-2 transition-all duration-300',
                  active ? 'border-purple-400 bg-purple-400/20 scale-100' : 'border-gray-600 scale-75 opacity-30'
                )}
                style={{ transitionDelay: `${i * 0.1}s` }}
              />
              {i < 5 && (
                <svg width="8" height="2" className="text-purple-400/50">
                  <line x1="0" y1="1" x2="8" y2="1" stroke="currentColor" strokeWidth="1" />
                </svg>
              )}
            </div>
          ))}
        </div>
      )}

      {model === 'transformer' && (
        <div className={cn(
          'grid gap-0.5 transition-all duration-500',
          active ? 'opacity-100 scale-100' : 'opacity-30 scale-75'
        )}>
          {Array.from({ length: 5 }).map((_, row) => (
            <div key={row} className="flex gap-0.5">
              {Array.from({ length: 5 }).map((_, col) => (
                <div
                  key={col}
                  className="w-4 h-4 rounded-sm transition-all duration-700"
                  style={{
                    backgroundColor: active
                      ? `rgba(0, 245, 255, ${Math.abs(2 - row) * Math.abs(2 - col) * 0.08 + 0.05})`
                      : 'rgba(255, 255, 255, 0.05)',
                    transitionDelay: `${(row + col) * 50}ms`,
                  }}
                />
              ))}
            </div>
          ))}
        </div>
      )}

      {model === 'timesnet' && (
        <div className="relative">
          <div className={cn(
            'flex flex-col gap-0.5 transition-all duration-500',
            active ? 'opacity-100 scale-100' : 'opacity-30 scale-75'
          )}>
            {Array.from({ length: 4 }).map((_, row) => (
              <div key={row} className="flex gap-0.5">
                {Array.from({ length: 6 }).map((_, col) => (
                  <div
                    key={col}
                    className="w-4 h-4 rounded-sm transition-all duration-700"
                    style={{
                      backgroundColor: active
                        ? `rgba(0, 255, 149, ${0.1 + Math.sin(row * 0.8 + col * 0.5) * 0.15})`
                        : 'rgba(255, 255, 255, 0.05)',
                      transitionDelay: `${(row + col) * 60}ms`,
                    }}
                  />
                ))}
              </div>
            ))}
          </div>
          {active && (
            <div className="absolute inset-0 border-2 border-quant-green/30 rounded animate-pulse rounded-lg" />
          )}
        </div>
      )}

      {model === 'autoformer' && (
        <div className="relative w-full h-full">
          {/* Trend line (slow, smooth) */}
          <svg className="absolute inset-0 w-full h-full" viewBox="0 0 100 60">
            <polyline
              fill="none"
              stroke={active ? 'rgba(251, 146, 60, 0.7)' : '#374151'}
              strokeWidth="2"
              points="0,35 20,33 40,30 60,28 80,25 100,22"
              className={active ? 'animate-pulse' : ''}
            />
            {/* Seasonal wave (oscillating around trend) */}
            <path
              fill="none"
              stroke={active ? 'rgba(0, 245, 255, 0.5)' : '#374151'}
              strokeWidth="1.5"
              d="M0,30 Q12,10 25,28 Q37,48 50,26 Q62,5 75,24 Q87,44 100,22"
              className={active ? 'animate-pulse' : ''}
              style={{ animationDelay: '0.3s' }}
            />
          </svg>
        </div>
      )}

      {model === 'nonstationary' && (
        <div className="flex items-end gap-1.5">
          {Array.from({ length: 10 }).map((_, i) => (
            <div
              key={i}
              className={cn(
                'w-2.5 rounded-t transition-all duration-500',
                active ? 'scale-y-100' : 'opacity-30'
              )}
              style={{
                height: active
                  ? `${Math.abs(Math.sin(i * 0.8)) * 35 + 15}px`
                  : `${15 + (i % 3) * 8}px`,
                backgroundColor: active
                  ? `hsl(${320 + i * 8}, 80%, ${55 + Math.sin(i * 0.6) * 15}%)`
                  : '#374151',
                transitionDelay: `${i * 80}ms`,
                transformOrigin: 'bottom',
              }}
            />
          ))}
        </div>
      )}

      {model === 'dlinear' && (
        <div className="relative w-full h-full flex flex-col justify-center gap-3 px-4">
          {/* Moving average (trend) — straight line moving up */}
          <div className="relative h-1.5 w-full bg-gray-700/30 rounded overflow-hidden">
            <div
              className={cn(
                'absolute inset-y-0 left-0 bg-cyan-400/70 rounded transition-all duration-700',
                active ? 'w-3/4' : 'w-1/4'
              )}
            />
          </div>
          {/* Residual (seasonal) — oscillating dots */}
          <div className="flex justify-between px-2">
            {Array.from({ length: 8 }).map((_, i) => (
              <div
                key={i}
                className="w-1.5 h-1.5 rounded-full transition-all duration-300"
                style={{
                  backgroundColor: active
                    ? `hsl(${180 + i * 15}, 80%, 55%)`
                    : '#374151',
                  transform: active
                    ? `translateY(${Math.sin(i * 1.1) * 6}px)`
                    : 'translateY(0)',
                  transitionDelay: `${i * 0.1}s`,
                }}
              />
            ))}
          </div>
        </div>
      )}

      {model === 'informer' && (
        <div className="grid gap-0.5" style={{ gridTemplateColumns: 'repeat(7, 1fr)' }}>
          {Array.from({ length: 7 }).map((_, row) =>
            Array.from({ length: 7 }).map((_, col) => {
              // Sparse attention: only some cells are active (top 30%)
              const isActive = (row * 7 + col) % 3 === 0 || row === col
              return (
                <div
                  key={`${row}-${col}`}
                  className="w-3 h-3 rounded-sm transition-all duration-500"
                  style={{
                    backgroundColor: active && isActive
                      ? `rgba(250, 204, 21, ${0.15 + (1 - Math.abs(row - col) / 7) * 0.4})`
                      : 'rgba(255, 255, 255, 0.04)',
                    transitionDelay: `${(row + col) * 40}ms`,
                  }}
                />
              )
            })
          )}
        </div>
      )}

      {model === 'patchtst' && (
        <div className="flex gap-1.5">
          {Array.from({ length: 5 }).map((_, p) => (
            <div
              key={p}
              className={cn(
                'flex flex-col gap-0.5 border rounded p-0.5 transition-all duration-300',
                active ? 'border-indigo-400/40 bg-indigo-400/5' : 'border-gray-600/30'
              )}
              style={{ transitionDelay: `${p * 0.1}s` }}
            >
              {Array.from({ length: 4 }).map((_, b) => (
                <div
                  key={b}
                  className="w-3 h-3 rounded-sm transition-all duration-500"
                  style={{
                    backgroundColor: active
                      ? `rgba(129, 140, 248, ${0.2 + Math.sin(p * 0.6 + b * 0.9) * 0.2})`
                      : 'rgba(255, 255, 255, 0.05)',
                    transitionDelay: `${(p + b) * 60}ms`,
                  }}
                />
              ))}
            </div>
          ))}
        </div>
      )}

      {model === 'itransformer' && (
        <div className="flex flex-col gap-0.5">
          {Array.from({ length: 4 }).map((_, row) => (
            <div key={row} className="flex gap-0.5">
              {Array.from({ length: 8 }).map((_, col) => (
                <div
                  key={col}
                  className="w-3 h-3 rounded-sm transition-all duration-500"
                  style={{
                    backgroundColor: active
                      ? `rgba(45, 212, 191, ${0.1 + Math.abs(1.5 - row) * 0.15 + Math.sin(col * 0.7) * 0.1})`
                      : 'rgba(255, 255, 255, 0.04)',
                    transitionDelay: `${col * 50 + row * 80}ms`,
                  }}
                />
              ))}
            </div>
          ))}
        </div>
      )}

      {model === 'xgb' && (
        <div className="flex items-end gap-1">
          {Array.from({ length: 9 }).map((_, i) => {
            const heights = [30, 18, 40, 22, 50, 28, 44, 20, 34]
            return (
              <div key={i} className="flex flex-col items-center gap-0.5">
                {Array.from({ length: 3 }).map((_, layer) => (
                  <div
                    key={layer}
                    className={cn(
                      'w-3 rounded-t-sm transition-all duration-500',
                      active ? 'opacity-100' : 'opacity-25'
                    )}
                    style={{
                      height: `${Math.max(3, heights[i] / 3 - layer * 4)}px`,
                      backgroundColor: active
                        ? layer === 0
                          ? `hsl(${355 + i * 3}, 70%, ${50 - layer * 8}%)`
                          : layer === 1
                          ? `hsl(${355 + i * 3}, 65%, ${55 - layer * 8}%)`
                          : `hsl(${355 + i * 3}, 60%, ${60 - layer * 8}%)`
                        : '#374151',
                      transitionDelay: `${i * 60 + layer * 40}ms`,
                    }}
                  />
                ))}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
