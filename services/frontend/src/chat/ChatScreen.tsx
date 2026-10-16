import { useCallback, useState, type SubmitEvent } from 'react'

import { ApiError } from '../api/client'
import { useSignedInAuth } from '../auth/useSignedInAuth'
import { formatAuthError } from '../app/auth-error-messages'
import { CHAT_MESSAGE_MAX_LENGTH } from '../types/api'
import type { ChatMessage } from '../types/chat-ui'
import { getOrCreateChatSessionId } from './session'
import { AdoptWizardPanel, type AdoptWizardPhase } from './adopt/AdoptWizardPanel'
import { isAdoptionIntent } from './adopt/intent'
import { PostAdoptionActions } from './adopt/PostAdoptionActions'
import { LiveTelemetryChatBubble } from '../realtime/LiveTelemetryChatBubble'
import { POST_SUCCESS_MENU, PRECHECK_ASSISTANT } from './adopt/progressCopy'
import type { ChatResponse } from '../types/api/chat'

export function ChatScreen() {
  const { profile, api, actions, getAccessToken } = useSignedInAuth()
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [draft, setDraft] = useState('')
  const [sending, setSending] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [adoptPhase, setAdoptPhase] = useState<AdoptWizardPhase | null>(null)

  const sessionId = getOrCreateChatSessionId()

  const appendAssistant = useCallback((text: string) => {
    setMessages((prev) => [
      ...prev,
      { id: crypto.randomUUID(), role: 'assistant', text },
    ])
  }, [])

  const closeAdoptWizard = useCallback(() => {
    setAdoptPhase(null)
  }, [])

  const appendChatResponse = useCallback((response: ChatResponse) => {
    setMessages((prev) => {
      const next: ChatMessage[] = [
        ...prev,
        { id: crypto.randomUUID(), role: 'assistant', text: response.reply },
      ]
      const ui = response.suggested_ui
      if (ui?.kind === 'realtime_telemetry') {
        const withoutLive = next.filter((m) => m.role !== 'live_telemetry')
        return [
          ...withoutLive,
          {
            id: crypto.randomUUID(),
            role: 'live_telemetry',
            deviceId: ui.device_id,
            deviceName: ui.device_name ?? null,
          },
        ]
      }
      return next
    })
  }, [])

  const sendChatMessage = useCallback(
    async (text: string) => {
      const trimmed = text.trim()
      if (!trimmed || sending) {
        return
      }

      setError(null)
      setSending(true)

      const userMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: 'user',
        text: trimmed,
      }
      setMessages((prev) => [...prev, userMsg])

      if (isAdoptionIntent(trimmed) && adoptPhase === null) {
        appendAssistant(PRECHECK_ASSISTANT)
        setAdoptPhase('precheck')
        setSending(false)
        return
      }

      try {
        const response = await api.postChat({ message: trimmed, session_id: sessionId })
        appendChatResponse(response)
      } catch (err) {
        const code = err instanceof ApiError ? err.detail : 'chat_failed'
        setError(formatAuthError(code) ?? code)
      } finally {
        setSending(false)
      }
    },
    [adoptPhase, appendAssistant, appendChatResponse, api, sending, sessionId],
  )

  const onSubmit = useCallback(
    async (event: SubmitEvent<HTMLFormElement>) => {
      event.preventDefault()
      const text = draft.trim()
      if (!text || sending) {
        return
      }
      setDraft('')
      await sendChatMessage(text)
    },
    [draft, sendChatMessage, sending],
  )

  const handlePostAdoption = useCallback(
    async (deviceId: string | null | undefined) => {
      if (!deviceId) {
        appendAssistant(POST_SUCCESS_MENU)
        return
      }
      setError(null)
      try {
        const response = await api.postChatPostAdoption({
          session_id: sessionId,
          device_id: deviceId,
        })
        setMessages((prev) => [
          ...prev,
          {
            id: crypto.randomUUID(),
            role: 'post_adoption',
            text: response.message,
            actions: response.actions,
          },
        ])
      } catch (err) {
        const code = err instanceof ApiError ? err.detail : 'post_adoption_failed'
        setError(formatAuthError(code) ?? code)
        appendAssistant(POST_SUCCESS_MENU)
      }
    },
    [api, appendAssistant, sessionId],
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
        {messages.map((msg) =>
          msg.role === 'live_telemetry' ? (
            <li key={msg.id} className="chat-bubble assistant live-telemetry-wrap">
              <LiveTelemetryChatBubble
                deviceId={msg.deviceId}
                deviceName={msg.deviceName}
                getAccessToken={getAccessToken}
                onStop={() =>
                  setMessages((prev) => prev.filter((m) => m.id !== msg.id))
                }
              />
            </li>
          ) : msg.role === 'post_adoption' ? (
            <li key={msg.id} className="chat-bubble assistant post-adoption-wrap">
              <p>{msg.text}</p>
              <PostAdoptionActions
                actions={msg.actions}
                disabled={sending}
                onSelect={(prompt) => void sendChatMessage(prompt)}
              />
            </li>
          ) : (
            <li key={msg.id} className={`chat-bubble ${msg.role}`}>
              {msg.text}
            </li>
          ),
        )}
      </ul>

      {adoptPhase !== null && (
        <AdoptWizardPanel
          api={api}
          phase={adoptPhase}
          onPhaseChange={(phase, meta) => {
            setAdoptPhase(phase)
            if (phase === 'done' && meta?.committed) {
              void handlePostAdoption(meta.deviceId)
            }
          }}
          onAssistantLine={appendAssistant}
          onClose={closeAdoptWizard}
        />
      )}

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
