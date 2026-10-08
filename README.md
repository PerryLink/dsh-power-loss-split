# dsh-power-loss-split — Line-loss energy split and assessment-table check

`dsh-power-loss-split` reads one metering period for one line or transformer district — 供电量, 售电量, the declared 线损电量 and 线损率 and, when the material carries one, the list of metering points — and does arithmetic and interval checks on that material: the energy balance, the loss rate, the sum of the metering points, the loss-rate band you configure and the three-phase unbalance. Every finding carries the numbers and the tolerance it used, so a reviewer can redo the sum, and every check that could not run is listed in `skipped` instead of passing silently.

## What it answers

| You ask | What it answers |
|---|---|
| The declared 线损电量 does not match 供电量 − 售电量. Which of the three figures is wrong? | `PL-001` will not say. It reports the gap — `供电量 1000 kWh − 售电量 900 kWh = 100 kWh，与填报的线损电量 50 kWh 相差 50 kWh` — and compares it with the tolerance `toleranceKwh`, which ships at 0, so the three figures must agree exactly (report in 万 kWh and a rounding difference survives, so configure a non-zero tolerance). The rule only does the subtraction: it does not decide which of the three values is correct and does not check whether the readings are from the same period (抄表同期性). |
| 线损率 is filled in as 5.00%, but 线损电量 ÷ 供电量 gives 6.25%. Is the denominator the problem? | `PL-002` shows the division: it computes 线损电量 ÷ 供电量 × 100 and reports the gap in 个百分点 against the declared rate, allowing `tolerancePoints` 0.01 个百分点 for rounding — the rounding rules themselves are cited separately, from GB/T 8170-2008, whose verbatim text this pack also does not have. It does not judge whether the denominator's caliber is right (口径, e.g. whether 无损电量 should be deducted): that has to be stated in the material or configured. |
| Our line's loss rate looks high to me. Will the tool flag it? | Not on its own. `PL-003` compares the 线损率 only with the band you configure (`minRate` / `maxRate`); both ship at 0, meaning unconfigured, and then the rule is listed in `skipped` with its reason instead of passing silently. Even configured, it is capped at `info`: a hit means the rate is outside the band you set, not that the loss is abnormal. The assessment target is issued per line and per year by your own institution, so no target value is hard-coded. |
| The list of metering points sums to less than the declared 售电量. Is a metering point missing? | `PL-004` reports the gap and nothing more: it adds the metering points that carry an energy value and compares the total with the declared 售电量 — or with 供电量 when no 售电量 is given — allowing `toleranceKwh` (0 by default). An omitted metering point, one counted twice and readings taken at different times (抄表不同期) all produce the same gap, so the cause must be checked by hand; the rule only does the addition. |
| The sheet carries only A-phase and B-phase values. What does the unbalance check do? | `PL-005` lists itself in `skipped`: it needs metering points named A, B and C, and with fewer than three phase values it cannot run. Even with all three, the limit `maxUnbalancePercent` ships unconfigured (0) and the rule goes to `skipped` again. Once you set a limit it computes (最大值 − 最小值) ÷ 最大值, prints that formula with the finding, and is capped at `info` — it does not judge whether the unbalance constitutes a defect (是否构成缺陷). |

## Standards it follows

| Document | Number | Cited by rules |
|---|---|---|
| 《电力网电能损耗计算导则》 | DL/T 686-2018 | PL-001, PL-002, PL-003, PL-004, PL-005 |
| 《数值修约规则与极限数值的表示和判定》 | GB/T 8170-2008 | PL-002 |

**Boundary:** this plugin does **arithmetic and interval checks** on one metering period's line-loss
figures — the energy balance, the loss rate, the meter-list sum, the phase unbalance — and shows its
working in every finding. It is not a metering or metering-fault tool (there is no probe, no AMI
integration, no hardware model) and it does not decide whether a loss figure is reasonable or whether
tampering occurred. It reads a spreadsheet export and reports which sums do not close.

> ### ⚠️ Read this before trusting a citation in the report
>
> **Every `excerpt` in this plugin's rule pack says, in so many words, that the clause text was not
> obtained.** The two relations the plugin checks — 线损电量 = 供电量 − 售电量 and
> 线损率 = 线损电量 ÷ 供电量 × 100 — are **definitional**, and their normative home is
> **DL/T 686-2018《电力网电能损耗计算导则》**. That standard is **in force**, and its table of
> contents was verified (chapter 3 is 术语和定义, chapter 8 is 电力网电能损耗分析与降损措施效果计算),
> but **its body is not published for free**, so no verbatim clause could be read.
>
> Rather than paraphrase a quotation, this pack states the gap outright in the `excerpt` field and puts
> the honest reasoning in `note`. Everything is therefore capped at `warn` (principle-derived) or `info`
> (locally configured), and a test asserts that no rule claims a quotation it does not have. **When the
> standard text is in hand, two things must be done: replace each `excerpt` with the real clause, and
> raise `kind` to `direct`.** Until then a finding means "these two numbers do not close", not
> "you violated a standard".
>
> **Assessment thresholds are yours, not the standard's.** Line-loss targets are issued per line and per
> year by the enterprise or its superior, so `PL-003`'s band and `PL-005`'s unbalance limit ship
> **empty**, and a rule that cannot run says so in `skipped` rather than passing silently.

## Compatibility

| Surface | Status |
|---|---|
| Harness | Peer range `>=0.1.2-rc.1 <0.2.0 \|\| >=0.2.0-0 <0.3.0` — verified to accept both `0.2.0-rc.2` and `0.2.1-alpha.1`. `engines.dsh` is deliberately not declared: it has no reader and cannot reject a host |
| Node | `^22.19.0 || >=24.0.0` |
| Platforms | All (plain ESM; no native code, no network, no model call) |
| Tool mode | Works in `native`, `ptc` and `both`; for a period-by-period batch use `ptc` |

