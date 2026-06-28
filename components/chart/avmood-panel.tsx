'use client'

import { useMemo } from 'react'
import {
  ComposedChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, ReferenceLine, ReferenceDot,
} from 'recharts'
import type { ChartDataPoint } from './types'

const C_AVMOOD = '#AB63FA'

interface AvmoodPanelProps {
  data: ChartDataPoint[]
  height?: number
}

export function AvmoodPanel({ data, height = 120 }: AvmoodPanelProps) {
  // Detect zero crossings
  const { crossUp, crossDown } = useMemo(() => {
    const up: { time: string; y: number }[] = []
    const down: { time: string; y: number }[] = []
    for (let i = 1; i < data.length; i++) {
      const prev = data[i - 1]?.avmood
      const curr = data[i]?.avmood
      if (prev == null || curr == null) continue
      if (prev <= 0 && curr > 0) up.push({ time: data[i].time, y: 0 })
      else if (prev >= 0 && curr < 0) down.push({ time: data[i].time, y: 0 })
    }
    return { crossUp: up, crossDown: down }
  }, [data])

  const formatDate = (t: string) => {
    try { return `${new Date(t).getMonth() + 1}/${new Date(t).getDate()}` }
    catch { return t.substring(5, 10) }
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <ComposedChart data={data} margin={{ top: 4, right: 10, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.4} />
        <XAxis dataKey="time" tickFormatter={formatDate}
          tick={{ fontSize: 10, fontFamily: 'JetBrains Mono', fill: 'hsl(var(--muted-foreground))' }}
          axisLine={{ stroke: 'hsl(var(--border))' }} tickLine={false} interval="preserveStartEnd" />
        <YAxis domain={['auto', 'auto']}
          tick={{ fontSize: 10, fontFamily: 'JetBrains Mono', fill: 'hsl(var(--muted-foreground))' }}
          axisLine={false} tickLine={false} width={55} />

        <Tooltip
          content={({ active, payload }: any) => {
            if (!active || !payload?.length) return null
            const d = payload[0]?.payload as ChartDataPoint
            if (!d) return null
            return (
              <div className="glass-card-variant p-2 text-[10px] font-mono">
                <p className="text-terminal-muted">{d.time?.substring(0, 10)}</p>
                {d.avmood != null && <p style={{ color: C_AVMOOD }}>avmood: {d.avmood.toFixed(6)}</p>}
              </div>
            )
          }}
        />

        {/* avmood curve */}
        <Line type="monotone" dataKey="avmood" stroke={C_AVMOOD} dot={false} strokeWidth={1.2} connectNulls />

        {/* Zero line */}
        <ReferenceLine y={0} stroke="#F59E0B" strokeWidth={0.8} strokeDasharray="4 3" />

        {/* Cross-up markers (▲ green at y=0) */}
        {crossUp.map((m, i) => (
          <ReferenceDot key={`cup-${i}`} x={m.time} y={m.y} r={5} fill="#16A34A" stroke="#059669" strokeWidth={1}
            shape={(p: any) => (
              <g transform={`translate(${p.cx},${p.cy})`}>
                <polygon points="0,-7 6,4 -6,4" fill="#16A34A" stroke="#059669" strokeWidth={0.8} />
              </g>
            )} />
        ))}

        {/* Cross-down markers (▼ red at y=0) */}
        {crossDown.map((m, i) => (
          <ReferenceDot key={`cdn-${i}`} x={m.time} y={m.y} r={5} fill="#DC2626" stroke="#991B1B" strokeWidth={1}
            shape={(p: any) => (
              <g transform={`translate(${p.cx},${p.cy})`}>
                <polygon points="0,7 6,-4 -6,-4" fill="#DC2626" stroke="#991B1B" strokeWidth={0.8} />
              </g>
            )} />
        ))}
      </ComposedChart>
    </ResponsiveContainer>
  )
}
