import { lazy, Suspense } from 'react'

import type { TelemetryChartPoint } from '../charts/TelemetryChart'

const TelemetryChart = lazy(() =>
  import('../charts/TelemetryChart').then((m) => ({ default: m.TelemetryChart })),
)

type TelemetryChartBubbleProps = {
  deviceName: string | null
  metric: string
  unit: string | null
  periodLabel: string
  points: TelemetryChartPoint[]
}

export function TelemetryChartBubble(props: TelemetryChartBubbleProps) {
  return (
    <Suspense
      fallback={
        <p className="text-sm text-muted-foreground">Carregando gráfico…</p>
      }
    >
      <TelemetryChart {...props} />
    </Suspense>
  )
}
