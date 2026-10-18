import { useEffect, useState } from 'react'

export function LoadingScreen() {
  const [slow, setSlow] = useState(false)

  useEffect(() => {
    const id = window.setTimeout(() => setSlow(true), 8000)
    return () => window.clearTimeout(id)
  }, [])

  return (
    <div className="mx-auto flex min-h-screen max-w-lg flex-col justify-center gap-3 px-5 py-12">
      <p className="text-sm text-muted-foreground">Carregando sessão…</p>
      <p className="text-sm text-muted-foreground">
        Validando login e carregando perfil no servidor.
      </p>
      {slow && (
        <p className="max-w-md text-sm text-destructive">
          Demorou mais que o normal. Confira se a API está rodando (
          <code className="text-xs">uv run mqtt-chat-api</code>), use{' '}
          <code className="text-xs">http://localhost:5173</code> e abra o DevTools → Rede para
          ver se <code className="text-xs">/api/v1/me</code> responde.
        </p>
      )}
    </div>
  )
}
