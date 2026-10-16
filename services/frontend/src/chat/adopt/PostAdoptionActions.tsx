import type { PostAdoptionAction } from '../../types/api/chat'

type Props = {
  actions: PostAdoptionAction[]
  disabled: boolean
  onSelect: (prompt: string) => void
}

export function PostAdoptionActions({ actions, disabled, onSelect }: Props) {
  if (actions.length === 0) {
    return null
  }
  return (
    <div className="post-adoption-actions" role="group" aria-label="Próximas ações">
      {actions.map((action) => (
        <button
          key={action.action_id}
          type="button"
          className="btn secondary post-adoption-chip"
          disabled={disabled || action.disabled === true}
          title={
            action.disabled
              ? 'Disponível quando o sensor estiver online'
              : undefined
          }
          onClick={() => onSelect(action.prompt)}
        >
          {action.label}
        </button>
      ))}
    </div>
  )
}
