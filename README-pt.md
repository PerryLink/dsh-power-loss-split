# dsh-power-loss-split — Repartição da energia de perdas de linha e verificação da tabela de avaliação

[![DSH Market](https://raw.githubusercontent.com/2BingLing/dsh-market/master/assets/readme/badge-listed-en.svg)](https://dsh.market/)

`dsh-power-loss-split` lê um período de medição de uma linha ou de um posto de transformação — 供电量, 售电量, a 线损电量 e a 线损率 declaradas e, quando o material a traz, a lista de pontos de medição — e faz verificações aritméticas e de intervalo sobre esse material: o balanço de energia, a taxa de perdas, a soma dos pontos de medição, a faixa de taxa de perdas que você configurar e o desequilíbrio entre fases. Cada achado traz os números e a tolerância utilizados, para que a conta possa ser refeita, e toda verificação que não pôde ser executada é listada em `skipped` em vez de passar em silêncio.

## Como é a saída

![Terminal demo of dsh-power-loss-split: real output over its PL-001 fixture](https://raw.githubusercontent.com/PerryLink/dsh-power-loss-split/main/docs/assets/dsh-power-loss-split-demo.png)

Saída real deste plugin sobre o seu próprio fixture de teste `PL-001` — não é uma simulação. O pacote de regras não inventa citações, por isso cada achado nomeia a cláusula aplicada e avisa que o seu texto não foi obtido.

## O que ele responde

| Você pergunta | O que ele responde |
|---|---|
| A 线损电量 declarada não fecha com 供电量 − 售电量. Qual das três cifras está errada? | `PL-001` não o dirá. Reporta a diferença — `供电量 1000 kWh − 售电量 900 kWh = 100 kWh，与填报的线损电量 50 kWh 相差 50 kWh` — e compara-a com a tolerância `toleranceKwh`, que vem em 0, pelo que as três cifras têm de coincidir exatamente (se reportar em 万 kWh fica uma diferença de arredondamento, e então é preciso configurar uma tolerância diferente de zero). A regra só faz a subtração: não decide qual dos três valores está correto nem verifica se as leituras são do mesmo período (抄表同期性). |
| A 线损率 está preenchida como 5.00%, mas 线损电量 ÷ 供电量 dá 6.25%. O problema está no denominador? | `PL-002` mostra a divisão: calcula 线损电量 ÷ 供电量 × 100 e reporta a diferença em 个百分点 face à taxa declarada, admitindo por omissão `tolerancePoints` 0.01 个百分点 para arredondamento — as regras de arredondamento são citadas à parte, da GB/T 8170-2008, cujo texto literal este pacote também não tem. Não julga se o critério do denominador está correto (口径, por exemplo se a 无损电量 devia ser deduzida): isso tem de ser explicado no material ou configurado por você. |
| A taxa de perdas da minha linha parece-me alta. A ferramenta vai assinalá-la? | Não por si só. `PL-003` compara a 线损率 apenas com a faixa que você configurar (`minRate` / `maxRate`); ambas vêm em 0, ou seja não configuradas, e então a regra é listada em `skipped` com o motivo, em vez de passar em silêncio. Mesmo configurada, está limitada a `info`: um achado significa que a taxa está fora da faixa que você definiu, não que as perdas sejam anómalas. A meta de avaliação é atribuída pela sua instituição por linha e por ano, pelo que nenhum valor é fixado. |
| A lista de pontos de medição soma menos do que a 售电量 declarada. Falta algum ponto de medição? | `PL-004` reporta a diferença e nada mais: soma os pontos de medição que trazem um valor de energia e compara o total com a 售电量 declarada — ou com a 供电量 quando não há 售电量 —, com a tolerância `toleranceKwh` (0 por omissão). Um ponto de medição omitido, um contado duas vezes e leituras não simultâneas (抄表不同期) produzem a mesma diferença, pelo que a causa tem de ser verificada à mão; a regra só faz a adição. |
| A folha só traz valores da fase A e da fase B. O que faz a verificação de desequilíbrio? | `PL-005` é listada em `skipped`: precisa de pontos de medição chamados A, B e C, e com menos de três valores de fase não pode ser executada. Mesmo com os três, o limite `maxUnbalancePercent` vem não configurado (0) e a regra volta a `skipped`. Quando definir um limite, calcula (最大值 − 最小值) ÷ 最大值, imprime essa fórmula junto ao achado e está limitada a `info`: não julga se o desequilíbrio constitui um defeito (是否构成缺陷). |

## Normas que segue

| Documento | Número | Regras que o citam |
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

| Superfície | Estado |
|---|---|
| Harness | Faixa de peers `>=0.1.2-rc.1 <0.2.0 \|\| >=0.2.0-0 <0.3.0` — verificada para aceitar tanto `0.2.0-rc.2` quanto `0.2.1-alpha.1`. **`engines.dsh` não é declarado**: não tem leitor e não pode recusar nenhum host |
| Node | `^22.19.0 || >=24.0.0` |
| Plataformas | Todas (ESM puro; sem código nativo, sem rede, sem chamada ao modelo) |
| Modo de ferramenta | Funciona em `native`, `ptc` e `both`; para um diretório inteiro use `ptc` |

## What it does

A tabela de regras, os campos e o comportamento detalhado estão em [README.md](README.md#what-it-does) (versão principal em inglês). O plugin apenas lista divergências literais frente às cláusulas citadas e indica em `skipped` cada verificação que não pôde ser executada.

## Install

```sh
dsh plugin --profile <name> add dsh-power-loss-split
dsh --profile <name> --dump-config | grep 'dsh-power-loss-split'
```

## Configuration

Todos os parâmetros ajustáveis ficam no esquema Schemastery de `src/config.ts`, portanto mudam pelo `cordis.yml` sem editar código; os limites por regra ficam no pacote de regras sob `rules/`.

| Chave | Tipo | Padrão | Descrição |
|---|---|---|---|
| `rulesFile` | string | `rules/power-loss-split.yaml` | Caminho do pacote de regras, relativo à raiz do pacote |
| `disabledRules` | string[] | `[]` | Ids de regras a desativar; cada uma aparece em `skipped` |
| `onlyRules` | string[] | `[]` | Executar apenas estas regras; vazio executa todas |
| `skipNotes` | string | `""` | Nota acrescentada a cada motivo de `skipped` |
| `timeoutMs` | number | `120000` | Orçamento de tempo limite cooperativo da ferramenta |

## Material format

Aceita JSON ou YAML. O exemplo completo de campos está em [README.md](README.md#material-format) (versão principal em inglês). Os campos são opcionais na camada de leitura e validados pelo motor, de modo que uma exportação parcial gera achados sobre o que falta em vez de falhar.

## Rule sources

Os dados das regras ficam separados do código: cada regra traz documento, número, cláusula na numeração própria da fonte, trecho literal e URL de origem. O carregador impõe que o trecho seja citação real de pelo menos oito caracteres e que uma verificação baseada apenas em princípio geral (`kind: derived-from-principle`, teto `warn`) ou em política local (`kind: institutional-configuration`, teto `info`) nunca seja declarada `error`.

Os limites verificados e as conclusões deliberadamente **não** afirmadas estão em [README.md](README.md#rule-sources) (versão principal em inglês) e em `rules/evidence/`.

## Troubleshooting

- **O plugin instala mas a ferramenta não aparece**: confirme que `main` resolve para `lib/index.mjs` e que `pnpm run build` o gerou.
- **`dsh plugin add` recusa o pacote**: a faixa de peers cobre `0.1.x` e `0.2.x`; fora dela, conceda isenção explícita com `dsh plugin --profile <name> allow-version <pkg@ver> --dsh-version <runtime> --accept-risk`.
- **Uma regra não executou**: leia o arranjo `skipped`.
- **`check` informa `manifest-peers` como falha**: problema conhecido do `dsh-plugin-dev`; o runtime aplica a compatibilidade na instalação.
- **Os horários parecem deslocados**: toda a aritmética é de hora local sobre as cadeias fornecidas.

## Development

```sh
pnpm install
pnpm run typecheck
pnpm test
pnpm run build
node ../scripts/sync-shared.mjs dsh-power-loss-split
```

O último comando copia o kit compartilhado de `../_shared` para `src/shared/`; execute-o novamente após cada alteração compartilhada.

## License

[Apache License 2.0](LICENSE) © 2026 dsh-power-loss-split contributors.
