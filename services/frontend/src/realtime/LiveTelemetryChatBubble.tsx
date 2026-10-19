import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
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

  const title = deviceName ?? 'Sensor'
  const offlineBlocked = lastError === 'device_not_online_for_realtime'

  return (
    <div className="rounded-xl border border-border bg-card px-4 py-3 text-sm text-card-foreground shadow-sm">
      <div className="flex flex-wrap items-center gap-2">
        {/* 016-03: indicador “ao vivo” usa foreground (zinc) — semântico de presença, não verde PoC. */}
        <span
          className={cn(
            'size-2 shrink-0 rounded-full',
            connected ? 'bg-foreground shadow-[0_0_0_2px_var(--ring)]' : 'bg-muted-foreground',
          )}
          aria-hidden
        />
        <strong className="text-sm font-semibold">{title}</strong>
        <Button type="button" variant="secondary" size="sm" className="ml-auto" onClick={onStop}>
          Parar ao vivo
        </Button>
      </div>
      <p className="mt-2 text-xs text-muted-foreground">
        {offlineBlocked
          ? 'Sensor offline ou sem confirmação de presença — tempo real indisponível. Peça a última leitura no chat.'
          : connected
            ? 'Ao vivo'
            : 'Conectando…'}
        {!offlineBlocked && summary ? ` — ${summary}` : ''}
        {!offlineBlocked && connected && !summary ? ' — aguardando telemetria' : ''}
        {!offlineBlocked && lastError && !connected ? ` (${lastError})` : ''}
      </p>
    </div>
  )
}
