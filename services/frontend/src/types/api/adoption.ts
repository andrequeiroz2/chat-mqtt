/** Contratos HTTP adoção (v1.2-dev). */

export type AdoptionSessionStatus =
  | 'started'
  | 'device_verified'
  | 'config_sent'
  | 'awaiting_device_ack'
  | 'committed'
  | 'failed'
  | 'expired'

export type AdoptionStartRequest = {
  mac_address: string
  device_name?: string
}

export type AdoptionSession = {
  session_id: string
  session_status: AdoptionSessionStatus
  mac_address: string
  expires_at: string
  user_message: string | null
  failure_reason: string | null
  device_id: string | null
  device_name: string | null
}
