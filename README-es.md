# dsh-power-loss-split — Reparto de la energía de pérdidas de línea y verificación de la tabla de evaluación

`dsh-power-loss-split` lee un período de medición de una línea o de un centro de transformación — 供电量, 售电量, la 线损电量 y la 线损率 declaradas y, cuando el material la trae, la lista de puntos de medida — y hace comprobaciones aritméticas y de intervalo sobre ese material: el balance de energía, la tasa de pérdidas, la suma de los puntos de medida, la banda de tasa de pérdidas que usted configure y el desequilibrio entre fases. Cada hallazgo lleva los números y la tolerancia que utilizó, de modo que la cuenta se puede rehacer, y toda comprobación que no pudo ejecutarse se lista en `skipped` en lugar de pasar en silencio.

## Qué responde

| Usted pregunta | Qué responde |
|---|---|
| La 线损电量 declarada no cuadra con 供电量 − 售电量. ¿Cuál de las tres cifras está mal? | `PL-001` no lo dirá. Informa de la diferencia — `供电量 1000 kWh − 售电量 900 kWh = 100 kWh，与填报的线损电量 50 kWh 相差 50 kWh` — y la compara con la tolerancia `toleranceKwh`, que viene en 0, así que las tres cifras deben coincidir exactamente (si se declara en 万 kWh queda una diferencia de redondeo, y entonces hay que configurar una tolerancia distinta de cero). La regla solo hace la resta: no decide cuál de los tres valores es correcto ni comprueba si las lecturas son del mismo período (抄表同期性). |
| La 线损率 figura como 5.00%, pero 线损电量 ÷ 供电量 da 6.25%. ¿El problema está en el denominador? | `PL-002` muestra la división: calcula 线损电量 ÷ 供电量 × 100 e informa de la diferencia en 个百分点 frente a la tasa declarada, admitiendo por defecto `tolerancePoints` 0.01 个百分点 por redondeo — las reglas de redondeo se citan aparte, de GB/T 8170-2008, cuyo texto literal este paquete tampoco tiene. No juzga si el criterio del denominador es correcto (口径, por ejemplo si debería deducirse la 无损电量): eso debe explicarlo el material o configurarlo usted. |
| La tasa de pérdidas de mi línea me parece alta. ¿La herramienta la señalará? | No por sí sola. `PL-003` compara la 线损率 solo con la banda que usted configure (`minRate` / `maxRate`); ambas vienen en 0, es decir sin configurar, y entonces la regla se lista en `skipped` con su motivo en lugar de pasar en silencio. Aun configurada, está limitada a `info`: un hallazgo significa que la tasa queda fuera de la banda que usted fijó, no que las pérdidas sean anómalas. El objetivo de evaluación lo asigna su institución por línea y por año, así que no se fija ningún valor. |
| La lista de puntos de medida suma menos que la 售电量 declarada. ¿Falta algún punto de medida? | `PL-004` informa de la diferencia y nada más: suma los puntos de medida que llevan un valor de energía y compara el total con la 售电量 declarada — o con la 供电量 cuando no hay 售电量 —, con la tolerancia `toleranceKwh` (0 por defecto). Un punto de medida omitido, uno contado dos veces y lecturas no simultáneas (抄表不同期) producen la misma diferencia, así que la causa debe verificarse a mano; la regla solo hace la suma. |
| La hoja solo trae valores de la fase A y de la fase B. ¿Qué hace la comprobación de desequilibrio? | `PL-005` se lista en `skipped`: necesita puntos de medida llamados A, B y C, y con menos de tres valores de fase no puede ejecutarse. Aun con los tres, el límite `maxUnbalancePercent` viene sin configurar (0) y la regla vuelve a `skipped`. Cuando fije un límite, calcula (最大值 − 最小值) ÷ 最大值, imprime esa fórmula junto al hallazgo y está limitada a `info`: no juzga si el desequilibrio constituye un defecto (是否构成缺陷). |

## Normas que sigue

| Documento | Número | Reglas que lo citan |
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

