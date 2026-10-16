import { apiBaseUrl } from '../config/env'
import type { AdoptionSession, AdoptionStartRequest } from '../types/api/adoption'
import type { ChatRequest, UserProfile, UserProfileUpdateRequest } from '../types/api'
import type { ChatResponse, PostAdoptionRequest, PostAdoptionResponse } from '../types/api/chat'
import { API_PATHS } from './paths'
import {
  assertAdoptionSession,
  assertChatResponse,
  assertPostAdoptionResponse,
  assertUserProfile,
  parseApiErrorBody,
} from './parse'

export class ApiError extends Error {
  readonly status: number
  readonly detail: string

  constructor(status: number, detail: string) {
    super(detail)
    this.name = 'ApiError'
    this.status = status
    this.detail = detail
  }
}

async function parseDetail(response: Response): Promise<string> {
  try {
    const raw: unknown = await response.json()
    const body = parseApiErrorBody(raw)
    if (body?.detail && typeof body.detail === 'string') {
      return body.detail
    }
  } catch {
    /* corpo não JSON */
  }
  return response.statusText || 'request_failed'
}

export function createApiClient(getAccessToken: () => Promise<string | null>) {
  async function requestJson(path: string, init: RequestInit = {}): Promise<unknown> {
    const token = await getAccessToken()
    if (!token) {
      throw new ApiError(401, 'not_authenticated')
    }

    const headers = new Headers(init.headers)
    headers.set('Authorization', `Bearer ${token}`)
    if (init.body && !headers.has('Content-Type')) {
      headers.set('Content-Type', 'application/json')
    }

    const response = await fetch(`${apiBaseUrl}${path}`, {
      ...init,
      headers,
    })

    if (!response.ok) {
      throw new ApiError(response.status, await parseDetail(response))
    }

    return response.json() as Promise<unknown>
  }

  return {
    getMe: async (): Promise<UserProfile> =>
      assertUserProfile(await requestJson(API_PATHS.me)),

    patchDisplayName: async (display_name: UserProfileUpdateRequest['display_name']): Promise<UserProfile> => {
      const body: UserProfileUpdateRequest = { display_name }
      return assertUserProfile(
        await requestJson(API_PATHS.me, {
          method: 'PATCH',
          body: JSON.stringify(body),
        }),
      )
    },

    postChat: async (body: ChatRequest): Promise<ChatResponse> =>
      assertChatResponse(
        await requestJson(API_PATHS.chat, {
          method: 'POST',
          body: JSON.stringify(body),
        }),
      ),

    postChatPostAdoption: async (body: PostAdoptionRequest): Promise<PostAdoptionResponse> =>
      assertPostAdoptionResponse(
        await requestJson(API_PATHS.chatPostAdoption, {
          method: 'POST',
          body: JSON.stringify(body),
        }),
      ),

    postAdoptStart: async (body: AdoptionStartRequest): Promise<AdoptionSession> =>
      assertAdoptionSession(
        await requestJson(API_PATHS.adoptStart, {
          method: 'POST',
          body: JSON.stringify(body),
        }),
      ),

    getAdoptionSession: async (sessionId: string): Promise<AdoptionSession> =>
      assertAdoptionSession(await requestJson(API_PATHS.adoptSession(sessionId))),

    cancelAdoptionSession: async (sessionId: string): Promise<AdoptionSession> =>
      assertAdoptionSession(
        await requestJson(API_PATHS.adoptCancel(sessionId), { method: 'POST' }),
      ),
  }
}

export type ApiClient = ReturnType<typeof createApiClient>
