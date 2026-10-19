import { useEffect, useState, type FormEvent } from 'react'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import type { ApiClient } from '../../api/client'
import type { AdoptionSession } from '../../types/api/adoption'
import { ApiError } from '../../api/client'
import { formatAuthError } from '../../app/auth-error-messages'
import { parseMacFromUserInput } from './parseMacInput'
import { progressCopy, SCAN_ASSISTANT } from './progressCopy'
import { useAdoptionPoll } from './useAdoptionPoll'

export type AdoptWizardPhase = 'precheck' | 'scan' | 'adopting' | 'done'

export type AdoptPhaseMeta = {
  committed: boolean
  deviceId?: string | null
  deviceName?: string | null
}

type Props = {
  api: ApiClient
  phase: AdoptWizardPhase
  onPhaseChange: (phase: AdoptWizardPhase, meta?: AdoptPhaseMeta) => void
  onAssistantLine: (text: string) => void
  onClose: () => void
}

export function AdoptWizardPanel({
  api,
  phase,
  onPhaseChange,
  onAssistantLine,
  onClose,
}: Props) {
  const [macInput, setMacInput] = useState('')
  const [deviceName, setDeviceName] = useState('Meu sensor')
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [lastStatus, setLastStatus] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [pollOffline, setPollOffline] = useState(false)

  // 016-01: ao voltar para precheck, limpa dados da tentativa anterior (evita MAC/sessão fantasma).
  useEffect(() => {
    if (phase !== 'precheck') {
      return
    }
    setMacInput('')
    setDeviceName('Meu sensor')
    setSessionId(null)
    setLastStatus(null)
    setError(null)
    setPollOffline(false)
  }, [phase])

  useAdoptionPoll({
    sessionId: phase === 'adopting' ? sessionId : null,
    api,
    onUpdate: (session: AdoptionSession) => {
      const line = progressCopy(session.session_status, session.user_message)
      if (line !== lastStatus) {
        setLastStatus(line)
        onAssistantLine(line)
      }
    },
    onTerminal: (session: AdoptionSession) => {
      onAssistantLine(progressCopy(session.session_status, session.user_message))
      onPhaseChange('done', {
        committed: session.session_status === 'committed',
        deviceId: session.device_id,
        deviceName: session.device_name,
      })
    },
    onConnectivityChange: (connected) => setPollOffline(!connected),
  })

  async function startAdoption(event: FormEvent) {
    event.preventDefault()
    setError(null)
    const mac = parseMacFromUserInput(macInput)
    if (!mac) {
      setError('MAC inválido. Use AA:BB:CC:DD:EE:FF ou 12 caracteres hex.')
      return
    }

    try {
      const session = await api.postAdoptStart({
        mac_address: mac,
        device_name: deviceName.trim() || 'Meu dispositivo',
      })
      setSessionId(session.session_id)
      setLastStatus(null)
      onPhaseChange('adopting')
      onAssistantLine('Pareamento iniciado. Aguarde…')
    } catch (err) {
      const code = err instanceof ApiError ? err.detail : 'adopt_start_failed'
      setError(formatAuthError(code) ?? 'Não foi possível iniciar a adoção.')
    }
  }

  if (phase === 'precheck') {
    return (
      <Card className="mb-4">
        <CardHeader>
          <CardTitle className="text-sm">Adicionar dispositivo</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-2">
          <Button
            type="button"
            variant="secondary"
            onClick={() => {
              onAssistantLine(SCAN_ASSISTANT)
              onPhaseChange('scan')
            }}
          >
            Sim, está ligado e no Wi‑Fi
          </Button>
          <Button type="button" variant="secondary" onClick={onClose}>
            Ainda não
          </Button>
        </CardContent>
      </Card>
    )
  }

  if (phase === 'scan') {
    return (
      <Card className="mb-4">
        <CardHeader>
          <CardTitle className="text-sm">MAC ou QR (dev)</CardTitle>
        </CardHeader>
        <CardContent>
          <form className="flex flex-col gap-3" onSubmit={(e) => void startAdoption(e)}>
            <label className="flex flex-col gap-1.5 text-sm">
              MAC
              <Input
                value={macInput}
                onChange={(e) => setMacInput(e.target.value)}
                placeholder="3C:71:BF:4D:DB:0C"
                autoComplete="off"
              />
            </label>
            <label className="flex flex-col gap-1.5 text-sm">
              Nome amigável
              <Input
                value={deviceName}
                onChange={(e) => setDeviceName(e.target.value)}
                maxLength={120}
              />
            </label>
            {error && <p className="text-sm text-destructive">{error}</p>}
            <div className="flex flex-wrap gap-2">
              <Button type="submit" variant="secondary">
                Iniciar pareamento
              </Button>
              <Button type="button" variant="secondary" onClick={onClose}>
                Cancelar
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    )
  }

  if (phase === 'adopting') {
    return (
      <Card className="mb-4">
        <CardHeader>
          <CardTitle className="text-sm">Pareamento em andamento</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-2">
          <p className="text-sm text-muted-foreground">{lastStatus ?? 'Aguarde…'}</p>
          {pollOffline && (
            <p className="text-sm text-muted-foreground">
              Sem conexão com o servidor. Tentando novamente…
            </p>
          )}
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="mb-4">
      <CardContent className="pt-4">
        <Button type="button" variant="secondary" onClick={onClose}>
          Fechar assistente de adoção
        </Button>
      </CardContent>
    </Card>
  )
}
