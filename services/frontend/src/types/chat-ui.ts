import type { PostAdoptionAction } from './api/chat'

/** Estado local da UI de chat (não persistido no backend nesta fase). */

export type ChatMessageRole =
  | 'user'
  | 'assistant'
  | 'live_telemetry'
  | 'telemetry_chart'
  | 'post_adoption'

export type ChatMessage =
  | {
      id: string
      role: 'user' | 'assistant'
      text: string
      /** Placeholder enquanto aguarda `POST /chat` (RF-UX-STREAM-02). */
      status?: 'thinking'
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
  | {
      id: string
      role: 'telemetry_chart'
      deviceId: string
      deviceName: string | null
      metric: string
      unit: string | null
      periodLabel: string
      points: { received_at: string; value: number }[]
    }

/** ID de sessão enviado em `ChatRequest.session_id`. */
export type ChatSessionId = string
