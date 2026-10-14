#!/usr/bin/env python3
"""
Gera QR code **QR-A dev** para adoção mqtt-chat (contrato §3.3).

Payload padrão (JSON) — mesmo formato aceito em `parseMacInput.ts`:
  {"v":1,"mac":"AA:BB:CC:DD:EE:FF"}

Uso:
  uv run --with 'qrcode[pil]' python embedded/scripts/generate_adoption_qr.py --mac AA:BB:CC:DD:EE:FF
  uv run --with 'qrcode[pil]' python embedded/scripts/generate_adoption_qr.py --mac AA:BB:CC:DD:EE:FF --plain
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Repo root on PYTHONPATH when invoked via uv from mqtt-chat
from mqtt_chat.validators.mac_address import InvalidMacAddressError, normalize_mac_address


def _payload(mac: str, *, plain: bool) -> str:
    if plain:
        return mac
    return json.dumps({"v": 1, "mac": mac}, separators=(",", ":"))


def main() -> None:
    parser = argparse.ArgumentParser(description="QR-A dev para adoção (MAC)")
    parser.add_argument(
        "--mac",
        required=True,
        help="MAC da placa (colon ou 12 hex) — ver log 'main: MAC' no serial",
    )
    parser.add_argument(
        "--plain",
        action="store_true",
        help="QR só com texto MAC (sem JSON); também aceito na UI",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("embedded/out/adoption-qr.png"),
        help="Arquivo PNG de saída",
    )
    args = parser.parse_args()

    try:
        mac = normalize_mac_address(args.mac)
    except InvalidMacAddressError:
        print("MAC inválido", file=sys.stderr)
        sys.exit(1)

    payload = _payload(mac, plain=args.plain)

    try:
        import qrcode
    except ImportError:
        print(
            "Instale: uv run --with 'qrcode[pil]' python embedded/scripts/generate_adoption_qr.py ...",
            file=sys.stderr,
        )
        sys.exit(1)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    img = qrcode.make(payload)
    img.save(args.output)

    print("MAC:", mac)
    print("Payload QR:", payload)
    print("Tópico UC-A: unclaimed/devices/" + mac.replace(":", "").upper())
    print("PNG:", args.output.resolve())


if __name__ == "__main__":
    main()
