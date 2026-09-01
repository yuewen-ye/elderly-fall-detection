# 01 - 图片单帧规则式检测原型

Type: prototype
Status: resolved
Blocked by:

## Question

Gradio 图片输入模式下，单帧如何做跌倒判断？需要确定：用哪些特征（body_angle / bbox 宽高比 / 重心高度？）、阈值定多少（如角度>60°、宽高比>1.5）、输出什么（跌倒/正常 + 置信度/分数 + 骨架可视化）。产出：一个可运行的图片检测原型（脚本或函数），供用户对真实图片看效果。

## 背景

pipeline 只有 `process_video`（LSTM 需 30 帧时序）；`detect_frame` 支持单帧 YOLO+特征提取。图片模式走规则式判断（Q6-A）。

## Answer

**规则已定（用户确认采用原型默认）**：单帧图片跌倒判断 = 躯干角度>45° **或** bbox宽高比>1.4 → FALL；置信度 = 0.5 + 0.25×触发规则数（封顶 1.0），NORMAL 反向。

原型验证（测试视频真实帧，与 ground truth 吻合）：站立 17.6°→NORMAL、行走 7.9°→NORMAL、过渡 35.3°→NORMAL（未误报）、跌倒瞬间 60.6°→FALL 0.75、倒地 84.5°+宽高比3.25→FALL 1.00。

**关键结论**：躯干角度是"跌倒检测"特征（跌倒瞬间即触发），宽高比是"倒地确认"特征（完全倒地才触发）——两特征互补，印证申报书"多特征融合降低误判"叙事；单用宽高比会漏检跌倒瞬间。

原型代码（throwaway，已确认，后续逻辑并入正式代码）：`fall-detection-vison/prototypes/image_rule_prototype.py`，标注图在 `prototypes/out/`。
