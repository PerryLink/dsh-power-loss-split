/**
 * Pure check core: `(input, ruleset, options) => Report`.
 *
 * No plugin context, no I/O, no clock and no model access, so the whole rule set
 * is unit-testable without credentials. Every finding carries the verbatim clause
 * that produced it, and every check that could not run is reported in `skipped`.
 *
 * The arithmetic here is deliberately shown, not hidden: a finding says what the
 * numbers are and what the tolerance is, because a reviewer who cannot redo the
 * sum cannot judge the finding. Tolerances and thresholds come from the rule pack,
 * never from a constant in this file — the acceptable loss rate for a given line
 * is a local planning figure, not a national one.
 */

import { disabledAsSkipped, formatBasis } from './shared/rules.ts'
import { paramNumber, ruleById } from './shared/ruleset.ts'
import { issueId, makeReport } from './shared/report.ts'
import type { Issue, Locator, Report, Skipped } from './shared/report.ts'
import type { Ruleset } from './shared/rules.ts'
import type { LossInput } from './model.ts'

/** Options that come from the plugin configuration rather than the rule pack. */
export interface CheckOptions {
  plugin: string
  checkedAt: string
  disabledRules: readonly string[]
  onlyRules: readonly string[]
  skipNotes?: string
}

interface RuleContext {
  input: LossInput
  ruleset: Ruleset
  issues: Issue[]
  skipped: Skipped[]
  fired: Set<string>
  skipReasons: Map<string, string>
  add(ruleId: string, locator: Locator, found: string, expected: string, fix?: string): void
  skip(ruleId: string, reason: string): void
}

function makeAdd(context: Omit<RuleContext, 'add' | 'skip'>): RuleContext['add'] {
  return (ruleId, locator, found, expected, fix) => {
    const rule = ruleById(context.ruleset, ruleId)
    const issue: Issue = {
      id: issueId(context.ruleset.plugin, ruleId, locator),
      ruleId,
      severity: rule.severity,
      locator,
      found,
      expected,
      basis: formatBasis(rule.basis, rule.alsoBasis ?? []),
    }
    if (fix !== undefined) issue.fix = fix
    context.issues.push(issue)
    context.fired.add(ruleId)
  }
}

/** Format a kWh figure for the report without exponent noise. */
function kwh(value: number): string {
  return `${Number(value.toFixed(4))} kWh`
}

/** Format a percent figure for the report. */
function pct(value: number): string {
  return `${Number(value.toFixed(4))}%`
}

/** PL-001 — 供电量 = 售电量 + 线损电量. */
function checkBalance(context: RuleContext): void {
  const ruleId = 'PL-001'
  const rule = ruleById(context.ruleset, ruleId)
  const tolerance = paramNumber(rule, 'toleranceKwh', 0)
  const { supplied, sold, loss } = context.input
  if (supplied === undefined || sold === undefined) {
    context.skip(ruleId, '材料缺少供电量或售电量，无法核对量平衡')
    return
  }
  const derived = supplied - sold
  if (loss === undefined) {
    context.skip(
      ruleId,
      `材料未提供线损电量；按供电量与售电量推算为 ${kwh(derived)}，本条不判断该推算值是否为填报值`,
    )
    return
  }
  const gap = Math.abs(supplied - sold - loss)
  if (gap <= tolerance) return
  context.add(
    ruleId,
    { column: '线损电量' },
    `供电量 ${kwh(supplied)} − 售电量 ${kwh(sold)} = ${kwh(derived)}，与填报的线损电量 ${kwh(loss)} 相差 ${kwh(gap)}`,
    `线损电量应等于供电量减售电量，允许偏差 ${kwh(tolerance)}`,
    '核对三个数值的来源口径与抄表同期性；本条只做减法核对，不判断哪一个数值正确',
  )
}

