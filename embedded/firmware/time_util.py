# Timestamps ISO-8601 UTC (Z)


def iso_utc():
    import time

    y, m, d, H, M, S, _, _ = time.gmtime()
    return "{:04d}-{:02d}-{:02d}T{:02d}:{:02d}:{:02d}Z".format(y, m, d, H, M, S)
