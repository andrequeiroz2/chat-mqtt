import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type KeyboardEvent,
  type SubmitEvent,
} from 'react'

import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { ApiError } from '../api/client'
import { useSignedInAuth } from '../auth/useSignedInAuth'
import { formatAuthError } from '../app/auth-error-messages'
import { CHAT_MESSAGE_MAX_LENGTH } from '../types/api'
import type { ChatMessage } from '../types/chat-ui'
import { getOrCreateChatSessionId } from './session'
import { AdoptWizardPanel, type AdoptWizardPhase } from './adopt/AdoptWizardPanel'
import { isAdoptionIntent } from './adopt/intent'
import { ChatMessageItem } from './ChatMessageItem'
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

  const applyChatResponse = useCallback(
    (thinkingId: string, response: ChatResponse) => {
      setMessages((prev) => {
        const withoutThinking = prev.filter((m) => m.id !== thinkingId)
        const next: ChatMessage[] = [
          ...withoutThinking,
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
        if (ui?.kind === 'telemetry_chart') {
          return [
            ...next,
            {
              id: crypto.randomUUID(),
              role: 'telemetry_chart',
              deviceId: ui.device_id,
              deviceName: ui.device_name ?? null,
              metric: ui.metric,
              unit: ui.unit,
              periodLabel: ui.period_label,
              points: ui.points,
            },
          ]
        }
        return next
      })
    },
    [],
  )

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

      const thinkingId = crypto.randomUUID()
      setMessages((prev) => [
        ...prev,
        { id: thinkingId, role: 'assistant', text: '', status: 'thinking' },
      ])

      try {
        const response = await api.postChat({ message: trimmed, session_id: sessionId })
        applyChatResponse(thinkingId, response)
      } catch (err) {
        setMessages((prev) => prev.filter((m) => m.id !== thinkingId))
        const code = err instanceof ApiError ? err.detail : 'chat_failed'
        setError(formatAuthError(code) ?? code)
      } finally {
        setSending(false)
      }
    },
    [adoptPhase, appendAssistant, applyChatResponse, api, sending, sessionId],
  )

  const submitDraft = useCallback(async () => {
    const text = draft.trim()
    if (!text || sending) {
      return
    }
    setDraft('')
    await sendChatMessage(text)
  }, [draft, sendChatMessage, sending])

  const onSubmit = useCallback(
    (event: SubmitEvent<HTMLFormElement>) => {
      event.preventDefault()
      void submitDraft()
    },
    [submitDraft],
  )

  const onComposerKeyDown = useCallback(
    (event: KeyboardEvent<HTMLTextAreaElement>) => {
      if (event.key !== 'Enter' || event.shiftKey || event.nativeEvent.isComposing) {
        return
      }
      event.preventDefault()
      void submitDraft()
    },
    [submitDraft],
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

  const threadEndRef = useRef<HTMLLIElement>(null)
  useEffect(() => {
    threadEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [messages, sending])

  return (
    <div className="mx-auto flex min-h-screen max-w-3xl flex-col px-5 py-8 pb-12">
      <header className="mb-6 flex items-start justify-between gap-4">
        <div>
          <h1 className="text-xl font-semibold tracking-tight">TomatoIA</h1>
          <p className="text-sm text-muted-foreground">
            Olá, <strong className="font-medium text-foreground">{profile.display_name}</strong>
          </p>
        </div>
        <Button type="button" variant="secondary" size="sm" onClick={() => void actions.signOut()}>
          Sair
        </Button>
      </header>

      <ul className="mb-4 flex min-h-60 flex-1 list-none flex-col gap-3 p-0" aria-live="polite">
        {messages.length === 0 && (
          <li className="text-sm text-muted-foreground">Envie uma mensagem para começar.</li>
        )}
        {messages.map((msg) => (
          <ChatMessageItem
            key={msg.id}
            message={msg}
            sending={sending}
            getAccessToken={getAccessToken}
            onRemoveLiveTelemetry={(id) =>
              setMessages((prev) => prev.filter((m) => m.id !== id))
            }
            onPostAdoptionSelect={(prompt) => void sendChatMessage(prompt)}
          />
        ))}
        <li ref={threadEndRef} className="m-0 h-0 list-none p-0" aria-hidden />
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

      {error && <p className="text-sm text-destructive">{error}</p>}

      <form className="flex flex-col" onSubmit={onSubmit}>
        <Textarea
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={onComposerKeyDown}
          placeholder="Digite sua mensagem… (Enter envia, Shift+Enter nova linha)"
          rows={3}
          disabled={sending}
          maxLength={CHAT_MESSAGE_MAX_LENGTH}
          aria-label="Mensagem para o TomatoIA"
        />
      </form>
    </div>
  )
}
