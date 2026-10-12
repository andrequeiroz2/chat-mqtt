import { useCallback, useState, type SubmitEvent } from 'react'

import { ApiError } from '../api/client'
import { useSignedInAuth } from '../auth/useSignedInAuth'
import { formatAuthError } from '../app/auth-error-messages'
import { CHAT_MESSAGE_MAX_LENGTH } from '../types/api'
import type { ChatMessage } from '../types/chat-ui'
import { getOrCreateChatSessionId } from './session'

export function ChatScreen() {
  const { profile, api, actions } = useSignedInAuth()
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [draft, setDraft] = useState('')
  const [sending, setSending] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const sessionId = getOrCreateChatSessionId()

  const onSubmit = useCallback(
    async (event: SubmitEvent<HTMLFormElement>) => {
      event.preventDefault()
      const text = draft.trim()
      if (!text || sending) {
        return
      }

      setDraft('')
      setError(null)
      setSending(true)

      const userMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: 'user',
        text,
      }
      setMessages((prev) => [...prev, userMsg])

      try {
        const { reply } = await api.postChat({ message: text, session_id: sessionId })
        setMessages((prev) => [
          ...prev,
          { id: crypto.randomUUID(), role: 'assistant', text: reply },
        ])
      } catch (err) {
        const code = err instanceof ApiError ? err.detail : 'chat_failed'
        setError(formatAuthError(code) ?? code)
      } finally {
        setSending(false)
      }
    },
    [api, draft, sending, sessionId],
  )

  return (
    <div className="chat-shell">
      <header className="chat-header">
        <div>
          <h1>TomatoIA</h1>
          <p className="muted">
            Olá, <strong>{profile.display_name}</strong>
          </p>
        </div>
        <button type="button" className="btn secondary" onClick={() => void actions.signOut()}>
          Sair
        </button>
      </header>

      <ul className="chat-messages" aria-live="polite">
        {messages.length === 0 && (
          <li className="chat-empty muted">Envie uma mensagem para começar.</li>
        )}
        {messages.map((msg) => (
          <li key={msg.id} className={`chat-bubble ${msg.role}`}>
            {msg.text}
          </li>
        ))}
      </ul>

      {error && <p className="chat-error">{error}</p>}

      <form className="chat-composer" onSubmit={(e) => void onSubmit(e)}>
        <textarea
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder="Digite sua mensagem…"
          rows={3}
          disabled={sending}
          maxLength={CHAT_MESSAGE_MAX_LENGTH}
        />
        <button type="submit" className="btn primary" disabled={sending || !draft.trim()}>
          {sending ? 'Enviando…' : 'Enviar'}
        </button>
      </form>
    </div>
  )
}
