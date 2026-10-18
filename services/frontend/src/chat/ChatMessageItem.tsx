import { cn } from '@/lib/utils'
import type { ChatMessage } from '../types/chat-ui'
import { AssistantMessageText } from './AssistantMessageText'
import { AssistantThinkingDots } from './AssistantThinkingDots'
import { LiveTelemetryChatBubble } from '../realtime/LiveTelemetryChatBubble'
import { PostAdoptionActions } from './adopt/PostAdoptionActions'
import { TelemetryChartBubble } from './TelemetryChartBubble'

type ChatMessageItemProps = {
  message: ChatMessage
  sending: boolean
  getAccessToken: () => Promise<string | null>
  onRemoveLiveTelemetry: (id: string) => void
  onPostAdoptionSelect: (prompt: string) => void
}

export function ChatMessageItem({
  message,
  sending,
  getAccessToken,
  onRemoveLiveTelemetry,
  onPostAdoptionSelect,
}: ChatMessageItemProps) {
  if (message.role === 'telemetry_chart') {
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

  if (message.role === 'live_telemetry') {
    return (
      <li className="max-w-full self-start">
        <LiveTelemetryChatBubble
          deviceId={message.deviceId}
          deviceName={message.deviceName}
          getAccessToken={getAccessToken}
          onStop={() => onRemoveLiveTelemetry(message.id)}
        />
      </li>
    )
  }

  if (message.role === 'post_adoption') {
    return (
      <li
        className={cn(
          'max-w-[90%] self-start rounded-xl border border-border bg-card px-4 py-3 text-sm text-card-foreground',
        )}
      >
        <p className="mb-2.5">{message.text}</p>
        <PostAdoptionActions
          actions={message.actions}
          disabled={sending}
          onSelect={(prompt) => onPostAdoptionSelect(prompt)}
        />
      </li>
    )
  }

  const isThinking = message.role === 'assistant' && message.status === 'thinking'

  return (
    <li
      className={cn(
        'max-w-[90%] whitespace-pre-wrap rounded-xl px-4 py-3 text-sm',
        message.role === 'user' &&
          'self-end border border-border bg-secondary text-secondary-foreground shadow-sm ring-1 ring-white/5',
        message.role === 'assistant' &&
          'self-start border border-border bg-card text-card-foreground shadow-sm',
        isThinking && 'flex min-h-11 min-w-14 items-center',
      )}
    >
      {isThinking ? (
        <AssistantThinkingDots />
      ) : message.role === 'assistant' ? (
        <AssistantMessageText text={message.text} />
      ) : (
        message.text
      )}
    </li>
  )
}
