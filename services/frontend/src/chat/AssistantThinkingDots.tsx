/** Indicador de três pontos enquanto o assistant aguarda resposta REST. */

type AssistantThinkingDotsProps = {
  label?: string
}

export function AssistantThinkingDots({ label = 'Pensando' }: AssistantThinkingDotsProps) {
  return (
    <span
      className="inline-flex h-4 items-center gap-1.5"
      role="status"
      aria-live="polite"
      aria-label={label}
    >
      <span className="assistant-thinking-dot size-1.5 rounded-full bg-muted-foreground" aria-hidden />
      <span className="assistant-thinking-dot size-1.5 rounded-full bg-muted-foreground" aria-hidden />
      <span className="assistant-thinking-dot size-1.5 rounded-full bg-muted-foreground" aria-hidden />
    </span>
  )
}
