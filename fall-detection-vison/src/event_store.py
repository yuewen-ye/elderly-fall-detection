"""SQLite-based fall event storage with alert level tracking."""

import json
import logging
import sqlite3
import time
from pathlib import Path

logger = logging.getLogger(__name__)


class EventStore:
    """Persists fall events and alert history to SQLite."""

    def __init__(self, db_path: str | Path = "data/events.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    track_id INTEGER NOT NULL,
                    state TEXT NOT NULL,
                    alert_level TEXT NOT NULL,
                    confidence REAL DEFAULT 0.0,
                    frame_num INTEGER DEFAULT 0,
                    timestamp REAL NOT NULL,
                    duration_s REAL DEFAULT 0.0,
                    features TEXT DEFAULT '{}',
                    reason TEXT DEFAULT '',
                    screenshot_path TEXT DEFAULT ''
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id INTEGER,
                    level TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    message TEXT DEFAULT '',
                    acknowledged INTEGER DEFAULT 0,
                    FOREIGN KEY (event_id) REFERENCES events(id)
                )
            """)

    def record_transition(self, track_id: int, transition, screenshot_path: str = "") -> int:
        """Record a state transition as an event. Returns event id."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """INSERT INTO events (track_id, state, alert_level, confidence, frame_num,
                   timestamp, duration_s, features, reason, screenshot_path)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    track_id,
                    transition.to_state.value,
                    transition.to_state.value.upper() if transition.to_state.value in ("falling", "fallen") else "INFO",
                    transition.confidence,
                    transition.frame_num,
                    transition.timestamp,
                    0.0,
                    json.dumps(transition.features),
                    transition.reason,
                    screenshot_path,
                ),
            )
            return cursor.lastrowid

    def record_event(self, track_id: int, state: str, alert_level: str,
                     confidence: float, frame_num: int,
                     features: dict, reason: str, timestamp: float | None = None) -> int:
        """Record an event from dict data. Returns event id."""
        ts = timestamp if timestamp is not None else time.time()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """INSERT INTO events (track_id, state, alert_level, confidence, frame_num,
                   timestamp, duration_s, features, reason, screenshot_path)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    track_id, state, alert_level, confidence, frame_num,
                    ts, 0.0, json.dumps(features), reason, "",
                ),
            )
            return cursor.lastrowid

    def record_alert(self, level: str, message: str, event_id: int | None = None) -> int:
        """Record an alert. Returns alert id."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "INSERT INTO alerts (event_id, level, timestamp, message) VALUES (?, ?, ?, ?)",
                (event_id, level, time.time(), message),
            )
            return cursor.lastrowid

    def acknowledge_alert(self, alert_id: int):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("UPDATE alerts SET acknowledged = 1 WHERE id = ?", (alert_id,))

    def recent_events(self, limit: int = 50) -> list[dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM events ORDER BY timestamp DESC LIMIT ?", (limit,)
            ).fetchall()
            return [dict(r) for r in rows]

    def unacknowledged_alerts(self) -> list[dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM alerts WHERE acknowledged = 0 ORDER BY timestamp DESC"
            ).fetchall()
            return [dict(r) for r in rows]

    def stats(self) -> dict:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            total = conn.execute("SELECT COUNT(*) as c FROM events").fetchone()["c"]
            falls = conn.execute(
                "SELECT COUNT(*) as c FROM events WHERE state IN ('falling','fallen')"
            ).fetchone()["c"]
            critical = conn.execute(
                "SELECT COUNT(*) as c FROM events WHERE alert_level = 'CRITICAL'"
            ).fetchone()["c"]
            emergency = conn.execute(
                "SELECT COUNT(*) as c FROM alerts WHERE level = 'EMERGENCY'"
            ).fetchone()["c"]
            unack = conn.execute(
                "SELECT COUNT(*) as c FROM alerts WHERE acknowledged = 0"
            ).fetchone()["c"]
            return {
                "total_events": total,
                "total_falls": falls,
                "critical_alerts": critical,
                "emergency_alerts": emergency,
                "unacknowledged": unack,
            }
