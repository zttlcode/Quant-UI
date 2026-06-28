'use client'

import { cn } from '@/lib/utils'

interface TimelinePoint {
  time: string
  price: number
  signal?: 'BUY' | 'SELL' | null
  confidence?: number
  label?: string
}

interface InferenceTimelineProps {
  data: TimelinePoint[]
  className?: string
}

export function InferenceTimeline({ data, className }: InferenceTimelineProps) {
  if (!data.length) return null

  const minPrice = Math.min(...data.map(d => d.price))
  const maxPrice = Math.max(...data.map(d => d.price))
  const range = maxPrice - minPrice || 1

  return (
    <div className={cn('glass-card-variant p-5', className)}>
      <div className="flex items-center gap-2 mb-4">
        <div className="w-2 h-2 bg-quant-cyan rounded-full animate-pulse" />
        <span className="text-xs font-mono text-quant-cyan tracking-wider uppercase">
          Signal Timeline
        </span>
      </div>

      {/* Timeline */}
      <div className="relative h-40">
        {/* Price line */}
        <svg className="w-full h-full" viewBox={`0 0 ${data.length * 10} 100`} preserveAspectRatio="none">
          {/* Grid lines */}
          {[0.25, 0.5, 0.75].map((p) => (
            <line
              key={p}
              x1="0"
              y1={p * 100}
              x2={data.length * 10}
              y2={p * 100}
              stroke="rgba(255,255,255,0.03)"
              strokeWidth="0.5"
            />
          ))}

          {/* Price path */}
          <path
            d={data
              .map((d, i) => {
                const x = i * 10 + 5
                const y = 100 - ((d.price - minPrice) / range) * 80 - 10
                return `${i === 0 ? 'M' : 'L'} ${x} ${y}`
              })
              .join(' ')}
            fill="none"
            stroke="rgba(0, 245, 255, 0.4)"
            strokeWidth="1.5"
          />

          {/* Signal markers */}
          {data.map((d, i) => {
            if (!d.signal) return null
            const x = i * 10 + 5
            const y = 100 - ((d.price - minPrice) / range) * 80 - 10
            const isBuy = d.signal === 'BUY'
            return (
              <g key={i}>
                <circle
                  cx={x}
                  cy={y}
                  r="3"
                  fill={isBuy ? '#16A34A' : '#DC2626'}
                />
                <circle
                  cx={x}
                  cy={y}
                  r="6"
                  fill="none"
                  stroke={isBuy ? '#16A34A' : '#DC2626'}
                  strokeWidth="0.5"
                  opacity="0.5"
                />
                <text
                  x={x}
                  y={y - 6}
                  textAnchor="middle"
                  fill={isBuy ? '#16A34A' : '#DC2626'}
                  fontSize="4"
                  fontFamily="monospace"
                >
                  {d.signal}
                </text>
              </g>
            )
          })}
        </svg>
      </div>

      {/* Time labels */}
      <div className="flex justify-between mt-2 text-[10px] text-terminal-muted font-mono">
        <span>{data[0]?.time}</span>
        <span>{data[data.length - 1]?.time}</span>
      </div>
    </div>
  )
}
