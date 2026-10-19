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
  /** 016-04: chamado quando o polling falha (rede/API) ou volta a responder. */
  onConnectivityChange?: (connected: boolean) => void
}

export function useAdoptionPoll({
  sessionId,
  api,
  onUpdate,
  onTerminal,
  onConnectivityChange,
}: Options): void {
  const onUpdateRef = useRef(onUpdate)
  const onTerminalRef = useRef(onTerminal)
  const onConnectivityRef = useRef(onConnectivityChange)
  onUpdateRef.current = onUpdate
  onTerminalRef.current = onTerminal
  onConnectivityRef.current = onConnectivityChange

  useEffect(() => {
    if (!sessionId) {
      return
    }

    let cancelled = false
    let intervalId: number | undefined
    let hadFailure = false

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
        if (hadFailure) {
          hadFailure = false
          onConnectivityRef.current?.(true)
        }
        if (!TERMINAL.has(session.session_status)) {
          onUpdateRef.current(session)
          return
        }
        onTerminalRef.current(session)
        stop()
      } catch {
        if (!cancelled && !hadFailure) {
          hadFailure = true
          onConnectivityRef.current?.(false)
        }
      }
    }

    void tick()
    intervalId = window.setInterval(() => void tick(), POLL_MS)
    return () => {
      stop()
    }
  }, [sessionId, api])
}
