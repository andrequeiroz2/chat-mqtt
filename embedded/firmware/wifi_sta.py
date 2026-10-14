# Conexão WiFi station (credenciais fixas em secrets_wifi)


def connect_wifi(ssid, password, timeout_s=20):
    import network
    import time

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if wlan.isconnected() and wlan.config("essid") == ssid:
        return True, wlan.ifconfig()[0]

    wlan.connect(ssid, password)
    deadline = time.ticks_add(time.ticks_ms(), timeout_s * 1000)
    while time.ticks_diff(deadline, time.ticks_ms()) > 0:
        if wlan.isconnected():
            return True, wlan.ifconfig()[0]
        time.sleep_ms(250)

    return False, None
