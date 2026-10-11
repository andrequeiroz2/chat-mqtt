/** Mensagens PT para códigos `detail` da API / auth. */

const MESSAGES: Record<string, string> = {
  api_unreachable:
    'Não foi possível contactar a API. Confira se o backend está no ar (uv run mqtt-chat-api) e VITE_API_BASE_URL no .env.',
  firebase_not_configured:
    'Backend sem Firebase configurado (FIREBASE_PROJECT_ID e credenciais no .env da raiz).',
  profile_load_failed: 'Falha ao carregar perfil após login.',
  invalid_user_profile_response:
    'Resposta de /me inesperada. Atualize front e back na mesma versão.',
  chat_model_not_configured:
    'Chat indisponível: defina GOOGLE_API_KEY no .env da raiz e reinicie mqtt-chat-api.',
  chat_model_unavailable:
    'Modelo Gemini não existe ou foi descontinuado. No .env da raiz use CHAT_MODEL=google:gemini-3.5-flash e reinicie a API.',
  chat_model_busy:
    'Gemini temporariamente indisponível (503). Aguarde e tente de novo; se persistir, CHAT_MODEL=google:gemini-3.7-flash no .env da raiz.',
  missing_authentication: 'Sessão inválida. Tente entrar de novo.',
  invalid_token: 'Token rejeitado pelo servidor. Verifique o projeto Firebase (mesmo projectId no front e back).',
}

export function formatAuthError(code: string | null): string | null {
  if (!code) {
    return null
  }
  return MESSAGES[code] ?? code
}
