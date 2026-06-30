/**
 * Data Service — fetches from Python API server ONLY. No mock fallbacks.
 *
 * Start the Python API:  python api_server.py   (→ http://localhost:8765)
 *
 * All functions return { data } on success or { error } on failure.
 */

import type { Strategy } from '@/types/strategy'

// 本地开发默认直连 localhost:8765
// Docker 构建时通过 NEXT_PUBLIC_API_URL= 覆盖为空（?? 不会回退空字符串）
const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8765'

// ---------------------------------------------------------------
// Types matching Python API responses
// ---------------------------------------------------------------

export interface StockSummary {
  code: string
  name: string
  isHolding: boolean
  pnlPct: number | null
  entryPrice: number | null
  currentPrice: number | null
  signalCount: number
  tradeCount: number
  lastDate: string
  stopLossPrice: number | null
  stopLossDate: string | null
}

export interface PriceBar {
  time: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

export interface SignalItem {
  time: string
  type: 'buy' | 'sell'
  price: number
  label: number | null
}

export interface TradeItem {
  entryTime: string
  exitTime: string | null
  entryPrice: number
  exitPrice: number | null
  pnlPct: number | null
  isHolding: boolean
}

export interface StockDetailResponse {
  stockCode: string
  strategyName: string
  priceData: PriceBar[]
  signals: SignalItem[]
  trades: TradeItem[]
  hasOpenPosition: boolean
  avmoodData?: { time: string; value: number }[] | null
  stats: {
    totalTrades: number
    winCount: number
    winRate: number
    totalPnlPct: number
    latestPrice: number
  }
}

export interface IndexBar {
  time: string
  open: number
  high: number
  low: number
  close: number
  volume: number
  marketCondition: 'trend_up' | 'trend_down' | 'range' | null
  probability: number | null
}

export interface MarketConditionResponse {
  indexCode: string
  indexName: string
  totalBars: number
  barsWithCondition: number
  conditionCounts: Record<string, number>
  latestBar: IndexBar | null
  bars: IndexBar[]
  avmoodData?: { time: string; value: number }[] | null
}

export interface IndexOverviewItem {
  code: string
  name: string
  latestClose: number
  prevClose: number
  change: number
  changePct: number
  latestDate: string
  marketCondition: 'trend_up' | 'trend_down' | 'range' | null
  probability: number | null
  /** Fuzzy MA avmood trend — only available when Python API is running */
  avmoodTrend?: string | null
  avmoodLatest?: number | null
}

export const MARKET_INDICES: { code: string; name: string }[] = [
  { code: '000001', name: '上证指数' },
  { code: '399006', name: '创业板指' },
]

type ApiResult<T> = { data: T; error?: undefined } | { data?: undefined; error: string }

// ---------------------------------------------------------------
// Internal fetch
// ---------------------------------------------------------------

async function apiFetch<T>(path: string): Promise<ApiResult<T>> {
  try {
    const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), 8000)
    const res = await fetch(`${API_BASE}${path}`, { signal: controller.signal })
    clearTimeout(timeout)

    if (!res.ok) {
      const text = await res.text().catch(() => '')
      return { error: `API ${path} → ${res.status}: ${text || res.statusText}` }
    }
    return { data: (await res.json()) as T }
  } catch (err: any) {
    if (err.name === 'AbortError') {
      return { error: `API 请求超时: ${API_BASE}${path}。请确认已启动 python api_server.py` }
    }
    return { error: `无法连接 API 服务器 (${API_BASE})。请先运行: python api_server.py` }
  }
}

// ---------------------------------------------------------------
// Public API — no mock fallbacks
// ---------------------------------------------------------------

export async function fetchStrategies(): Promise<ApiResult<Strategy[]>> {
  const result = await apiFetch<{ strategies: Strategy[] }>('/api/strategies')
  if (result.error) return result
  const strategies = result.data!.strategies || []
  return {
    data: strategies.map((s) => ({
      ...s,
      profitTrades: s.profitTrades || 0,
      lossTrades: s.lossTrades || 0,
      avgProfit: s.avgProfit || 0,
      avgLoss: s.avgLoss || 0,
      profitFactor: s.profitFactor || 0,
      createdAt: s.createdAt || '',
      updatedAt: s.updatedAt || '',
    })),
  }
}

export async function fetchStrategyStocks(strategyName: string): Promise<ApiResult<StockSummary[]>> {
  const result = await apiFetch<{ stocks: StockSummary[] }>(`/api/strategies/${strategyName}/stocks`)
  if (result.error) return result
  return { data: result.data!.stocks || [] }
}

export async function fetchStockDetail(
  strategyName: string,
  stockCode: string,
): Promise<ApiResult<StockDetailResponse>> {
  return apiFetch<StockDetailResponse>(`/api/strategies/${strategyName}/stocks/${stockCode}`)
}

export async function fetchMarketCondition(): Promise<ApiResult<MarketConditionResponse>> {
  // Prefer Python API; fall back to existing Next.js API route
  const result = await apiFetch<MarketConditionResponse>('/api/market-condition')
  if (!result.error) return result

  // Try the built-in Next.js API route (reads CSV directly)
  try {
    const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), 5000)
    const res = await fetch('/api/index-condition', { signal: controller.signal })
    clearTimeout(timeout)
    if (res.ok) return { data: (await res.json()) as MarketConditionResponse }
  } catch { /* ignore */ }

  return result // return original error
}

export async function fetchMarketConditionByCode(code: string): Promise<ApiResult<MarketConditionResponse>> {
  // Prefer Python API (provides avmood data); fall back to Next.js API route
  const result = await apiFetch<MarketConditionResponse>(`/api/market-condition?code=${code}`)
  if (!result.error) return result

  // Try the built-in Next.js dynamic API route (reads CSV directly, no avmood)
  try {
    const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), 8000)
    const res = await fetch(`/api/index-condition/${code}`, { signal: controller.signal })
    clearTimeout(timeout)
    if (res.ok) return { data: (await res.json()) as MarketConditionResponse }
    const text = await res.text().catch(() => '')
    return { error: `API /api/index-condition/${code} → ${res.status}: ${text || res.statusText}` }
  } catch (err: any) {
    if (err.name === 'AbortError') {
      return { error: `API 请求超时: /api/index-condition/${code}` }
    }
    return { error: `无法连接 API: ${err.message}` }
  }
}

export async function fetchMarketOverview(): Promise<ApiResult<IndexOverviewItem[]>> {
  // Prefer Python API (provides avmood data); fall back to Next.js API route
  const result = await apiFetch<{ indices: IndexOverviewItem[] }>('/api/market-overview')
  if (!result.error) return { data: result.data!.indices || [] }

  // Try the built-in Next.js API route (reads CSV directly, limited avmood)
  try {
    const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), 8000)
    const res = await fetch('/api/market-overview', { signal: controller.signal })
    clearTimeout(timeout)
    if (!res.ok) {
      const text = await res.text().catch(() => '')
      return { error: `API /api/market-overview → ${res.status}: ${text || res.statusText}` }
    }
    const json = await res.json()
    return { data: json.indices || [] }
  } catch (err: any) {
    if (err.name === 'AbortError') {
      return { error: 'API 请求超时: /api/market-overview' }
    }
    return { error: `无法连接 API: ${err.message}` }
  }
}
