'use client'

import { useState, useEffect } from 'react'
import { useTheme } from 'next-themes'
import { Moon, Sun, BarChart3, Menu, X } from 'lucide-react'
import { strategies } from '@/lib/mock-data'

export function Navbar() {
  const { theme, setTheme } = useTheme()
  const [mounted, setMounted] = useState(false)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  const runningStrategies = strategies.filter(s => s.status === 'running').length

  return (
    <nav className="border-b border-terminal-border bg-terminal-card sticky top-0 z-50">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <div className="flex items-center gap-3">
            <div className="p-2 bg-gradient-to-br from-primary to-profit rounded-lg">
              <BarChart3 className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold">Quant UI</h1>
              <p className="text-xs text-terminal-muted">量化交易策略平台</p>
            </div>
          </div>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center gap-6">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-profit rounded-full animate-pulse"></div>
              <span className="text-sm text-terminal-muted">
                运行中策略: <span className="profit-text font-semibold">{runningStrategies}</span>
              </span>
            </div>

            <div className="flex items-center gap-4">
              <button
                onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
                className="p-2 rounded-lg border border-terminal-border hover:bg-terminal-bg transition-colors w-9 h-9 flex items-center justify-center"
                aria-label="切换主题"
              >
                {!mounted ? (
                  <div className="w-5 h-5" /> // 占位符，避免水合不匹配
                ) : theme === 'dark' ? (
                  <Sun className="w-5 h-5" />
                ) : (
                  <Moon className="w-5 h-5" />
                )}
              </button>
            </div>
          </div>

          {/* Mobile menu button */}
          <button
            className="md:hidden p-2 rounded-lg border border-terminal-border"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            aria-label="菜单"
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
          <div className="md:hidden py-4 border-t border-terminal-border">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-terminal-muted">运行中策略:</span>
                <span className="profit-text font-semibold">{runningStrategies}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-terminal-muted">主题:</span>
                <button
                  onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
                  className="p-2 rounded-lg border border-terminal-border w-9 h-9 flex items-center justify-center"
                  aria-label="切换主题"
                >
                  {!mounted ? (
                    <div className="w-5 h-5" /> // 占位符，避免水合不匹配
                  ) : theme === 'dark' ? (
                    <Sun className="w-5 h-5" />
                  ) : (
                    <Moon className="w-5 h-5" />
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