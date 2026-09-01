#!/usr/bin/env python3
"""Gradio web app for the elderly fall detection system.

Run:  python app/app.py   (or: venv/Scripts/python.exe app/app.py)

Two tabs:
  - Image detection: rule-based single-frame judgment (src/image_detector.py)
  - Video detection: full LSTM pipeline (src/pipeline.py) → annotated video + events

Recent UI improvements:
  - Video tab plays an alert sound when a fall event is detected.
  - Image tab renders a plain-language Markdown summary with rule triggers and
    numeric values.
"""

import logging
import sys
import tempfile
import time
from pathlib import Path

import gradio as gr
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import cv2  # noqa: E402

from src.image_detector import ImageFallDetector  # noqa: E402
from src.pipeline import FallDetectionPipeline  # noqa: E402

# Alert sound asset (played when a fall event is detected in video)
ALERT_WAV = Path(__file__).resolve().parent / "assets" / "alert.wav"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

_image_detector: ImageFallDetector | None = None


def get_image_detector() -> ImageFallDetector:
    global _image_detector
    if _image_detector is None:
        _image_detector = ImageFallDetector()
    return _image_detector


def _format_image_result(result) -> str:
    """Build a clear, plain-language Markdown summary from an ImageFallResult."""
    if result.label == "NO_PERSON":
        return (
            "**未检测到人**\n\n"
            "建议上传包含正面全身、光线清晰的图片，以便姿态识别模型准确判断。"
        )

    header = (
        f"**检测到疑似跌倒！**（最高置信度 {result.confidence:.0%}）"
        if result.label == "FALL"
        else f"**未检测到跌倒**（置信度 {result.confidence:.0%}）"
    )

    lines = [header, f"\n检测到 **{result.persons_detected}** 人：\n"]
    for p in result.persons:
        status = "🚨 跌倒" if p["label"] == "FALL" else "✅ 正常"
        lines.append(
            f"- **人{p['person_id']}**：{status} 置信度 {p['confidence']:.0%}  \\"
            f"  躯干角度 {p['angle_deg']:.0f}°，宽高比 {p['aspect_ratio']:.2f}，重心高度 {p['cog_height']:.2f}"
        )
        if p["triggers"]:
            lines.append(
                f"  - **触发规则**：{ '、'.join(p['triggers']) }"
            )

    if result.label == "FALL":
        lines.append(
            "\n> 提示：规则检测结果仅供参考，建议结合视频时序检测或人工复核确认。"
        )
    return "\n".join(lines)


def detect_image(image: np.ndarray | None):
    """Image tab handler.

    gradio returns RGB arrays; the detector draws in BGR, so convert on
    both sides of the call to keep alert colors correct on screen.
    """
    if image is None:
        return None, "请上传图片"
    bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    result, annotated_bgr = get_image_detector().detect(bgr)
    annotated = cv2.cvtColor(annotated_bgr, cv2.COLOR_BGR2RGB)
    summary = _format_image_result(result)
    return annotated, summary


def detect_video(video_path: str | None, progress=gr.Progress()):
    """Video tab handler: reuse the LSTM pipeline.

    Returns annotated video path, summary text, and an alert audio path
    when at least one fall event is detected.
    """
    if not video_path:
        return None, "请上传视频", None

    tmp_dir = Path(tempfile.mkdtemp(prefix="fall_app_"))
    out_video = tmp_dir / "result.mp4"
    out_json = tmp_dir / "result.json"

    progress(0, desc="初始化管线...")
    pipeline = FallDetectionPipeline(device="cpu")
    progress(0.02, desc="检测中（CPU 推理，视频越长越慢）...")

    t0 = time.time()
    result = pipeline.process_video(
        input_path=video_path,
        output_path=str(out_video),
        json_path=str(out_json),
        progress_callback=lambda frac: progress(0.02 + 0.96 * frac),
    )
    elapsed = time.time() - t0

    events = result["events"]
    summary = result["summary"]
    lines = [f"检测跌倒 {summary['total_falls']} 次，跟踪 {summary['persons_tracked']} 人"]
    lines.append(f"耗时 {elapsed:.1f}s（CPU 推理）")
    if events:
        lines.append("\n事件:")
        for e in events:
            lines.append(
                f"- 跌倒: {e['timestamp_start']} → {e['timestamp_end']} "
                f"(track {e['track_id']}, conf {e['confidence']})"
            )
    else:
        lines.append("（未检测到跌倒事件）")

    progress(1.0, desc="完成")
    alert_path = str(ALERT_WAV) if events and ALERT_WAV.exists() else None
    return str(out_video), "\n".join(lines), alert_path


def build_app() -> gr.Blocks:
    with gr.Blocks(title="老年人跌倒检测系统") as demo:
        gr.Markdown(
            "## 🧓 老年人跌倒检测系统\n"
            "基于 YOLO11-Pose 姿态识别 + LSTM 时序分类，支持图片与视频输入"
        )

        with gr.Tab("📷 图片检测"):
            gr.Markdown("上传单张图片，基于躯干角度与边界框宽高比规则判断是否跌倒。")
            with gr.Row():
                img_in = gr.Image(label="上传图片", type="numpy")
                img_out = gr.Image(label="检测结果")
            img_btn = gr.Button("开始检测", variant="primary")
            img_result = gr.Markdown(label="判断详情")

        with gr.Tab("🎬 视频检测"):
            gr.Markdown("上传视频，完整 LSTM 管线将输出标注视频与跌倒事件日志；检测到跌倒时会自动播放警报音。")
            with gr.Row():
                vid_in = gr.Video(label="上传视频")
                vid_out = gr.Video(label="标注结果视频")
            vid_btn = gr.Button("开始检测", variant="primary")
            vid_result = gr.Textbox(label="检测信息", lines=8)
            vid_audio = gr.Audio(
                label="跌倒警报（检测到跌倒时自动播放，也可手动点击播放）",
                autoplay=True,
                type="filepath",
            )

        img_btn.click(detect_image, inputs=img_in, outputs=[img_out, img_result])
        vid_btn.click(
            detect_video, inputs=vid_in, outputs=[vid_out, vid_result, vid_audio]
        )

    return demo


if __name__ == "__main__":
    app = build_app()
    app.launch(share=True, server_name="0.0.0.0")
