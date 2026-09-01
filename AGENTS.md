# AGENTS.md

上海应用技术大学「专业实践」专项课题：基于姿态识别的老年人跌倒检测系统研究与开发。工作区是课题的实现基地。

## 课题要点（权威需求见申报书 docx）

- 技术路线：**预训练姿态模型 + 可解释规则特征**（躯干倾斜角度、重心高度、边界框宽高比），不从头训练，轻量低成本。
- 数据集：UR Fall Detection Dataset、Le2i Fall Dataset（公开、无版权风险）。
- 交付物：跌倒检测原型系统（含 **Gradio 可视化界面，支持图片/视频输入**）、3000 字调研报告、系统演示视频；目标准确率 80%+。
- 申报书：`经管学院-专业实践-基于姿态识别的老年人跌到检测系统研究与开发.docx`（文件名照抄原文，含错别字"跌到"）。docx 无法被 read 直接解析，改需求前用解压提取文本的方式读它，并以它为准。

## 代码

基础项目在 `fall-detection-vison/`（克隆自 bakhtiyorjondadajonov/fall-detection-vison）。管线：视频 → YOLO11-Pose 17 关键点 → BoT-SORT 跟踪 → 5 个生物力学特征 → LSTM 三分类（normal/falling/fallen）→ 标注视频 + JSON 事件日志。

- 入口：`fall-detection-vison/detect_falls.py`（参数见 `--help`）。
- 已用自带测试视频验证：检出 1 次跌倒（conf 0.92→1.0），输出 `output/result_test.mp4` + `output/result_test.json`。
- 自带训练好的 LSTM 权重 `models/checkpoints/best.pth`（测试准确率 0.97）；`yolo11n-pose.pt` 在项目根目录。
- 上游 plan 文档 `fall_detection_project_plan.md` 是作者的目标设想（YOLO26 等），与当前代码略有出入，仅作参考。

## 环境

- Python 3.14 venv：`fall-detection-vison/venv`。在 Windows 下用 `venv/Scripts/python.exe`、`venv/Scripts/pip.exe`，**绝不装到全局**。
- torch 是 CPU 版（2.13.0+cpu）。**装依赖前先 `df -h`；不要装 CUDA 版 torch**——它的 nvidia 依赖 2G+，本机根分区曾 100% 满并因此安装失败。安装用 `--no-cache-dir`。
- 推理走 CPU（约 0.14s/帧 @4K）；`--device auto` 在有 GPU 的机器上自动加速。

## 现状

系统已实现（wayfinder 地图 5 个 ticket 全部 resolved，见 `.scratch/elderly-fall-detection/`）：`src/image_detector.py`（图片单帧规则检测）+ `app/app.py`（Gradio 双 Tab，share=True，启动 `venv/Scripts/python.exe app/app.py`）。演示素材在 `fall-detection-vison/demo/`。103 个测试全过，已提交 `0496dcd`。

正在进行 UI 体验优化（wayfinder 地图见 `.scratch/gradio-ui-optimization/`）：视频检测检出跌倒事件时自动播放 `app/assets/alert.wav` 并支持手动播放；图片检测结果改用 Markdown 自然语言总结，包含规则触发标签与具体数值。

## 许可

ultralytics 为 AGPL-3.0：学生实践项目合规；商用需替换或购买授权。

## Agent skills

### Issue tracker

Issues are tracked as local markdown files under `.scratch/<feature>/`. See `docs/agents/issue-tracker.md`.

### Domain docs

Single-context: one root `CONTEXT.md` glossary + `docs/adr/` for decisions. See `docs/agents/domain.md`.
