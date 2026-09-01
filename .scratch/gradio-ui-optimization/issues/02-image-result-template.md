# 02 - 图片检测结果自然语言模板

Type: prototype
Status: resolved
Blocked by:

## Question

图片检测 Tab 的结果文案应该以什么模板、在什么组件里展示，才能既清晰又详细？

## Background

当前图片检测返回纯文本：`检测结果: FALL（置信度 75%）` + 每行特征值。用户希望改成自然语言结论 + 规则触发标签 + 具体数值，NORMAL/NO_PERSON 也给出说明。

## Needs to decide

1. 展示组件：继续使用 `gr.Textbox`，还是改用 `gr.Markdown` 以支持标签/加粗/列表？
2. 文案模板：
   - FALL：一句话结论 + 触发规则标签（如 `躯干倾斜 62°`、`宽高比 1.76` 等）。
   - NORMAL：一句话正常说明 + 当前姿态简述。
   - NO_PERSON：明确提示未检测到人。
3. 输出项是否包括：检测人数、每人标签、每人置信度、关键数值、建议操作（如“建议人工复核”）？

## Answer

- 展示组件从 `gr.Textbox` 改为 `gr.Markdown`，支持加粗、列表、emoji 状态标签，渲染效果更清晰。
- 文案模板由 `app.app._format_image_result()` 统一生成：
  - **FALL**：标题“检测到疑似跌倒！（最高置信度 X%）”，列出每人状态、置信度、躯干角度、宽高比、重心高度，以及触发规则标签（如“躯干倾斜”）。
  - **NORMAL**：标题“未检测到跌倒（置信度 X%）”，同样列出每人姿态数值，触发规则为空。
  - **NO_PERSON**：明确提示“未检测到人”，并给出上传建议。
- `src/image_detector.ImageFallResult` 新增结构化 `persons` 字段，包含 `person_id/label/confidence/angle_deg/aspect_ratio/cog_height/triggers`，供 UI 层直接格式化，无需再解析文本。
- 示例验证：`test/images/fall_frame_04s.jpg` 输出包含“🚨 跌倒 置信度 75% | 躯干角度 46° | 宽高比 0.56 | 重心高度 0.73 | 触发规则：躯干倾斜”。
