import { cn } from '@/lib/utils'
import { type ReactNode } from 'react'

interface SectionHeadingProps {
  label?: string
  title: string
  subtitle?: string
  className?: string
  align?: 'left' | 'center'
  children?: ReactNode
}

export function SectionHeading({
  label,
  title,
  subtitle,
  className,
  align = 'center',
  children,
}: SectionHeadingProps) {
  return (
    <div
      className={cn(
        'mb-12',
        align === 'center' && 'text-center',
        className
      )}
    >
      {label && (
        <p className="section-label">{label}</p>
      )}
      <h2 className="section-heading">{title}</h2>
      {subtitle && (
        <p className="mt-3 text-terminal-muted text-sm max-w-xl mx-auto leading-relaxed">
          {subtitle}
        </p>
      )}
      {children}
    </div>
  )
}
