import { useRealtimeStream } from './useRealtimeStream'

type LiveTelemetryChatBubbleProps = {
  deviceId: string
  deviceName: string | null
  getAccessToken: () => Promise<string | null>
  onStop: () => void
}

/** Bolha no thread — WebSocket só enquanto montada (pedido via chat). */
export function LiveTelemetryChatBubble({
  deviceId,
  deviceName,
  getAccessToken,
  onStop,
}: LiveTelemetryChatBubbleProps) {
  const live = useRealtimeStream({
    getAccessToken,
    deviceId,
    enabled: true,
  })

  const { connected, lastTelemetry, lastError } = live
  const readings = lastTelemetry?.readings ?? []
  const summary =
    readings.length > 0
      ? readings
          .map((r) => {
            const unit = r.unit ? ` ${r.unit}` : ''
            return `${r.metric}: ${r.value}${unit}`
          })
          .join(' · ')
      : null

  const title = deviceName ? `${deviceName} (${deviceId.slice(0, 8)}…)` : deviceId

  return (
    <div className="live-telemetry-bubble">
      <div className="live-telemetry-bubble-head">
        <span className={`live-dot ${connected ? 'on' : 'off'}`} aria-hidden />
        <strong style={{ fontSize: '0.9rem' }}>{title}</strong>
        <button type="button" className="btn secondary live-stop" onClick={onStop}>
          Parar ao vivo
        </button>
      </div>
      <p className="muted" style={{ margin: '0.5rem 0 0', fontSize: '0.85rem' }}>
        {connected ? 'Ao vivo' : 'Conectando…'}
        {summary ? ` — ${summary}` : connected && !summary ? ' — aguardando telemetria' : ''}
        {lastError && !connected ? ` (${lastError})` : ''}
      </p>
    </div>
  )
}
