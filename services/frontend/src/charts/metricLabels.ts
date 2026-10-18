/** Rótulos de métrica para UX (PT). */

const METRIC_PT: Record<string, string> = {
  temperature: 'Temperatura',
  humidity: 'Umidade',
}

export function formatMetricLabel(metric: string, unit: string | null): string {
  const name = METRIC_PT[metric] ?? metric
  return unit ? `${name} (${unit})` : name
}

export function formatPeriodLabel(periodLabel: string): string {
  const trimmed = periodLabel.trim()
  if (trimmed === '1d-last') {
    return 'último dia com registros'
  }
  const match = /^(\d+)d$/.exec(trimmed)
  if (match) {
    const days = Number(match[1])
    return days === 1 ? '1 dia' : `${days} dias`
  }
  return periodLabel
}
