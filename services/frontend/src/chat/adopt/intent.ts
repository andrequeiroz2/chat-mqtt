/** Detecta intenção de instalar/adotar device (RF-UX-ADOPT-01). */

const ADOPT_INTENT =
  /\b(adotar|adote|adota|instalar|instale|instala|parear|pareie)\b/i

const ADOPT_ACQUIRE =
  /\b(comprei|adquiri)\b[\s\S]{0,80}\b(sensor|device|dispositivo|placa)\b/i

const ADOPT_REGISTER_DEVICE =
  /\b(registrar|cadastrar)\b[\s\S]{0,40}\b(device|dispositivo|sensor|placa)\b/i

export function isAdoptionIntent(text: string): boolean {
  const trimmed = text.trim()
  if (!trimmed) {
    return false
  }
  // 016-08: PRODUCT_TELEMETRY_CONTEXT foi removido da condição — ambos os ramos
  // anteriores retornavam a mesma expressão (espelho do bug em que “registros”
  // de telemetria não devem abrir adoção está em tests/test_adopt_intent_frontend.py).
  return (
    ADOPT_INTENT.test(trimmed) ||
    ADOPT_ACQUIRE.test(trimmed) ||
    ADOPT_REGISTER_DEVICE.test(trimmed)
  )
}
