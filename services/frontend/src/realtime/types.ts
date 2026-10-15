/** Eventos WebSocket — espelho `schemas/realtime.py`. */

export type RealtimeReading = {
  metric: string
  value: number
  unit?: string | null
}

export type RealtimeTelemetryPayload = {
  device_id: string
  device_ts?: string | null
  received_at: string
  readings: RealtimeReading[]
}

export type RealtimeDeviceStatusPayload = {
  device_id: string
  operation_status?: string | null
  last_seen_at?: string | null
}

export type RealtimeEnvelope =
  | { type: 'connected'; payload: { user_id: string; device_id_filter: string | null } }
  | { type: 'telemetry'; payload: RealtimeTelemetryPayload }
  | { type: 'device_status'; payload: RealtimeDeviceStatusPayload }
  | { type: 'error'; payload: { code?: string; message?: string } }
