import { cn } from '@/lib/utils'
import { PostAdoptionActions } from '../adopt/PostAdoptionActions'
import type { ChatMessage } from '../../types/chat-ui'

type PostAdoptionMessageProps = {
  message: Extract<ChatMessage, { role: 'post_adoption' }>
  disabled: boolean
  onSelect: (prompt: string) => void
}

export function PostAdoptionMessage({ message, disabled, onSelect }: PostAdoptionMessageProps) {
  return (
    <li
      className={cn(
        'max-w-[90%] self-start rounded-xl border border-border bg-card px-4 py-3 text-sm text-card-foreground',
      )}
    >
      <p className="mb-2.5">{message.text}</p>
      <PostAdoptionActions
        actions={message.actions}
        disabled={disabled}
        onSelect={onSelect}
      />
    </li>
  )
}
