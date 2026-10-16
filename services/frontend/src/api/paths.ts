/** Rotas da API mqtt-chat (sem host). */

export const API_PATHS = {
  me: '/api/v1/me',
  chat: '/api/v1/chat',
  chatPostAdoption: '/api/v1/chat/post-adoption',
  chatStream: '/api/v1/chat/stream',
  adoptStart: '/api/v1/devices/adopt/start',
  adoptSession: (sessionId: string) =>
    `/api/v1/devices/adopt/sessions/${encodeURIComponent(sessionId)}`,
  adoptCancel: (sessionId: string) =>
    `/api/v1/devices/adopt/sessions/${encodeURIComponent(sessionId)}/cancel`,
} as const
