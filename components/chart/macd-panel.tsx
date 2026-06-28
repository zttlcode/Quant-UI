'use client'

import {
  ComposedChart, Bar, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell, ReferenceLine,
} from 'recharts'
import type { ChartDataPoint } from './types'

const COLORS = {
  dif: '#636EFA',       // blue
  dea: '#FFA15A',       // orange
  macdUp: '#EF553B',    // red
  macdDown: '#00CC96',  // green
}

interface MACDPanelProps {
  data: ChartDataPoint[]
  height?: number
}

export function MACDPanel({ data, height = 160 }: MACDPanelProps) {
  const formatDate = (t: string) => {
    try { return `${new Date(t).getMonth() + 1}/${new Date(t).getDate()}` }
    catch { return t.substring(5, 10) }
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <ComposedChart data={data} margin={{ top: 4, right: 10, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.4} />
        <XAxis
          dataKey="time" tickFormatter={formatDate}
          tick={{ fontSize: 10, fontFamily: 'JetBrains Mono', fill: 'hsl(var(--muted-foreground))' }}
          axisLine={{ stroke: 'hsl(var(--border))' }} tickLine={false} interval="preserveStartEnd"
        />
        <YAxis
          domain={['auto', 'auto']}
          tick={{ fontSize: 10, fontFamily: 'JetBrains Mono', fill: 'hsl(var(--muted-foreground))' }}
          axisLine={false} tickLine={false} width={55}
        />
        <Tooltip
          content={({ active, payload }) => {
            if (!active || !payload?.length) return null
            const d = payload[0]?.payload as ChartDataPoint | undefined
            if (!d) return null
            return (
              <div className="glass-card-variant p-2 text-[10px] font-mono">
                <p className="text-terminal-muted">{d.time?.substring(0, 10)}</p>
                {d.dif != null && <p className="text-[#636EFA]">DIF: {d.dif.toFixed(6)}</p>}
                {d.dea != null && <p className="text-[#FFA15A]">DEA: {d.dea.toFixed(6)}</p>}
                {d.macd != null && <p className={d.macd >= 0 ? 'text-quant-red' : 'text-quant-green'}>MACD: {d.macd.toFixed(6)}</p>}
              </div>
            )
          }}
        />

        {/* ── MACD Histogram ── */}
        <Bar dataKey="macd" barSize={4}>
          {data.map((d, i) => (
            <Cell key={`m-${i}`} fill={(d.macd ?? 0) >= 0 ? COLORS.macdUp : COLORS.macdDown} />
          ))}
        </Bar>

        {/* ── DIF line ── */}
        <Line type="monotone" dataKey="dif" stroke={COLORS.dif} dot={false} strokeWidth={1} name="DIF" />

        {/* ── DEA line ── */}
        <Line type="monotone" dataKey="dea" stroke={COLORS.dea} dot={false} strokeWidth={1} name="DEA" />

        {/* ── Zero line ── */}
        <ReferenceLine y={0} stroke="hsl(var(--muted-foreground))" strokeWidth={0.5} strokeDasharray="3 3" />
      </ComposedChart>
    </ResponsiveContainer>
  )
}
