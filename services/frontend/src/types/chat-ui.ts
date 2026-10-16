import type { PostAdoptionAction } from './api/chat'

/** Estado local da UI de chat (não persistido no backend nesta fase). */

export type ChatMessageRole = 'user' | 'assistant' | 'live_telemetry' | 'post_adoption'

export type ChatMessage =
  | {
      id: string
      role: 'user' | 'assistant'
      text: string
    }
  | {
      id: string
      role: 'post_adoption'
      text: string
      actions: PostAdoptionAction[]
    }
  | {
      id: string
      role: 'live_telemetry'
      deviceId: string
      deviceName: string | null
    }

/** ID de sessão enviado em `ChatRequest.session_id`. */
export type ChatSessionId = string
