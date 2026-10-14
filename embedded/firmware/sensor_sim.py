# Leituras aleatórias dentro de parameter_ranges (substituto DHT11 em dev)

import random

import device_profile


def random_readings():
    """
    Gera uma leitura por métrica em PARAMETER_RANGES.
    value ∈ [min_reading, max_reading].
    """
    readings = []
    ranges = device_profile.PARAMETER_RANGES or {}
    for metric, spec in ranges.items():
        lo = float(spec.get("min_reading", 0))
        hi = float(spec.get("max_reading", 100))
        if hi < lo:
            lo, hi = hi, lo
        value = random.uniform(lo, hi)
        value = round(value, 1)
        item = {"metric": metric, "value": value}
        unit = spec.get("unit")
        if unit:
            item["unit"] = unit
        readings.append(item)
    return readings