## What it does

Registers the `power_loss_split` tool. It reads one period's figures — supply, sales, declared loss,
declared rate, and optionally the meter list — applies a versioned rule pack, and returns a report.

| Rule | Check | Severity | Basis kind |
|---|---|---|---|
| `PL-001` | 供电量 − 售电量 = 线损电量 | warn | principle |
| `PL-002` | 线损电量 ÷ 供电量 × 100 = 线损率 | warn | principle |
| `PL-003` | the loss rate sits inside your configured band (off by default) | info | local |
| `PL-004` | the meter list sums to the declared sales (or supply) | warn | principle |
| `PL-005` | three-phase unbalance is within your configured limit (off by default) | info | local |

Findings always carry the numbers: `供电量 1000 kWh − 售电量 900 kWh = 100 kWh，与填报的线损电量 50 kWh
相差 50 kWh`. A reviewer who cannot redo the sum cannot judge the finding, so the sum is in the text.

## Install

```sh
dsh plugin --profile <name> add dsh-power-loss-split
dsh --profile <name> --dump-config | grep 'dsh-power-loss-split'
```

## Configuration

| Key | Type | Default | Description |
|---|---|---|---|
| `rulesFile` | string | `rules/power-loss-split.yaml` | Rule-pack path, relative to the package root |
| `disabledRules` | string[] | `[]` | Rule ids to stop running; each appears in `skipped` |
| `onlyRules` | string[] | `[]` | Run only these rule ids; empty runs every rule |
| `skipNotes` | string | `""` | Note appended to every `skipped` reason |
| `timeoutMs` | number | `120000` | Cooperative tool timeout budget |

Rule-level parameters worth knowing:

- `PL-001` / `PL-004` `toleranceKwh` — the rounding slack allowed. Zero demands an exact match; set it
  when figures are reported in 万 kWh and carry rounding.
- `PL-002` `tolerancePoints` — the slack in percentage points, default `0.01`.
- `PL-003` `minRate` / `maxRate` — **your** assessment band for this line this year. `maxRate` of `0`
  means the rule does not run.
- `PL-005` `maxUnbalancePercent` — **your** unbalance limit for this voltage class. `0` means the rule
  does not run.

## Material format

The tool accepts JSON or YAML:

```yaml
name: 10kV 某某线
supplied: 120000      # 供电量 kWh
sold: 114000          # 售电量 kWh
loss: 6000            # 线损电量 kWh
lossRate: 5           # 线损率 %
meters:
  - { 名称: 1号配变, 电量: 60000 }
  - { 名称: 2号配变, 电量: 54000 }
  - { 名称: A, 电量: 100 }      # A/B/C rows drive PL-005
  - { 名称: B, 电量: 98 }
  - { 名称: C, 电量: 96 }
```

Numbers are read from strings too, so a spreadsheet export works as-is: `1,200.5`, `1200 kWh`,
full-width digits `１２３４`, `5%` and `12.5万` all parse. A cell that is not numeric (`—`, blank)
is simply absent, and the affected check reports what it could not do.

## Rule sources

Rule data lives in `rules/power-loss-split.yaml`. The pack's header states the citation gap in full, and
each rule's `note` repeats the part that matters for that rule. The load-time guard that normally
enforces "an excerpt must be a real quotation of at least eight characters" cannot tell a quotation from
a description — so this pack leans on the header, the per-rule notes and a test that asserts every
`excerpt` admits the gap.

Thresholds that belong to the enterprise ship **empty** on purpose. A rule whose threshold is unset
reports itself in `skipped`, so "no findings" can never silently mean "nothing was checked".

## Troubleshooting

- **A finding says a sum does not close but the spreadsheet looks right.** Compare the calculation
  periods: a meter read on a different date from the supply figure produces exactly this difference.
  The plugin reports the gap; it cannot see your meter-reading calendar.
- **`PL-002` fires on a rate that looks correct.** The denominator is taken as 供电量. If your figure
  uses a different base (for example supply net of untransformed energy), that is a declared-scope
  question, not an arithmetic one — supply the scope in the material, or disable the rule.
- **`PL-003` or `PL-005` never run.** Their thresholds are empty. Set this line's assessment band and
  this voltage class's unbalance limit.
- **The plugin installs but the tool never appears.** Check that `main` resolves to `lib/index.mjs` and
  that `pnpm run build` produced it; a wrong `main` makes the loader skip the entry silently.
- **`dsh plugin add` refuses the package as incompatible.** The peer range covers `0.1.x` and `0.2.x`;
  if your runtime sits outside it, grant an explicit exemption:
  `dsh plugin --profile <name> allow-version dsh-power-loss-split@0.1.0 --dsh-version <runtime> --accept-risk`
- **`check` reports `manifest-peers` as failed.** The static checker compares against a hard-coded peer
  range that predates the 0.2 line. The runtime enforces peer compatibility at install time, so the
  declared range is the correct one; this is a known upstream issue in `dsh-plugin-dev`.

## Development

```sh
pnpm install
pnpm run typecheck   # tsc --noEmit
pnpm test            # vitest, paired fixtures per rule
pnpm run build       # tsdown -> lib/index.mjs + lib/index.d.mts
node ../scripts/sync-shared.mjs dsh-power-loss-split   # refresh src/shared from ../_shared
```

## License

[Apache License 2.0](LICENSE) © 2026 dsh-power-loss-split contributors.
