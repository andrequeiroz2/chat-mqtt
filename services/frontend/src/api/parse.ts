import type { ApiErrorBody } from '../types/api'
import type { ChatResponse } from '../types/api/chat'
import type { UserProfile } from '../types/api/user'

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
  return isString(value.reply) && isString(value.session_id)
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
