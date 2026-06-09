import { NextResponse } from 'next/server'
import fs from 'fs'
import path from 'path'

// CSV 文件路径
const PRICE_CSV_PATH = 'D:\\github\\RobotMeQ_Dataset\\QuantData\\live_index\\live_bar_A_000001_d.csv'
const CONDITION_CSV_PATH = 'D:\\github\\RobotMeQ_Dataset\\QuantData\\market_condition_live\\A_000001_d.csv'

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

function parsePriceCsv(content: string): Map<string, Omit<IndexBar, 'marketCondition' | 'probability'>> {
  const map = new Map()
  const lines = content.trim().split('\n')
  // 跳过 header 行
  for (let i = 1; i < lines.length; i++) {
    const line = lines[i].trim()
    if (!line) continue
    const parts = line.split(',')
    if (parts.length < 6) continue
    const timeStr = parts[0].trim()
    // 提取日期部分 (YYYY-MM-DD)，去掉时间
    const dateStr = timeStr.substring(0, 10)
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
  const map = new Map()
  const lines = content.trim().split('\n')
  // 跳过 header 行
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

export async function GET() {
  try {
    // 读取价格数据
    if (!fs.existsSync(PRICE_CSV_PATH)) {
      return NextResponse.json(
        { error: `价格数据文件不存在: ${PRICE_CSV_PATH}` },
        { status: 404 }
      )
    }
    const priceContent = fs.readFileSync(PRICE_CSV_PATH, 'utf-8')
    const priceMap = parsePriceCsv(priceContent)

    // 读取行情分类数据
    if (!fs.existsSync(CONDITION_CSV_PATH)) {
      return NextResponse.json(
        { error: `行情分类数据文件不存在: ${CONDITION_CSV_PATH}` },
        { status: 404 }
      )
    }
    const conditionContent = fs.readFileSync(CONDITION_CSV_PATH, 'utf-8')
    const conditionMap = parseConditionCsv(conditionContent)

    // 合并数据：以价格数据为准，将分类数据按日期匹配
    const bars: IndexBar[] = []
    priceMap.forEach((priceData, dateStr) => {
      const conditionData = conditionMap.get(dateStr)
      bars.push({
        ...priceData,
        marketCondition: conditionData?.marketCondition ?? null,
        probability: conditionData?.probability ?? null,
      })
    })

    // 按时间排序
    bars.sort((a, b) => a.time.localeCompare(b.time))

    // 计算汇总信息
    const latestBar = bars[bars.length - 1]
    const barsWithCondition = bars.filter(b => b.marketCondition !== null)
    const conditionCounts = {
      trend_up: barsWithCondition.filter(b => b.marketCondition === 'trend_up').length,
      trend_down: barsWithCondition.filter(b => b.marketCondition === 'trend_down').length,
      range: barsWithCondition.filter(b => b.marketCondition === 'range').length,
    }

    return NextResponse.json({
      indexCode: '000001',
      indexName: '上证指数',
      totalBars: bars.length,
      barsWithCondition: barsWithCondition.length,
      conditionCounts,
      latestBar: bars[bars.length - 1] ?? null,
      bars,
    })
  } catch (error: any) {
    return NextResponse.json(
      { error: `读取数据失败: ${error.message}` },
      { status: 500 }
    )
  }
}
