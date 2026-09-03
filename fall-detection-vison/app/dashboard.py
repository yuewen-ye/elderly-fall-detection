#!/usr/bin/env python3
"""Monitoring dashboard for the elderly fall detection system.

Flask web app with dark surveillance-style UI:
- Upload image or video for fall detection
- Real-time state machine visualization
- Alert level management with escalation
- Event timeline with SQLite persistence
"""

import json
import logging
import sys
import tempfile
import time
from pathlib import Path

import cv2
import numpy as np
from flask import Flask, jsonify, render_template, request

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import yaml

from src.alert_manager import AlertManager
from src.event_store import EventStore
from src.image_detector import ImageFallDetector
from src.pipeline import FallDetectionPipeline
from src.state_machine import StateMachineManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

APP_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = APP_ROOT / "configs" / "system.yaml"

with open(CONFIG_PATH) as f:
    CONFIG = yaml.safe_load(f)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024  # 500MB

event_store = EventStore(CONFIG["storage"]["db_path"])
alert_manager = AlertManager(fallen_timeout_s=CONFIG["state_machine"]["fallen_timeout_s"])
state_mgr = StateMachineManager(
    smooth_frames=CONFIG["state_machine"]["smooth_frames"],
    fallen_timeout_s=CONFIG["state_machine"]["fallen_timeout_s"],
)

_image_detector: ImageFallDetector | None = None
_pipeline: FallDetectionPipeline | None = None


def get_image_detector() -> ImageFallDetector:
    global _image_detector
    if _image_detector is None:
        _image_detector = ImageFallDetector()
    return _image_detector


def get_pipeline() -> FallDetectionPipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = FallDetectionPipeline(device=CONFIG["detection"]["device"])
    return _pipeline


@app.route("/")
def index():
    return render_template("dashboard.html")


@app.route("/api/detect/image", methods=["POST"])
def detect_image_api():
    if "image" not in request.files:
        return jsonify({"error": "No image uploaded"}), 400
    file = request.files["image"]
    img_bytes = np.frombuffer(file.read(), np.uint8)
    img = cv2.imdecode(img_bytes, cv2.IMREAD_COLOR)
    if img is None:
        return jsonify({"error": "Invalid image"}), 400

    detector = get_image_detector()
    result, annotated_bgr = detector.detect(img)

    # Save annotated image
    out_dir = Path(tempfile.mkdtemp(prefix="fall_dash_"))
    out_path = out_dir / "annotated.jpg"
    cv2.imwrite(str(out_path), annotated_bgr)

    persons = []
    for p in result.persons:
        persons.append({
            "person_id": p["person_id"],
            "label": p["label"],
            "confidence": round(p["confidence"], 2),
            "angle_deg": round(p["angle_deg"], 1),
            "aspect_ratio": round(p["aspect_ratio"], 2),
            "cog_height": round(p["cog_height"], 2),
            "triggers": p["triggers"],
        })

    return jsonify({
        "label": result.label,
        "confidence": round(result.confidence, 2),
        "persons_detected": result.persons_detected,
        "persons": persons,
        "annotated_url": f"/api/serve_file?path={out_path}",
    })


@app.route("/api/detect/video", methods=["POST"])
def detect_video_api():
    if "video" not in request.files:
        return jsonify({"error": "No video uploaded"}), 400
    file = request.files["video"]
    tmp_dir = Path(tempfile.mkdtemp(prefix="fall_dash_"))
    in_path = tmp_dir / file.filename
    file.save(str(in_path))

    out_video = tmp_dir / "result.mp4"
    out_json = tmp_dir / "result.json"

    pipeline = get_pipeline()
    t0 = time.time()
    result = pipeline.process_video(
        input_path=str(in_path),
        output_path=str(out_video),
        json_path=str(out_json),
    )
    elapsed = time.time() - t0

    events = result.get("events", [])
    summary = result.get("summary", {})
    transitions = result.get("state_transitions", [])

    # Record fall events in store
    for e in events:
        event_store.record_alert("CRITICAL", f"Fall detected: track {e.get('track_id','?')} conf {e.get('confidence','?')}")

    # Record state transitions and alert escalations
    for t in transitions:
        level = "CRITICAL" if t.get("to") == "fallen" else "WARNING" if t.get("to") == "falling" else "INFO"
        event_store.record_event(
            track_id=t.get("track_id", 0),
            state=t.get("to", "unknown"),
            alert_level=level,
            confidence=0.0,
            frame_num=t.get("frame", 0),
            features=t.get("features", {}),
            reason=t.get("reason", ""),
        )
        if t.get("to") in ("falling", "fallen"):
            event_store.record_alert(level, t.get("reason", ""), None)

    return jsonify({
        "total_falls": summary.get("total_falls", 0),
        "persons_tracked": summary.get("persons_tracked", 0),
        "elapsed_s": round(elapsed, 1),
        "events": events,
        "state_transitions": transitions,
        "video_url": f"/api/serve_file?path={out_video}",
    })


@app.route("/api/events")
def get_events():
    return jsonify(event_store.recent_events(50))


@app.route("/api/alerts")
def get_alerts():
    return jsonify(event_store.unacknowledged_alerts())


@app.route("/api/alerts/ack", methods=["POST"])
def ack_alert():
    data = request.get_json()
    if "alert_id" in data:
        event_store.acknowledge_alert(data["alert_id"])
    return jsonify({"ok": True})


@app.route("/api/stats")
def get_stats():
    return jsonify(event_store.stats())


@app.route("/api/serve_file")
def serve_file():
    from flask import send_file
    path = request.args.get("path", "")
    p = Path(path)
    if not p.exists():
        return jsonify({"error": "File not found"}), 404
    return send_file(str(p))


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001, debug=False)
