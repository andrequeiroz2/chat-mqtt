# Persistência pós-adoção (flash)

CONFIG_PATH = "/device_config.json"


def load():
    try:
        import ujson as json
    except ImportError:
        import json

    try:
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def save(data):
    try:
        import ujson as json
    except ImportError:
        import json

    with open(CONFIG_PATH, "w") as f:
        json.dump(data, f)
    return True


def is_adopted():
    cfg = load()
    if not cfg:
        return False
    return cfg.get("adopted_status") == 1
