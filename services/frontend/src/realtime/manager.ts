import type { RealtimeEnvelope, RealtimeTelemetryPayload } from './types'
import { buildRealtimeWsUrl } from './wsUrl'

type TelemetryListener = (payload: RealtimeTelemetryPayload) => void
type StatusListener = (connected: boolean, error: string | null) => void

/** Uma conexão WebSocket por aba — evita storm com Strict Mode / re-renders. */
class RealtimeConnectionManager {
  private ws: WebSocket | null = null
  private refCount = 0
  private deviceKey = '__all__'
  private pingTimer: number | null = null
  private telemetryListeners = new Set<TelemetryListener>()
  private statusListeners = new Set<StatusListener>()
  private lastError: string | null = null

  private notifyStatus(connected: boolean) {
    for (const fn of this.statusListeners) {
      fn(connected, this.lastError)
    }
  }

  private dispatch(msg: RealtimeEnvelope) {
    if (msg.type === 'connected') {
      this.notifyStatus(true)
    } else if (msg.type === 'telemetry') {
      for (const fn of this.telemetryListeners) {
        fn(msg.payload)
      }
    } else if (msg.type === 'error') {
      this.lastError = msg.payload.message ?? msg.payload.code ?? 'realtime_error'
      this.notifyStatus(false)
    }
  }

  private teardown() {
    if (this.pingTimer !== null) {
      window.clearInterval(this.pingTimer)
      this.pingTimer = null
    }
    if (this.ws) {
      this.ws.onopen = null
      this.ws.onmessage = null
      this.ws.onerror = null
      this.ws.onclose = null
      this.ws.close()
      this.ws = null
    }
    this.notifyStatus(false)
  }

  private async open(
    getAccessToken: () => Promise<string | null>,
    deviceId: string | null | undefined,
  ) {
    const key = deviceId?.trim() || '__all__'
    if (
      this.ws &&
      this.deviceKey === key &&
      (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)
    ) {
      return
    }

    this.teardown()
    this.deviceKey = key
    this.lastError = null

    const token = await getAccessToken()
    if (!token) {
      this.lastError = 'not_authenticated'
      this.notifyStatus(false)
      return
    }

    const ws = new WebSocket(buildRealtimeWsUrl(token, deviceId))
    this.ws = ws

    ws.onopen = () => {
      this.pingTimer = window.setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send('ping')
        }
      }, 25_000)
    }

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(String(event.data)) as RealtimeEnvelope
        this.dispatch(msg)
      } catch {
        /* ignore */
      }
    }

    ws.onerror = () => {
      this.lastError = 'websocket_error'
      this.notifyStatus(false)
    }

    ws.onclose = (event) => {
      if (event.code === 4409) {
        this.lastError = 'device_not_online_for_realtime'
      }
      if (this.pingTimer !== null) {
        window.clearInterval(this.pingTimer)
        this.pingTimer = null
      }
      if (this.ws === ws) {
        this.ws = null
      }
      this.notifyStatus(false)
    }
  }

  acquire(
    getAccessToken: () => Promise<string | null>,
    deviceId: string | null | undefined,
    onTelemetry: TelemetryListener,
    onStatus: StatusListener,
  ): () => void {
    this.refCount += 1
    this.telemetryListeners.add(onTelemetry)
    this.statusListeners.add(onStatus)
    void this.open(getAccessToken, deviceId)

    return () => {
      this.telemetryListeners.delete(onTelemetry)
      this.statusListeners.delete(onStatus)
      this.refCount = Math.max(0, this.refCount - 1)
      if (this.refCount === 0) {
        this.teardown()
      }
    }
  }
}

export const realtimeConnectionManager = new RealtimeConnectionManager()
