import { apiBaseUrl } from '../config/env'

/** Verifica se o backend mqtt-chat-api responde (sem auth). */
export async function isApiReachable(): Promise<boolean> {
  try {
    const response = await fetch(`${apiBaseUrl}/health`, { method: 'GET' })
    return response.ok
  } catch {
    return false
  }
}
