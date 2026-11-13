<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/assets/dsh-power-loss-split-hero-en-dark.webp">
  <img src="docs/assets/dsh-power-loss-split-hero-en-light.webp" width="100%" alt="dsh-power-loss-split, portada: la columna izquierda lleva la etiqueta PLUGIN, el título, las dos líneas de valor y la nota de ejecución local; el panel derecho usa el ejemplo del quickstart como dos reglas — PL-001 enfrenta la energía de pérdidas declarada de 5 500 kWh con los 6 000 kWh derivados (diferencia 500 kWh, tolerancia 0), PL-002 enfrenta el 5 % declarado con el 4,5833 % calculado (diferencia 0,4167 puntos, tolerancia ±0,01) — con dos hallazgos warn y tres comprobaciones omitidas, cada una con su motivo">
</picture>

# dsh-power-loss-split

**Un período de medición de pérdidas de línea, resuelto de una vez: qué fila no cuadra, cuánto se desvía y qué corregir.**

Un verificador DSH para equipos de pérdidas de línea: lee la energía suministrada, la energía vendida, la energía de pérdidas declarada y su tasa, más la lista de puntos de medida cuando el material la trae, y aplica comprobaciones aritméticas y de intervalo. Cada hallazgo lleva sus números y su tolerancia; toda comprobación que no puede ejecutarse queda en `skipped` con su motivo.

