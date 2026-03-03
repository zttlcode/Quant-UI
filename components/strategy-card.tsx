import { Strategy } from '@/types/strategy'
import { TrendingUp, TrendingDown, Activity, BarChart3, Target, Zap } from 'lucide-react'

interface StrategyCardProps {
  strategy: Strategy
}

export default function StrategyCard({ strategy }: StrategyCardProps) {
  const getStatusColor = (status: Strategy['status']) => {
    switch (status) {
      case 'running': return 'profit'
      case 'paused': return 'yellow'
      case 'stopped': return 'loss'
      case 'backtesting': return 'blue'
      default: return 'gray'
    }
  }

  const getStatusText = (status: Strategy['status']) => {
    switch (status) {
      case 'running': return '运行中'
      case 'paused': return '已暂停'
      case 'stopped': return '已停止'
      case 'backtesting': return '回测中'
      default: return '未知'
    }
  }

  const statItems = [
    {
      label: 'Sharpe',
      value: strategy.sharpe.toFixed(2),
      icon: BarChart3,
      color: strategy.sharpe >= 2 ? 'profit' : strategy.sharpe >= 1 ? 'yellow' : 'loss'
    },
    {
      label: '最大回撤',
      value: `${strategy.maxDrawdown.toFixed(1)}%`,
      icon: TrendingDown,
      color: strategy.maxDrawdown <= 10 ? 'profit' : strategy.maxDrawdown <= 20 ? 'yellow' : 'loss'
    },
    {
      label: '胜率',
      value: `${strategy.winRate.toFixed(1)}%`,
      icon: Target,
      color: strategy.winRate >= 70 ? 'profit' : strategy.winRate >= 60 ? 'yellow' : 'loss'
    }
  ]

  return (
    <div className="bg-terminal-card border border-terminal-border rounded-xl p-6 card-hover-glow hover:scale-[1.02] transition-all duration-300">
      {/* 头部 */}
      <div className="flex items-start justify-between mb-4">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <h3 className="font-bold text-lg">{strategy.name}</h3>
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${
              getStatusColor(strategy.status) === 'profit' ? 'bg-profit/10 text-profit' :
              getStatusColor(strategy.status) === 'loss' ? 'bg-loss/10 text-loss' :
              getStatusColor(strategy.status) === 'yellow' ? 'bg-yellow-500/10 text-yellow-500' :
              'bg-blue-500/10 text-blue-500'
            }`}>
              {getStatusText(strategy.status)}
            </span>
          </div>
          <p className="text-sm text-terminal-muted">{strategy.description}</p>
        </div>
        <div className={`text-2xl font-bold ${strategy.pnl >= 0 ? 'profit-text' : 'loss-text'}`}>
          {strategy.pnl >= 0 ? '+' : ''}{strategy.pnl.toFixed(1)}%
        </div>
      </div>

      {/* 市场标签 */}
      <div className="flex flex-wrap gap-2 mb-6">
        {strategy.markets.map((market) => (
          <span
            key={market}
            className="px-3 py-1 bg-terminal-bg border border-terminal-border rounded-lg text-sm"
          >
            {market}
          </span>
        ))}
      </div>

      {/* 统计指标 */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        {statItems.map((item) => (
          <div key={item.label} className="text-center">
            <div className={`flex items-center justify-center gap-1 mb-1 ${
              item.color === 'profit' ? 'text-profit' :
              item.color === 'loss' ? 'text-loss' :
              'text-yellow-500'
            }`}>
              <item.icon className="w-4 h-4" />
              <span className="font-bold">{item.value}</span>
            </div>
            <div className="text-xs text-terminal-muted">{item.label}</div>
          </div>
        ))}
      </div>

      {/* 交易统计 */}
      <div className="pt-4 border-t border-terminal-border">
        <div className="flex items-center justify-between text-sm">
          <div className="flex items-center gap-4">
            <div>
              <div className="font-semibold">{strategy.totalTrades}</div>
              <div className="text-xs text-terminal-muted">总交易数</div>
            </div>
            <div>
              <div className="font-semibold profit-text">{strategy.profitTrades}</div>
              <div className="text-xs text-terminal-muted">盈利交易</div>
            </div>
            <div>
              <div className="font-semibold loss-text">{strategy.lossTrades}</div>
              <div className="text-xs text-terminal-muted">亏损交易</div>
            </div>
          </div>
          <div className="text-right">
            <div className="font-semibold">{strategy.profitFactor.toFixed(2)}</div>
            <div className="text-xs text-terminal-muted">盈亏比</div>
          </div>
        </div>
      </div>

      {/* 底部信息 */}
      <div className="mt-4 pt-4 border-t border-terminal-border flex items-center justify-between text-xs text-terminal-muted">
        <div>创建: {strategy.createdAt}</div>
        <div className="flex items-center gap-1">
          <Activity className="w-3 h-3" />
          更新: {strategy.updatedAt}
        </div>
      </div>
    </div>
  )
}