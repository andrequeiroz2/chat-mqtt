"""
Pacote de logging estruturado do mqtt-chat.

Arquitetura (camadas):

    worker / api / services / clients
              │
              ▼
         emit.log_event(logger, level, event, message, **attributes)
              │
              ▼
    logging.Logger (stdlib) + extra { event, attributes }
              │
              ▼
    SecretRedactionFilter → JsonLogFormatter | TextLogFormatter → stdout

Documentação: docs/logging.md

Uso:

    from mqtt_chat.logging import setup_logging, log_event, events

    setup_logging(level="INFO", log_format="json")
    log = logging.getLogger(__name__)
    log_event(log, logging.INFO, events.MQTT_CONNECTED, "Connected to broker", host="127.0.0.1")
"""

from mqtt_chat.logging import events
from mqtt_chat.logging.emit import log_event
from mqtt_chat.logging.setup import setup_logging

__all__ = ["setup_logging", "log_event", "events"]
