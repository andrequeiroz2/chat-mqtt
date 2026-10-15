import { useEffect, useRef, useState } from 'react'

import { realtimeConnectionManager } from './manager'
import type { RealtimeTelemetryPayload } from './types'

export type LiveTelemetryState = {
  connected: boolean
  lastTelemetry: RealtimeTelemetryPayload | null
  lastError: string | null
}

type UseRealtimeStreamOptions = {
  /** Retorna Firebase ID token (renovado). */
  getAccessToken: () => Promise<string | null>
  deviceId?: string | null
  enabled?: boolean
}

/** Assina telemetria/status ao vivo via WebSocket autenticado (uma conexão por aba). */
export function useRealtimeStream({
  getAccessToken,
  deviceId,
  enabled = true,
}: UseRealtimeStreamOptions): LiveTelemetryState {
  const [connected, setConnected] = useState(false)
  const [lastTelemetry, setLastTelemetry] = useState<RealtimeTelemetryPayload | null>(null)
  const [lastError, setLastError] = useState<string | null>(null)
  const getTokenRef = useRef(getAccessToken)
  getTokenRef.current = getAccessToken

  useEffect(() => {
    if (!enabled) {
      return undefined
    }

    return realtimeConnectionManager.acquire(
      () => getTokenRef.current(),
      deviceId,
      (payload) => setLastTelemetry(payload),
      (isConnected, error) => {
        setConnected(isConnected)
        if (error) {
          setLastError(error)
        }
      },
    )
  }, [deviceId, enabled])

  return { connected, lastTelemetry, lastError }
}
