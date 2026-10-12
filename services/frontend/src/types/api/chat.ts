/**
 * Contrato HTTP do chat — espelha `ChatRequest` / resposta JSON de POST /chat.
 */

export type ChatRequest = {
  message: string
  session_id: string
}

export type ChatResponse = {
  reply: string
  session_id: string
  persisted: boolean
}
