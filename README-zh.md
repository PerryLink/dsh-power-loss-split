# dsh-power-loss-split — 线损电量拆分与考核表核对

`dsh-power-loss-split` 读取一条线路或一台配变某一个抄表周期的线损材料——供电量、售电量、填报的线损电量与线损率，以及材料里有则一并读取的计量点清单——对这些数字做算术与区间核对：量平衡、线损率、计量点合计、你配置的线损率区间、三相不平衡度。每条命中都带着它用到的数字与容差，复核者可以自己重算；凡是跑不起来的检查都列在 `skipped` 里，而不是静默通过。

## 它回答什么问题

| 你会问 | 它怎么答 |
|---|---|
| 填报的线损电量与「供电量 − 售电量」对不上，这三个数里哪一个错了？ | `PL-001` 不作判断。它报出差额——`供电量 1000 kWh − 售电量 900 kWh = 100 kWh，与填报的线损电量 50 kWh 相差 50 kWh`——并与容差 `toleranceKwh` 比较；该参数出场为 0，要求三个数严格相等（按万 kWh 报送会留下进位差，此时应配置一个非零容差）。本条只做减法核对：不判断三个数值中哪一个正确，也不核对几次抄表是否同期。 |
| 线损率填的是 5.00%，但线损电量 ÷ 供电量 算出 6.25%，是分母口径的问题吗？ | `PL-002` 会把除法写出来：按 线损电量 ÷ 供电量 × 100 计算，与填报的线损率比较相差几个百分点，默认允许 `tolerancePoints` 0.01 个百分点的四舍五入偏差——修约规则另引 GB/T 8170-2008，该标准本次同样未取得逐字条文。它不判断分母口径是否正确（例如是否应扣除无损电量）：口径问题必须由使用方在材料中说明或配置。 |
| 我这条线路的线损率看着偏高，插件会报出来吗？ | 不会自己报。`PL-003` 只拿线损率与你配置的区间（`minRate` / `maxRate`）比较；两个参数出场均为 0 即未配置，此时本条连同原因列入 `skipped`，而不是静默通过。即使配置了，本条封顶 `info`：命中只表示超出你配置的区间，不表示线损异常。线损考核指标是按线路、按年下达的本机构指标，插件不硬编码任何考核值。 |
| 计量点清单加起来比填报的售电量少，是不是漏了计量点？ | `PL-004` 只报出差额：把带电量数值的计量点相加，与填报的售电量核对——没有售电量时与供电量核对——允许偏差为 `toleranceKwh`（出场为 0）。计量点遗漏、重复计入、抄表不同期都会造成同样的差额，具体原因必须人工核查；本条只做加法核对。 |
| 材料里只有 A 相和 B 相的数值，不平衡度这一条会怎么处理？ | `PL-005` 会把自己列入 `skipped`：它需要按 A、B、C 相命名的计量点，相别数值不足三个就跑不起来。即使三个都有，限值 `maxUnbalancePercent` 出场为 0 即未配置，本条同样进 `skipped`。配置限值后，它按 (最大值 − 最小值) ÷ 最大值 计算，并把这条公式随命中信息一起给出，封顶 `info`——不判断是否构成缺陷。 |

## 依据的标准

| 文件 | 文号 | 引用它的规则 |
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

| 项目 | 状态 |
|---|---|
| Harness | 对等版本范围 `>=0.1.2-rc.1 <0.2.0 \|\| >=0.2.0-0 <0.3.0` —— 已实测同时接受 `0.2.0-rc.2` 与 `0.2.1-alpha.1`。**刻意不声明 `engines.dsh`**：它没有任何读取者，也无法拒装任何宿主 |
| Node | `^22.19.0 || >=24.0.0` |
| 平台 | 全平台（纯 ESM；无原生代码、无联网、不调用模型） |
| 工具模式 | `native` / `ptc` / `both` 均可；批量校验整个目录时建议 `ptc`，schema 成本只付一次 |

## What it does

规则表、字段说明与行为细节见 [README.md](README.md#what-it-does)（英文主版本）。本插件只列出材料与所引条款之间的字面差异，并对无法执行的检查在 `skipped` 中逐项说明。

## Install

```sh
dsh plugin --profile <name> add dsh-power-loss-split
dsh --profile <name> --dump-config | grep 'dsh-power-loss-split'
```

## Configuration

全部可调参数都在 `src/config.ts` 的 Schemastery schema 中，只改 `cordis.yml` 即可生效，无需改代码；逐条阈值在 `rules/` 下的规则库文件里。

| 键 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `rulesFile` | string | `rules/power-loss-split.yaml` | 规则库文件路径，相对插件包根目录 |
| `disabledRules` | string[] | `[]` | 要停用的规则 id 列表；每条都会出现在 `skipped` 中 |
| `onlyRules` | string[] | `[]` | 只执行这些规则 id；留空表示执行全部规则 |
| `skipNotes` | string | `""` | 附加到每条 `skipped` 说明后的备注 |
| `timeoutMs` | number | `120000` | 工具协作式超时预算（毫秒） |

## Material format

支持 JSON 与 YAML。完整字段示例见 [README.md](README.md#material-format)（英文主版本）。字段在读取层是可选的，由检查引擎校验，因此部分导出的材料会产生"缺项"类差异，而不是让程序崩溃。

## Rule sources

规则数据与代码分离，每条规则都带文件名、文号、按原文自身编号体系的条款号、逐字摘录与来源地址。加载期强制：摘录必须是真实引文且不少于八个字符；依据仅为原则性条款（`kind: derived-from-principle`，严重级上限 `warn`）或本机构配置（`kind: institutional-configuration`，上限 `info`）的检查不得标为 `error`。夸大依据的规则库会在加载期失败，而不会产出一份看起来很有底气的报告。

核验中确认的边界与"刻意没有作出的结论"见 [README.md](README.md#rule-sources)（英文主版本）与随包的 `rules/evidence/` 目录。

## Troubleshooting

- **插件装上了但工具不出现**：确认 `main` 指向 `lib/index.mjs` 且 `pnpm run build` 已生成该文件；`main` 写错会让加载器静默跳过该条目。
- **`dsh plugin add` 报版本不兼容**：peer 范围覆盖 `0.1.x` 与 `0.2.x`；若运行时在其之外，可显式豁免：`dsh plugin --profile <name> allow-version <包名@版本> --dsh-version <runtime> --accept-risk`
- **某条规则没有执行**：查看 `skipped` 数组，其中写明了规则 id 与原因。
- **`check` 报 `manifest-peers` 失败**：静态检查器比对的是一份早于 0.2 世代的硬编码 peer 范围；安装期的 peer 校验以运行时为准。这是 `dsh-plugin-dev` 的已知上游问题。
- **时间看起来偏移**：全部计算都是对输入字符串做墙上时钟运算，不做时区换算。

## Development

```sh
pnpm install
pnpm run typecheck
pnpm test
pnpm run build
node ../scripts/sync-shared.mjs dsh-power-loss-split
```

第 4 项把 `../_shared` 的共享件同步进 `src/shared/`；每次改动共享件后都要重跑。

## License

[Apache License 2.0](LICENSE) © 2026 dsh-power-loss-split contributors.
