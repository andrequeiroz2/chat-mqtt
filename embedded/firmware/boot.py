# boot.py — XIAO ESP32C3 (MicroPython)
import esp
import gc
import machine

esp.osdebug(None)
gc.collect()
# ESP32-C3: 160 MHz típico (ver device_app embedded)
machine.freq(160000000)
