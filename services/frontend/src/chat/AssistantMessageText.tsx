/** Renderização mínima de **negrito** nas respostas do assistant (templates backend). */

type AssistantMessageTextProps = {
  text: string
}

export function AssistantMessageText({ text }: AssistantMessageTextProps) {
  const parts = text.split(/(\*\*[^*]+\*\*)/g)
  return (
    <>
      {parts.map((part, index) => {
        if (part.startsWith('**') && part.endsWith('**') && part.length > 4) {
          return (
            <strong key={index} className="font-semibold text-foreground">
              {part.slice(2, -2)}
            </strong>
          )
        }
        return <span key={index}>{part}</span>
      })}
    </>
  )
}
