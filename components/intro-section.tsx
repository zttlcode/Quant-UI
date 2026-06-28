'use client'

import { SectionHeading } from '@/components/section-heading'
import { GlassCard } from '@/components/glass-card'
import { Brain, Network, Cog, TrendingUp } from 'lucide-react'

const FEATURES = [
  {
    icon: Brain,
    title: 'Meta-labeling',
    desc: '基于 Marcos López de Prado 理论，用次级模型过滤主策略的错误信号，有效降低假阳性率。',
    gradient: 'from-quant-cyan/20 to-blue-500/10',
  },
  {
    icon: Network,
    title: 'TimesNet Model',
    desc: '深度时序模型将 1D 时间序列转换为 2D 张量，捕捉多周期模式，实现高精度推理预测。',
    gradient: 'from-purple-500/20 to-quant-cyan/10',
  },
  {
    icon: Cog,
    title: 'Strategy Engine',
    desc: 'MACD 背离 + Triple Barrier 和模糊理论 + 贝叶斯寻优双策略驱动，覆盖不同市场状态。',
    gradient: 'from-quant-green/20 to-emerald-500/10',
  },
  {
    icon: TrendingUp,
    title: 'Live Trading',
    desc: '实盘信号记录与跟踪，AI 模型持续推理，实时更新策略表现与市场行情分类。',
    gradient: 'from-amber-500/20 to-quant-green/10',
  },
]

export function IntroSection() {
  return (
    <section id="intro" className="py-24 relative">
      <div className="container mx-auto px-4">
        <SectionHeading
          label="What is this?"
          title="AI 量化研究平台"
          subtitle="This platform combines Meta-labeling, Deep Time Series Models and Bayesian Optimization to generate robust trading decisions."
        />

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mt-12">
          {FEATURES.map((feature) => (
            <GlassCard key={feature.title} className="group text-center">
              <div className={`w-14 h-14 rounded-2xl bg-gradient-to-br ${feature.gradient} flex items-center justify-center mx-auto mb-4 border border-border group-hover:scale-110 transition-transform duration-300`}>
                <feature.icon className="w-7 h-7 text-quant-cyan" />
              </div>
              <h3 className="font-display font-semibold text-foreground mb-2">{feature.title}</h3>
              <p className="text-terminal-muted text-xs leading-relaxed">{feature.desc}</p>
            </GlassCard>
          ))}
        </div>
      </div>
    </section>
  )
}
