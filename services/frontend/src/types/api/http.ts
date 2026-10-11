/** Erros JSON do FastAPI (`HTTPException`, validação 422). */

export type ValidationErrorItem = {
  type?: string
  loc?: (string | number)[]
  msg?: string
  input?: unknown
}

export type ApiErrorDetail = string | ValidationErrorItem[]

export type ApiErrorBody = {
  detail?: ApiErrorDetail
}

/** Códigos `detail` string conhecidos do backend mqtt-chat. */
export type KnownApiErrorCode =
  | 'not_authenticated'
  | 'chat_model_not_configured'
  | 'user_profile_not_found'
  | 'request_failed'
