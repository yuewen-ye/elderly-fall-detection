# 03 - Gradio 界面交互原型

Type: prototype
Status: resolved
Blocked by: 01

## Question

Gradio 界面长什么样、怎么交互？需要确定：布局（两个 Tab：图片 / 视频？）、组件（上传控件、示例、结果显示区、置信度/状态文字）、视频输入的处理方式（等待时长、进度提示、结果视频回放）以及运行时行为（本地 `share=True`）。产出：可运行的 Gradio 应用 stub，供用户看交互效果。

## 背景

申报书要求"可视化交互界面，支持图片输入"（视频也要，Q3-A）。依赖 01（图片检测）确定后再设计结果展示。

## Answer

**界面设计已确认（用户采用）**：Gradio 两个 Tab——「📷 图片检测」（上传→标注图+判断详情）和「🎬 视频检测」（上传→LSTM 管线→标注视频+事件信息+进度条）。正式实现启用 `share=True` 支持公网临时链接。

原型验证：图片模式（站立→NORMAL 100%、跌倒瞬间→FALL 75%、倒地→FALL 100%）与视频模式（test_result.avi 检出 1 次跌倒 conf 1.0，30.8s CPU）均通过。

原型代码：`fall-detection-vison/prototypes/gradio_ui_prototype.py`。
