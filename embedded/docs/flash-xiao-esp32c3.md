# Flash — Seeed XIAO ESP32C3 + MicroPython

## Pré-requisitos

- Cabo USB-C data
- Linux: usuário no grupo `dialout` (acesso `/dev/ttyACM0`)
- [esptool](https://docs.espressif.com/projects/esptool/en/latest/esp32c3/esptool/basic-options.html): `pip install esptool` ou equivalente

## Baixar firmware

1. Abra [MicroPython — SEEED_XIAO_ESP32C3](https://micropython.org/download/SEEED_XIAO_ESP32C3/).
2. Baixe **v1.29.0** (ou a versão pinada em [`task/010-embedded-esp32c3-micropython.md`](../../task/010-embedded-esp32c3-micropython.md)) — arquivo `.bin`.

## Apagar flash

Substitua `PORT` por `/dev/ttyACM0` (Linux), `/dev/cu.usbmodem*` (macOS) ou `COMx` (Windows):

```bash
esptool.py --chip esp32c3 --port PORT erase_flash
```

## Gravar MicroPython

```bash
esptool.py --chip esp32c3 --port PORT write_flash 0 SEEED_XIAO_ESP32C3-*.bin
```

## Copiar aplicação

Ver [`../README.md`](../README.md) — arquivos em `embedded/firmware/` para a raiz do filesystem (`boot.py`, `main.py`, módulos `.py`).

## mpremote (instalação)

```bash
uv tool install mpremote
# PATH: ~/.local/bin/mpremote
```

## REPL

```bash
mpremote connect PORT repl
```

Importação manual de teste: `import main; main.run()` se necessário.
