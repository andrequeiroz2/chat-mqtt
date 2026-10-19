import { cn } from '@/lib/utils'
import { AssistantMessageText } from '../AssistantMessageText'
import { AssistantThinkingDots } from '../AssistantThinkingDots'
import type { ChatMessage } from '../../types/chat-ui'

type TextMessageProps = {
  message: Extract<ChatMessage, { role: 'user' | 'assistant' }>
}

export function TextMessage({ message }: TextMessageProps) {
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
