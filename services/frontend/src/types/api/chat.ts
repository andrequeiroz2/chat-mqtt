/**
 * Contrato HTTP do chat — espelha `ChatRequest` / resposta JSON de POST /chat.
 */

export type ChatRequest = {
  message: string
  session_id: string
}

export type TelemetryChartPoint = {
  received_at: string
  value: number
}

export type RealtimeTelemetrySuggestedUi = {
  kind: 'realtime_telemetry'
  device_id: string
  device_name: string | null
}

export type TelemetryChartSuggestedUi = {
  kind: 'telemetry_chart'
  device_id: string
  device_name: string | null
  metric: string
  unit: string | null
  period_label: string
  points: TelemetryChartPoint[]
}

export type SuggestedUiAction = RealtimeTelemetrySuggestedUi | TelemetryChartSuggestedUi

export type ChatResponse = {
  reply: string
  session_id: string
  persisted: boolean
  suggested_ui?: SuggestedUiAction | null
}

export type PostAdoptionActionId =
  | 'read_latest'
  | 'realtime'
  | 'list_devices'
  | 'actuator_help'

export type PostAdoptionAction = {
  action_id: PostAdoptionActionId
  label: string
  prompt: string
  disabled?: boolean
}

export type PostAdoptionRequest = {
  session_id: string
  device_id: string
}

export type PostAdoptionResponse = {
  message: string
  session_id: string
  device_id: string
  device_name: string | null
  device_type: 'sensor' | 'actuator'
  actions: PostAdoptionAction[]
}
