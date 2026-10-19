import { TelemetryChartBubble } from '../TelemetryChartBubble'
import type { ChatMessage } from '../../types/chat-ui'

type TelemetryChartMessageProps = {
  message: Extract<ChatMessage, { role: 'telemetry_chart' }>
}

export function TelemetryChartMessage({ message }: TelemetryChartMessageProps) {
  return (
    <li className="w-full max-w-none self-start">
      <div className="rounded-xl border border-border bg-card px-4 py-3 text-card-foreground shadow-sm">
        <TelemetryChartBubble
          deviceName={message.deviceName}
          metric={message.metric}
          unit={message.unit}
          periodLabel={message.periodLabel}
          points={message.points}
        />
      </div>
    </li>
  )
}
