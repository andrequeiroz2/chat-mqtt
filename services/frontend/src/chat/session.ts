import type { ChatSessionId } from '../types/chat-ui'

const STORAGE_KEY = 'mqtt_chat_session_id'

export function getOrCreateChatSessionId(): ChatSessionId {
  const existing = sessionStorage.getItem(STORAGE_KEY)
  if (existing) {
    return existing
  }
  const id = crypto.randomUUID()
  sessionStorage.setItem(STORAGE_KEY, id)
  return id
}
