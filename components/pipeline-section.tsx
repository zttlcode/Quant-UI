'use client'

import { useState, useEffect } from 'react'
import { SectionHeading } from '@/components/section-heading'
import { cn } from '@/lib/utils'

const PIPELINE_STEPS = [
  { label: 'Historical\nMarket', color: 'border-quant-cyan/50 bg-quant-cyan/5' },
  { label: 'Feature\nEngineering', color: 'border-quant-cyan/40 bg-quant-cyan/5' },
  { label: 'Strategy\nSignal', color: 'border-blue-400/50 bg-blue-400/5' },
  { label: 'Meta\nLabel', color: 'border-purple-400/50 bg-purple-400/5' },
  { label: 'Deep Time Series\nInference', color: 'border-quant-green/50 bg-quant-green/5' },
  { label: 'Trading\nSignal', color: 'border-quant-green/40 bg-quant-green/5' },
  { label: 'Portfolio\nStats', color: 'border-amber-400/50 bg-amber-400/5' },
]

export function PipelineSection() {
  const [highlightIndex, setHighlightIndex] = useState(0)

  useEffect(() => {
    const interval = setInterval(() => {
      setHighlightIndex(prev => (prev + 1) % PIPELINE_STEPS.length)
    }, 500)
    return () => clearInterval(interval)
  }, [])

  return (
    <section className="py-24 relative overflow-hidden">
      <div className="container mx-auto px-4">
        <SectionHeading
          label="AI Pipeline"
          title="量化交易流水线"
          subtitle="从历史市场数据到最终交易决策，每个环节都由 AI 驱动，形成完整的量化研究闭环。"
        />

        {/* Pipeline Flow */}
        <div className="relative mt-16 max-w-5xl mx-auto">
          {/* Flow line */}
          <div className="absolute top-8 left-[8%] right-[8%] h-0.5 bg-gradient-to-r from-quant-cyan/30 via-quant-cyan/10 to-quant-cyan/30 hidden md:block">
            {/* Animated flow dots */}
            <div className="absolute inset-0 overflow-hidden">
              <div className="absolute top-0 w-3 h-3 bg-quant-cyan rounded-full shadow-cyan-glow animate-flow-right" />
              <div className="absolute top-0 w-3 h-3 bg-quant-cyan rounded-full shadow-cyan-glow animate-flow-right" style={{ animationDelay: '0.7s' }} />
              <div className="absolute top-0 w-3 h-3 bg-quant-cyan rounded-full shadow-cyan-glow animate-flow-right" style={{ animationDelay: '1.4s' }} />
            </div>
          </div>

          {/* Steps */}
          <div className="grid grid-cols-4 md:grid-cols-7 gap-2 md:gap-4">
            {PIPELINE_STEPS.map((step, i) => (
              <div key={step.label} className="flex flex-col items-center">
                {/* Node */}
                <div
                  className={cn(
                    'w-12 h-12 md:w-16 md:h-16 rounded-2xl border flex items-center justify-center relative z-10 transition-all duration-300 hover:scale-110',
                    step.color,
                    highlightIndex === i && 'shadow-cyan-glow animate-pulse-glow'
                  )}
                >
                  <span className="text-xs md:text-sm font-mono font-bold text-foreground text-center leading-tight whitespace-pre-line">
                    {i + 1}
                  </span>
                </div>
                {/* Label */}
                <p className={cn(
                  'mt-3 text-[10px] md:text-xs text-center font-mono whitespace-pre-line leading-tight',
                  highlightIndex === i ? 'text-quant-cyan' : 'text-terminal-muted'
                )}>
                  {step.label}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}
