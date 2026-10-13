import type { ApiErrorBody } from '../types/api'
import type { AdoptionSession, AdoptionSessionStatus } from '../types/api/adoption'
import type { ChatResponse } from '../types/api/chat'
import type { UserProfile } from '../types/api/user'

const SESSION_STATUSES: AdoptionSessionStatus[] = [
  'started',
  'device_verified',
  'config_sent',
  'awaiting_device_ack',
  'committed',
  'failed',
  'expired',
]

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null
}

function isString(value: unknown): value is string {
  return typeof value === 'string'
}

function isStringArray(value: unknown): value is string[] {
  return Array.isArray(value) && value.every((item) => typeof item === 'string')
}

function isOptionalNullableString(value: unknown): boolean {
  return value === undefined || value === null || isString(value)
}

export function isUserProfile(value: unknown): value is UserProfile {
  if (!isRecord(value)) {
    return false
  }
  const providers = value.auth_providers
  const providersOk =
    providers === undefined || isStringArray(providers)
  return (
    isString(value.user_id) &&
    isOptionalNullableString(value.email) &&
    isString(value.display_name) &&
    isOptionalNullableString(value.photo_url) &&
    providersOk &&
    isString(value.created_at) &&
    isString(value.updated_at)
  )
}

/** Normaliza JSON da API para `UserProfile` (defaults de campos opcionais). */
export function normalizeUserProfile(value: UserProfile): UserProfile {
  return {
    ...value,
    email: value.email ?? null,
    photo_url: value.photo_url ?? null,
    auth_providers: value.auth_providers ?? [],
  }
}

export function isChatResponse(value: unknown): value is ChatResponse {
  if (!isRecord(value)) {
    return false
  }
  return (
    isString(value.reply) &&
    isString(value.session_id) &&
    typeof value.persisted === 'boolean'
  )
}

export function parseApiErrorBody(value: unknown): ApiErrorBody | null {
  if (!isRecord(value)) {
    return null
  }
  const { detail } = value
  if (detail === undefined) {
    return {}
  }
  if (isString(detail)) {
    return { detail }
  }
  if (Array.isArray(detail)) {
    return { detail: detail as ApiErrorBody['detail'] }
  }
  return null
}

export function assertUserProfile(value: unknown): UserProfile {
  if (!isUserProfile(value)) {
    throw new Error('invalid_user_profile_response')
  }
  return normalizeUserProfile(value)
}

export function assertChatResponse(value: unknown): ChatResponse {
  if (!isChatResponse(value)) {
    throw new Error('invalid_chat_response')
  }
  return value
}

export function isAdoptionSession(value: unknown): value is AdoptionSession {
  if (!isRecord(value)) {
    return false
  }
  const status = value.session_status
  return (
    isString(value.session_id) &&
    isString(status) &&
    SESSION_STATUSES.includes(status as AdoptionSessionStatus) &&
    isString(value.mac_address) &&
    isString(value.expires_at) &&
    isOptionalNullableString(value.user_message) &&
    isOptionalNullableString(value.failure_reason) &&
    isOptionalNullableString(value.device_id) &&
    isOptionalNullableString(value.device_name)
  )
}

export function assertAdoptionSession(value: unknown): AdoptionSession {
  if (!isAdoptionSession(value)) {
    throw new Error('invalid_adoption_session_response')
  }
  return value
}
