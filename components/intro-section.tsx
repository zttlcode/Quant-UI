'use client'

import { SectionHeading } from '@/components/section-heading'
import { GlassCard } from '@/components/glass-card'
import { Brain, Network, Cog, TrendingUp } from 'lucide-react'
import { useT } from '@/lib/i18n'

export function IntroSection() {
  const t = useT('intro')

  const FEATURES = [
    {
      icon: Brain,
      title: t('features.metaLabeling.title'),
      desc: t('features.metaLabeling.desc'),
      gradient: 'from-quant-cyan/20 to-blue-500/10',
    },
    {
      icon: Network,
      title: t('features.deepTS.title'),
      desc: t('features.deepTS.desc'),
      gradient: 'from-purple-500/20 to-quant-cyan/10',
    },
    {
      icon: Cog,
      title: t('features.strategyEngine.title'),
      desc: t('features.strategyEngine.desc'),
      gradient: 'from-quant-green/20 to-emerald-500/10',
    },
    {
      icon: TrendingUp,
      title: t('features.liveTrading.title'),
      desc: t('features.liveTrading.desc'),
      gradient: 'from-amber-500/20 to-quant-green/10',
    },
  ]

  return (
    <section id="intro" className="py-24 relative">
      <div className="container mx-auto px-4">
        <SectionHeading
          label={t('label')}
          title={t('title')}
          subtitle={t('subtitle')}
        />

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mt-12">
          {FEATURES.map((feature) => (
            <GlassCard key={feature.title} className="group text-center">
              <div className={`w-14 h-14 rounded-2xl bg-gradient-to-br ${feature.gradient} flex items-center justify-center mx-auto mb-4 border border-border group-hover:scale-110 transition-transform duration-300`}>
                <feature.icon className="w-7 h-7 text-quant-cyan" />
              </div>
              <h3 className="font-display font-semibold text-foreground mb-2">{feature.title}</h3>
              <p className="text-terminal-muted text-xs leading-relaxed">{feature.desc}</p>
            </GlassCard>
          ))}
        </div>
      </div>
    </section>
  )
}
