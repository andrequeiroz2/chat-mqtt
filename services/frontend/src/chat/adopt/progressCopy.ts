import type { AdoptionSessionStatus } from '../../types/api/adoption'

const STATUS_COPY: Partial<Record<AdoptionSessionStatus, string>> = {
  started: 'Iniciando pareamento…',
  device_verified: 'Dispositivo reconhecido, validando…',
  config_sent: 'Enviando configuração ao dispositivo…',
  awaiting_device_ack: 'Aguardando confirmação do dispositivo…',
  committed: 'Pronto! Seu dispositivo foi adicionado.',
}

export function progressCopy(status: AdoptionSessionStatus, userMessage: string | null): string {
  if (status === 'failed' || status === 'expired') {
    return userMessage ?? 'A adoção não foi concluída. Nada foi salvo na sua conta.'
  }
  return STATUS_COPY[status] ?? 'Processando adoção…'
}

export const PRECHECK_ASSISTANT =
  'Vamos adicionar seu dispositivo à conta. Antes de continuar: ele está ligado e já conectado ao Wi‑Fi (mesma rede que alcança o serviço)?'

export const SCAN_ASSISTANT =
  'Informe o endereço MAC da placa (formato AA:BB:CC:DD:EE:FF) ou cole o JSON do QR de desenvolvimento. Em seguida inicie o pareamento.'

export const POST_SUCCESS_MENU =
  'O que você gostaria de fazer agora?\n• Ver informações do dispositivo\n• Ver telemetria ou gráficos\n• Enviar comando (se for atuador)\n• Listar todos os seus dispositivos\n\n(Essas ações completas chegam com as ferramentas IoT em breve; por enquanto você pode perguntar no chat.)'