| Superficie | Estado |
|---|---|
| Harness | Rango de peers `>=0.1.2-rc.1 <0.2.0 \|\| >=0.2.0-0 <0.3.0` — verificado para aceptar tanto `0.2.0-rc.2` como `0.2.1-alpha.1`. **No se declara `engines.dsh`**: no tiene lector y no puede rechazar ningún host |
| Node | `^22.19.0 || >=24.0.0` |
| Plataformas | Todas (ESM puro; sin código nativo, sin red, sin llamada al modelo) |
| Modo de herramienta | Funciona en `native`, `ptc` y `both`; para un directorio completo use `ptc` |

## What it does

La tabla de reglas, los campos y el comportamiento detallado están en [README.md](README.md#what-it-does) (versión principal en inglés). El plugin sólo enumera divergencias literales frente a las cláusulas citadas e indica en `skipped` cada comprobación que no pudo ejecutarse.

## Install

```sh
dsh plugin --profile <name> add dsh-power-loss-split
dsh --profile <name> --dump-config | grep 'dsh-power-loss-split'
```

## Configuration

Todos los parámetros ajustables viven en el esquema Schemastery de `src/config.ts`, por lo que se cambian desde `cordis.yml` sin tocar el código; los umbrales por regla están en el paquete de reglas bajo `rules/`.

| Clave | Tipo | Predeterminado | Descripción |
|---|---|---|---|
| `rulesFile` | string | `rules/power-loss-split.yaml` | Ruta del paquete de reglas, relativa a la raíz del paquete |
| `disabledRules` | string[] | `[]` | Ids de reglas que se dejan de ejecutar; cada una aparece en `skipped` |
| `onlyRules` | string[] | `[]` | Ejecutar solo estas reglas; vacío ejecuta todas |
| `skipNotes` | string | `""` | Nota añadida a cada motivo de `skipped` |
| `timeoutMs` | number | `120000` | Presupuesto de tiempo de espera cooperativo de la herramienta |

## Material format

Acepta JSON o YAML. El ejemplo completo de campos está en [README.md](README.md#material-format) (versión principal en inglés). Los campos son opcionales en la capa de lectura y los valida el motor, de modo que una exportación parcial produce hallazgos sobre lo que falta en lugar de un fallo.

## Rule sources

Los datos de las reglas están separados del código: cada regla lleva documento, número, cláusula en la numeración propia de la fuente, extracto literal y URL de origen. El cargador impone que el extracto sea una cita real de al menos ocho caracteres y que una comprobación basada sólo en un principio general (`kind: derived-from-principle`, tope `warn`) o en una política local (`kind: institutional-configuration`, tope `info`) nunca se declare `error`.

Los límites verificados y las conclusiones deliberadamente **no** afirmadas están en [README.md](README.md#rule-sources) (versión principal en inglés) y en `rules/evidence/`.

## Troubleshooting

- **El plugin se instala pero la herramienta no aparece**: compruebe que `main` resuelve a `lib/index.mjs` y que `pnpm run build` lo generó.
- **`dsh plugin add` rechaza el paquete**: la faixa de peers cubre `0.1.x` y `0.2.x`; fuera de ella, conceda una exención explícita con `dsh plugin --profile <name> allow-version <pkg@ver> --dsh-version <runtime> --accept-risk`.
- **Una regla no se ejecutó**: lea el arreglo `skipped`.
- **`check` informa `manifest-peers` como fallo**: es un problema conocido de `dsh-plugin-dev`; el runtime aplica la compatibilidad al instalar.
- **Los horarios parecen desplazados**: toda la aritmética es de hora local sobre las cadenas entregadas.

## Development

```sh
pnpm install
pnpm run typecheck
pnpm test
pnpm run build
node ../scripts/sync-shared.mjs dsh-power-loss-split
```

El último comando copia el kit compartido de `../_shared` a `src/shared/`; vuelva a ejecutarlo tras cada cambio compartido.

## License

[Apache License 2.0](LICENSE) © 2026 dsh-power-loss-split contributors.
