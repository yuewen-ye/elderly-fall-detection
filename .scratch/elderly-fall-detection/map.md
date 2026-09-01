# Wayfinder Map: 老年人跌倒检测系统（基于 fall-detection-vison）

## Destination

地图走完 = **系统可演示 + 演示视频就绪**：在 `fall-detection-vison` 基础上，Gradio 界面支持图片/视频输入并输出检测结果，演示视频（标注结果视频 + 界面录屏）就绪。**不需要调研报告**。

## Notes

- 领域：计算机视觉跌倒检测。基础项目 `fall-detection-vison/`（YOLO11-Pose + BoT-SORT + LSTM 三分类），已在本机验证跑通（测试视频检出 1 次跌倒，conf 0.92→1.0）。
- 每次 session 加载的 skills：`grilling`、`domain-modeling`、`prototype`。
- 已定基调（charting 阶段用户拍板）：
  - 技术路线：**保留 LSTM**（视频时序检测），图片单帧用**规则式判断**（Q2、Q6）
  - 界面：Gradio，本地运行 + `share=True` 公网链接（Q7）
  - 准确率：用现有训练报告背书（test_accuracy 0.9703），不做独立数据集评估（Q4）
  - 执行类工作也放进地图（Q1-A）；交付物打包仅限技术执行，不做报告（Q9-A）
  - 验收：清单 + 现场演示（Q10-C）
- 环境：venv 在 `fall-detection-vison/venv`（CPU torch），绝不装全局；装依赖前先 `df -h`。

## Decisions so far

<!-- 索引：每个已关闭 ticket 一行（gist + 链接）。 -->

- [01 - 图片单帧规则式检测原型](../../.scratch/elderly-fall-detection/issues/01-image-rule-detection.md): 单帧规则 = 躯干角度>45° 或 bbox宽高比>1.4 → FALL；置信度 0.5+0.25×触发规则数。角度是跌倒检测特征、宽高比是倒地确认特征，互补。原型在 `fall-detection-vison/prototypes/image_rule_prototype.py`。
- [02 - 演示素材调研](../../.scratch/elderly-fall-detection/issues/02-demo-material-research.md): 演示主体用现有 `test_result.avi`（已确认真实跌倒场景）；对比片段可选 UR Fall 小 mp4（<10MB，CC BY-NC-SA 4.0，直链可用）；Le2i 下载已失效不采用。
- [03 - Gradio 界面交互原型](../../.scratch/elderly-fall-detection/issues/03-gradio-ui-prototype.md): 界面 = 两个 Tab（图片检测/视频检测），图片用 01 规则，视频复用 LSTM 管线，带进度条；正式实现 `share=True` 支持公网链接。原型在 `fall-detection-vison/prototypes/gradio_ui_prototype.py`。
- [04 - 系统实现与集成](../../.scratch/elderly-fall-detection/issues/04-implementation.md): 正式代码就绪——`src/image_detector.py`（图片规则检测）+ `app/app.py`（Gradio 双 Tab，share=True）。启动 `./venv/bin/python app/app.py`。图片/视频/服务器启动均验证通过。
- [05 - 演示视频与验收](../../.scratch/elderly-fall-detection/issues/05-demo-video-acceptance.md): 演示素材就绪（`demo/`：4K 主演示 + UR fall 对比，均检出跌倒 conf 1.0）；自动化验收清单 4 项全 PASS；待用户现场验收。

## Not yet specified

- 图片模式规则式检测的具体特征阈值与输出格式（将随 01 原型清晰化）
- 演示视频的录制工具与最终形态（素材已定，录制工具待 04/05）
- Gradio 视频输入时的进度/耗时反馈方案（将随 03 原型清晰化）

## Out of scope

- 调研报告/调研问卷（用户明确不需要）
- YOLO 模型重训/微调（守住"无需从零训练"叙事）
- 移动端/嵌入式/多摄像头部署
- 独立数据集（UR/Le2i）准确率评估
