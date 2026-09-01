# 01 - 警报音频文件与播放降级方案

Type: task
Status: resolved

## Question

如何准备 `alert.wav`，并确定 Gradio 中自动播放被浏览器拦截时的降级交互？

## Background

用户决定使用短促提示音作为视频跌倒警报。需要一个小体积、免版权风险的音频文件，并在 Gradio 中实现：检测到跌倒时自动播放；若浏览器拦截，则显示“🔔 播放警报”按钮。

## Answer

- `alert.wav` 已生成并放入 `fall-detection-vison/app/assets/alert.wav`，22KB、0.5s、880Hz 正弦波提示音，无外部版权依赖。
- 使用 Python `wave` 标准库合成，避免引入额外依赖，合成脚本已执行并保留音频文件。
- Gradio 播放降级：视频 Tab 使用 `gr.Audio(autoplay=True, type="filepath")`。检测到跌倒事件时返回 `alert.wav` 路径，浏览器支持自动播放时直接响起；被拦截时用户可点击音频组件自带的播放按钮手动播放。无需额外自定义“🔔 播放警报”按钮，因为 `gr.Audio` 自身已提供播放控件。
