import { Button } from '@/components/ui/button'
import { useAuth } from '../auth/useAuth'
import { formatAuthError } from './auth-error-messages'

export function SignedOutScreen() {
  const { state, actions } = useAuth()
  const errorMessage = formatAuthError(state.error)

  return (
    <div className="mx-auto flex min-h-screen max-w-lg flex-col justify-center gap-4 px-5 py-12">
      <h1 className="text-2xl font-semibold tracking-tight">TomatoIA</h1>
      <p className="max-w-md text-base text-foreground">
        Assistente IoT do seu painel — entre com Google para continuar.
      </p>
      <p className="text-sm text-muted-foreground">
        Após o Google, a URL continua a mesma; a tela de chat abre aqui (SPA).
      </p>
      {errorMessage && <p className="text-sm text-destructive">{errorMessage}</p>}
      <Button type="button" variant="secondary" onClick={() => void actions.signInWithGoogle()}>
        Entrar com Google
      </Button>
    </div>
  )
}
