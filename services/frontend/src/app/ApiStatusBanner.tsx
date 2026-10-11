import { useEffect, useState } from 'react'

import { isApiReachable } from '../api/health'

export function ApiStatusBanner() {
  const [reachable, setReachable] = useState<boolean | null>(null)

  useEffect(() => {
    let cancelled = false
    void isApiReachable().then((ok) => {
      if (!cancelled) {
        setReachable(ok)
      }
    })
    return () => {
      cancelled = true
    }
  }, [])

  if (reachable !== false) {
    return null
  }

  return (
    <div className="api-banner" role="status">
      Backend offline — na raiz do repo rode <code>uv run mqtt-chat-api</code> e confira{' '}
      <code>VITE_API_BASE_URL</code> (ex.: http://127.0.0.1:8000).
    </div>
  )
}
