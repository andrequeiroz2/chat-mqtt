import { apiBaseUrl } from '../config/env'

/** Converte http(s) base da API em ws(s) para o stream tempo real. */
export function buildRealtimeWsUrl(token: string, deviceId?: string | null): string {
  const base = apiBaseUrl.replace(/^http/, 'ws').replace(/\/$/, '')
  const params = new URLSearchParams({ token })
  if (deviceId?.trim()) {
    params.set('device_id', deviceId.trim())
  }
  return `${base}/api/v1/realtime/ws?${params.toString()}`
}
