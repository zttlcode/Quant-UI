'use client'

import { cn } from '@/lib/utils'
import { type ReactNode } from 'react'

interface GlassCardProps {
  children: ReactNode
  className?: string
  variant?: 'default' | 'subtle'
  hover?: boolean
  onClick?: () => void
}

export function GlassCard({
  children,
  className,
  variant = 'default',
  hover = true,
  onClick,
}: GlassCardProps) {
  return (
    <div
      className={cn(
        'relative overflow-hidden',
        variant === 'default' && 'glass-card p-6',
        variant === 'subtle' && 'glass-card-variant p-5',
        hover && 'cursor-pointer',
        className
      )}
      onClick={onClick}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
      onKeyDown={onClick ? (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onClick() } } : undefined}
    >
      {children}
    </div>
  )
}

interface GlassCardHeaderProps {
  children: ReactNode
  className?: string
}

export function GlassCardHeader({ children, className }: GlassCardHeaderProps) {
  return (
    <div className={cn('flex items-center gap-2 mb-4', className)}>
      {children}
    </div>
  )
}

interface GlassCardContentProps {
  children: ReactNode
  className?: string
}

export function GlassCardContent({ children, className }: GlassCardContentProps) {
  return (
    <div className={cn('', className)}>
      {children}
    </div>
  )
}
