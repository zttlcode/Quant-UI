import Link from 'next/link'
import { ArrowLeft } from 'lucide-react'
import { SectionHeading } from '@/components/section-heading'
import { GlassCard } from '@/components/glass-card'
import { ContactSection } from '@/components/contact-section'

export default function AboutPage() {
  return (
    <div className="container mx-auto px-4 py-12">
      {/* Back */}
      <Link href="/" className="inline-flex items-center gap-2 text-terminal-muted hover:text-quant-cyan transition-colors text-sm mb-8">
        <ArrowLeft className="w-4 h-4" />
        Back to Research
      </Link>

      <SectionHeading
        label="About"
        title="关于项目"
        subtitle="AI Quant Research Platform — 一个人工智能量化交易研究平台。"
        align="left"
      />

      {/* Project Intro */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mt-8 mb-16">
        <GlassCard variant="subtle" className="p-6">
          <h2 className="font-display font-semibold text-lg text-foreground mb-4">项目背景</h2>
          <div className="space-y-3 text-sm text-terminal-muted leading-relaxed">
            <p>
              本平台的理论框架借鉴了 <strong className="text-foreground">Marcos López de Prado</strong> 在其 2018 年著作
              《Advances in Financial Machine Learning》中阐述的 Meta-labeling 方法。
            </p>
            <p>
              Meta-labeling 的核心思想是：先由主策略（Primary Model）生成候选交易信号，再由次级模型（Secondary Model）
              对信号质量进行二次判断。这种架构有效过滤了假阳性信号，显著提升策略的夏普比率与胜率。
            </p>
            <p>
              在此基础上，我们引入了 <strong className="text-quant-cyan">TimesNet</strong>（ICLR 2023）作为深度时序推理引擎，
              将 1D 时间序列转换为 2D 张量，通过跨周期卷积捕捉多尺度时序模式，实现了对市场状态的高精度建模。
            </p>
          </div>
        </GlassCard>

        <GlassCard variant="subtle" className="p-6">
          <h2 className="font-display font-semibold text-lg text-foreground mb-4">策略体系</h2>
          <div className="space-y-4">
            <div className="p-4 rounded-xl bg-quant-cyan/5 border border-quant-cyan/10">
              <h3 className="font-mono font-semibold text-quant-cyan text-sm mb-1">Strategy 1</h3>
              <p className="text-foreground font-medium mb-1">MACD 背离 + Triple Barrier Method</p>
              <p className="text-xs text-terminal-muted">
                利用 MACD 指标捕捉价格与指标的背离信号，结合 Triple Barrier Method
                （止盈/止损/时间三重屏障）进行标签化训练，最终由 TimesNet 模型推理产生交易信号。
              </p>
            </div>
            <div className="p-4 rounded-xl bg-purple-500/5 border border-purple-500/10">
              <h3 className="font-mono font-semibold text-purple-400 text-sm mb-1">Strategy 2</h3>
              <p className="text-foreground font-medium mb-1">模糊理论 + 目标导向贝叶斯寻优</p>
              <p className="text-xs text-terminal-muted">
                将市场特征通过模糊隶属度函数进行非线性变换，结合贝叶斯优化在参数空间中
                高效搜索最优策略配置，最终由 TimesNet 模型进行信号层面的推理与决策。
              </p>
            </div>
          </div>
        </GlassCard>
      </div>

      {/* Tech Stack */}
      <GlassCard variant="subtle" className="p-6 mb-16">
        <h2 className="font-display font-semibold text-lg text-foreground mb-4">技术栈</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { category: 'Frontend', items: ['Next.js 14', 'React 18', 'Tailwind CSS', 'Three.js'] },
            { category: 'Visualization', items: ['ECharts', 'Recharts', 'React Three Fiber', 'tsParticles'] },
            { category: 'AI / ML', items: ['TimesNet', 'PyTorch', 'Meta-labeling', 'Bayesian Opt'] },
            { category: 'Backend', items: ['Python', 'Pandas', 'Plotly', 'Streamlit'] },
          ].map((stack) => (
            <div key={stack.category}>
              <p className="text-xs font-mono text-quant-cyan mb-2 tracking-wider">{stack.category}</p>
              <ul className="space-y-1">
                {stack.items.map((item) => (
                  <li key={item} className="text-sm text-terminal-muted">{item}</li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </GlassCard>

      {/* Contact (reuse section) */}
      <ContactSection />
    </div>
  )
}
