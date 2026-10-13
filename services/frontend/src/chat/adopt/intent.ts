/** Detecta intenção de instalar/adotar device (RF-UX-ADOPT-01). */

const ADOPT_INTENT =
  /\b(adot|instal|parear|conect|registr|configur).*(device|dispositivo|sensor|placa)?\b|\b(comprei|adquiri).*(sensor|device|dispositivo)\b/i

export function isAdoptionIntent(text: string): boolean {
  return ADOPT_INTENT.test(text.trim())
}
