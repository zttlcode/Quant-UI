'use client'

import { cn } from '@/lib/utils'

interface FeatureHeatmapProps {
  title?: string
  rows?: number
  cols?: number
  data?: number[][]       // row-major values 0-1
  rowLabels?: string[]
  colLabels?: string[]
  className?: string
}

export function FeatureHeatmap({
  title = 'Feature Heatmap',
  rows = 8,
  cols = 12,
  data,
  rowLabels,
  colLabels,
  className,
}: FeatureHeatmapProps) {
  // Generate mock data if none provided
  const heatmapData = data || Array.from({ length: rows }, (_, r) =>
    Array.from({ length: cols }, (_, c) =>
      Math.sin(r * 0.5 + c * 0.3) * 0.4 + Math.sin(c * 0.7) * 0.3 + Math.random() * 0.1 + 0.5
    )
  )

  const defaultRowLabels = Array.from({ length: rows }, (_, i) => `Period ${i + 1}`)
  const defaultColLabels = Array.from({ length: cols }, (_, i) => `T${i + 1}`)

  return (
    <div className={cn('glass-card-variant p-5', className)}>
      <div className="flex items-center gap-2 mb-4">
        <div className="w-2 h-2 bg-quant-green rounded-full animate-pulse" />
        <span className="text-xs font-mono text-quant-green tracking-wider uppercase">
          {title}
        </span>
      </div>

      {/* Heatmap Grid */}
      <div className="overflow-x-auto">
        <div className="inline-block min-w-full">
          {/* Column labels */}
          <div className="flex mb-1 ml-12">
            {(colLabels || defaultColLabels).map((label, i) => (
              <div key={i} className="flex-1 min-w-[20px] text-center">
                <span className="text-[8px] font-mono text-terminal-muted">{label}</span>
              </div>
            ))}
          </div>

          {/* Rows */}
          {heatmapData.map((row, r) => (
            <div key={r} className="flex items-center">
              {/* Row label */}
              <div className="w-12 pr-2 text-right">
                <span className="text-[8px] font-mono text-terminal-muted">
                  {(rowLabels || defaultRowLabels)[r]}
                </span>
              </div>
              {/* Cells */}
              {row.map((value, c) => {
                // Color: blue (low) → cyan → green (high)
                const hue = value < 0.5 ? 200 : 160
                const saturation = 70 + value * 30
                const lightness = 30 + (1 - value) * 30
                return (
                  <div
                    key={c}
                    className="flex-1 min-w-[20px] h-6 rounded-sm transition-all duration-300 hover:scale-125 hover:z-10 relative group"
                    style={{
                      backgroundColor: `hsla(${hue}, ${saturation}%, ${lightness}%, 0.8)`,
                      border: value > 0.7 ? '1px solid rgba(0, 255, 149, 0.3)' : '1px solid transparent',
                    }}
                    title={`Row ${r + 1}, Col ${c + 1}: ${(value * 100).toFixed(1)}%`}
                  />
                )
              })}
            </div>
          ))}
        </div>
      </div>

      {/* Color scale legend */}
      <div className="flex items-center justify-end gap-2 mt-3">
        <span className="text-[9px] font-mono text-terminal-muted">Low</span>
        <div className="h-3 w-24 rounded-full" style={{
          background: 'linear-gradient(90deg, hsl(220, 70%, 40%) 0%, hsl(200, 80%, 50%) 30%, hsl(180, 80%, 50%) 50%, hsl(160, 80%, 50%) 70%, hsl(150, 80%, 40%) 100%)',
        }} />
        <span className="text-[9px] font-mono text-terminal-muted">High</span>
      </div>
    </div>
  )
}
