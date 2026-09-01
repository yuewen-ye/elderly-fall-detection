# Wayfinder Map: Gradio 界面体验优化

## Destination

Gradio 界面完成两项体验优化并验证通过：

1. **视频检测音频警报**：当 LSTM 管线检出完整跌倒事件（`falling`/`fallen` 且置信度 ≥ 阈值）时，自动播放一次短促提示音 `alert.wav`；若浏览器拦截自动播放，则提供“🔔 播放警报”按钮作为降级。
2. **图片检测结果可读性提升**：在图片检测 Tab 以“自然语言结论 + 规则触发标签 + 具体数值”的方式展示结果，NORMAL/NO_PERSON 也给出对应说明。

只改 UI 层，不动检测模型与阈值。

## Notes

- 基础项目：`fall-detection-vison/`（YOLO11-Pose + LSTM），当前 `app/app.py` 已实现双 Tab Gradio 界面。
- 相关代码：`app/app.py`、`src/image_detector.py`、`src/pipeline.py`。
- 已确认的决策（Q1–Q6）：
  - 警报触发：以“事件”为单位，完整跌倒事件触发一次。
  - 警报形式：短促提示音 `alert.wav`。
  - 播放策略：自动播放 + 手动播放按钮降级。
  - 图片结果：自然语言总结 + 规则标签（躯干角度 / 宽高比 / 重心高度）+ 数值。
  - NORMAL/NO_PERSON 也给出简要说明。
  - 范围：仅 UI 层，不改模型/阈值。
- 环境：venv 在 `fall-detection-vison/venv`（CPU torch），不装全局。

## Decisions so far

<!-- 索引：每个已关闭 ticket 一行（gist + 链接）。 -->

- [01 - 警报音频文件与播放降级方案](issues/01-alert-audio-source.md)：使用 Python `wave` 标准库生成 0.5s 880Hz 提示音 `fall-detection-vison/app/assets/alert.wav`；Gradio `gr.Audio(autoplay=True)` 自动播放，被拦截时靠组件自带播放按钮降级。
- [02 - 图片检测结果自然语言模板](issues/02-image-result-template.md)：结果改用 `gr.Markdown` 展示；文案包含自然语言结论、每人姿态数值（躯干角度 / 宽高比 / 重心高度）及触发规则标签；NORMAL/NO_PERSON 也给出对应说明。
- [03 - 集成音频警报与图片结果优化到 Gradio](issues/03-integrate-ui-optimizations.md)：视频 Tab 在检出完整跌倒事件时返回 `alert.wav`；图片 Tab 调用 `_format_image_result()`；`pipeline.process_video()` 增加主线程判断避免 Gradio 工作线程 signal 报错；`pytest -q` 103 通过。

## Not yet specified

（当前地图全部决策已关闭，无剩余未明确项。）

## Out of scope

- 修改跌倒检测模型、阈值、跟踪逻辑。
- 引入第三方短信/推送/实时报警服务。
- 移动端/嵌入式部署。
- 调研报告或演示视频录制。
