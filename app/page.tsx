import HeroStats from '@/components/hero-stats'
import StrategyCard from '@/components/strategy-card'
import MarketChart from '@/components/market-chart'
import PerformanceDashboard from '@/components/performance-dashboard'
import IndexConditionChart from '@/components/index-condition-chart'
import { strategies, marketData, tradeSignals } from '@/lib/mock-data'

export default function Home() {
  return (
    <div className="space-y-8">
      {/* Hero 总览 */}
      <section>
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-3xl font-bold">量化策略实盘展示平台</h1>
          <div className="flex items-center gap-2">
            <span className="px-3 py-1 bg-profit/10 text-profit rounded-full text-sm font-medium flex items-center gap-2">
              <span className="w-2 h-2 bg-profit rounded-full animate-pulse"></span>
              LIVE 实时更新
            </span>
          </div>
        </div>
        <HeroStats />
      </section>

      {/* AI 指数行情分类 */}
      <section>
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-2xl font-bold">AI 指数行情分类</h2>
            <p className="text-sm text-terminal-muted mt-1">
              基于深度学习模型实时预测指数行情状态（趋势上涨 / 趋势下跌 / 震荡）
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="px-3 py-1 bg-primary/10 text-primary rounded-full text-sm font-medium flex items-center gap-2">
              <span className="w-2 h-2 bg-primary rounded-full animate-pulse" />
              AI 实时推理
            </span>
          </div>
        </div>
        <IndexConditionChart />
      </section>

      {/* 策略列表 */}
      <section>
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold">策略列表</h2>
          <div className="text-terminal-muted">
            <span className="profit-text font-semibold">{strategies.filter(s => s.status === 'running').length}</span> 个运行中策略
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {strategies.map((strategy) => (
            <StrategyCard key={strategy.id} strategy={strategy} />
          ))}
        </div>
      </section>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* 全球市场行情模块 */}
        <section className="lg:col-span-1">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold">全球市场行情</h2>
            <div className="text-sm text-terminal-muted">
              数据更新: <span className="text-profit">实时</span>
            </div>
          </div>
          <div className="space-y-6">
            {marketData.map((market) => (
              <MarketChart
                key={market.id}
                market={market}
                signals={tradeSignals.filter(s => s.marketId === market.id)}
              />
            ))}
          </div>
        </section>

        {/* 策略对比仪表盘 */}
        <section className="lg:col-span-1">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold">策略对比仪表盘</h2>
            <div className="text-sm text-terminal-muted">
              按 Sharpe 比率排序
            </div>
          </div>
          <PerformanceDashboard strategies={strategies} />
        </section>
      </div>
    </div>
  )
}