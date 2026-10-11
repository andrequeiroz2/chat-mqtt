/** Rotas da API mqtt-chat (sem host). */

export const API_PATHS = {
  me: '/api/v1/me',
  chat: '/api/v1/chat',
  chatStream: '/api/v1/chat/stream',
} as const satisfies Record<string, `/api/v1/${string}`>
