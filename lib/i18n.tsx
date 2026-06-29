'use client'

import { createContext, useContext, useMemo, type ReactNode } from 'react'

type Messages = Record<string, any>
type Locale = 'zh' | 'en'

interface I18nContextType {
  locale: Locale
  messages: Messages
}

const I18nContext = createContext<I18nContextType | null>(null)

function getNested(obj: any, path: string): any {
  const keys = path.split('.')
  let result: any = obj
  for (const k of keys) {
    if (result == null) break
    result = result[k]
  }
  return result
}

function interpolate(text: string, values?: Record<string, string | number>): string {
  if (!values) return text
  let result = text
  for (const [k, v] of Object.entries(values)) {
    result = result.replace(`{${k}}`, String(v))
  }
  return result
}

export function I18nProvider({
  locale,
  messages,
  children,
}: {
  locale: Locale
  messages: Messages
  children: ReactNode
}) {
  const value = useMemo(() => ({ locale, messages }), [locale, messages])
  return (
    <I18nContext.Provider value={value}>
      {children}
    </I18nContext.Provider>
  )
}

/**
 * Translation hook with namespace support.
 * Returns a stable function reference — safe to use in useEffect/useMemo deps.
 * Usage: const t = useT('namespace')
 * Supports: t('key'), t('key', { count: 5 }), t.raw('key')
 */
export function useT(namespace?: string) {
  const ctx = useContext(I18nContext)

  return useMemo(() => {
    const translate = (key: string, values?: Record<string, string | number>): string => {
      const fullKey = namespace ? `${namespace}.${key}` : key
      const result = ctx ? getNested(ctx.messages, fullKey) : undefined
      if (typeof result === 'string') return interpolate(result, values)
      return key
    }

    translate.raw = (key: string): any => {
      const fullKey = namespace ? `${namespace}.${key}` : key
      return ctx ? getNested(ctx.messages, fullKey) : undefined
    }

    return translate
  }, [ctx, namespace])
}

/** Returns a function that translates strategy names by ID. Safe to use in loops. */
export function useStrategyName() {
  const ctx = useContext(I18nContext)
  return (id: string, fallback?: string): string => {
    if (!ctx) return fallback || id
    const name = getNested(ctx.messages, `strategyNames.${id}`)
    return typeof name === 'string' ? name : (fallback || id)
  }
}

/** Returns a function that translates strategy descriptions by ID. Safe to use in loops. */
export function useStrategyDesc() {
  const ctx = useContext(I18nContext)
  return (id: string, fallback?: string): string => {
    if (!ctx) return fallback || ''
    const desc = getNested(ctx.messages, `strategyDescs.${id}`)
    return typeof desc === 'string' ? desc : (fallback || '')
  }
}

export function useLocale(): Locale {
  const ctx = useContext(I18nContext)
  return ctx?.locale || 'zh'
}
