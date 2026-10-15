/**
 * Contrato HTTP do chat — espelha `ChatRequest` / resposta JSON de POST /chat.
 */

export type ChatRequest = {
  message: string
  session_id: string
}

export type SuggestedUiAction = {
  kind: 'realtime_telemetry'
  device_id: string
  device_name: string | null
}

export type ChatResponse = {
  reply: string
  session_id: string
  persisted: boolean
  suggested_ui?: SuggestedUiAction | null
}
