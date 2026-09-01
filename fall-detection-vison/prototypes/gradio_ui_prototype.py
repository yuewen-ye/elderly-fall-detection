#!/usr/bin/env python3
"""PROTOTYPE — Gradio 界面交互原型（ticket 03）

目的：回答"界面长什么样、怎么交互"。两个 Tab：
  - 图片检测：上传图片 → 规则式单帧判断（ticket 01 的规则）
  - 视频检测：上传视频 → 复用现有 LSTM pipeline 出标注视频 + 事件

用法：python prototypes/gradio_ui_prototype.py
这是 throwaway 原型，验证交互后正式实现会重构。
"""

import sys
import tempfile
import time
from pathlib import Path

import cv2
import gradio as gr
import numpy as np
from ultralytics import YOLO

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.feature_extraction import FeatureExtractor  # noqa: E402
from src.pipeline import FallDetectionPipeline  # noqa: E402

# ---- ticket 01 确认的规则 ----
ANGLE_FALL_THRESHOLD = 45.0
ASPECT_FALL_THRESHOLD = 1.4
MIN_CONF = 0.3

MODEL = YOLO("yolo11n-pose.pt")
FE = FeatureExtractor(confidence_threshold=MIN_CONF)


def _judge(angle_deg: float, aspect: float) -> tuple[str, float, list[str]]:
    triggers = []
    if angle_deg > ANGLE_FALL_THRESHOLD:
        triggers.append(f"躯干角度 {angle_deg:.0f}°")
    if aspect > ASPECT_FALL_THRESHOLD:
        triggers.append(f"宽高比 {aspect:.2f}")
    if triggers:
        conf = min(1.0, 0.5 + 0.25 * len(triggers))
        return "FALL", conf, triggers
    return "NORMAL", 1.0, []


def detect_image(img: np.ndarray | None):
    """图片模式：规则式单帧判断。"""
    if img is None:
        return None, "请上传图片"
    h, w = img.shape[:2]
    results = MODEL(img, conf=0.3, verbose=False)[0]
    out = img.copy()

    if results.boxes is None or len(results.boxes) == 0:
        return out, "未检测到人"

    kps_all = results.keypoints.data.cpu().numpy()
    boxes = results.boxes.xyxy.cpu().numpy()
    lines = []
    for i, (box, kps) in enumerate(zip(boxes, kps_all)):
        bbox = tuple(float(v) for v in box)
        fv = FE.extract(kps, bbox, frame_height=h, prev_cog_height=None)
        angle_deg = fv.body_angle * 180.0
        label, conf, triggers = _judge(angle_deg, fv.bbox_aspect_ratio)

        x1, y1, x2, y2 = (int(v) for v in bbox)
        color = (0, 0, 255) if label == "FALL" else (0, 255, 0)
        cv2.rectangle(out, (x1, y1), (x2, y2), color, 3)
        cv2.putText(out, f"{label} {conf:.0%}", (x1, max(y1 - 10, 20)),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 3)
        for j in range(0, 17, 2):
            px, py, pc = kps[j]
            if pc > MIN_CONF:
                cv2.circle(out, (int(px), int(py)), 6, (255, 255, 0), -1)

        trig = "、".join(triggers) if triggers else "无"
        lines.append(
            f"人{i+1}: {label} 置信度{conf:.0%} | 躯干角度{angle_deg:.0f}° | "
            f"宽高比{fv.bbox_aspect_ratio:.2f} | 触发: {trig}"
        )
    return out, "\n".join(lines)


def detect_video(video_path: str | None, progress=gr.Progress()):
    """视频模式：复用现有 LSTM pipeline。"""
    if not video_path:
        return None, None, "请上传视频"

    tmp_out = Path(tempfile.mkdtemp(prefix="fall_demo_")) / "result.mp4"
    tmp_json = tmp_out.with_suffix(".json")

    progress(0, desc="初始化管线...")
    pipeline = FallDetectionPipeline(device="cpu")
    progress(0.2, desc="检测中（CPU 推理，视频越长越慢）...")

    t0 = time.time()
    result = pipeline.process_video(
        input_path=video_path,
        output_path=str(tmp_out),
        json_path=str(tmp_json),
    )
    elapsed = time.time() - t0

    events = result["events"]
    summary = result["summary"]
    ev_lines = "\n".join(
        f"- 跌倒: {e['timestamp_start']} → {e['timestamp_end']} "
        f"(track {e['track_id']}, conf {e['confidence']})"
        for e in events
    ) or "（无跌倒事件）"

    info = (
        f"检测跌倒 {summary['total_falls']} 次，跟踪 {summary['persons_tracked']} 人\n"
        f"耗时 {elapsed:.1f}s（CPU 推理）\n\n事件:\n{ev_lines}"
    )
    return str(tmp_out), info, None


with gr.Blocks(title="老年人跌倒检测系统 - 原型") as demo:
    gr.Markdown("## 🧓 老年人跌倒检测系统（原型）\n基于 YOLO11-Pose + LSTM，支持图片/视频输入")

    with gr.Tab("📷 图片检测"):
        with gr.Row():
            img_in = gr.Image(label="上传图片", type="numpy")
            img_out = gr.Image(label="检测结果")
        img_btn = gr.Button("开始检测", variant="primary")
        img_result = gr.Textbox(label="判断详情", lines=6)

    with gr.Tab("🎬 视频检测"):
        with gr.Row():
            vid_in = gr.Video(label="上传视频")
            vid_out = gr.Video(label="标注结果视频")
        vid_btn = gr.Button("开始检测", variant="primary")
        vid_result = gr.Textbox(label="检测信息", lines=8)

    img_btn.click(detect_image, inputs=img_in, outputs=[img_out, img_result])
    vid_btn.click(detect_video, inputs=vid_in, outputs=[vid_out, vid_result])

if __name__ == "__main__":
    demo.launch(share=False, server_name="127.0.0.1")
