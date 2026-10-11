import { useAuth } from '../auth/useAuth'
import { ChatScreen } from '../chat/ChatScreen'
import { LoadingScreen } from './LoadingScreen'
import { SignedOutScreen } from './SignedOutScreen'

/** Variantes explícitas por estado de auth (sem props booleanas no layout). */
export function AppRoot() {
  const { state } = useAuth()

  switch (state.status) {
    case 'loading':
      return <LoadingScreen />
    case 'signed_out':
      return <SignedOutScreen />
    case 'signed_in':
      return <ChatScreen />
  }
}
