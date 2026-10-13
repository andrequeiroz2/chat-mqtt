/** Extrai MAC de texto livre ou JSON QR-A dev `{ "v": 1, "mac": "..." }`. */

const MAC_COLON = /^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$/
const MAC_HEX12 = /^[0-9A-Fa-f]{12}$/

export function parseMacFromUserInput(raw: string): string | null {
  const text = raw.trim()
  if (!text) {
    return null
  }

  try {
    const json = JSON.parse(text) as unknown
    if (typeof json === 'object' && json !== null && 'mac' in json) {
      const mac = (json as { mac: unknown }).mac
      if (typeof mac === 'string') {
        return normalizeMac(mac)
      }
    }
  } catch {
    /* não JSON */
  }

  return normalizeMac(text)
}

function normalizeMac(input: string): string | null {
  const t = input.trim()
  if (MAC_COLON.test(t)) {
    return t.toUpperCase()
  }
  const compact = t.replace(/[-:]/g, '').toUpperCase()
  if (MAC_HEX12.test(compact)) {
    return compact.match(/.{2}/g)!.join(':')
  }
  return null
}
