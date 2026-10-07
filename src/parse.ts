/**
 * Reader for the line-loss material.
 *
 * The material is JSON or YAML: a header with the period's energy figures, plus
 * an optional `meters` list. Numbers are accepted as numbers or as strings with
 * thousands separators and units, because a spreadsheet export produces both.
 */

import { YamlSubsetError, parseYaml } from './shared/yaml.ts'
import type { LossInput, MeterRow } from './model.ts'

/** Raised when the material cannot be read at all. */
export class MaterialError extends Error {
  constructor(message: string) {
    super(message)
    this.name = 'MaterialError'
  }
}

/** Column names that hold the meter's name rather than its energy. */
const NAME_COLUMNS = ['名称', '表名', '计量点', '台区', '线路', 'name', 'meter']

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function text(value: unknown): string | undefined {
  if (value === undefined || value === null) return undefined
  if (typeof value === 'string') return value.trim() === '' ? undefined : value.trim()
  if (typeof value === 'number' && Number.isFinite(value)) return String(value)
  return undefined
}

/**
 * Read a number, tolerating the shapes a spreadsheet export produces:
 * thousands separators, a trailing unit, full-width digits, and a percent sign.
 * @returns the number, or undefined when the cell is not numeric.
 */
export function numberOf(value: unknown): number | undefined {
  if (typeof value === 'number') return Number.isFinite(value) ? value : undefined
  const raw = text(value)
  if (raw === undefined) return undefined
  const normalized = raw
    .replace(/[\uff10-\uff19]/g, (char) => String.fromCharCode(char.charCodeAt(0) - 0xfee0))
    .replace(/[,\s，]/g, '')
    .replace(/(kWh|kwh|KWH|千瓦时|kW·h|万kWh|万)/g, '')
    .replace(/%$/, '')
  if (!/^[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?$/.test(normalized)) return undefined
  return Number.parseFloat(normalized)
}

/** Pick the meter's name out of a row's raw values. */
function pickName(raw: Record<string, string>): string {
  for (const column of NAME_COLUMNS) {
    const value = raw[column]
    if (value !== undefined && value !== '') return value
  }
  return ''
}

function parseMeter(raw: unknown, index: number): MeterRow {
  if (!isRecord(raw)) throw new MaterialError(`meters[${index}] 必须是映射`)
  const texts: Record<string, string> = {}
  const numbers: Record<string, number> = {}
  for (const [key, value] of Object.entries(raw)) {
    const rendered = text(value)
    if (rendered !== undefined) texts[key] = rendered
    const parsed = numberOf(value)
    if (parsed !== undefined) numbers[key] = parsed
  }
  const row: MeterRow = {
    row: index + 1,
    name: pickName(texts),
    fields: numbers,
    raw: texts,
  }
  const declared = numberOf(raw.row)
  if (declared !== undefined && Number.isInteger(declared)) row.row = declared
  const single = numbers.电量 ?? numbers.energy ?? numbers.抄见电量
  if (single !== undefined) row.energy = single
  return row
}

/**
 * Parse material into the normalized input contract.
 * @param source - JSON or YAML text.
 * @param target - description of where the material came from.
 * @returns the normalized input.
 */
export function parseMaterial(source: string, target: string): LossInput {
  const trimmed = source.trim()
  if (trimmed === '') throw new MaterialError('材料为空')
  let document: unknown
  if (trimmed.startsWith('{') || trimmed.startsWith('[')) {
    try {
      document = JSON.parse(trimmed)
    } catch (error) {
      throw new MaterialError(`JSON 无法解析：${error instanceof Error ? error.message : String(error)}`)
    }
  } else {
    try {
      document = parseYaml(trimmed)
    } catch (error) {
      if (error instanceof YamlSubsetError) throw new MaterialError(`YAML 无法解析：${error.message}`)
      throw error
    }
  }
  if (!isRecord(document)) throw new MaterialError('材料根节点必须是映射')

  const warnings: string[] = []
  const input: LossInput = { target, meters: [], warnings }

  const name = text(document.name ?? document.title ?? document.线路名称)
  if (name !== undefined) input.name = name

  const supplied = numberOf(document.supplied ?? document.供电量 ?? document.供电)
  if (supplied !== undefined) input.supplied = supplied
  const sold = numberOf(document.sold ?? document.售电量 ?? document.售电)
  if (sold !== undefined) input.sold = sold
  const loss = numberOf(document.loss ?? document.线损电量 ?? document.损失电量)
  if (loss !== undefined) input.loss = loss
  const lossRate = numberOf(document.lossRate ?? document.线损率)
  if (lossRate !== undefined) input.lossRate = lossRate
  const capacity = numberOf(document.capacity ?? document.容量)
  if (capacity !== undefined) input.capacity = capacity
  const days = numberOf(document.days ?? document.天数)
  if (days !== undefined) input.days = days

  const meters = document.meters ?? document.计量点 ?? document.rows
  if (meters !== undefined && meters !== null) {
    if (!Array.isArray(meters)) throw new MaterialError('meters 必须是列表')
    input.meters = meters.map((entry, index) => parseMeter(entry, index))
  }

  const hasAny =
    input.supplied !== undefined ||
    input.sold !== undefined ||
    input.loss !== undefined ||
    input.lossRate !== undefined ||
    input.meters.length > 0
  if (!hasAny) {
    throw new MaterialError('材料中没有供电量、售电量、线损电量、线损率或计量点列表，无法执行检查')
  }
  if (input.meters.length > 0 && input.supplied === undefined && input.sold === undefined) {
    warnings.push('材料提供了计量点列表但没有供电量与售电量合计，部分平衡检查将无法执行')
  }
  if (input.meters.length > 0) {
    const withoutEnergy = input.meters.filter((meter) => meter.energy === undefined).length
    if (withoutEnergy > 0) {
      warnings.push(`有 ${withoutEnergy} 个计量点没有可识别的电量列，这些行不参与合计核对`)
    }
  }

  return input
}
