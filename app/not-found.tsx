'use client'

import Link from 'next/link'
import { useT } from '@/lib/i18n'
import { Button } from '@/components/ui/button'

export default function NotFound() {
  const t = useT('errors')

  return (
    <div className="container mx-auto px-4 py-20 flex flex-col items-center justify-center min-h-[60vh] text-center">
      <div className="text-6xl font-display font-bold text-gradient-cyan mb-4">404</div>
      <h2 className="text-xl font-display font-bold mb-2">{t('pageNotFound')}</h2>
      <p className="text-terminal-muted text-sm mb-6">{t('pageNotFoundDesc')}</p>
      <Link href="/"><Button variant="default">{t('backToHome')}</Button></Link>
    </div>
  )
}
