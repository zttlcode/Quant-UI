import { NextResponse } from 'next/server'
import fs from 'fs'

// ── Index metadata ──────────────────────────────────────────────

const DATA_ROOT = 'D:\\github\\RobotMeQ_Dataset\\QuantData'

const INDEX_NAMES: Record<string, string> = {
  '000001': '上证指数',
  '399006': '创业板指',
}

// ── Shared types ─────────────────────────────────────────────────

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

// ── CSV parsers ──────────────────────────────────────────────────

function parsePriceCsv(content: string): Map<string, Omit<IndexBar, 'marketCondition' | 'probability'>> {
  const map = new Map<string, Omit<IndexBar, 'marketCondition' | 'probability'>>()
  const lines = content.trim().split('\n')
  for (let i = 1; i < lines.length; i++) {
    const line = lines[i].trim()
    if (!line) continue
    const parts = line.split(',')
    if (parts.length < 6) continue
    const dateStr = parts[0].trim().substring(0, 10)
    map.set(dateStr, {
      time: dateStr,
      open: parseFloat(parts[1]),
      high: parseFloat(parts[2]),
      low: parseFloat(parts[3]),
      close: parseFloat(parts[4]),
      volume: parseInt(parts[5], 10),
    })
  }
  return map
}

function parseConditionCsv(content: string): Map<string, { marketCondition: IndexBar['marketCondition']; probability: number }> {
  const map = new Map<string, { marketCondition: IndexBar['marketCondition']; probability: number }>()
  const lines = content.trim().split('\n')
  for (let i = 1; i < lines.length; i++) {
    const line = lines[i].trim()
    if (!line) continue
    const parts = line.split(',')
    if (parts.length < 4) continue
    const dateStr = parts[0].trim()
    const condition = parts[2].trim() as IndexBar['marketCondition']
    const probability = parseFloat(parts[3])
    map.set(dateStr, { marketCondition: condition, probability })
  }
  return map
}

// ── Handler ──────────────────────────────────────────────────────

export async function GET(
  _request: Request,
  { params }: { params: { code: string } }
) {
  const code = params.code
  const indexName = INDEX_NAMES[code] || code

  const pricePath = `${DATA_ROOT}\\live_index\\live_bar_A_${code}_d.csv`
  const conditionPath = `${DATA_ROOT}\\market_condition_live\\A_${code}_d.csv`

  try {
    // Read price data
    if (!fs.existsSync(pricePath)) {
      return NextResponse.json(
        { error: `价格数据文件不存在: ${pricePath}` },
        { status: 404 }
      )
    }
    const priceContent = fs.readFileSync(pricePath, 'utf-8')
    const priceMap = parsePriceCsv(priceContent)

    // Read condition data
    let conditionMap = new Map<string, { marketCondition: IndexBar['marketCondition']; probability: number }>()
    if (fs.existsSync(conditionPath)) {
      const conditionContent = fs.readFileSync(conditionPath, 'utf-8')
      conditionMap = parseConditionCsv(conditionContent)
    }

    // Merge
    const bars: IndexBar[] = []
    priceMap.forEach((priceData, dateStr) => {
      const conditionData = conditionMap.get(dateStr)
      bars.push({
        ...priceData,
        marketCondition: conditionData?.marketCondition ?? null,
        probability: conditionData?.probability ?? null,
      })
    })

    bars.sort((a, b) => a.time.localeCompare(b.time))

    const latestBar = bars.length > 0 ? bars[bars.length - 1] : null
    const barsWithCondition = bars.filter(b => b.marketCondition !== null)
    const conditionCounts = {
      trend_up: barsWithCondition.filter(b => b.marketCondition === 'trend_up').length,
      trend_down: barsWithCondition.filter(b => b.marketCondition === 'trend_down').length,
      range: barsWithCondition.filter(b => b.marketCondition === 'range').length,
    }

    return NextResponse.json({
      indexCode: code,
      indexName,
      totalBars: bars.length,
      barsWithCondition: barsWithCondition.length,
      conditionCounts,
      latestBar,
      bars,
    })
  } catch (error: any) {
    return NextResponse.json(
      { error: `读取数据失败: ${error.message}` },
      { status: 500 }
    )
  }
}
