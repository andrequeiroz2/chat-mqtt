/** Renderização mínima de **negrito** nas respostas do assistant (templates backend). */

type AssistantMessageTextProps = {
  text: string
}

export function AssistantMessageText({ text }: AssistantMessageTextProps) {
  const parts = text.split(/(\*\*[^*]+\*\*)/g)
  return (
    <>
      {parts.map((part, index) => {
        // 016-10: chave estável (índice + conteúdo) — evita reuse errado ao atualizar texto.
        const key = `${index}:${part}`
        if (part.startsWith('**') && part.endsWith('**') && part.length > 4) {
          return (
            <strong key={key} className="font-semibold text-foreground">
              {part.slice(2, -2)}
            </strong>
          )
        }
        return <span key={key}>{part}</span>
      })}
    </>
  )
}
