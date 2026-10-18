import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import { formatMetricLabel, formatPeriodLabel } from './metricLabels'

export type TelemetryChartPoint = {
  received_at: string
  value: number
}

type TelemetryChartProps = {
  deviceName: string | null
  metric: string
  unit: string | null
  periodLabel: string
  points: TelemetryChartPoint[]
}

function formatAxisTime(iso: string): string {
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) {
    return iso.slice(0, 10)
  }
  return date.toLocaleString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function TelemetryChart({
  deviceName,
  metric,
  unit,
  periodLabel,
  points,
}: TelemetryChartProps) {
  const data = points.map((p) => ({
    ...p,
    label: formatAxisTime(p.received_at),
  }))

  const title = deviceName ?? 'Sensor'
  const yLabel = formatMetricLabel(metric, unit)
  const period = formatPeriodLabel(periodLabel)

  return (
    <div className="w-full min-w-[260px]">
      <p className="mb-3 text-sm font-medium text-card-foreground">
        {title}
        <span className="text-muted-foreground"> · {yLabel}</span>
        <span className="font-normal text-muted-foreground"> · {period}</span>
      </p>
      <div className="h-56 w-full" role="img" aria-label={`Gráfico ${yLabel} ${period}`}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 8, right: 12, left: 4, bottom: 4 }}>
            <CartesianGrid stroke="oklch(1 0 0 / 10%)" vertical={false} />
            <XAxis
              dataKey="label"
              tick={{ fill: 'oklch(0.705 0.015 286.067)', fontSize: 10 }}
              tickLine={false}
              axisLine={false}
              minTickGap={28}
            />
            <YAxis
              width={40}
              tick={{ fill: 'oklch(0.705 0.015 286.067)', fontSize: 10 }}
              tickLine={false}
              axisLine={false}
              domain={['auto', 'auto']}
            />
            <Tooltip
              contentStyle={{
                background: 'oklch(0.23 0.006 285.885)',
                border: '1px solid oklch(1 0 0 / 10%)',
                borderRadius: '0.5rem',
                color: 'oklch(0.985 0 0)',
                fontSize: '12px',
              }}
              labelFormatter={(_, payload) =>
                payload?.[0]?.payload?.received_at
                  ? formatAxisTime(String(payload[0].payload.received_at))
                  : ''
              }
              formatter={(value) => {
                const n = typeof value === 'number' ? value : Number(value)
                const text = Number.isFinite(n)
                  ? unit
                    ? `${n} ${unit}`
                    : String(n)
                  : '—'
                return [text, formatMetricLabel(metric, null)]
              }}
            />
            <Line
              type="monotone"
              dataKey="value"
              stroke="oklch(0.88 0 0)"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4, fill: 'oklch(0.88 0 0)' }}
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
