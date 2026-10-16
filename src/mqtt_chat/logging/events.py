"""Nomes estáveis de eventos (contrato JSON field `event`)."""

from __future__ import annotations

# MQTT / worker
MQTT_CONNECTED = "mqtt.connected"
MQTT_SUBSCRIBED = "mqtt.subscribed"
MQTT_MESSAGE_RECEIVED = "mqtt.message.received"
MQTT_CONNECTION_LOST = "mqtt.connection.lost"
MQTT_CONNECTION_RESTORED = "mqtt.connection.restored"
MQTT_BACKOFF = "mqtt.backoff"
MQTT_PUBLISHED = "mqtt.published"
MQTT_PUBLISH_FAILED = "mqtt.publish.failed"
MQTT_WORKER_STOPPED = "mqtt.worker.stopped"

# Parse / transform
DEVICE_TOPIC_PARSED = "device.topic.parsed"
TELEMETRY_PARSE_FAILED = "telemetry.parse.failed"
TELEMETRY_PARSE_COMPLETED = "telemetry.parse.completed"

# Persist
TELEMETRY_PERSIST_COMPLETED = "telemetry.persist.completed"
TELEMETRY_PERSIST_FAILED = "telemetry.persist.failed"
DEVICE_METADATA_UPDATED = "device.metadata.updated"

# Firebase
FIREBASE_INITIALIZED = "firebase.initialized"
FIREBASE_UNAVAILABLE = "firebase.unavailable"

# API
API_STARTED = "api.started"
API_SHUTDOWN = "api.shutdown"

# Auth / user profile
AUTH_TOKEN_REJECTED = "auth.token.rejected"
USER_PROFILE_CREATED = "user.profile.created"
USER_PROFILE_UPDATED = "user.profile.updated"
CHAT_TURN_PERSISTED = "chat.turn.persisted"
CHAT_TURN_OFF_TOPIC = "chat.turn.off_topic"
CHAT_RESOLVER_OUTCOME = "chat.resolver.outcome"

# MCP
MCP_TOOL_CALL = "mcp.tool.call"
MCP_TOOL_LIST_DEVICES = "mcp.tool.list_devices"
MCP_TOOL_READ_LATEST_TELEMETRY = "mcp.tool.read_latest_telemetry"
REALTIME_WS_CONNECTED = "realtime.ws.connected"
REALTIME_WS_SEND_FAILED = "realtime.ws.send_failed"
REALTIME_EVENT_PUBLISHED = "realtime.event.published"
MCP_AUTH_REJECTED = "mcp.auth.rejected"

# Adoção
ADOPTION_SESSION_STARTED = "adoption.session.started"
ADOPTION_SESSION_FAILED = "adoption.session.failed"
ADOPTION_SESSION_COMMITTED = "adoption.session.committed"
ADOPTION_MQTT_INFO = "adoption.mqtt.info"
ADOPTION_MQTT_ACK = "adoption.mqtt.ack"

# Genérico
HANDLER_FAILED = "handler.failed"
UNEXPECTED_ERROR = "unexpected.error"
