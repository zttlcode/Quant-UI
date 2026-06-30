import { NextResponse } from 'next/server'
import fs from 'fs'
import path from 'path'

// ── Index configuration ──────────────────────────────────────────

const DATA_ROOT = process.env.QUANT_UI_DATA_ROOT || 'D:\\github\\RobotMeQ_Dataset\\QuantData'

/** Known index name mapping. Key is the bare code (without market prefix). */
const INDEX_NAME_MAP: Record<string, string> = {
  '000001': '上证指数',
  '399006': '创业板指',
  '399001': '深证成指',
  '399005': '中小板指',
  '000016': '上证50',
  '000300': '沪深300',
  '000905': '中证500',
  '000852': '中证1000',
  '399673': '创业板50',
  'NDX': '纳斯达克100',
}

interface IndexEntry {
  code: string
  market: string
  name: string
}

/** Scan live_index/ directory for all available index CSV files.
 *  Parses filename live_bar_{market}_{code}_{level}.csv → extracts
 *  market and code separately. */
function scanAvailableIndices(): IndexEntry[] {
  const liveIndexDir = path.join(DATA_ROOT, 'live_index')
  if (!fs.existsSync(liveIndexDir)) return []

  const indices: IndexEntry[] = []
  try {
    const files = fs.readdirSync(liveIndexDir)
    // live_bar_{market}_{code}_{level}.csv
    // market = first segment, code = middle, level = last segment
    const re = /^live_bar_([^_]+)_(.+)_([^_]+)\.csv$/
    for (const f of files) {
      const m = f.match(re)
      if (m) {
        const market = m[1]
        const code = m[2]
        indices.push({
          code,
          market,
          name: INDEX_NAME_MAP[code] || `${market}:${code}`,
        })
      }
    }
  } catch {
    // fall through
  }

  // Sort by known indices first, then by code
  indices.sort((a, b) => {
    const aKnown = INDEX_NAME_MAP[a.code] ? 0 : 1
    const bKnown = INDEX_NAME_MAP[b.code] ? 0 : 1
    if (aKnown !== bKnown) return aKnown - bKnown
    return a.code.localeCompare(b.code)
  })

  return indices
}

export interface IndexOverviewItem {
  code: string
  market: string
  name: string
  latestClose: number
  prevClose: number
  change: number
  changePct: number
  latestDate: string
  marketCondition: 'trend_up' | 'trend_down' | 'range' | null
  probability: number | null
  avmoodTrend?: string | null
  avmoodLatest?: number | null
}

// ── Helpers ──────────────────────────────────────────────────────

function readLastTwoPriceLines(
  code: string, market: string
): { latest: { close: number; date: string }; prev: { close: number; date: string } } | null {
  const pricePath = path.join(DATA_ROOT, 'live_index', `live_bar_${market}_${code}_d.csv`)
  if (!fs.existsSync(pricePath)) return null

  try {
    const content = fs.readFileSync(pricePath, 'utf-8')
    const lines = content.trim().split('\n')
    // Need at least header + 1 data row
    if (lines.length < 2) return null

    const parseLine = (line: string) => {
      const parts = line.trim().split(',')
      return {
        date: parts[0].trim().substring(0, 10),
        open: parseFloat(parts[1]),
        high: parseFloat(parts[2]),
        low: parseFloat(parts[3]),
        close: parseFloat(parts[4]),
        volume: parseInt(parts[5], 10),
      }
    }

    const latest = parseLine(lines[lines.length - 1])
    const prev = lines.length >= 3 ? parseLine(lines[lines.length - 2]) : latest

    return {
      latest: { close: latest.close, date: latest.date },
      prev: { close: prev.close, date: prev.date },
    }
  } catch {
    return null
  }
}

function readLastConditionLine(
  code: string, market: string
): { marketCondition: string; probability: number } | null {
  const conditionPath = path.join(DATA_ROOT, 'market_condition_live', `${market}_${code}_d.csv`)
  if (!fs.existsSync(conditionPath)) return null

  try {
    const content = fs.readFileSync(conditionPath, 'utf-8')
    const lines = content.trim().split('\n')
    if (lines.length < 2) return null

    const lastLine = lines[lines.length - 1].trim()
    const parts = lastLine.split(',')
    if (parts.length < 4) return null

    return {
      marketCondition: parts[2].trim(),
      probability: parseFloat(parts[3]),
    }
  } catch {
    return null
  }
}

// ── avmood trend helper ─────────────────────────────────────────

function computeAvmoodTrend(
  avmoodData: { time: string; value: number }[] | null | undefined
): { trend: string; latest: number } | null {
  if (!avmoodData || avmoodData.length < 4) return null
  const vals = avmoodData.filter(a => a.value != null).map(a => a.value)
  if (vals.length < 4) return null
  const latest = vals[vals.length - 1]
  const prev3 = vals[vals.length - 4]
  const slope = latest - prev3
  const trend = slope > 0.005 ? '↑ Strengthening' : slope < -0.005 ? '↓ Weakening' : '→ Flat'
  return { trend, latest }
}


// ── Handler ──────────────────────────────────────────────────────

export async function GET() {
  try {
    const indices: IndexOverviewItem[] = []

    const INDICES = scanAvailableIndices()
    for (const idx of INDICES) {
      const { code, market, name } = idx
      const priceData = readLastTwoPriceLines(code, market)
      const conditionData = readLastConditionLine(code, market)

      if (!priceData) continue // skip indices with no data

      const latestClose = priceData.latest.close
      const prevClose = priceData.prev.close
      const change = latestClose - prevClose
      const changePct = prevClose !== 0 ? (change / prevClose) * 100 : 0

      let marketCondition: IndexOverviewItem['marketCondition'] = null
      let probability: number | null = null
      if (conditionData) {
        const mc = conditionData.marketCondition
        if (mc === 'trend_up' || mc === 'trend_down' || mc === 'range') {
          marketCondition = mc
        }
        probability = conditionData.probability
      }

      indices.push({
        code,
        market,
        name,
        latestClose,
        prevClose,
        change,
        changePct: Math.round(changePct * 100) / 100,
        latestDate: priceData.latest.date,
        marketCondition,
        probability,
      })
    }

    // ── Try to enrich with avmood trend from Python API ──
    const PYTHON_API = process.env.API_URL || 'http://localhost:8765'
    try {
      const avmoodResults = await Promise.allSettled(
        indices.map(async (idx) => {
          const controller = new AbortController()
          const timeout = setTimeout(() => controller.abort(), 5000)
          try {
            const res = await fetch(
              `${PYTHON_API}/api/market-condition?code=${idx.code}`,
              { signal: controller.signal }
            )
            clearTimeout(timeout)
            if (!res.ok) return null
            const json = await res.json()
            const avmood = json.avmoodData as { time: string; value: number }[] | null
            return computeAvmoodTrend(avmood)
          } catch {
            clearTimeout(timeout)
            return null
          }
        })
      )

      avmoodResults.forEach((result, i) => {
        if (result.status === 'fulfilled' && result.value) {
          indices[i].avmoodTrend = result.value.trend
          indices[i].avmoodLatest = result.value.latest
        }
      })
    } catch {
      // Python API not available — cards will show market condition instead
    }

    return NextResponse.json({ indices })
  } catch (error: any) {
    return NextResponse.json(
      { error: `读取行情概览失败: ${error.message}` },
      { status: 500 }
    )
  }
}
