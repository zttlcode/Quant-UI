'use client'

import { useEffect } from 'react'
import Link from 'next/link'
import { useT } from '@/lib/i18n'
import { Button } from '@/components/ui/button'

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  const t = useT('errors')

  useEffect(() => {
    console.error('Page error:', error)
  }, [error])

  return (
    <div className="container mx-auto px-4 py-20 flex flex-col items-center justify-center min-h-[60vh] text-center">
      <div className="w-16 h-16 rounded-2xl bg-quant-red/10 border border-quant-red/20 flex items-center justify-center mb-6">
        <span className="text-2xl">⚠</span>
      </div>
      <h2 className="text-xl font-display font-bold mb-2">{t('somethingWentWrong')}</h2>
      <p className="text-terminal-muted text-sm mb-6 max-w-md">
        {error.message || t('unexpectedError')}
      </p>
      <div className="flex gap-3">
        <Button variant="outline" onClick={reset}>{t('tryAgain')}</Button>
        <Link href="/"><Button variant="default">{t('backToHome')}</Button></Link>
      </div>
    </div>
  )
}