/** PL-002 — 线损率 = 线损电量 / 供电量 × 100%. */
function checkRate(context: RuleContext): void {
  const ruleId = 'PL-002'
  const rule = ruleById(context.ruleset, ruleId)
  const tolerance = paramNumber(rule, 'tolerancePoints', 0)
  const { supplied, loss } = context.input
  if (context.input.lossRate === undefined) {
    context.skip(ruleId, '材料未提供线损率，无法核对其与电量的一致性')
    return
  }
  if (supplied === undefined || supplied === 0) {
    context.skip(ruleId, '材料缺少供电量（或供电量为 0），无法核对线损率')
    return
  }
  if (loss === undefined) {
    context.skip(ruleId, '材料缺少线损电量，无法核对线损率')
    return
  }
  const derived = (loss / supplied) * 100
  const gap = Math.abs(derived - context.input.lossRate)
  if (gap <= tolerance) return
  context.add(
    ruleId,
    { column: '线损率' },
    `线损电量 ${kwh(loss)} ÷ 供电量 ${kwh(supplied)} × 100% = ${pct(derived)}，与填报的线损率 ${pct(context.input.lossRate)} 相差 ${Number(gap.toFixed(4))} 个百分点`,
    `线损率应为线损电量与供电量之比，允许偏差 ${tolerance} 个百分点`,
    '核对线损率的计算口径（分母是否为供电量、是否含无损电量）；本条只做除法核对',
  )
}

/** PL-003 — the loss rate sits inside the configured band. */
function checkRateBand(context: RuleContext): void {
  const ruleId = 'PL-003'
  const rule = ruleById(context.ruleset, ruleId)
  const min = paramNumber(rule, 'minRate', 0)
  const max = paramNumber(rule, 'maxRate', 0)
  const rate = context.input.lossRate
  if (rate === undefined) {
    context.skip(ruleId, '材料未提供线损率')
    return
  }
  if (max <= 0) {
    context.skip(
      ruleId,
      '规则库未配置 maxRate：线损考核指标是按线路、按年下达的本机构指标，本插件不硬编码任何考核值',
    )
    return
  }
  if (rate < min || rate > max) {
    context.add(
      ruleId,
      { column: '线损率' },
      `线损率 ${pct(rate)} 超出本机构配置的区间 [${min}, ${max}]`,
      `按本机构配置，线损率应在 ${min}%~${max}% 之间`,
      '核对考核指标与本线路的实际口径；本条不判断该线损率是否合理',
    )
  }
}

/** PL-004 — the meter list sums to the declared sold energy. */
function checkMeterSum(context: RuleContext): void {
  const ruleId = 'PL-004'
  const rule = ruleById(context.ruleset, ruleId)
  const tolerance = paramNumber(rule, 'toleranceKwh', 0)
  const meters = context.input.meters.filter((meter) => meter.energy !== undefined)
  if (meters.length === 0) {
    context.skip(ruleId, '材料没有带电量数值的计量点，无法核对合计')
    return
  }
  const sum = meters.reduce((total, meter) => total + (meter.energy ?? 0), 0)
  const declared = context.input.sold ?? context.input.supplied
  const label = context.input.sold !== undefined ? '售电量' : '供电量'
  if (declared === undefined) {
    context.skip(ruleId, `材料未提供售电量或供电量，无法与 ${meters.length} 个计量点的合计核对`)
    return
  }
  const gap = Math.abs(sum - declared)
  if (gap <= tolerance) return
  context.add(
    ruleId,
    { column: '售电量' },
    `${meters.length} 个计量点电量合计 ${kwh(sum)}，与填报的${label} ${kwh(declared)} 相差 ${kwh(gap)}`,
    `计量点电量合计应与${label}一致，允许偏差 ${kwh(tolerance)}`,
    '核对是否有计量点遗漏、重复计入或抄表不同期；本条只做加法核对',
  )
}

