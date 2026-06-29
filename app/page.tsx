'use client'

import { useState, useEffect } from 'react'
import { useT } from '@/lib/i18n'
import { HeroSection } from '@/components/hero-section'
import { IntroSection } from '@/components/intro-section'
import { PipelineSection } from '@/components/pipeline-section'
import { StrategiesSection } from '@/components/strategies-section'
import { ModelSection } from '@/components/model-section'
import { StatsSection } from '@/components/stats-section'
import { ContactSection } from '@/components/contact-section'
import { fetchStrategies } from '@/lib/data-service'
import type { Strategy } from '@/types/strategy'

export default function Home() {
  const [strategies, setStrategies] = useState<Strategy[]>([])
  const [error, setError] = useState<string | null>(null)
  const t = useT('errors')

  useEffect(() => {
    fetchStrategies().then((result) => {
      if (result.error) { setError(result.error); return }
      setStrategies(result.data!)
    })
  }, [])

  return (
    <div className="relative">
      {error && (
        <div className="container mx-auto px-4 py-12">
          <div className="glass-card-variant p-8 text-center border-quant-red/30">
            <p className="text-quant-red font-mono text-sm font-semibold mb-2">{t('dataLoadFailed')}</p>
            <p className="text-terminal-muted text-xs font-mono">{error}</p>
          </div>
        </div>
      )}
      <HeroSection strategies={strategies} />
      <IntroSection />
      <PipelineSection />
      <StrategiesSection strategies={strategies} />
      <ModelSection />
      <StatsSection strategies={strategies} />
      <ContactSection />
    </div>
  )
}
