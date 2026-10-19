import type { ChatMessage } from '../types/chat-ui'
import { LiveTelemetryMessage } from './messages/LiveTelemetryMessage'
import { PostAdoptionMessage } from './messages/PostAdoptionMessage'
import { TelemetryChartMessage } from './messages/TelemetryChartMessage'
import { TextMessage } from './messages/TextMessage'

type ChatMessageItemProps = {
  message: ChatMessage
  sending: boolean
  getAccessToken: () => Promise<string | null>
  onRemoveLiveTelemetry: (id: string) => void
  onPostAdoptionSelect: (prompt: string) => void
}

/** Dispatcher por papel (016-07) — sem switch de render props no pai. */
export function ChatMessageItem({
  message,
  sending,
  getAccessToken,
  onRemoveLiveTelemetry,
  onPostAdoptionSelect,
}: ChatMessageItemProps) {
  switch (message.role) {
    case 'telemetry_chart':
      return <TelemetryChartMessage message={message} />
    case 'live_telemetry':
      return (
        <LiveTelemetryMessage
          message={message}
          getAccessToken={getAccessToken}
          onStop={onRemoveLiveTelemetry}
        />
      )
    case 'post_adoption':
      return (
        <PostAdoptionMessage
          message={message}
          disabled={sending}
          onSelect={onPostAdoptionSelect}
        />
      )
    case 'user':
    case 'assistant':
      return <TextMessage message={message} />
  }
}
