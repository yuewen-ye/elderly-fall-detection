#!/usr/bin/env python3
"""Batch-run fall detection on every video in test/videos/.

For each ``<name>.mp4`` in ``test/videos/`` this invokes the project pipeline
(``fall-detection-vison/detect_falls.py``) and writes:

- ``test/video_results/result_<name>.mp4``   annotated video
- ``test/video_results/result_<name>.json``  event log

CPU inference takes roughly 2-4x realtime, so long videos need patience.

Usage (from the repo root):

    fall-detection-vison/venv/Scripts/python.exe test/run_all_videos.py
"""

import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PROJECT = REPO_ROOT / "fall-detection-vison"
DETECT = PROJECT / "detect_falls.py"
VIDEO_DIR = REPO_ROOT / "test" / "videos"
RESULT_DIR = REPO_ROOT / "test" / "video_results"

VIDEO_EXTS = {".mp4", ".avi", ".mov", ".mkv"}


def main() -> int:
    python = PROJECT / "venv" / "Scripts" / "python.exe"
    if not python.exists():
        python = Path(sys.executable)

    videos = sorted(p for p in VIDEO_DIR.iterdir() if p.suffix.lower() in VIDEO_EXTS)
    if not videos:
        print(f"no videos found in {VIDEO_DIR}")
        return 1

    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    failures = 0

    for video in videos:
        out_video = RESULT_DIR / f"result_{video.stem}.mp4"
        out_json = RESULT_DIR / f"result_{video.stem}.json"
        print(f"\n=== {video.name} -> {out_video.name} ===", flush=True)
        start = time.time()
        proc = subprocess.run(
            [
                str(python), str(DETECT),
                "--input", str(video),
                "--output", str(out_video),
                "--json-log", str(out_json),
                "--device", "auto",
            ],
            cwd=str(PROJECT),
        )
        elapsed = time.time() - start
        status = "OK" if proc.returncode == 0 else f"FAILED (exit {proc.returncode})"
        print(f"=== {status} in {elapsed:.0f}s ===", flush=True)
        if proc.returncode != 0:
            failures += 1

    print(f"\ndone: {len(videos) - failures}/{len(videos)} succeeded")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
