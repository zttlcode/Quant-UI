'use client'

import { useState } from 'react'
import { SectionHeading } from '@/components/section-heading'
import { GlassCard } from '@/components/glass-card'
import { cn } from '@/lib/utils'

const MODELS = [
  {
    id: 'cnn',
    name: 'CNN',
    fullName: 'Convolutional Neural Network',
    desc: '通过卷积核滑动提取局部时序模式，捕捉价格形态的平移不变特征。',
    color: 'border-blue-400/30',
    glow: 'shadow-blue-500/10',
  },
  {
    id: 'rnn',
    name: 'RNN',
    fullName: 'Recurrent Neural Network',
    desc: '循环处理时序数据，隐藏状态在时间步间传递，建模序列依赖关系。',
    color: 'border-purple-400/30',
    glow: 'shadow-purple-500/10',
  },
  {
    id: 'transformer',
    name: 'Transformer',
    fullName: 'Self-Attention Architecture',
    desc: '通过多头自注意力机制并行处理序列，捕捉全局时序依赖关系。',
    color: 'border-amber-400/30',
    glow: 'shadow-amber-500/10',
  },
  {
    id: 'timesnet',
    name: 'TimesNet',
    fullName: 'TimesBlock Architecture',
    desc: '将 1D 时间序列转为 2D 张量，用卷积捕捉多周期模式，ICLR 2023 顶会论文。',
    color: 'border-quant-green/40',
    glow: 'shadow-quant-green/20',
    highlight: true,
  },
]

export function ModelSection() {
  const [activeModel, setActiveModel] = useState<string | null>(null)

  return (
    <section className="py-24 relative">
      <div className="container mx-auto px-4">
        <SectionHeading
          label="Model Architecture"
          title="深度时序模型架构"
          subtitle="探索驱动本平台的四种核心深度时序模型架构，TimesNet 为当前主力推理引擎。"
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
                {model.highlight && <span className="ml-2 text-[10px] bg-quant-green/10 text-quant-green px-1.5 py-0.5 rounded-full">Core</span>}
              </h3>
              <p className="text-xs text-terminal-muted mb-2">{model.fullName}</p>
              <p className="text-xs text-terminal-muted leading-relaxed opacity-70">{model.desc}</p>
            </GlassCard>
          ))}
        </div>

        {activeModel && (
          <div className="mt-8 glass-card p-6 animate-count-up">
            <div className="flex items-center gap-2 mb-3">
              <div className="w-2 h-2 bg-quant-cyan rounded-full animate-pulse" />
              <span className="text-xs font-mono text-quant-cyan tracking-wider">
                {MODELS.find(m => m.id === activeModel)?.name} — 结构演示
              </span>
            </div>
            <p className="text-sm text-terminal-muted">
              {activeModel === 'cnn' && '滑动卷积核沿时间轴扫描，提取价格序列中的局部形态特征。每一层卷积捕获不同尺度的时间模式。'}
              {activeModel === 'rnn' && '隐藏状态 h_t 沿时间步传递，每个时间步融合当前输入 x_t 和上一时刻的隐藏状态 h_{t-1}，建模时序依赖。'}
              {activeModel === 'transformer' && 'Query、Key、Value 矩阵通过 Scaled Dot-Product Attention 并行计算，每个位置关注所有其他位置。'}
              {activeModel === 'timesnet' && 'TimesBlock 将 1D 序列 reshape 为 2D 张量，通过 Inception 模块提取跨周期模式，再 flatten 回 1D 输出。核心创新在于发现时间序列的多周期性。'}
            </p>
          </div>
        )}
      </div>
    </section>
  )
}

function ModelAnimation({ model, active }: { model: string; active: boolean }) {
  // CSS-based model animations
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
          {/* Convolution kernel */}
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
          {/* 1D to 2D transformation animation */}
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
    </div>
  )
}
