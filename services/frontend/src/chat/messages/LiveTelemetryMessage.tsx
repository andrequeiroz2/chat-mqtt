import { LiveTelemetryChatBubble } from '../../realtime/LiveTelemetryChatBubble'
import type { ChatMessage } from '../../types/chat-ui'

type LiveTelemetryMessageProps = {
  message: Extract<ChatMessage, { role: 'live_telemetry' }>
  getAccessToken: () => Promise<string | null>
  onStop: (id: string) => void
}

export function LiveTelemetryMessage({ message, getAccessToken, onStop }: LiveTelemetryMessageProps) {
  return (
    <li className="max-w-full self-start">
      <LiveTelemetryChatBubble
        deviceId={message.deviceId}
        deviceName={message.deviceName}
        getAccessToken={getAccessToken}
        onStop={() => onStop(message.id)}
      />
    </li>
  )
}
