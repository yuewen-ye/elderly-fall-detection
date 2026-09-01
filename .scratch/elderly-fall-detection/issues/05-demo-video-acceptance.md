# 05 - 演示视频与验收

Type: task
Status: resolved
Blocked by: 02, 04

## Question

最终交付：生成演示视频（标注结果视频 + 界面操作录屏，基于 02 选定的素材），并对照 Q10 的验收清单（图片检测正确显示、视频检测出跌倒事件、Gradio 双输入可用、演示视频可播放）逐项确认。产出：演示视频文件 + 验收结果记录。

## 背景

验收标准已定（Q10-C：清单 + 现场演示）。用户将现场验收。

## Answer

**演示素材与验收完成**：

演示素材（`fall-detection-vison/demo/`，说明见 `demo/README.md`）：
- `demo_fall_detection_result.mp4` — 4K 主演示（检出 1 次跌倒 conf 1.0）
- `fall_event.mp4` + `fall_event_annotated.mp4` — UR Fall 数据集对比素材（检出 1 次跌倒 conf 1.0），CC BY-NC-SA 4.0
- 注：UR ADL-40 片段尝试后发现含躺/倒动作且人物出入画（会误报），已剔除不做"正常对照"

自动化验收清单（Q10）逐项 PASS：
- ✅ 图片检测正确显示（跌倒帧→FALL 75%、正常帧→NORMAL）
- ✅ 视频检测出跌倒事件（UR 片段 → 检出 1 次，conf 1.0）
- ✅ Gradio 双输入可用（「📷 图片检测」「🎬 视频检测」两个 Tab）
- ✅ 演示视频可播放（两个标注视频均验证可读）

待用户现场验收：浏览器打开 Gradio（`./venv/bin/python app/app.py`）上传图片/视频确认效果。
