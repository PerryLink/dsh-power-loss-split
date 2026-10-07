/**
 * Input contract for the line-loss split checker.
 *
 * The material is one metering period for one line (or transformer district):
 * the energy that went in, the energy that was billed, the loss that was
 * computed, and the subsidiary meters that feed the balance. Every check is
 * arithmetic on these numbers or a comparison the rule pack parameterises, so the
 * report can always show the reader the numbers it used.
 */

/** One meter reading row. */
export interface MeterRow {
  /** 1-based row number in the source. */
  row: number
  /** Meter name or identifier, as recorded. */
  name: string
  /** Energy in kWh, when the row carries a single figure. */
  energy?: number
  /** Values keyed by the source's own column names. */
  fields: Record<string, number>
  /** The row's raw text values, for the 'which column' error messages. */
  raw: Record<string, string>
}

/** The whole normalized input. */
export interface LossInput {
  target: string
  /** Line or district name. */
  name?: string
  /** 供电量 in kWh. */
  supplied?: number
  /** 售电量 in kWh. */
  sold?: number
  /** 线损电量 in kWh, as declared by the material. */
  loss?: number
  /** 线损率 in percent, as declared by the material. */
  lossRate?: number
  /** Per-meter rows, when the material is a meter list. */
  meters: MeterRow[]
  /** Line and transformer capacity in kVA, when declared. */
  capacity?: number
  /** Number of days the period covers. */
  days?: number
  warnings: string[]
}
