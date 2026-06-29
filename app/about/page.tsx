'use client'

import Link from 'next/link'
import { ArrowLeft } from 'lucide-react'
import { SectionHeading } from '@/components/section-heading'
import { GlassCard } from '@/components/glass-card'
import { ContactSection } from '@/components/contact-section'
import { useT } from '@/lib/i18n'

export default function AboutPage() {
  const t = useT('about')

  return (
    <div className="container mx-auto px-4 py-12">
      {/* Back */}
      <Link href="/" className="inline-flex items-center gap-2 text-terminal-muted hover:text-quant-cyan transition-colors text-sm mb-8">
        <ArrowLeft className="w-4 h-4" />
        {t('backToResearch')}
      </Link>

      <SectionHeading
        label={t('label')}
        title={t('title')}
        subtitle={t('subtitle')}
        align="left"
      />

      {/* Project Intro */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mt-8 mb-16">
        <GlassCard variant="subtle" className="p-6">
          <h2 className="font-display font-semibold text-lg text-foreground mb-4">{t('projectBackground')}</h2>
          <div className="space-y-3 text-sm text-terminal-muted leading-relaxed">
            <p dangerouslySetInnerHTML={{ __html: t('backgroundP1') }} />
            <p dangerouslySetInnerHTML={{ __html: t('backgroundP2') }} />
            <p dangerouslySetInnerHTML={{ __html: t('backgroundP3') }} />
          </div>
        </GlassCard>

        <GlassCard variant="subtle" className="p-6">
          <h2 className="font-display font-semibold text-lg text-foreground mb-4">{t('strategySystem')}</h2>
          <div className="space-y-4">
            <div className="p-4 rounded-xl bg-quant-cyan/5 border border-quant-cyan/10">
              <h3 className="font-mono font-semibold text-quant-cyan text-sm mb-1">Strategy 1</h3>
              <p className="text-foreground font-medium mb-1">{t('strategy1Name')}</p>
              <p className="text-xs text-terminal-muted">{t('strategy1Desc')}</p>
            </div>
            <div className="p-4 rounded-xl bg-purple-500/5 border border-purple-500/10">
              <h3 className="font-mono font-semibold text-purple-400 text-sm mb-1">Strategy 2</h3>
              <p className="text-foreground font-medium mb-1">{t('strategy2Name')}</p>
              <p className="text-xs text-terminal-muted">{t('strategy2Desc')}</p>
            </div>
          </div>
        </GlassCard>
      </div>

      {/* Tech Stack */}
      <GlassCard variant="subtle" className="p-6 mb-16">
        <h2 className="font-display font-semibold text-lg text-foreground mb-4">{t('techStack')}</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { category: t('frontend'), items: ['Next.js 14', 'React 18', 'Tailwind CSS', 'Three.js'] },
            { category: t('visualization'), items: ['ECharts', 'Recharts', 'React Three Fiber', 'tsParticles'] },
            { category: t('aiMl'), items: ['Deep Time Series', 'PyTorch', 'Meta-labeling', 'Bayesian Opt'] },
            { category: t('backend'), items: ['Python', 'Starlette', 'Pandas', 'Plotly'] },
          ].map((stack) => (
            <div key={stack.category}>
              <p className="text-xs font-mono text-quant-cyan mb-2 tracking-wider">{stack.category}</p>
              <ul className="space-y-1">
                {stack.items.map((item) => (
                  <li key={item} className="text-sm text-terminal-muted">{item}</li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </GlassCard>

      {/* Contact (reuse section) */}
      <ContactSection />
    </div>
  )
}
