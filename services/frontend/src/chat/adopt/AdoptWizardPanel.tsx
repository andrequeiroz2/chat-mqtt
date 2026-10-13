import { useState, type FormEvent } from 'react'

import type { ApiClient } from '../../api/client'
import type { AdoptionSession } from '../../types/api/adoption'
import { ApiError } from '../../api/client'
import { formatAuthError } from '../../app/auth-error-messages'
import { parseMacFromUserInput } from './parseMacInput'
import { progressCopy, SCAN_ASSISTANT } from './progressCopy'
import { useAdoptionPoll } from './useAdoptionPoll'

export type AdoptWizardPhase = 'precheck' | 'scan' | 'adopting' | 'done'

type AdoptPhaseMeta = { committed: boolean }

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
      const committed = session.session_status === 'committed'
      onAssistantLine(progressCopy(session.session_status, session.user_message))
      onPhaseChange('done', { committed })
    },
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
      <div className="adopt-panel">
        <p className="adopt-panel-title">Adicionar dispositivo</p>
        <div className="adopt-actions">
          <button
            type="button"
            className="btn primary"
            onClick={() => {
              onAssistantLine(SCAN_ASSISTANT)
              onPhaseChange('scan')
            }}
          >
            Sim, está ligado e no Wi‑Fi
          </button>
          <button type="button" className="btn secondary" onClick={onClose}>
            Ainda não
          </button>
        </div>
      </div>
    )
  }

  if (phase === 'scan') {
    return (
      <div className="adopt-panel">
        <p className="adopt-panel-title">MAC ou QR (dev)</p>
        <form className="adopt-form" onSubmit={(e) => void startAdoption(e)}>
          <label className="adopt-label">
            MAC
            <input
              value={macInput}
              onChange={(e) => setMacInput(e.target.value)}
              placeholder="3C:71:BF:4D:DB:0C"
              autoComplete="off"
            />
          </label>
          <label className="adopt-label">
            Nome amigável
            <input
              value={deviceName}
              onChange={(e) => setDeviceName(e.target.value)}
              maxLength={120}
            />
          </label>
          {error && <p className="chat-error">{error}</p>}
          <div className="adopt-actions">
            <button type="submit" className="btn primary">
              Iniciar pareamento
            </button>
            <button type="button" className="btn secondary" onClick={onClose}>
              Cancelar
            </button>
          </div>
        </form>
      </div>
    )
  }

  if (phase === 'adopting') {
    return (
      <div className="adopt-panel adopt-panel-progress">
        <p className="adopt-panel-title">Pareamento em andamento</p>
        <p className="muted">{lastStatus ?? 'Aguarde…'}</p>
      </div>
    )
  }

  return (
    <div className="adopt-panel">
      <button type="button" className="btn secondary" onClick={onClose}>
        Fechar assistente de adoção
      </button>
    </div>
  )
}