[Instalación](#instalación-en-tres-pasos) · [Configuración](#configuración) · [FAQ](#faq) · [简体中文](README.md) · [English](README.en.md) · [Español](README.es.md) · [Português](README.pt.md) · [हिन्दी](README.hi.md)

[![License](https://img.shields.io/badge/license-Apache--2.0-3366CC?style=flat-square&labelColor=2B3245)](LICENSE)
[![DSH](https://img.shields.io/badge/DSH-%E2%89%A50.2.1%20%3C0.3.0-4B67B4?style=flat-square&labelColor=2B3245)](#compatibilidad)
[![npm](https://img.shields.io/npm/v/dsh-power-loss-split?style=flat-square&labelColor=2B3245&color=CB3837)](https://www.npmjs.com/package/dsh-power-loss-split)
[![CI](https://img.shields.io/github/actions/workflow/status/PerryLink/dsh-power-loss-split/ci.yml?branch=main&label=CI&style=flat-square&labelColor=2B3245)](https://github.com/PerryLink/dsh-power-loss-split/actions/workflows/ci.yml)
[![Node](https://img.shields.io/badge/node-%5E22.19%20%7C%7C%20%3E%3D24-339933?style=flat-square&labelColor=2B3245)](#compatibilidad)

[![Stars](https://img.shields.io/github/stars/PerryLink/dsh-power-loss-split?style=flat-square&labelColor=2B3245)](https://github.com/PerryLink/dsh-power-loss-split/stargazers)
[![npm downloads](https://img.shields.io/npm/dm/dsh-power-loss-split?style=flat-square&labelColor=2B3245&color=CB3837)](https://www.npmjs.com/package/dsh-power-loss-split)
[![dshfind](https://dshfind.com/api/badge/PerryLink/dsh-power-loss-split?metric=downloads)](https://dshfind.com/plugins/PerryLink/dsh-power-loss-split?ref=badge)
[![OpenSSF Scorecard](https://api.securityscorecards.dev/projects/github.com/PerryLink/dsh-power-loss-split/badge)](https://securityscorecards.dev/viewer/?uri=github.com/PerryLink/dsh-power-loss-split)
[![DSH Market](https://img.shields.io/badge/DSH_Market-listed-4B67B4?style=flat-square&labelColor=2B3245)](https://dsh.market/)
[![Gitee](https://img.shields.io/badge/Gitee-mirror-C71D23?style=flat-square&labelColor=2B3245&logo=gitee)](https://gitee.com/perrylink/dsh-power-loss-split)

```sh
dsh plugin --profile <name> add dsh-power-loss-split
```

</div>

<sub>Plugin comunitario, no afiliado a DeepSeek. Repositorio canónico: <https://github.com/PerryLink/dsh-power-loss-split> (Gitee es un espejo).</sub>

## Qué es

`dsh-power-loss-split` lee un período de medición de una línea o de un centro de transformación — `supplied` (energía suministrada), `sold` (energía vendida), `loss` (energía de pérdidas declarada), `lossRate` (tasa de pérdidas declarada) y la lista `meters` cuando el material la trae — y aplica comprobaciones aritméticas y de intervalo sobre esas cifras: el balance de energía, la tasa de pérdidas, la suma de los puntos de medida, la banda de tasa de pérdidas que usted configure y el desequilibrio entre fases. Cada hallazgo lleva los números y la tolerancia utilizados, de modo que la cuenta se puede rehacer; toda comprobación que no pudo ejecutarse se lista en `skipped` en lugar de pasar en silencio.

```text
material (JSON / YAML)──power_loss_split──▶ rules/power-loss-split.yaml
                                                │ PL-001 … PL-005
                                                ▼
                             informe: found · expected · fix
                                      skipped[]: id de regla + motivo
```

La herramienta es `power_loss_split`; el material se lee de una ruta `file` o del texto en línea `material`. Todo el cálculo ocurre en el host: sin red y sin llamadas al modelo.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/assets/dsh-power-loss-split-flow-v5-dark.svg">
  <img src="docs/assets/dsh-power-loss-split-flow-v5-light.svg" width="100%" alt="Diagrama de estructura de dsh-power-loss-split: el material de un período de medición (supplied / sold / loss / lossRate / meters) pasa por parseMaterial() a un mismo bus y entra en cinco interruptores de regla en paralelo — PL-001 balance de energía, PL-002 tasa de pérdidas, PL-003 banda configurada, PL-004 suma de contadores, PL-005 desequilibrio entre fases. Cada interruptor lleva su regla a uno de dos canales según su fórmula y tolerancia: una diferencia va a issues[] con found / expected / fix / basis y severidad warn; una comprobación que no pudo ejecutarse, o que se ejecutó sin diferencia, va a skipped[] con el id de la regla y el motivo (las ejecuciones limpias también se listan). Ambos canales terminan en una sola vista: summary, issueCount, skippedCount, markdown y reportJson; este ejemplo da 2 warn y 3 skipped">
</picture>

## Instalación en tres pasos

1. **Instalar** (elija un canal; npm tiene `0.3.0`):

   ```sh
   # canal git (última main)
   dsh plugin --profile web add github:PerryLink/dsh-power-loss-split
   # canal npm (versiones publicadas)
   dsh plugin --profile web add dsh-power-loss-split
   # canal tarball: tras pnpm pack en este repositorio
   dsh plugin --profile web add ./dsh-power-loss-split-<version>.tgz
   ```

   El paquete publicado incluye `lib/index.mjs`; un checkout del código fuente necesita antes `pnpm install && pnpm run build`.

2. **Configuración mínima** (los valores por defecto sirven; el paquete de reglas viene incluido):

   ```yaml
   - insert:
       - id: dsh-power-loss-split
         name: dsh-power-loss-split
         config:
           timeoutMs: 120000
   ```

3. **Comprobar que funciona** (ejemplo incluido, sin material propio):

   ```sh
   pnpm install && pnpm run build
   node samples/quickstart/run.mjs
   dsh --profile web --dump-config | grep 'dsh-power-loss-split'
   ```

   Debe salir `power_loss_split: 2 issue(s) — error 0, warn 2, info 0` y `skipped: 3`, igual que `samples/quickstart/expected/result.json`; hay una captura en `docs/assets/quickstart.png`.

**Desinstalar**: `dsh plugin --profile web remove dsh-power-loss-split` (o elimine la fila del patch del perfil).

## Capacidades clave

Los datos de las reglas están separados del código: sustituir `rules/power-loss-split.yaml` cambia la versión del conjunto de reglas sin tocar TypeScript.

| Regla | Comprobación | Gravedad | Tipo de base |
|---|---|---|---|
| `PL-001` | suministrada − vendida = energía de pérdidas | warn | derivada de principio |
| `PL-002` | energía de pérdidas ÷ suministrada × 100 = tasa | warn | derivada de principio |
| `PL-003` | la tasa cae dentro de la banda configurada (desactivada por defecto) | info | institucional |
| `PL-004` | la suma de puntos de medida iguala la energía vendida declarada (o la suministrada) | warn | derivada de principio |
| `PL-005` | el desequilibrio trifásico respeta el límite configurado (desactivado por defecto) | info | institucional |

- **Cada hallazgo muestra su operación.** El texto escribe `energía suministrada 1000 kWh − vendida 900 kWh = 100 kWh` y la cifra declarada con la que se compara; quien no puede rehacer la cuenta no puede juzgar el hallazgo, así que la operación siempre está.
- **Lo que no puede ejecutarse va a `skipped`.** Un umbral sin configurar, un campo ausente o menos de tres valores de fase ponen la regla en `skipped` con su id y su motivo: una lista de problemas vacía nunca puede leerse como «no hay nada mal».
- **Las lagunas de cita se declaran.** El paquete de reglas no inventa citas: cuando el texto literal no se pudo obtener, `excerpt` lo dice y la gravedad queda limitada a `warn` (derivada de principio) o `info` (configuración institucional). Una prueba asegura que ninguna regla afirma una cita que no tiene.
- **Lectura de números tolerante.** Separadores de miles, sufijos de unidad, dígitos de ancho completo, porcentajes y unidades de diez mil se analizan; véase «Formato del material» para la lista de ejemplos. Una celda no numérica (`—`, vacía) se trata como ausente y la comprobación afectada informa de lo que no pudo hacer.
- **Solo host.** ESM puro, sin código nativo, sin peticiones de red y sin llamadas al modelo; el registro de la herramienta devuelve un disposer, así que descargarla la elimina.

### Parámetros de la herramienta

| Argumento | Tipo | Significado |
|---|---|---|
| `file` | string | Ruta absoluta del archivo de material (JSON o YAML); excluyente con `material` |
| `material` | string | Texto de material en línea (JSON o YAML); excluyente con `file` |
| `rulesFile` | string | Sustituye la ruta del paquete de reglas configurada (relativa al paquete o absoluta) |
| `only` | string[] | Ejecutar solo estas reglas; vacío ejecuta todas |

## Una salida real

La salida siguiente procede de una ejecución real de este plugin sobre su fixture `PL-002`, no es un montaje. El paquete de reglas no inventa citas, así que cada hallazgo nombra la cláusula aplicada y advierte que su texto no se obtuvo esta vez.

**Herramienta** `power_loss_split`

**Entrada**

~~~json
{"name":"10kV 某某线","supplied":120000,"sold":114000,"loss":6000,"lossRate":4.2}
~~~

**Salida**

~~~json
{
  "id": "dsh-power-loss-split.PL-002.f0566556",
  "ruleId": "PL-002",
  "severity": "warn",
  "locator": {
    "column": "线损率"
  },
  "found": "线损电量 6000 kWh ÷ 供电量 120000 kWh × 100% = 5%，与填报的线损率 4.2% 相差 0.8 个百分点",
  "expected": "线损率应为线损电量与供电量之比，允许偏差 0.01 个百分点",
  "fix": "核对线损率的计算口径（分母是否为供电量、是否含无损电量）；本条只做除法核对"
}
~~~

*Observed from `dsh-power-loss-split/tests/fixtures/PL-002/PL-002-unsafe.json (cases.json expects 1×PL-002); executed parseMaterial+runCheck, checkedAt=2026-10-06T00:00:00.000Z`*

La tabla siguiente es el conjunto de ejemplos: la primera fila es el caso detallado y las demás son casos breves.

| Usted pregunta | Qué responde |
|---|---|
| La energía de pérdidas declarada no cuadra con suministrada − vendida. ¿Cuál de las tres cifras está mal? | `PL-001` no lo dirá. Informa de la diferencia — `suministrada 1000 kWh − vendida 900 kWh = 100 kWh`, 50 kWh de diferencia frente a los 50 kWh declarados — y la compara con `toleranceKwh`, que viene en 0, así que las tres cifras deben coincidir exactamente (si se declara en decenas de miles de kWh queda una diferencia de redondeo, y entonces hay que configurar una tolerancia distinta de cero). La regla solo hace la resta: no decide cuál de los valores es correcto ni comprueba si las lecturas son del mismo período (sincronía de lecturas). |
| La tasa de pérdidas figura como 5,00%, pero energía de pérdidas ÷ suministrada da 6,25%. ¿El problema está en el denominador? | `PL-002` muestra la división: calcula energía de pérdidas ÷ suministrada × 100 e informa de la diferencia en puntos porcentuales frente a la tasa declarada, admitiendo por defecto `tolerancePoints` 0,01 puntos por redondeo — las reglas de redondeo se citan aparte, de GB/T 8170-2008, cuyo texto literal este paquete tampoco tiene. No juzga si el criterio del denominador es correcto (por ejemplo si debería deducirse la energía sin pérdidas): eso debe explicarlo el material o configurarlo usted. |
| La tasa de pérdidas de mi línea me parece alta. ¿La herramienta la señalará? | No por sí sola. `PL-003` compara la tasa solo con la banda que usted configure (`minRate` / `maxRate`); ambas vienen en 0, es decir sin configurar, y entonces la regla se lista en `skipped` con su motivo en lugar de pasar en silencio. Aun configurada, está limitada a `info`: un hallazgo significa que la tasa queda fuera de la banda que usted fijó, no que las pérdidas sean anómalas. El objetivo de evaluación lo asigna su institución por línea y por año, así que no se fija ningún valor. |
| La lista de puntos de medida suma menos que la energía vendida declarada. ¿Falta algún punto de medida? | `PL-004` informa de la diferencia y nada más: suma los puntos de medida que llevan un valor de energía y compara el total con la energía vendida declarada — o con la suministrada cuando no hay cifra de venta —, con la tolerancia `toleranceKwh` (0 por defecto). Un punto omitido, uno contado dos veces y lecturas no simultáneas producen la misma diferencia, así que la causa debe verificarse a mano; la regla solo hace la suma. |
| La hoja solo trae valores de la fase A y de la fase B. ¿Qué hace la comprobación de desequilibrio? | `PL-005` se lista en `skipped`: necesita puntos de medida llamados A, B y C, y con menos de tres valores de fase no puede ejecutarse. Aun con los tres, el límite `maxUnbalancePercent` viene sin configurar (0) y la regla vuelve a `skipped`. Cuando fije un límite, calcula (máximo − mínimo) ÷ máximo, imprime esa fórmula junto al hallazgo y está limitada a `info`: no juzga si el desequilibrio constituye un defecto. |

## Reglas y base

| Documento | Número | Reglas que lo citan |
|---|---|---|
| Guía para el cálculo de pérdidas de energía en redes eléctricas | DL/T 686-2018 | PL-001, PL-002, PL-003, PL-004, PL-005 |
| Reglas de redondeo de valores numéricos y juicio de valores límite | GB/T 8170-2008 | PL-002 |

**Límite:** este plugin hace **comprobaciones aritméticas y de intervalo** sobre las cifras de pérdidas de un período de medición — el balance de energía, la tasa de pérdidas, la suma de puntos de medida, el desequilibrio entre fases — y muestra su cálculo en cada hallazgo. No es una herramienta de medida ni de diagnóstico de fallos de medida (no hay sonda, ni integración AMI, ni modelo de hardware) y no decide si una cifra de pérdidas es razonable ni si hubo manipulación. Lee una exportación de hoja de cálculo e informa de qué sumas no cuadran.

> ### ⚠️ Lea esto antes de fiarse de una cita del informe
>
> **Cada `excerpt` del paquete de reglas dice, con todas las letras, que el texto de la cláusula no se obtuvo.** Las dos relaciones que comprueba el plugin — energía de pérdidas = suministrada − vendida y tasa = energía de pérdidas ÷ suministrada × 100 — son **definitorias**, y su sede normativa es **DL/T 686-2018, Guía para el cálculo de pérdidas de energía en redes eléctricas**. La norma está **vigente**, y su índice se verificó (el capítulo 3 es Términos y definiciones; el capítulo 8 es Análisis de pérdidas de energía y cálculo del efecto de las medidas de reducción), pero **su cuerpo no se publica gratis**, así que no se pudo leer ninguna cláusula literal.
>
> En lugar de parafrasear una cita, este paquete declara la laguna en el campo `excerpt` y pone el razonamiento honesto en `note`. Todo queda por tanto limitado a `warn` (derivado de principio) o `info` (configurado localmente), y una prueba asegura que ninguna regla afirma una cita que no tiene. **Cuando se tenga el texto de la norma, hay que hacer dos cosas: sustituir cada `excerpt` por la cláusula real y elevar `kind` a `direct`.** Hasta entonces, un hallazgo significa «estas dos cifras no cuadran», no «usted incumplió una norma».
>
> **Los umbrales de evaluación son suyos, no de la norma.** Los objetivos de pérdidas los emite la empresa o su superior por línea y por año, así que la banda de `PL-003` y el límite de desequilibrio de `PL-005` vienen **vacíos**, y una regla que no puede ejecutarse lo dice en `skipped` en lugar de pasar en silencio.

<details>
<summary>Fuentes de las reglas y validación al cargar</summary>

Los datos de las reglas están separados del código: cada regla lleva documento, número, cláusula en la numeración propia de la fuente, extracto literal y URL de origen. Validación al cargar: el extracto debe ser una cita real de al menos ocho caracteres, y una comprobación basada solo en un principio (`kind: derived-from-principle`, techo `warn`) o en una política local (`kind: institutional-configuration`, techo `info`) nunca puede declararse `error`. Un paquete de reglas que exagera su base falla al cargar en lugar de producir un informe que parece sólido.

Los límites verificados y las conclusiones deliberadamente **no** afirmadas están en el directorio `rules/evidence/` incluido; la `note` de cada regla repite la parte que importa para esa regla.

Los umbrales que pertenecen a la empresa vienen **vacíos** (0 = sin configurar). Una regla con umbral sin definir se declara en `skipped`, así que «sin hallazgos» nunca puede significar en silencio «no se comprobó nada».

</details>

## Formato del material

La herramienta acepta JSON o YAML:

```yaml
name: 10kV 某某线
supplied: 120000      # energía suministrada, kWh
sold: 114000          # energía vendida, kWh
loss: 6000            # energía de pérdidas, kWh
lossRate: 5           # tasa de pérdidas, %
meters:
  - { 名称: 1号配变, 电量: 60000 }
  - { 名称: 2号配变, 电量: 54000 }
  - { 名称: A, 电量: 100 }      # las filas A/B/C alimentan PL-005
  - { 名称: B, 电量: 98 }
  - { 名称: C, 电量: 96 }
```

Los números también se leen de cadenas, así que una exportación de hoja de cálculo sirve tal cual. Estos ejemplos se analizan:

```text
1,200.5   1200 kWh   １２３４   5%   12.5万
```

Una celda no numérica (`—`, vacía) simplemente falta, y la comprobación afectada informa de lo que no pudo hacer. Los campos son opcionales en la capa de lectura y los valida el motor, de modo que una exportación parcial produce hallazgos sobre lo que falta en lugar de un fallo.

## Configuración

Todos los parámetros ajustables viven en el esquema Schemastery de `src/config.ts`, por lo que se cambian desde `cordis.yml` sin tocar el código; los umbrales por regla están en el paquete de reglas bajo `rules/`.

| Clave | Tipo | Predeterminado | Descripción |
|---|---|---|---|
| `rulesFile` | string | `rules/power-loss-split.yaml` | Ruta del paquete de reglas, relativa a la raíz del paquete |
| `disabledRules` | string[] | `[]` | Ids de reglas que se dejan de ejecutar; cada una aparece en `skipped` |
| `onlyRules` | string[] | `[]` | Ejecutar solo estas reglas; vacío ejecuta todas |
| `skipNotes` | string | `""` | Nota añadida a cada motivo de `skipped` |
| `timeoutMs` | number | `120000` | Presupuesto de tiempo de espera cooperativo de la herramienta (ms) |

Parámetros por regla que conviene conocer:

- `PL-001` / `PL-004` `toleranceKwh`: el margen de redondeo permitido. Cero exige coincidencia exacta; configúrelo cuando las cifras se declaren en decenas de miles de kWh y lleven redondeo.
- `PL-002` `tolerancePoints`: el margen en puntos porcentuales, por defecto `0.01`.
- `PL-003` `minRate` / `maxRate`: **su** banda de evaluación para esta línea este año. `maxRate` en `0` significa que la regla no se ejecuta.
- `PL-005` `maxUnbalancePercent`: **su** límite de desequilibrio para esta clase de tensión. `0` significa que la regla no se ejecuta.

Ejemplo de sustitución en el patch de un perfil:

```yaml
- insert:
    - id: dsh-power-loss-split
      name: dsh-power-loss-split
      config:
        disabledRules: [PL-003]
        skipNotes: este trimestre solo se concilia el balance de energía
```

## FAQ

<details>
<summary>¿Dónde viven el material y el informe? ¿Sale algo a la red?</summary>

El plugin **no tiene almacenamiento propio**: el material se lee solo para esta llamada a la herramienta (una ruta `file` o el texto en línea `material`) y el informe se devuelve como resultado de la herramienta; después el host gestiona el registro de sesión. El cálculo no hace peticiones de red ni llama a ningún modelo, y el archivo original nunca se modifica. El `dsh.demo` de `package.json` declara además `network: false` y `writes: []`.

</details>

<details>
<summary>El informe no muestra problemas, ¿significa que la línea está bien?</summary>

No. Mire primero `skipped`: un umbral sin configurar (`maxRate: 0`, `maxUnbalancePercent: 0`), un campo ausente o menos de tres valores de fase hacen que la comprobación correspondiente se omita por completo con su motivo. Una lista de problemas vacía solo significa «las comprobaciones que se ejecutaron no hallaron diferencias», no «se ejecutaron todas».

</details>

<details>
<summary>¿Por qué una regla nunca se ejecuta?</summary>

`PL-003` y `PL-005` vienen con umbral 0, es decir sin configurar; sin configurar significa `skipped`. Los objetivos de pérdidas los emite la institución por línea y por año, y los límites de desequilibrio se gradúan por clase de tensión y capacidad del equipo: el plugin no fija ninguno, así que debe introducir la banda de este año y el límite de esta clase de tensión en el paquete de reglas o en la configuración. Las reglas listadas en `disabledRules` también se omiten y aparecen en `skipped`.

</details>

<details>
<summary>¿Cuánto coste de rendimiento supone? ¿Puede bloquear una sesión?</summary>

Sin peticiones de red, sin llamadas al modelo y sin retroceso de expresiones regulares; el coste es una lectura de material, unas pocas operaciones aritméticas y el formateo del informe. `timeoutMs` es el presupuesto de tiempo cooperativo que se pasa a la herramienta (por defecto `120000` ms), y la herramienta también respeta la señal de aborto del host. Para un directorio completo, use el modo de herramienta `ptc` para pagar el coste del esquema una sola vez.

</details>

<details>
<summary>Solución de problemas: instalación, herramienta ausente, reglas que no se ejecutan</summary>

- **El plugin se instala pero la herramienta no aparece**: compruebe que `main` resuelve a `lib/index.mjs` y que `pnpm run build` lo generó; un `main` incorrecto hace que el cargador omita la entrada en silencio.
- **`dsh plugin add` rechaza el paquete por incompatibilidad**: la franja de peers cubre `0.1.x` y `0.2.x`; si su runtime queda fuera, conceda una exención explícita: `dsh plugin --profile <name> allow-version <pkg@ver> --dsh-version <runtime> --accept-risk`.
- **Una regla no se ejecutó**: lea el arreglo `skipped`; indica el id de la regla y el motivo.
- **`check` informa `manifest-peers` como fallo**: el verificador estático compara con una franja de peers codificada que es anterior a la línea 0.2; la compatibilidad de peers en la instalación la aplica el runtime. Es un problema conocido de `dsh-plugin-dev`.
- **Los horarios parecen desplazados**: toda la aritmética es de hora local sobre las cadenas entregadas; no se hace conversión de zona horaria.
- **Un hallazgo dice que una suma no cuadra pero la hoja parece correcta**: compare los períodos de cálculo; un contador leído en una fecha distinta de la cifra de suministro produce exactamente esa diferencia. El plugin informa de la diferencia, pero no ve su calendario de lecturas.
- **`PL-002` salta con una tasa que parece correcta**: el denominador se toma como energía suministrada. Si su cifra usa otra base (por ejemplo, suministrada neta de energía sin pérdidas), es una cuestión de alcance declarado, no de aritmética: declare el alcance en el material o desactive la regla.
- **`PL-003` / `PL-005` nunca se ejecutan**: sus umbrales vienen vacíos. Fije la banda de evaluación de esta línea y el límite de desequilibrio de esta clase de tensión.

</details>

## Límites de seguridad y limitaciones conocidas

- **Solo comprobaciones aritméticas y de intervalo.** Balance de energía, tasa de pérdidas, suma de puntos de medida, desequilibrio entre fases y el cálculo de cada hallazgo. No es una herramienta de medida ni de diagnóstico de fallos de medida (sin sonda, sin integración AMI, sin modelo de hardware) y no juzga si una cifra de pérdidas es razonable ni si hubo manipulación.
- **Las lagunas de cita se declaran.** El paquete de reglas no fabrica citas; `excerpt` declara que el texto de la cláusula no se obtuvo, y el tipo de base y la gravedad quedan limitados por la evidencia. Un hallazgo significa «estas dos cifras no cuadran», no «usted incumplió una norma».
- **Una lista vacía no es «todo correcto».** Las comprobaciones que no pueden ejecutarse van a `skipped` con un motivo; «sin hallazgos» no debe leerse como «no se comprobó nada».
- **Los umbrales de evaluación son de su institución.** `minRate` / `maxRate` / `maxUnbalancePercent` vienen en 0 (sin configurar); el plugin no fija ningún objetivo ni adivina.
- **Un período, sin veredicto de sincronía.** Solo se comprueba el período que usted pasa; si las lecturas son del mismo período y si faltan o se duplican puntos de medida exige revisión manual.
- **Sin conversión de zona horaria.** Toda la aritmética es de hora local sobre las cadenas entregadas.
- **Se ejecuta en local.** Sin peticiones de red, sin credenciales, sin escribir de vuelta en el material original; la única ruta leída es la que pasa en `file`.

## Interoperabilidad con otros plugins DSH

Este plugin registra exactamente una herramienta, así que su superficie de registro es estrecha:

- **Una herramienta, un nombre.** Solo registra `power_loss_split`; no ocupa ningún nombre desnudo de una herramienta integrada ni de otro plugin.
- **Sin clave de servicio, ruta HTTP ni slot de cliente.** No aporta clave de servicio, no registra ningún prefijo `webServer` y no tiene mitad de navegador (este repositorio no tiene directorio `client/`), así que no compite por slots de cliente.
- **Sin mutación global.** No parchea prototipos, no reescribe `process.env` ni sustituye el despachador global de fetch.
- **El registro es un efecto.** El disposer que devuelve `ctx.tools.register` elimina la herramienta al descargar o recargar en caliente; `inject: ['tools']` significa que solo carga cuando existe el servicio `tools`.

Evidencia: la superficie de registro en `src/index.ts` (`export const inject = ['tools']`, una sola llamada a `ctx.tools.register`, ninguna otra).

## Compatibilidad

| Superficie | Estado |
|---|---|
| Harness | Rango de peers `>=0.1.2-rc.1 <0.2.0 \|\| >=0.2.0-0 <0.3.0` — verificado para aceptar tanto `0.2.0-rc.2` como `0.2.1-rc.2`. `engines.dsh` se declara como `>=0.2.1-0 <0.3.0` y el host lo aplica desde 0.2.1 |
| Node | `^22.19.0 \|\| >=24.0.0` |
| Plataformas | Todas (ESM puro; sin código nativo, sin red, sin llamada al modelo) |
| Modo de herramienta | Funciona en `native` y `ptc`; para un directorio completo use `ptc` |

## Ecosistema y calidad

- [Página de dshfind](https://dshfind.com/plugins/PerryLink/dsh-power-loss-split) (instalaciones y clasificación)
- [Informe de OpenSSF Scorecard](https://securityscorecards.dev/viewer/?uri=github.com/PerryLink/dsh-power-loss-split) (impulsado por [.github/workflows/scorecard.yml](.github/workflows/scorecard.yml))
- [DSH Market](https://dsh.market/) (listado)
- [Espejo en Gitee](https://gitee.com/perrylink/dsh-power-loss-split) (espejo sincronizado; GitHub es el canónico)
- [Elegir un verificador por material](https://perrylink.github.io/zh/checkers/choose/) (el índice de verificadores al que pertenece este plugin)
- [Seguimiento de problemas](https://github.com/PerryLink/dsh-power-loss-split/issues) (incluya versión, comando y un material mínimo redactado)

## Desarrollo

```sh
pnpm install
pnpm run typecheck        # tsc --noEmit
pnpm test                 # vitest, un par de fixtures conforme/infractor por regla
pnpm run build            # tsdown -> lib/index.mjs + lib/index.d.mts
pnpm run verify:self-contained
pnpm run check:lockfile
pnpm run check:readmes    # consistencia de los README multilingües
pnpm run check:citations
node ../scripts/sync-shared.mjs dsh-power-loss-split   # refrescar src/shared
```

El último comando copia el kit compartido de `../_shared` a `src/shared/`; vuelva a ejecutarlo tras cada cambio compartido. Las imágenes del README las genera [`scripts/gen-readme-assets.py`](scripts/gen-readme-assets.py) (Pillow crea la portada en zh/en × claro/oscuro; el diagrama de estructura es un par de SVG escritos a mano) y se pueden volver a ejecutar: `python scripts/gen-readme-assets.py`.

<details>
<summary>Estructura de directorios</summary>

| Ruta | Contenido |
|---|---|
| `src/index.ts` | Registro de la herramienta y resolución del paquete de reglas (contrato function-plugin, sin export por defecto) |
| `src/config.ts` | Esquema de configuración Schemastery; aquí viven todos los parámetros |
| `src/check.ts` | Núcleo puro `(input, ruleset, options) => Report`; sin E/S, reloj ni modelo |
| `src/parse.ts` | Lector de material JSON / YAML |
| `src/view.ts` | Proyección del informe para el modelo; `output.schema` la refleja |
| `src/shared/` | Kit compartido (carga del ruleset, forma del informe, subconjunto YAML, aritmética de fechas), copiado, no importado |
| `rules/power-loss-split.yaml` | El paquete de 5 reglas |
| `rules/evidence/` | Registro de verificación de cada cita |
| `tests/` | vitest; cada regla tiene fixtures emparejados en `tests/fixtures/<RULE>/` |
| `scripts/` | Verificadores mecánicos: autocontención, deriva del lockfile, sincronía de README, citas |

</details>

Topics: `dsh`, `dsh-plugin`, `deepseek-harness`, `deepseek`, `cordis`, `power`, `loss`, `split`

## Familia y agradecimientos

Este proyecto forma parte de la familia de plugins de DeepSeek Harness de [PerryLink](https://github.com/PerryLink) (todos Apache-2.0). El índice completo está en [elegir un verificador por material](https://perrylink.github.io/zh/checkers/choose/) y [todos los plugins](https://github.com/PerryLink); este repositorio es uno de ellos. Si le resulta útil, **una estrella ayuda a que la siguiente persona lo encuentre** — no desbloquea nada.

- [@PerryLink](https://github.com/PerryLink) — creador y mantenedor: el paquete de reglas, el núcleo de comprobación, la documentación en cinco idiomas y el script de imágenes.

<details>
<summary>Expandir todos los plugins</summary>

| Plugin | Estado |
|---|---|
| **[dsh-aqua-input-check](https://github.com/PerryLink/dsh-aqua-input-check)** |  |
| **[dsh-archive-check](https://github.com/PerryLink/dsh-archive-check)** |  |
| **[dsh-auto-review](https://github.com/PerryLink/dsh-auto-review)** |  |
| **[dsh-autotier](https://github.com/PerryLink/dsh-autotier)** | 🧊 CONGELADO — ver el README del repo |
| **[dsh-bid-ca-precheck](https://github.com/PerryLink/dsh-bid-ca-precheck)** |  |
| **[dsh-bid-qual-check](https://github.com/PerryLink/dsh-bid-qual-check)** |  |
| **[dsh-cert-mcp](https://github.com/PerryLink/dsh-cert-mcp)** | 🧊 CONGELADO — ver el README del repo |
| **[dsh-checkpoint-rewind](https://github.com/PerryLink/dsh-checkpoint-rewind)** |  |
| **[dsh-click](https://github.com/PerryLink/dsh-click)** |  |
| **[dsh-composer-history](https://github.com/PerryLink/dsh-composer-history)** |  |
| **[dsh-contract-stance](https://github.com/PerryLink/dsh-contract-stance)** |  |
| **[dsh-customs-doc-check](https://github.com/PerryLink/dsh-customs-doc-check)** |  |
| **[dsh-data-quality](https://github.com/PerryLink/dsh-data-quality)** |  |
| **[dsh-demurrage-ledger](https://github.com/PerryLink/dsh-demurrage-ledger)** |  |
| **[dsh-doublecheck](https://github.com/PerryLink/dsh-doublecheck)** |  |
| **[dsh-drill-script-check](https://github.com/PerryLink/dsh-drill-script-check)** |  |
| **[dsh-eia-guide-check](https://github.com/PerryLink/dsh-eia-guide-check)** |  |
| **[dsh-emergency-plan](https://github.com/PerryLink/dsh-emergency-plan)** |  |
| **[dsh-essay-rubric-check](https://github.com/PerryLink/dsh-essay-rubric-check)** |  |
| **[dsh-evidence-check](https://github.com/PerryLink/dsh-evidence-check)** |  |
| **[dsh-export-ctl-check](https://github.com/PerryLink/dsh-export-ctl-check)** |  |
| **[dsh-fast](https://github.com/PerryLink/dsh-fast)** |  |
| **[dsh-fmea-table-check](https://github.com/PerryLink/dsh-fmea-table-check)** |  |
| **[dsh-forecast-penalty](https://github.com/PerryLink/dsh-forecast-penalty)** |  |
| **[dsh-fund-research](https://github.com/PerryLink/dsh-fund-research)** |  |
| **[dsh-github](https://github.com/PerryLink/dsh-github)** |  |
| **[dsh-gongwen-flow-check](https://github.com/PerryLink/dsh-gongwen-flow-check)** |  |
| **[dsh-gongwen-word-check](https://github.com/PerryLink/dsh-gongwen-word-check)** |  |
| **[dsh-guard-plan-qc](https://github.com/PerryLink/dsh-guard-plan-qc)** |  |
| **[dsh-hazchem-check](https://github.com/PerryLink/dsh-hazchem-check)** |  |
| **[dsh-hazplan-check](https://github.com/PerryLink/dsh-hazplan-check)** |  |
| **[dsh-hidden-risk-map](https://github.com/PerryLink/dsh-hidden-risk-map)** |  |
| **[dsh-hs-classify](https://github.com/PerryLink/dsh-hs-classify)** |  |
| **[dsh-icd-rule-check](https://github.com/PerryLink/dsh-icd-rule-check)** |  |
| **[dsh-industry-research](https://github.com/PerryLink/dsh-industry-research)** |  |
| **[dsh-lawcite-adapter](https://github.com/PerryLink/dsh-lawcite-adapter)** |  |
| **[dsh-laya](https://github.com/PerryLink/dsh-laya)** |  |
| **[dsh-lc-doc-check](https://github.com/PerryLink/dsh-lc-doc-check)** |  |
| **[dsh-learning-gap-check](https://github.com/PerryLink/dsh-learning-gap-check)** |  |
| **[dsh-library](https://github.com/PerryLink/dsh-library)** |  |
| **[dsh-local-ai](https://github.com/PerryLink/dsh-local-ai)** |  |
| **[dsh-lsp-actions](https://github.com/PerryLink/dsh-lsp-actions)** |  |
| **[dsh-mask](https://github.com/PerryLink/dsh-mask)** |  |
| **[dsh-mcp-panel](https://github.com/PerryLink/dsh-mcp-panel)** |  |
| **[dsh-medrec-qc](https://github.com/PerryLink/dsh-medrec-qc)** |  |
| **[dsh-memento](https://github.com/PerryLink/dsh-memento)** |  |
| **[dsh-nsfc-form-check](https://github.com/PerryLink/dsh-nsfc-form-check)** |  |
| **[dsh-nurse-record-check](https://github.com/PerryLink/dsh-nurse-record-check)** |  |
| **[dsh-observe](https://github.com/PerryLink/dsh-observe)** |  |
| **[dsh-origin-rvc-check](https://github.com/PerryLink/dsh-origin-rvc-check)** |  |
| **[dsh-ota-review-check](https://github.com/PerryLink/dsh-ota-review-check)** |  |
| **[dsh-output-styles](https://github.com/PerryLink/dsh-output-styles)** |  |
| **[dsh-paper-doc-adapter](https://github.com/PerryLink/dsh-paper-doc-adapter)** |  |
| **[dsh-permission-rules](https://github.com/PerryLink/dsh-permission-rules)** |  |
| **[dsh-permit-report-check](https://github.com/PerryLink/dsh-permit-report-check)** |  |
| **[dsh-pipeline-check](https://github.com/PerryLink/dsh-pipeline-check)** |  |
| **[dsh-pleading-draft](https://github.com/PerryLink/dsh-pleading-draft)** |  |
| **[dsh-plugin-doctor](https://github.com/PerryLink/dsh-plugin-doctor)** | 🚫 RETIRADO (repo archivado) |
| **[dsh-plugin-guide](https://github.com/PerryLink/dsh-plugin-guide)** |  |
| **[dsh-plugin-kit](https://github.com/PerryLink/dsh-plugin-kit)** | 🚫 RETIRADO (repo archivado) |
| **[dsh-plugin-upgrade](https://github.com/PerryLink/dsh-plugin-upgrade)** | 🚫 RETIRADO (repo archivado) |
| **[dsh-policy-brief-draft](https://github.com/PerryLink/dsh-policy-brief-draft)** |  |
| **[dsh-power-loss-split](https://github.com/PerryLink/dsh-power-loss-split)** |  |
| **[dsh-power-ticket-check](https://github.com/PerryLink/dsh-power-ticket-check)** |  |
| **[dsh-ppap-check](https://github.com/PerryLink/dsh-ppap-check)** |  |
| **[dsh-protest-deadline](https://github.com/PerryLink/dsh-protest-deadline)** |  |
| **[dsh-railway-window](https://github.com/PerryLink/dsh-railway-window)** |  |
| **[dsh-repair-order-qc](https://github.com/PerryLink/dsh-repair-order-qc)** |  |
| **[dsh-research-report](https://github.com/PerryLink/dsh-research-report)** |  |
| **[dsh-review-reply-check](https://github.com/PerryLink/dsh-review-reply-check)** |  |
| **[dsh-rulefile-check](https://github.com/PerryLink/dsh-rulefile-check)** |  |
| **[dsh-safety-brief-check](https://github.com/PerryLink/dsh-safety-brief-check)** |  |
| **[dsh-score](https://github.com/PerryLink/dsh-score)** |  |
| **[dsh-session-sync](https://github.com/PerryLink/dsh-session-sync)** |  |
| **[dsh-site-log-check](https://github.com/PerryLink/dsh-site-log-check)** |  |
| **[dsh-skill-pack-security](https://github.com/PerryLink/dsh-skill-pack-security)** |  |
| **[dsh-soe-decision-check](https://github.com/PerryLink/dsh-soe-decision-check)** |  |
| **[dsh-soilwater-check](https://github.com/PerryLink/dsh-soilwater-check)** |  |
| **[dsh-sop-sync-check](https://github.com/PerryLink/dsh-sop-sync-check)** |  |
| **[dsh-spc-gbt-adapter](https://github.com/PerryLink/dsh-spc-gbt-adapter)** |  |
| **[dsh-talk](https://github.com/PerryLink/dsh-talk)** |  |
| **[dsh-tender-extract](https://github.com/PerryLink/dsh-tender-extract)** |  |
| **[dsh-tender-matrix](https://github.com/PerryLink/dsh-tender-matrix)** |  |
| **[dsh-test-drive](https://github.com/PerryLink/dsh-test-drive)** |  |
| **[dsh-ticktick](https://github.com/PerryLink/dsh-ticktick)** | 🚫 RETIRADO (repo archivado) |
| **[dsh-translate](https://github.com/PerryLink/dsh-translate)** |  |
| **[dsh-warranty-calc](https://github.com/PerryLink/dsh-warranty-calc)** |  |
| **[dsh-budget](https://github.com/PerryLink/dsh-budget)** | 🧊 CONGELADO — ver el README del repo |
| **[dsh-claude-move](https://github.com/PerryLink/dsh-claude-move)** | 🧊 CONGELADO — ver el README del repo |
| **[dsh-defend](https://github.com/PerryLink/dsh-defend)** | 🧊 CONGELADO — ver el README del repo |
| **[dsh-draw](https://github.com/PerryLink/dsh-draw)** | 🧊 CONGELADO — ver el README del repo |
| **[dsh-reach](https://github.com/PerryLink/dsh-reach)** | 🧊 CONGELADO — ver el README del repo |
| **[dsh-background-agents](https://github.com/PerryLink/dsh-background-agents)** | 🚫 RETIRADO (repo archivado) |
| **[dsh-session-pin](https://github.com/PerryLink/dsh-session-pin)** | 🚫 RETIRADO (repo archivado) |
| **[dsh-team-rooms](https://github.com/PerryLink/dsh-team-rooms)** | 🚫 RETIRADO (repo archivado) |

</details>

## Licencia

[LICENSE](LICENSE) (Apache License 2.0) © 2026 dsh-power-loss-split contributors

<p align="center"><sub>Apache-2.0 · Plugin comunitario, no afiliado a DeepSeek.</sub></p>
