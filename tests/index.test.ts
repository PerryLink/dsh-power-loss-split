import { readFile, readdir } from 'node:fs/promises'
import { dirname, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { describe, expect, it } from 'vitest'
import { loadRuleset } from '../src/shared/ruleset.ts'
import { numberOf, parseMaterial } from '../src/parse.ts'
import { runCheck } from '../src/check.ts'
import { buildView } from '../src/view.ts'
import { findForbiddenWording } from '../src/shared/wording.ts'
import { addDays, diffDays, parseWallClock } from '../src/shared/datetime.ts'
import { parseYaml } from '../src/shared/yaml.ts'
import { Config as ConfigSchema } from '../src/config.ts'
import { inject, name as pluginName, resolvePackageFile, TOOL_NAME } from '../src/index.ts'
import type { Report } from '../src/shared/report.ts'
import type { CheckOptions } from '../src/check.ts'

const here = dirname(fileURLToPath(import.meta.url))
const packageRoot = resolve(here, '..')
const rulesPath = join(packageRoot, 'rules', 'power-loss-split.yaml')
const fixturesRoot = join(here, 'fixtures')
const CHECKED_AT = '2026-10-06T00:00:00.000Z'

interface CaseFile {
  ruleId: string
  configure?: Record<string, Record<string, unknown>>
  pairs: { name: string; material: string; expect: { ruleId: string; count: number } }[]
}

async function loadPack() {
  return loadRuleset(await readFile(rulesPath, 'utf8'))
}

function runOptions(overrides: Partial<CheckOptions> = {}): CheckOptions {
  return { plugin: pluginName, checkedAt: CHECKED_AT, disabledRules: [], onlyRules: [], ...overrides }
}

function withConfiguration(ruleset: Awaited<ReturnType<typeof loadPack>>, configure: CaseFile['configure']) {
  if (configure === undefined) return ruleset
  return {
    ...ruleset,
    rules: ruleset.rules.map((rule) =>
      configure[rule.id] === undefined ? rule : { ...rule, params: { ...rule.params, ...configure[rule.id] } },
    ),
  }
}

async function runFixture(materialText: string, target: string, configure?: CaseFile['configure']): Promise<Report> {
  const ruleset = withConfiguration(await loadPack(), configure)
  return runCheck(parseMaterial(materialText, target), ruleset, runOptions())
}

function issuesOf(report: Report, ruleId: string) {
  return report.issues.filter((issue) => issue.ruleId === ruleId)
}

async function ruleDirectories(): Promise<string[]> {
  const entries = await readdir(fixturesRoot, { withFileTypes: true })
  return entries.filter((entry) => entry.isDirectory()).map((entry) => entry.name).sort()
}

async function readCases(directory: string): Promise<CaseFile> {
  return JSON.parse(await readFile(join(fixturesRoot, directory, 'cases.json'), 'utf8')) as CaseFile
}

const GOOD = { supplied: 120000, sold: 114000, loss: 6000, lossRate: 5 }

describe('rule pack', () => {
  it('declares a citable basis for every rule', async () => {
    const ruleset = await loadPack()
    expect(ruleset.plugin).toBe(pluginName)
    expect(ruleset.rules.length).toBeGreaterThanOrEqual(5)
    for (const rule of ruleset.rules) {
      expect(rule.basis.document, `${rule.id} document`).not.toBe('')
      expect(rule.basis.clause, `${rule.id} clause`).not.toBe('')
      expect(rule.basis.excerpt.length, `${rule.id} excerpt`).toBeGreaterThanOrEqual(8)
      expect(rule.basis.source, `${rule.id} source`).toMatch(/^https?:\/\//)
      expect(['direct', 'derived-from-principle', 'institutional-configuration']).toContain(rule.basis.kind)
    }
  })

  it('never lets a principle-derived or locally configured check be an error', async () => {
    const ruleset = await loadPack()
    for (const rule of ruleset.rules) {
      if (rule.basis.kind === 'derived-from-principle') expect(rule.severity, rule.id).not.toBe('error')
      if (rule.basis.kind === 'institutional-configuration') expect(rule.severity, rule.id).toBe('info')
    }
  })

  it('admits in every excerpt that no verbatim clause was obtained', async () => {
    const ruleset = await loadPack()
    for (const rule of ruleset.rules) {
      expect(rule.basis.excerpt, rule.id).toContain('本次未取得')
    }
    const source = await readFile(rulesPath, 'utf8')
    expect(source).toContain('**excerpt 一律不是引文。**')
    expect(source).toContain('取得标准正文后必须做两件事')
  })

  it('cites the standard whose table of contents was verified', async () => {
    const ruleset = await loadPack()
    for (const rule of ruleset.rules) {
      expect(rule.basis.number, rule.id).toBe('DL/T 686-2018')
    }
  })

  it('ships every locally-set threshold unconfigured', async () => {
    const ruleset = await loadPack()
    expect(ruleset.rules.find((rule) => rule.id === 'PL-003')?.params.maxRate).toBe(0)
    expect(ruleset.rules.find((rule) => rule.id === 'PL-005')?.params.maxUnbalancePercent).toBe(0)
    expect(ruleset.rules.find((rule) => rule.id === 'PL-003')?.basis.kind).toBe('institutional-configuration')
  })

  it('refuses a rule pack that overstates a principle-derived check', () => {
    const overstated = [
      'plugin: probe',
      'version: "0"',
      'rules:',
      '  - id: X-001',
      '    title: probe',
      '    severity: error',
      '    basis:',
      '      document: 《X》',
      '      number: X〔2020〕1号',
      '      clause: 第一条',
      '      excerpt: 这是一个足够长的逐字摘录示例。',
      '      kind: derived-from-principle',
      '      source: https://example.invalid/x',
    ].join('\n')
    expect(() => loadRuleset(overstated)).toThrow(/strongest permitted severity/)
  })
})

describe('paired fixtures', () => {
  it('has both a compliant and a violating sample for every rule', async () => {
    const ruleset = await loadPack()
    const covered = new Set<string>()
    for (const directory of await ruleDirectories()) {
      const cases = await readCases(directory)
      expect(cases.pairs.filter((pair) => pair.expect.count === 0).length, `${directory} compliant sample`).toBeGreaterThanOrEqual(1)
      expect(cases.pairs.filter((pair) => pair.expect.count > 0).length, `${directory} violating sample`).toBeGreaterThanOrEqual(1)
      for (const pair of cases.pairs) {
        const material = await readFile(join(fixturesRoot, directory, pair.material), 'utf8')
        const report = await runFixture(material, pair.material, cases.configure)
        const matched = issuesOf(report, cases.ruleId)
        expect(
          matched.length,
          `${directory}/${pair.name} expected ${pair.expect.count} × ${cases.ruleId}, got ${matched.map((issue) => issue.found).join(' | ')}`,
        ).toBe(pair.expect.count)
        covered.add(cases.ruleId)
      }
    }
    for (const rule of ruleset.rules) expect(covered.has(rule.id), `covered ${rule.id}`).toBe(true)
  })

  it('gives every issue a citable basis and a stable id', async () => {
    for (const directory of await ruleDirectories()) {
      const cases = await readCases(directory)
      for (const pair of cases.pairs) {
        const material = await readFile(join(fixturesRoot, directory, pair.material), 'utf8')
        const report = await runFixture(material, pair.material, cases.configure)
        for (const issue of report.issues) {
          expect(issue.basis).toContain('「')
          expect(issue.id).toMatch(/^dsh-power-loss-split\.PL-\d{3}\.[0-9a-f]{8}$/)
          expect(issue.found).not.toBe('')
          expect(issue.expected).not.toBe('')
        }
      }
    }
  })
})

describe('arithmetic reporting', () => {
  it('shows its working, so a reviewer can redo the sum', async () => {
    const ruleset = await loadPack()
    const report = runCheck(
      parseMaterial(JSON.stringify({ supplied: 1000, sold: 900, loss: 50 }), 'inline'),
      ruleset,
      runOptions(),
    )
    const issue = issuesOf(report, 'PL-001')[0]
    expect(issue?.found).toContain('1000 kWh')
    expect(issue?.found).toContain('900 kWh')
    expect(issue?.found).toContain('100 kWh')
    expect(issue?.found).toContain('50 kWh')
    expect(issue?.expected).toContain('允许偏差')
  })

  it('respects a configured tolerance instead of demanding an exact match', async () => {
    const ruleset = withConfiguration(await loadPack(), { 'PL-001': { toleranceKwh: 5 } })
    const report = runCheck(parseMaterial(JSON.stringify({ supplied: 1000, sold: 900, loss: 97 }), 'inline'), ruleset, runOptions())
    expect(issuesOf(report, 'PL-001')).toHaveLength(0)
  })

  it('reports a declared loss when no loss figure was given, without judging it', async () => {
    const ruleset = await loadPack()
    const report = runCheck(parseMaterial(JSON.stringify({ supplied: 1000, sold: 900 }), 'inline'), ruleset, runOptions())
    expect(issuesOf(report, 'PL-001')).toHaveLength(0)
    expect(report.skipped.find((entry) => entry.rule === 'PL-001')?.reason).toContain('推算为')
  })
})

describe('number reading', () => {
  it('accepts the shapes a spreadsheet export produces', () => {
    expect(numberOf('1,200.5')).toBe(1200.5)
    expect(numberOf('1200 kWh')).toBe(1200)
    expect(numberOf('１２３４')).toBe(1234)
    expect(numberOf('5%')).toBe(5)
    expect(numberOf('12.5万')).toBe(12.5)
    expect(numberOf('—')).toBeUndefined()
    expect(numberOf('')).toBeUndefined()
  })

  it('warns when a meter list has no energy column', () => {
    const input = parseMaterial(JSON.stringify({ supplied: 1, sold: 1, meters: [{ 名称: 'A' }] }), 'inline')
    expect(input.warnings.join(' ')).toContain('没有可识别的电量列')
  })

  it('warns when a meter list arrives without period totals', () => {
    const input = parseMaterial(JSON.stringify({ meters: [{ 名称: 'A', 电量: 10 }] }), 'inline')
    expect(input.warnings.join(' ')).toContain('没有供电量与售电量合计')
  })
})

describe('skipped reporting', () => {
  it('admits that the rate band cannot be checked without a configured ceiling', async () => {
    const report = await runFixture(JSON.stringify(GOOD), 'inline')
    expect(report.skipped.find((entry) => entry.rule === 'PL-003')?.reason).toContain('未配置 maxRate')
  })

  it('admits that the phase check needs three phases', async () => {
    const ruleset = await loadPack()
    const material = JSON.stringify({ supplied: 10, sold: 9, meters: [{ 名称: 'A', 电量: 5 }, { 名称: 'B', 电量: 4 }] })
    const report = runCheck(parseMaterial(material, 'inline'), ruleset, runOptions())
    expect(report.skipped.find((entry) => entry.rule === 'PL-005')?.reason).toContain('只提供了 2 个相别')
  })

  it('names disabled rules exactly once and appends the configured note', async () => {
    const ruleset = await loadPack()
    const input = parseMaterial(JSON.stringify(GOOD), 'inline')
    const report = runCheck(input, ruleset, runOptions({ disabledRules: ['PL-004'], skipNotes: '本机构口径' }))
    const entries = report.skipped.filter((item) => item.rule === 'PL-004')
    expect(entries).toHaveLength(1)
    expect(entries[0]?.reason).toContain('禁用')
    expect(entries[0]?.reason).toContain('本机构口径')
  })
})

describe('report rendering', () => {
  it('never uses adjudicating wording and always carries the disclaimer', async () => {
    const material = await readFile(join(fixturesRoot, 'PL-001', 'PL-001-unsafe.json'), 'utf8')
    const report = await runFixture(material, 'PL-001-unsafe.json')
    const view = buildView(report)
    expect(findForbiddenWording(view.markdown)).toEqual([])
    expect(view.markdown).toContain('免责声明')
    expect(view.markdown).toContain('未执行的检查')
    expect(JSON.parse(view.reportJson)).toMatchObject({ plugin: pluginName, summary: report.summary })
  })
})

describe('plugin contract', () => {
  it('declares a static inject array covering every service apply touches', () => {
    expect(Array.isArray(inject)).toBe(true)
    expect(inject).toContain('tools')
  })

  it('exposes a Schemastery Config with serializable defaults', () => {
    const resolved = ConfigSchema(null)
    expect(resolved.rulesFile).toBe('rules/power-loss-split.yaml')
    expect(resolved.disabledRules).toEqual([])
    expect(resolved.timeoutMs).toBeGreaterThan(0)
  })

  it('resolves the packaged rule pack and rejects a missing one', () => {
    expect(resolvePackageFile('rules/power-loss-split.yaml')).toBe(rulesPath)
    expect(() => resolvePackageFile('rules/does-not-exist.yaml')).toThrow(/未找到/)
  })

  it('names the tool after the package family convention', () => {
    expect(TOOL_NAME).toBe('power_loss_split')
  })
})

describe('material reader', () => {
  it('rejects empty material instead of reporting an empty result', () => {
    expect(() => parseMaterial('   ', 'inline')).toThrow(/材料为空/)
  })

  it('rejects material with no figures at all', () => {
    expect(() => parseMaterial('name: 某某线', 'inline')).toThrow(/无法执行检查/)
  })
})

describe('shared kit', () => {
  it('parses wall-clock timestamps and rejects impossible dates', () => {
    expect(parseWallClock('2026-03-15')).toEqual({ date: '2026-03-15', time: '00:00', hasTime: false, minutes: 0 })
    expect(parseWallClock('2026-02-30')).toBeUndefined()
  })

  it('does calendar arithmetic', () => {
    expect(addDays('2026-03-31', 1)).toBe('2026-04-01')
    expect(diffDays('2026-03-01', '2026-03-06')).toBe(5)
  })

  it('reads the supported YAML subset and rejects the rest', () => {
    expect(parseYaml('a: 1\nb:\n  - x\n')).toEqual({ a: 1, b: ['x'] })
    expect(() => parseYaml('a: 1\na: 2\n')).toThrow(/duplicate/)
  })
})
