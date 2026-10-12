import { useAuth } from '../auth/useAuth'
import { formatAuthError } from './auth-error-messages'

export function SignedOutScreen() {
  const { state, actions } = useAuth()
  const errorMessage = formatAuthError(state.error)

  return (
    <div className="auth-shell">
      <h1>TomatoIA</h1>
      <p className="lead">Assistente IoT do seu painel — entre com Google para continuar.</p>
      <p className="muted" style={{ fontSize: '0.9rem' }}>
        Após o Google, a URL continua a mesma; a tela de chat abre aqui (SPA).
      </p>
      {errorMessage && <p className="auth-error">{errorMessage}</p>}
      <button type="button" className="btn primary" onClick={() => void actions.signInWithGoogle()}>
        Entrar com Google
      </button>
    </div>
  )
}
