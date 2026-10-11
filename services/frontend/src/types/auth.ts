import type { User } from 'firebase/auth'

import type { ApiClient } from '../api/client'
import type { UserProfile } from './api'

export type AuthStatus = 'loading' | 'signed_out' | 'signed_in'

/** União discriminada por `status` — evita `profile`/`api` nulos quando autenticado. */
export type AuthState =
  | {
      status: 'loading'
      firebaseUser: null
      profile: null
      api: null
      error: null
    }
  | {
      status: 'signed_out'
      firebaseUser: null
      profile: null
      api: null
      error: string | null
    }
  | {
      status: 'signed_in'
      firebaseUser: User
      profile: UserProfile
      api: ApiClient
      error: null
    }

export type AuthActions = {
  signInWithGoogle: () => Promise<void>
  signOut: () => Promise<void>
  refreshProfile: () => Promise<void>
}

export type AuthContextValue = {
  state: AuthState
  actions: AuthActions
}

export type SignedInAuthSlice = Extract<AuthState, { status: 'signed_in' }>
