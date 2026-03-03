'use client'

import { Strategy } from '@/types/strategy'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { Trophy, TrendingUp, TrendingDown, Award } from 'lucide-react'

interface PerformanceDashboardProps {
  strategies: Strategy[]
}

export default function PerformanceDashboard({ strategies }: PerformanceDashboardProps) {
  // 按收益排序
  const sortedByPnl = [...strategies].sort((a, b) => b.pnl - a.pnl).slice(0, 5)

  // 按Sharpe排序
  const sortedBySharpe = [...strategies].sort((a, b) => b.sharpe - a.sharpe)

  // 按最大回撤排序（越低越好）
  const sortedByDrawdown = [...strategies].sort((a, b) => a.maxDrawdown - b.maxDrawdown).slice(0, 5)

  // 准备Sharpe对比数据
  const sharpeData = sortedBySharpe.map(strategy => ({
    name: strategy.name,
    sharpe: strategy.sharpe,
    pnl: strategy.pnl
  }))

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-terminal-card border border-terminal-border p-3 rounded-lg shadow-lg">
          <p className="font-bold mb-1">{label}</p>
          <p className="text-sm">
            Sharpe: <span className="profit-text font-semibold">{payload[0].value.toFixed(2)}</span>
          </p>
          <p className="text-sm">
            收益: <span className={`font-semibold ${payload[0].payload.pnl >= 0 ? 'profit-text' : 'loss-text'}`}>
              {payload[0].payload.pnl >= 0 ? '+' : ''}{payload[0].payload.pnl.toFixed(1)}%
            </span>
          </p>
        </div>
      )
    }
    return null
  }

  const getRankColor = (index: number) => {
    switch (index) {
      case 0: return '#F59E0B' // 金色
      case 1: return '#9CA3AF' // 银色
      case 2: return '#92400E' // 铜色
      default: return '#374151'
    }
  }

  return (
    <div className="bg-terminal-card border border-terminal-border rounded-xl p-6 card-hover-glow">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* 左侧：收益排行榜 */}
        <div>
          <div className="flex items-center gap-2 mb-6">
            <Trophy className="w-5 h-5 text-yellow-500" />
            <h3 className="text-lg font-bold">收益排行榜</h3>
          </div>

          <div className="space-y-3">
            {sortedByPnl.map((strategy, index) => (
              <div
                key={strategy.id}
                className="flex items-center justify-between p-4 bg-terminal-bg rounded-lg"
              >
                <div className="flex items-center gap-3">
                  <div
                    className="w-8 h-8 rounded-full flex items-center justify-center font-bold text-white"
                    style={{ backgroundColor: getRankColor(index) }}
                  >
                    {index + 1}
                  </div>
                  <div>
                    <div className="font-medium">{strategy.name}</div>
                    <div className="text-xs text-terminal-muted">
                      {strategy.markets.join(', ')}
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <div className={`text-xl font-bold ${strategy.pnl >= 0 ? 'profit-text' : 'loss-text'}`}>
                    {strategy.pnl >= 0 ? '+' : ''}{strategy.pnl.toFixed(1)}%
                  </div>
                  <div className="text-xs text-terminal-muted">
                    Sharpe: {strategy.sharpe.toFixed(2)}
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* 最大回撤对比 */}
          <div className="mt-8">
            <div className="flex items-center gap-2 mb-4">
              <TrendingDown className="w-5 h-5 text-loss" />
              <h3 className="text-lg font-bold">最大回撤对比</h3>
            </div>

            <div className="space-y-2">
              {sortedByDrawdown.map((strategy) => (
                <div key={strategy.id} className="space-y-1">
                  <div className="flex justify-between text-sm">
                    <span className="truncate max-w-[120px]">{strategy.name}</span>
                    <span className={`font-medium ${strategy.maxDrawdown <= 10 ? 'profit-text' : 'loss-text'}`}>
                      {strategy.maxDrawdown.toFixed(1)}%
                    </span>
                  </div>
                  <div className="h-2 bg-terminal-border rounded-full overflow-hidden">
                    <div
                      className={`h-full ${strategy.maxDrawdown <= 10 ? 'bg-profit' : strategy.maxDrawdown <= 20 ? 'bg-yellow-500' : 'bg-loss'}`}
                      style={{ width: `${Math.min(strategy.maxDrawdown * 2, 100)}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* 右侧：Sharpe对比条形图 */}
        <div>
          <div className="flex items-center gap-2 mb-6">
            <Award className="w-5 h-5 text-profit" />
            <h3 className="text-lg font-bold">Sharpe比率对比</h3>
          </div>

          <div className="h-[400px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={sharpeData} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" horizontal={false} />
                <XAxis
                  type="number"
                  stroke="#9CA3AF"
                  fontSize={12}
                  tickLine={false}
                  axisLine={false}
                  tickFormatter={(value) => value.toFixed(1)}
                />
                <YAxis
                  type="category"
                  dataKey="name"
                  stroke="#9CA3AF"
                  fontSize={12}
                  tickLine={false}
                  axisLine={false}
                  width={100}
                  tickFormatter={(value) => value.length > 12 ? value.substring(0, 10) + '...' : value}
                />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="sharpe" radius={[0, 4, 4, 0]}>
                  {sharpeData.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={entry.sharpe >= 2 ? '#10B981' : entry.sharpe >= 1 ? '#F59E0B' : '#EF4444'}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* 图例说明 */}
          <div className="mt-6 p-4 bg-terminal-bg rounded-lg">
            <div className="grid grid-cols-3 gap-4 text-sm">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-profit rounded"></div>
                <span>优秀 (≥2.0)</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-yellow-500 rounded"></div>
                <span>良好 (1.0-2.0)</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-loss rounded"></div>
                <span>需改进 (&lt;1.0)</span>
              </div>
            </div>
            <div className="mt-3 text-xs text-terminal-muted">
              <p>Sharpe比率衡量风险调整后收益，越高越好。通常大于1为可接受，大于2为优秀。</p>
            </div>
          </div>

          {/* 关键指标汇总 */}
          <div className="mt-6 grid grid-cols-3 gap-4">
            <div className="bg-terminal-bg p-4 rounded-lg text-center">
              <div className="text-2xl font-bold profit-text">
                {strategies.reduce((sum, s) => sum + s.pnl, 0).toFixed(1)}%
              </div>
              <div className="text-xs text-terminal-muted">总收益</div>
            </div>
            <div className="bg-terminal-bg p-4 rounded-lg text-center">
              <div className="text-2xl font-bold profit-text">
                {(strategies.reduce((sum, s) => sum + s.sharpe, 0) / strategies.length).toFixed(2)}
              </div>
              <div className="text-xs text-terminal-muted">平均Sharpe</div>
            </div>
            <div className="bg-terminal-bg p-4 rounded-lg text-center">
              <div className="text-2xl font-bold loss-text">
                {Math.max(...strategies.map(s => s.maxDrawdown)).toFixed(1)}%
              </div>
              <div className="text-xs text-terminal-muted">最大回撤</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}