/** PL-005 — three-phase currents are within the configured unbalance limit. */
function checkPhaseBalance(context: RuleContext): void {
  const ruleId = 'PL-005'
  const rule = ruleById(context.ruleset, ruleId)
  const limit = paramNumber(rule, 'maxUnbalancePercent', 0)
  const phases = ['A', 'B', 'C'].map((phase) => ({
    phase,
    value: context.input.meters.find((meter) => meter.name.trim().toUpperCase() === phase)?.energy,
  }))
  const present = phases.filter((entry): entry is { phase: string; value: number } => entry.value !== undefined)
  if (present.length === 0) {
    context.skip(ruleId, '材料中没有按 A/B/C 相命名的计量点，无法核对三相不平衡度')
    return
  }
  if (present.length < 3) {
    context.skip(ruleId, `材料只提供了 ${present.length} 个相别的数值（${present.map((entry) => entry.phase).join('、')}），无法核对三相不平衡度`)
    return
  }
  if (limit <= 0) {
    context.skip(ruleId, '规则库未配置 maxUnbalancePercent：三相不平衡度限值按电压等级与容量分档，本插件不硬编码')
    return
  }
  const values = present.map((entry) => entry.value)
  const max = Math.max(...values)
  const min = Math.min(...values)
  if (max === 0) {
    context.skip(ruleId, '三相数值均为 0，本条不适用')
    return
  }
  const unbalance = ((max - min) / max) * 100
  if (unbalance <= limit) return
  context.add(
    ruleId,
    { column: '三相电流' },
    `三相数值为 ${present.map((entry) => `${entry.phase}=${entry.value}`).join('、')}，不平衡度 ${pct(unbalance)} 超过配置上限 ${limit}%`,
    `三相不平衡度按 (最大值 − 最小值) ÷ 最大值 计算，应不超过 ${limit}%`,
    '核对计量点接带负荷情况；本条只按配置限值提示，不判断是否构成缺陷',
  )
}

const CHECKERS: readonly ((context: RuleContext) => void)[] = [
  checkBalance,
  checkRate,
  checkRateBand,
  checkMeterSum,
  checkPhaseBalance,
]

/**
 * Run the whole rule pack against one metering period.
 * @param input - normalized material.
 * @param ruleset - validated rule pack.
 * @param options - plugin identity, clock value and rule selection.
 * @returns the report, with `skipped` listing every check that did not run.
 */
export function runCheck(input: LossInput, ruleset: Ruleset, options: CheckOptions): Report {
  const disabled = new Set([...ruleset.disabled, ...options.disabledRules])
  const only = new Set(options.onlyRules)
  const base = {
    input,
    ruleset,
    issues: [] as Issue[],
    skipped: [] as Skipped[],
    fired: new Set<string>(),
    skipReasons: new Map<string, string>(),
  }
  const context: RuleContext = {
    ...base,
    add: makeAdd(base),
    skip: (ruleId, reason) => {
      base.skipReasons.set(ruleId, reason)
    },
  }

  for (const checker of CHECKERS) checker(context)

  const withNote = (reason: string): string => (options.skipNotes === undefined ? reason : `${reason}；${options.skipNotes}`)
  const skipped: Skipped[] = disabledAsSkipped(ruleset, [...disabled], withNote('该规则在当前配置中被禁用'))
  const already = new Set(skipped.map((entry) => entry.rule))
  for (const [ruleId, reason] of base.skipReasons) {
    if (already.has(ruleId)) continue
    if (disabled.has(ruleId) || (options.onlyRules.length > 0 && !only.has(ruleId))) continue
    skipped.push({ rule: ruleId, reason: withNote(reason) })
    already.add(ruleId)
  }
  for (const rule of ruleset.rules) {
    if (disabled.has(rule.id) || base.fired.has(rule.id) || already.has(rule.id)) continue
    if (options.onlyRules.length > 0 && !only.has(rule.id)) continue
    skipped.push({ rule: rule.id, reason: withNote('材料满足该检查的前置条件且未发现差异条目') })
  }
  if (options.onlyRules.length > 0) {
    const notSelected = ruleset.rules.filter((rule) => !only.has(rule.id) && !disabled.has(rule.id))
    if (notSelected.length > 0) {
      skipped.push({
        rule: notSelected.map((rule) => rule.id).join(','),
        reason: withNote(`本次调用通过 only 参数把执行范围限制为 ${[...only].join(', ')}，上列规则未执行`),
      })
    }
  }

  return makeReport({
    plugin: options.plugin,
    target: input.target,
    rulesetVersion: ruleset.version,
    checkedAt: options.checkedAt,
    issues: context.issues,
    skipped,
  })
}
