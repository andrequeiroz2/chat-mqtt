/** Estado local da UI de chat (não persistido no backend nesta fase). */

export type ChatMessageRole = 'user' | 'assistant'

export type ChatMessage = {
  id: string
  role: ChatMessageRole
  text: string
}

/** ID de sessão enviado em `ChatRequest.session_id`. */
export type ChatSessionId = string
