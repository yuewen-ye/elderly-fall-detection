# 03 - 集成音频警报与图片结果优化到 Gradio

Type: task
Status: resolved
Blocked by: 01, 02

## Question

如何在 `app/app.py` 中集成音频警报和图片结果优化，并保证现有视频/图片检测流程不受影响？

## Background

01 解决 `alert.wav` 与播放降级；02 确定图片结果模板。本 ticket 负责把两者写进正式代码并回归验证。

## Answer

- `app/app.py` 已完成集成：
  - 视频 Tab 增加 `gr.Audio(autoplay=True, type="filepath")`，`detect_video()` 在 `events` 非空时返回 `alert.wav` 路径，否则返回 `None`。
  - 图片 Tab 结果组件改为 `gr.Markdown`，调用 `_format_image_result()` 输出自然语言总结 + 规则标签 + 数值。
- 未检测到跌倒时音频组件无文件，不会播放。
- `src/pipeline.py` 中 `process_video()` 已增加主线程判断：仅在 `threading.current_thread() is threading.main_thread()` 时注册/恢复 SIGINT，避免在 Gradio 工作线程中触发 `ValueError: signal only works in main thread`。
- 回归验证：`pytest -q` 103 全部通过；直接调用 `detect_image()` 与 `detect_video()` 可正常输出 Markdown 文本与音频路径。
- `AGENTS.md` 已更新：Windows 启动命令改为 `fall-detection-vison/venv/Scripts/python.exe app/app.py`，并补充 UI 优化现状。
