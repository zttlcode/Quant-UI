import { NextResponse } from 'next/server'
import fs from 'fs'
import path from 'path'

// ── Index configuration ──────────────────────────────────────────

const DATA_ROOT = process.env.QUANT_UI_DATA_ROOT || 'D:\\github\\RobotMeQ_Dataset\\QuantData'

const INDICES: { code: string; name: string }[] = [
  { code: '000001', name: '上证指数' },
  { code: '399006', name: '创业板指' },
]

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
  avmoodTrend?: string | null
  avmoodLatest?: number | null
}

// ── Helpers ──────────────────────────────────────────────────────

function readLastTwoPriceLines(
  code: string
): { latest: { close: number; date: string }; prev: { close: number; date: string } } | null {
  const pricePath = path.join(DATA_ROOT, 'live_index', `live_bar_A_${code}_d.csv`)
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
  code: string
): { marketCondition: string; probability: number } | null {
  const conditionPath = path.join(DATA_ROOT, 'market_condition_live', `A_${code}_d.csv`)
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

    for (const idx of INDICES) {
      const priceData = readLastTwoPriceLines(idx.code)
      const conditionData = readLastConditionLine(idx.code)

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
        code: idx.code,
        name: idx.name,
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
    try {
      const avmoodResults = await Promise.allSettled(
        indices.map(async (idx) => {
          const controller = new AbortController()
          const timeout = setTimeout(() => controller.abort(), 5000)
          try {
            const res = await fetch(
              `http://localhost:8765/api/market-condition?code=${idx.code}`,
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
