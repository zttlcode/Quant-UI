'use client'

import { useEffect, useState } from 'react'
import { TrendingUp, DollarSign, Target, PlayCircle } from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { getOverviewStats } from '@/lib/mock-data'

// 确定性随机数生成器（避免 SSR 和客户端不匹配）
function deterministicRandom(seed: number): number {
  const x = Math.sin(seed) * 10000
  return x - Math.floor(x)
}

// 格式化数字（避免 SSR 和客户端不匹配）
function formatNumber(num: number): string {
  // 简单实现：添加千位分隔符
  return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',')
}

// 生成模拟资金曲线数据（使用确定性随机数）
function generateEquityCurve() {
  const data = []
  let equity = 1000000
  const now = new Date()
  let seed = 12345 // 固定种子确保 SSR 和客户端一致

  for (let i = 30; i >= 0; i--) {
    const date = new Date(now.getTime() - i * 24 * 60 * 60 * 1000)
    seed++
    const randomValue = deterministicRandom(seed)
    const dailyReturn = (randomValue - 0.45) * 0.02 // -0.9% 到 +1.1%
    equity = equity * (1 + dailyReturn)

    data.push({
      date: `${date.getMonth() + 1}/${date.getDate()}`, // 固定格式，避免 SSR 不匹配
      equity: Math.round(equity),
      pnl: dailyReturn * 100
    })
  }

  return data
}

export default function HeroStats() {
  const [countUpValues, setCountUpValues] = useState({
    totalPnl: 0,
    todayProfit: 0,
    winRate: 0,
    runningStrategies: 0
  })

  const equityData = generateEquityCurve()
  const stats = getOverviewStats()

  useEffect(() => {
    // 数字增长动画
    const duration = 1500
    const steps = 60
    const stepDuration = duration / steps

    let currentStep = 0
    const timer = setInterval(() => {
      currentStep++
      const progress = currentStep / steps

      setCountUpValues({
        totalPnl: Number((stats.totalPnl * progress).toFixed(1)),
        todayProfit: Number((stats.todayProfit * progress).toFixed(2)),
        winRate: Number((stats.winRate * progress).toFixed(1)),
        runningStrategies: Math.floor(stats.runningStrategies * progress)
      })

      if (currentStep >= steps) {
        clearInterval(timer)
      }
    }, stepDuration)

    return () => clearInterval(timer)
  }, [stats])

  const statCards = [
    {
      title: '总收益率',
      value: `${countUpValues.totalPnl > 0 ? '+' : ''}${countUpValues.totalPnl}%`,
      icon: TrendingUp,
      color: 'profit',
      change: '+2.1%'
    },
    {
      title: '今日收益',
      value: `$${formatNumber(countUpValues.todayProfit)}`,
      icon: DollarSign,
      color: 'profit',
      change: '+1.8%'
    },
    {
      title: '胜率',
      value: `${countUpValues.winRate}%`,
      icon: Target,
      color: 'profit',
      change: '稳定'
    },
    {
      title: '运行中策略',
      value: countUpValues.runningStrategies,
      icon: PlayCircle,
      color: 'primary',
      change: `${stats.totalStrategies} 个总计`
    }
  ]

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* 统计卡片 */}
      <div className="lg:col-span-2 grid grid-cols-2 gap-4">
        {statCards.map((card) => (
          <div
            key={card.title}
            className="bg-terminal-card border border-terminal-border rounded-xl p-6 card-hover-glow"
          >
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-terminal-muted mb-2">{card.title}</p>
                <p className={`text-3xl font-bold ${card.color === 'profit' ? 'profit-text' : 'text-primary'}`}>
                  {card.value}
                </p>
              </div>
              <div className="p-2 rounded-lg bg-terminal-bg">
                <card.icon className={`w-5 h-5 ${card.color === 'profit' ? 'text-profit' : 'text-primary'}`} />
              </div>
            </div>
            <div className="mt-4">
              <span className="text-xs px-2 py-1 rounded-full bg-terminal-bg text-terminal-muted">
                {card.change}
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* 资金曲线图 */}
      <div className="bg-terminal-card border border-terminal-border rounded-xl p-6 card-hover-glow">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h3 className="font-semibold">资金曲线</h3>
            <p className="text-sm text-terminal-muted">最近30天表现</p>
          </div>
          <div className="text-xs profit-text font-medium">
            峰值: ${formatNumber(Math.max(...equityData.map(d => d.equity)))}
          </div>
        </div>

        <div className="h-[200px]">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={equityData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis
                dataKey="date"
                stroke="#9CA3AF"
                fontSize={12}
                tickLine={false}
                axisLine={false}
              />
              <YAxis
                stroke="#9CA3AF"
                fontSize={12}
                tickLine={false}
                axisLine={false}
                tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#111827',
                  borderColor: '#374151',
                  borderRadius: '0.5rem',
                  color: '#F9FAFB'
                }}
                formatter={(value: number) => [`$${formatNumber(value)}`, '资金']}
              />
              <Line
                type="monotone"
                dataKey="equity"
                stroke="#10B981"
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4, fill: '#10B981' }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="mt-4 flex items-center justify-between text-sm">
          <div>
            <span className="text-terminal-muted">当前资金: </span>
            <span className="profit-text font-semibold">
              ${formatNumber(equityData[equityData.length - 1].equity)}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-profit rounded-full"></div>
            <span className="text-profit">+{((equityData[equityData.length - 1].equity - 1000000) / 1000000 * 100).toFixed(1)}%</span>
          </div>
        </div>
      </div>
    </div>
  )
}