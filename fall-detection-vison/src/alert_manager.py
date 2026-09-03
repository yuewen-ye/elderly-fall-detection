"""Alert level management with escalation logic.

Alert levels: NONE → WARNING → CRITICAL → EMERGENCY
- WARNING: person is FALLING (temporal state, not yet confirmed)
- CRITICAL: person is FALLEN (confirmed)
- EMERGENCY: FALLEN for > fallen_timeout_s without recovery
"""

import logging
import time

logger = logging.getLogger(__name__)


class AlertManager:
    """Manages alert escalation across multiple tracked persons."""

    def __init__(self, fallen_timeout_s: float = 30.0, warning_timeout_s: float = 2.0):
        self.fallen_timeout_s = fallen_timeout_s
        self.warning_timeout_s = warning_timeout_s
        # track_id -> {level, since, last_escalated}
        self.active_alerts: dict[int, dict] = {}

    def update(self, track_id: int, state: str, alert_level: str, fallen_duration_s: float = 0.0) -> dict | None:
        """Update alert for a person. Returns escalation event if level changed."""
        prev = self.active_alerts.get(track_id)

        if alert_level == "NONE":
            if prev:
                del self.active_alerts[track_id]
                logger.info("Track %d: alert cleared (was %s)", track_id, prev["level"])
            return None

        if prev is None:
            self.active_alerts[track_id] = {
                "level": alert_level,
                "since": time.time(),
                "fallen_duration_s": fallen_duration_s,
            }
            logger.info("Track %d: NEW alert %s", track_id, alert_level)
            return {"track_id": track_id, "action": "new", "level": alert_level}

        if alert_level != prev["level"]:
            escalated = alert_level in ("CRITICAL", "EMERGENCY") and alert_level > prev["level"]
            self.active_alerts[track_id]["level"] = alert_level
            self.active_alerts[track_id]["fallen_duration_s"] = fallen_duration_s
            action = "escalated" if escalated else "changed"
            logger.info("Track %d: alert %s %s → %s", track_id, action, prev["level"], alert_level)
            return {"track_id": track_id, "action": action, "level": alert_level, "from": prev["level"]}

        # Timeout escalation: FALLEN too long
        if alert_level == "CRITICAL" and fallen_duration_s >= self.fallen_timeout_s:
            self.active_alerts[track_id]["level"] = "EMERGENCY"
            logger.warning("Track %d: TIMEOUT escalation CRITICAL → EMERGENCY (%.0fs)", track_id, fallen_duration_s)
            return {"track_id": track_id, "action": "escalated", "level": "EMERGENCY", "from": "CRITICAL", "reason": f"FALLEN for {fallen_duration_s:.0f}s"}

        return None

    def get_active(self) -> list[dict]:
        return [
            {"track_id": tid, **info}
            for tid, info in self.active_alerts.items()
        ]

    def clear(self, track_id: int):
        self.active_alerts.pop(track_id, None)
