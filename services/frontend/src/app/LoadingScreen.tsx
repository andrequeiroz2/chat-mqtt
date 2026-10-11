export function LoadingScreen() {
  return (
    <div className="auth-shell">
      <p className="muted">Carregando sessão…</p>
      <p className="muted" style={{ fontSize: '0.9rem' }}>
        Validando login e carregando perfil no servidor.
      </p>
    </div>
  )
}
