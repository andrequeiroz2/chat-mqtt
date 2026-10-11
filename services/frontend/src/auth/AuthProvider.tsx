import {
  GoogleAuthProvider,
  onAuthStateChanged,
  signInWithPopup,
  signOut as firebaseSignOut,
  type User,
} from 'firebase/auth'
import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'

import { ApiError, createApiClient } from '../api/client'
import type { AuthState } from '../types/auth'
import { auth } from '../lib/firebase'
import { AuthContext } from './auth-context'

const googleProvider = new GoogleAuthProvider()

const initialState: AuthState = {
  status: 'loading',
  firebaseUser: null,
  profile: null,
  api: null,
  error: null,
}

function mapProfileError(err: unknown): string {
  if (err instanceof ApiError) {
    return err.detail
  }
  if (err instanceof TypeError) {
    return 'api_unreachable'
  }
  if (err instanceof Error && err.message === 'invalid_user_profile_response') {
    return 'invalid_user_profile_response'
  }
  return 'profile_load_failed'
}

async function loadSignedInState(user: User): Promise<Extract<AuthState, { status: 'signed_in' }>> {
  const api = createApiClient(() => user.getIdToken())
  const profile = await api.getMe()
  return {
    status: 'signed_in',
    firebaseUser: user,
    profile,
    api,
    error: null,
  }
}

const loadingState: AuthState = {
  status: 'loading',
  firebaseUser: null,
  profile: null,
  api: null,
  error: null,
}

type AuthProviderProps = {
  children: ReactNode
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [state, setState] = useState<AuthState>(initialState)

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (user) => {
      if (!user) {
        setState({
          status: 'signed_out',
          firebaseUser: null,
          profile: null,
          api: null,
          error: null,
        })
        return
      }

      setState(loadingState)
      try {
        setState(await loadSignedInState(user))
      } catch (err) {
        const detail = mapProfileError(err)
        setState({
          status: 'signed_out',
          firebaseUser: null,
          profile: null,
          api: null,
          error: detail,
        })
        await firebaseSignOut(auth)
      }
    })

    return () => unsubscribe()
  }, [])

  const signInWithGoogle = useCallback(async () => {
    setState((prev) => {
      if (prev.status === 'loading') {
        return prev
      }
      return { ...prev, error: null }
    })
    try {
      await signInWithPopup(auth, googleProvider)
    } catch {
      /* popup fechado ou cancelado — onAuthStateChanged não dispara login */
    }
  }, [])

  const signOut = useCallback(async () => {
    await firebaseSignOut(auth)
  }, [])

  const refreshProfile = useCallback(async () => {
    const user = auth.currentUser
    if (!user) {
      return
    }
    const next = await loadSignedInState(user)
    setState((prev) => (prev.status === 'signed_in' ? next : prev))
  }, [])

  const value = useMemo(
    () => ({
      state,
      actions: { signInWithGoogle, signOut, refreshProfile },
    }),
    [state, signInWithGoogle, signOut, refreshProfile],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
