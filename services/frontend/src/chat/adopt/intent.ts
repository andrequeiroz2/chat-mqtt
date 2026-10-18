/** Detecta intenção de instalar/adotar device (RF-UX-ADOPT-01). */

const ADOPT_INTENT =
  /\b(adotar|adote|adota|instalar|instale|instala|parear|pareie)\b/i

const ADOPT_ACQUIRE =
  /\b(comprei|adquiri)\b[\s\S]{0,80}\b(sensor|device|dispositivo|placa)\b/i

const ADOPT_REGISTER_DEVICE =
  /\b(registrar|cadastrar)\b[\s\S]{0,40}\b(device|dispositivo|sensor|placa)\b/i

/** Telemetria/gráfico — "registros" aqui não é adoção. */
const PRODUCT_TELEMETRY_CONTEXT =
  /\b(gr[aá]fico|historico|hist[oó]rico|telemetria|temperatura|umidade|leitura|ultim[oa]s?\s+(dia|dias|semana))\b/i

export function isAdoptionIntent(text: string): boolean {
  const trimmed = text.trim()
  if (!trimmed) {
    return false
  }
  if (PRODUCT_TELEMETRY_CONTEXT.test(trimmed)) {
    return (
      ADOPT_INTENT.test(trimmed) ||
      ADOPT_ACQUIRE.test(trimmed) ||
      ADOPT_REGISTER_DEVICE.test(trimmed)
    )
  }
  return (
    ADOPT_INTENT.test(trimmed) ||
    ADOPT_ACQUIRE.test(trimmed) ||
    ADOPT_REGISTER_DEVICE.test(trimmed)
  )
}
