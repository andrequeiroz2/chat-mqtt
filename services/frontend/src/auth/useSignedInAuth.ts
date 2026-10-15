import type { AuthActions } from '../types/auth'
import type { UserProfile } from '../types/api'
import type { ApiClient } from '../api/client'
import { useAuth } from './useAuth'

export type SignedInAuth = {
  profile: UserProfile
  api: ApiClient
  actions: AuthActions
  getAccessToken: () => Promise<string>
}

/** Só use em telas renderizadas quando `state.status === 'signed_in'`. */
export function useSignedInAuth(): SignedInAuth {
  const { state, actions } = useAuth()
  if (state.status !== 'signed_in') {
    throw new Error('useSignedInAuth requires signed_in auth state')
  }
  return {
    profile: state.profile,
    api: state.api,
    actions,
    getAccessToken: () => state.firebaseUser.getIdToken(),
  }
}
