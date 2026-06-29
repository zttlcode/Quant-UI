'use client'

import { useEffect, useState } from 'react'
import { SectionHeading } from '@/components/section-heading'
import { CountUp } from '@/components/count-up'
import type { Strategy } from '@/types/strategy'

export function StatsSection({ strategies = [] }: { strategies?: Strategy[] }) {
  const [mounted, setMounted] = useState(false)
  useEffect(() => setMounted(true), [])

  const runningCount = strategies.filter(s => s.status === 'running').length
  const stats = [
    {
      value: runningCount,
      label: 'Strategies',
      color: 'text-quant-cyan',
      glow: 'shadow-cyan-glow',
    },
    {
      value: 800,
      suffix: '+',
      label: 'Stocks Covered',
      color: 'text-quant-green',
      glow: 'shadow-green-glow',
    },
    {
      value: 'Deep TS',
      isText: true,
      label: 'Inference Engine',
      color: 'text-quant-cyan',
      glow: 'shadow-cyan-glow',
    },
    {
      value: 'Meta',
      suffix: '-labeling',
      isText: true,
      label: 'Core Engine',
      color: 'text-quant-green',
      glow: 'shadow-green-glow',
    },
  ]

  return (
    <section className="py-24 relative">
      <div className="container mx-auto px-4">
        <SectionHeading
          label="Statistics"
          title="项目数据统计"
        />

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-6 max-w-4xl mx-auto mt-12">
          {stats.map((stat, i) => (
            <div
              key={i}
              className="glass-card-variant p-8 text-center group hover:scale-105 transition-transform duration-300"
            >
              <div className={`text-3xl md:text-4xl font-bold font-mono mb-2 ${stat.color}`}>
                {mounted && !stat.isText ? (
                  <CountUp value={typeof stat.value === 'number' ? stat.value : 0} duration={1500 + i * 300} />
                ) : (
                  <span>{stat.value}</span>
                )}
                {stat.suffix && <span>{stat.suffix}</span>}
              </div>
              <p className="text-xs text-terminal-muted font-mono tracking-wider uppercase">
                {stat.label}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
