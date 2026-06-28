import * as React from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'

const badgeVariants = cva(
  'inline-flex items-center rounded-full px-3 py-1 text-xs font-medium transition-colors',
  {
    variants: {
      variant: {
        default:
          'bg-quant-cyan/10 text-quant-cyan border border-quant-cyan/20',
        success:
          'bg-quant-green/10 text-quant-green border border-quant-green/20',
        warning:
          'bg-quant-amber/10 text-quant-amber border border-quant-amber/20',
        destructive:
          'bg-quant-red/10 text-quant-red border border-quant-red/20',
        outline:
          'border border-white/10 text-terminal-muted',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  }
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  )
}

export { Badge, badgeVariants }
