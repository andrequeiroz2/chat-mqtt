"""Worker state → last_reported_state (011-i)."""

from mqtt_chat.services.telemetry import LAST_REPORTED_STATE_MAX_BYTES, summarize_state_payload


def test_summarize_state_small_payload_unchanged() -> None:
    raw = {"action": "set", "channel": 1, "value": 1, "command_id": "abc"}
    assert summarize_state_payload(raw) == raw


def test_summarize_state_large_payload_truncated() -> None:
    raw = {"action": "set", "value": 1, "blob": "x" * (LAST_REPORTED_STATE_MAX_BYTES + 100)}
    slim = summarize_state_payload(raw)
    assert slim.get("_truncated") is True
    assert "blob" not in slim
    assert slim.get("value") == 1
