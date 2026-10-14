import { useEffect, useState } from 'react'

export function LoadingScreen() {
  const [slow, setSlow] = useState(false)

  useEffect(() => {
    const id = window.setTimeout(() => setSlow(true), 8000)
    return () => window.clearTimeout(id)
  }, [])

  return (
    <div className="auth-shell">
      <p className="muted">Carregando sessão…</p>
      <p className="muted" style={{ fontSize: '0.9rem' }}>
        Validando login e carregando perfil no servidor.
      </p>
      {slow && (
        <p className="auth-error" style={{ fontSize: '0.9rem', maxWidth: '28rem' }}>
          Demorou mais que o normal. Confira se a API está rodando (
          <code>uv run mqtt-chat-api</code>), use <code>http://localhost:5173</code> e abra o
          DevTools → Rede para ver se <code>/api/v1/me</code> responde.
        </p>
      )}
    </div>
  )
}
