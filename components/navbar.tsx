'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useTheme } from 'next-themes'
import { useLocale, useT } from '@/lib/i18n'
import { Moon, Sun, BarChart3, Menu, X, Languages } from 'lucide-react'
import { cn } from '@/lib/utils'
import { fetchStrategies } from '@/lib/data-service'

export function Navbar() {
  const { theme, setTheme } = useTheme()
  const pathname = usePathname()
  const [mounted, setMounted] = useState(false)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [scrolled, setScrolled] = useState(false)
  const locale = useLocale()
  const t = useT('nav')

  const NAV_ITEMS = [
    { href: '/', label: t('research'), icon: BarChart3 },
    { href: '/strategies', label: t('strategies') },
    { href: '/market', label: t('market') },
    { href: '/about', label: t('about') },
  ]

  useEffect(() => {
    setMounted(true)
    const handleScroll = () => setScrolled(window.scrollY > 20)
    window.addEventListener('scroll', handleScroll, { passive: true })
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  // Close mobile menu on route change
  useEffect(() => {
    setMobileMenuOpen(false)
  }, [pathname])

  const [runningCount, setRunningCount] = useState(0)

  useEffect(() => {
    fetchStrategies().then((result) => {
      if (!result.error) {
        setRunningCount(result.data!.filter(s => s.status === 'running').length)
      }
    })
  }, [])

  const switchLocale = () => {
    const next = locale === 'zh' ? 'en' : 'zh'
    document.cookie = `NEXT_LOCALE=${next};path=/;max-age=31536000;SameSite=Lax`
    window.location.reload()
  }

  return (
    <nav
      className={cn(
        'sticky top-0 z-50 transition-all duration-300',
        scrolled
          ? 'bg-background/80 backdrop-blur-xl border-b border-border shadow-lg shadow-black/10'
          : 'bg-transparent border-b border-transparent'
      )}
    >
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-3 group">
            <div className="p-2 bg-gradient-to-br from-quant-cyan to-blue-600 rounded-lg transition-all duration-300 group-hover:shadow-cyan-glow">
              <BarChart3 className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-display font-bold tracking-tight">
                <span className="text-foreground">Quant</span>
                <span className="text-quant-cyan"> AI</span>
              </h1>
              <p className="text-[10px] text-terminal-muted font-mono tracking-wider">
                {t('researchPlatform')}
              </p>
            </div>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center gap-1">
            {NAV_ITEMS.map((item) => {
              const isActive = pathname === item.href
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    'relative px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200',
                    isActive
                      ? 'text-quant-cyan bg-quant-cyan/5'
                      : 'text-terminal-muted hover:text-foreground hover:bg-muted/50'
                  )}
                >
                  {/* Active indicator */}
                  {isActive && (
                    <span className="absolute bottom-0 left-1/2 -translate-x-1/2 w-6 h-0.5 bg-quant-cyan rounded-full shadow-cyan-glow" />
                  )}
                  {item.label}
                </Link>
              )
            })}
          </div>

          {/* Desktop Right Side */}
          <div className="hidden md:flex items-center gap-3">
            {/* Live indicator */}
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-quant-green/5 border border-quant-green/10">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-quant-green opacity-75" />
                <span className="relative inline-flex rounded-full h-2 w-2 bg-quant-green" />
              </span>
              <span className="text-[10px] font-mono text-quant-green tracking-wider">
                {t('live', { count: runningCount })}
              </span>
            </div>

            {/* GitHub */}
            <a
              href="https://github.com/zttlcode"
              target="_blank"
              rel="noopener noreferrer"
              className="p-2 rounded-lg text-terminal-muted hover:text-foreground hover:bg-muted/50 transition-colors"
              aria-label="GitHub"
            >
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
              </svg>
            </a>

            {/* Language Toggle */}
            <button
              onClick={switchLocale}
              className="p-2 rounded-lg border border-border hover:bg-muted/50 transition-all duration-200 w-9 h-9 flex items-center justify-center"
              aria-label={locale === 'zh' ? 'Switch to English' : '切换到中文'}
              title={locale === 'zh' ? 'Switch to English' : '切换到中文'}
            >
              {!mounted ? (
                <div className="w-4 h-4" />
              ) : (
                <span className="text-xs font-mono font-bold text-terminal-muted">
                  {locale === 'zh' ? 'EN' : '中'}
                </span>
              )}
            </button>

            {/* Theme Toggle */}
            <button
              onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
              className="p-2 rounded-lg border border-border hover:bg-muted/50 transition-all duration-200 w-9 h-9 flex items-center justify-center"
              aria-label={t('toggleTheme')}
            >
              {!mounted ? (
                <div className="w-4 h-4" />
              ) : theme === 'dark' ? (
                <Sun className="w-4 h-4 text-quant-amber" />
              ) : (
                <Moon className="w-4 h-4 text-terminal-muted" />
              )}
            </button>
          </div>

          {/* Mobile menu button */}
          <button
            className="md:hidden p-2 rounded-lg border border-border hover:bg-muted/50 transition-colors"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            aria-label={mobileMenuOpen ? t('closeMenu') : t('openMenu')}
          >
            {mobileMenuOpen ? (
              <X className="w-5 h-5" />
            ) : (
              <Menu className="w-5 h-5" />
            )}
          </button>
        </div>

        {/* Mobile menu */}
        {mobileMenuOpen && (
          <div className="md:hidden py-4 border-t border-border animate-count-up">
            <div className="space-y-1">
              {NAV_ITEMS.map((item) => {
                const isActive = pathname === item.href
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={cn(
                      'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all',
                      isActive
                        ? 'text-quant-cyan bg-quant-cyan/5 font-medium'
                        : 'text-terminal-muted hover:text-foreground hover:bg-muted/50'
                    )}
                  >
                    {item.label}
                  </Link>
                )
              })}
            </div>
            <div className="mt-4 pt-4 border-t border-border flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 bg-quant-green rounded-full animate-pulse" />
                <span className="text-xs text-terminal-muted">
                  {t('strategiesRunning', { count: runningCount })}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={switchLocale}
                  className="p-2 rounded-lg border border-border w-9 h-9 flex items-center justify-center"
                  aria-label={locale === 'zh' ? 'Switch to English' : '切换到中文'}
                >
                  <span className="text-xs font-mono font-bold text-terminal-muted">
                    {locale === 'zh' ? 'EN' : '中'}
                  </span>
                </button>
                <button
                  onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
                  className="p-2 rounded-lg border border-border w-9 h-9 flex items-center justify-center"
                  aria-label={t('toggleTheme')}
                >
                  {!mounted ? (
                    <div className="w-4 h-4" />
                  ) : theme === 'dark' ? (
                    <Sun className="w-4 h-4 text-quant-amber" />
                  ) : (
                    <Moon className="w-4 h-4 text-terminal-muted" />
                  )}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </nav>
  )
}
