import * as React from 'react'
import { Slot } from '@radix-ui/react-slot'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'

const buttonVariants = cva(
  'inline-flex items-center justify-center whitespace-nowrap rounded-xl text-sm font-medium transition-all duration-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-quant-cyan/50 focus-visible:ring-offset-2 focus-visible:ring-offset-ai-deep disabled:pointer-events-none disabled:opacity-50',
  {
    variants: {
      variant: {
        default:
          'bg-quant-cyan/10 text-quant-cyan border border-quant-cyan/20 hover:bg-quant-cyan/20 hover:border-quant-cyan/40 hover:shadow-cyan-glow',
        destructive:
          'bg-quant-red/10 text-quant-red border border-quant-red/20 hover:bg-quant-red/20',
        outline:
          'border border-white/10 bg-transparent hover:bg-white/5 hover:border-white/20 text-terminal-text',
        secondary:
          'bg-white/5 text-terminal-text hover:bg-white/10',
        ghost:
          'hover:bg-white/5 text-terminal-muted hover:text-terminal-text',
        link:
          'text-quant-cyan underline-offset-4 hover:underline',
        glow:
          'btn-glow',
        'glow-green':
          'btn-glow-green',
      },
      size: {
        default: 'h-10 px-4 py-2',
        sm: 'h-9 rounded-lg px-3',
        lg: 'h-12 rounded-xl px-8 text-base',
        icon: 'h-10 w-10',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : 'button'
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = 'Button'

export { Button, buttonVariants }
