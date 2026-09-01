# 04 - 系统实现与集成

Type: task
Status: resolved
Blocked by: 01, 03

## Question

把 01（图片规则检测）和 03（Gradio 界面）落成正式代码：图片检测函数、Gradio 应用（图片/视频双输入）、复用现有 `process_video` 管线做视频标注输出。产出：可运行的系统 + 演示录屏素材（标注结果视频）。

## 背景

执行类工作进 map（Q9-A）。环境已就绪（venv、CPU torch）。不做 YOLO 重训。

## Answer

**正式系统已实现并验证**：
- `src/image_detector.py` — 正式图片检测模块（ImageFallDetector，封装 ticket 01 规则：角度45°/宽高比1.4，含标注绘制）
- `app/app.py` — 正式 Gradio 应用（两个 Tab：图片/视频，`launch(share=True, server_name="0.0.0.0")` 支持公网链接，视频复用 `FallDetectionPipeline` 带进度条）
- 验证：图片（站立→NORMAL 100%、跌倒瞬间→FALL 75%、倒地→FALL 100%）、视频 handler（test_result.avi 检出 1 次跌倒 conf 1.0）、服务器启动 HTTP 200 均通过。

启动方式：`./venv/bin/python app/app.py`（会输出 localhost 地址 + share 公网链接）。

原型已按 prototype skill 规则固化进正式代码（`prototypes/` 保留为 throwaway 记录）。
