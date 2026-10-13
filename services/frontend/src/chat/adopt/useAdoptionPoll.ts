import { useEffect, useRef } from 'react'

import type { ApiClient } from '../../api/client'
import type { AdoptionSession } from '../../types/api/adoption'

const TERMINAL = new Set(['committed', 'failed', 'expired'])
const POLL_MS = 1500

type Options = {
  sessionId: string | null
  api: ApiClient
  onUpdate: (session: AdoptionSession) => void
  onTerminal: (session: AdoptionSession) => void
}

export function useAdoptionPoll({ sessionId, api, onUpdate, onTerminal }: Options): void {
  const onUpdateRef = useRef(onUpdate)
  const onTerminalRef = useRef(onTerminal)
  onUpdateRef.current = onUpdate
  onTerminalRef.current = onTerminal

  useEffect(() => {
    if (!sessionId) {
      return
    }

    let cancelled = false
    let intervalId: number | undefined

    const stop = () => {
      cancelled = true
      if (intervalId !== undefined) {
        window.clearInterval(intervalId)
        intervalId = undefined
      }
    }

    const tick = async () => {
      try {
        const session = await api.getAdoptionSession(sessionId)
        if (cancelled) {
          return
        }
        if (!TERMINAL.has(session.session_status)) {
          onUpdateRef.current(session)
          return
        }
        onTerminalRef.current(session)
        stop()
      } catch {
        /* polling silencioso; erro global no painel se necessário */
      }
    }

    void tick()
    intervalId = window.setInterval(() => void tick(), POLL_MS)
    return () => {
      stop()
    }
  }, [sessionId, api])
}
