'use client'

import { useEffect, useState } from 'react'
import dynamic from 'next/dynamic'
import { ArrowDown, Sparkles } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { CountUp } from '@/components/count-up'
import type { Strategy } from '@/types/strategy'

// Lazy-load Three.js canvas to avoid SSR issues & reduce initial bundle
const NeuralNetworkCanvas = dynamic(
  () => import('@/components/neural-network-canvas').then(m => ({ default: m.NeuralNetworkCanvas })),
  { ssr: false, loading: () => <div className="absolute inset-0 bg-background" /> }
)

export function HeroSection({ strategies = [] }: { strategies?: Strategy[] }) {
  const [mounted, setMounted] = useState(false)
  useEffect(() => setMounted(true), [])

  const totalReturn = strategies.length > 0
    ? strategies.reduce((sum, s) => sum + s.pnl, 0) / strategies.length
    : 0
  const runningCount = strategies.filter(s => s.status === 'running').length

  return (
    <section className="relative min-h-screen flex flex-col items-center justify-center overflow-hidden">
      {/* 3D Background */}
      <NeuralNetworkCanvas />

      {/* Content */}
      <div className="relative z-10 container mx-auto px-4 text-center">
        {/* Badge */}
        <div className="mb-6 animate-float">
          <Badge variant="default" className="px-4 py-1.5 text-sm gap-2">
            <Sparkles className="w-3.5 h-3.5" />
            <span className="font-mono">AI-Powered Quantitative Research</span>
          </Badge>
        </div>

        {/* Title */}
        <h1 className="font-display text-4xl md:text-6xl lg:text-7xl font-bold tracking-tight mb-6">
          <span className="bg-gradient-to-br from-white via-quant-cyan to-blue-400 bg-clip-text text-transparent">
            AI Quantitative
          </span>
          <br />
          <span className="bg-gradient-to-br from-quant-cyan to-quant-green bg-clip-text text-transparent">
            Research Platform
          </span>
        </h1>

        {/* Subtitle */}
        <p className="text-terminal-muted text-base md:text-lg max-w-2xl mx-auto mb-8 font-mono leading-relaxed">
          Meta-labeling + TimesNet + Bayesian Optimization
        </p>

        {/* CTA Buttons */}
        <div className="flex items-center justify-center gap-4 mb-16">
          <a href="#intro">
            <Button variant="glow" size="lg" className="group">
              Explore Platform
              <ArrowDown className="w-4 h-4 ml-1 group-hover:translate-y-0.5 transition-transform" />
            </Button>
          </a>
          <a href="/strategies">
            <Button variant="outline" size="lg">
              View Strategies
            </Button>
          </a>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-3xl mx-auto">
          {[
            { label: 'Avg Return', value: totalReturn, suffix: '%', color: 'text-quant-green' },
            { label: 'Strategies', value: runningCount, suffix: '', color: 'text-quant-cyan' },
            { label: 'AI Models', value: 4, suffix: '', color: 'text-quant-cyan' },
            { label: 'Meta-labeling', value: 1, suffix: '', color: 'text-quant-green', prefix: '✓ ' },
          ].map((stat) => (
            <div key={stat.label} className="glass-card-variant p-4 text-center">
              <div className={`text-xl md:text-2xl font-bold font-mono ${stat.color}`}>
                {stat.prefix || ''}
                {mounted && <CountUp value={stat.value} duration={1200} />}
                {!mounted && <span>{stat.value}</span>}
                {stat.suffix}
              </div>
              <div className="text-xs text-terminal-muted mt-1">{stat.label}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Bottom fade */}
      <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-background to-transparent pointer-events-none z-10" />
    </section>
  )
}
