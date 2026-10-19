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
        # Task 017: unit obrigatório no payload; default coerente com metric quando
        # o profile não declarar (evita descarte no worker).
        unit = spec.get("unit") or _DEFAULT_UNIT_BY_METRIC.get(metric, "")
        item = {"metric": metric, "value": value, "unit": unit}
        readings.append(item)
    return readings


_DEFAULT_UNIT_BY_METRIC = {
    "temperature": "C",
    "humidity": "%",
}
