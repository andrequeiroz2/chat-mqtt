import { Button } from '@/components/ui/button'
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
    <div className="flex flex-wrap gap-2" role="group" aria-label="Próximas ações">
      {actions.map((action) => (
        <Button
          key={action.action_id}
          type="button"
          variant="secondary"
          size="sm"
          disabled={disabled || action.disabled === true}
          title={
            action.disabled ? 'Disponível quando o sensor estiver online' : undefined
          }
          onClick={() => onSelect(action.prompt)}
        >
          {action.label}
        </Button>
      ))}
    </div>
  )
}
