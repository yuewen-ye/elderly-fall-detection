# Ticket: 02

**标题：演示素材调研**
**调研日期：2026-09-01（全部链接当日实测）**
**状态：完成**

---

## 结论速览（TL;DR）

1. **现有 `output/test_result.avi` 可用且内容已客观确认为真实跌倒场景**（4K、7.28s、检出 1 次跌倒，置信度 1.0），可作为标注结果视频的主体素材；缺点是单场景、时长偏短。
2. **补充素材首选 UR Fall Detection Dataset**：官方站直链已逐条验证可用，单段 mp4 仅 0.5–3MB，许可为 CC BY-NC-SA 4.0（非商业学术用途免费，无需申请）。
3. **Le2i Fall Detection Dataset 官方下载当前不可用**（原站失效，继承实验室 ImViA 页面标注 "waiting for new link"），仅剩 Kaggle 镜像（需登录）；不建议现在下载。
4. **推荐**：用现有 test_result.avi 做标注视频 + 从 UR 下载 1–2 段小 mp4（正常行走 ADL + 跌倒 fall）做"不告警 → 告警"对比片段，总下载量 <10MB。

---

## 1. 现有素材评估：`output/test_result.avi` 是否足够

### 1.1 元数据（ffprobe 实测）

| 项 | 值 |
|---|---|
| 文件 | `fall-detection-vison/output/test_result.avi` |
| 大小 | 19.7 MB（另有已压缩标注版 `result_test.mp4`，12 MB） |
| 编码/容器 | mpeg4（AVI） |
| 分辨率 | **4096×2160（4K UHD）** |
| 帧率 | 25 fps，共 182 帧 |
| 时长 | 7.28 s |

### 1.2 检出结果（`output/result_test.json` 实测）

- 检出 **1 次跌倒**：track_id=1，帧 102–181（时间 00:00:04.080–00:00:07.240），**置信度 1.0**；
- 全程跟踪到 **2 人**；处理耗时 37.4s（CPU @4K，约 0.14s/帧，与 AGENTS.md 记录一致）。

### 1.3 画面内容确认（本会话无图像视觉能力，改用客观量化验证）

> 说明：本调研会话的模型不支持图像输入，describe-image / modlens 视觉桥均不可用，故不使用"肉眼看帧"的方式，而是用**项目自带的 YOLO11-Pose（yolo11n-pose.pt）**对抽取帧做姿态量化，并与检测日志交叉印证。

对 AVI 抽取 10 帧（帧 10/30/50/70/90/105/120/140/160/180）跑姿态推理，躯干角定义：**0°=躯干竖直，90°=躯干水平**：

| 帧 | 人数 | bbox 宽高比 | 躯干角(°) | 判读 |
|---|---|---|---|---|
| 10 | 2 | 0.54（窄高） | 1.0 | 站立 |
| 30 | 2 | 0.55（窄高） | 7.8 | 站立/行走 |
| 50 | 2 | 0.83 | 14.0 | 站立/行走 |
| 70 | 2 | 0.34（窄高） | 7.4 | 站立 |
| 90 | 2 | 0.98 | 43.5 | **过渡（开始倾倒）** |
| 105 | 1 | 0.86 | 67.8 | 摔倒过程 |
| 120 | 1 | 1.49（宽扁） | 83.0 | 倒地（近水平） |
| 140 | 2 | 2.41（宽扁） | 82.2 | 倒地 |
| 160 | 1 | 2.63（宽扁） | 67.1 | 倒地 |
| 180 | 1 | 2.43（宽扁） | 34.6 | 倒地/起身中 |

- 前 4 帧躯干竖直、bbox 窄高（站立），帧 90 起躯干快速转水平、bbox 变宽扁（倒地），**与 JSON 中 fall 事件起始帧 102 高度吻合** → 内容确为**真实人物跌倒**场景。
- 既有抽帧文件（frame_before_fall / frame_fall_moment / frame_on_ground / frame_after_fall.jpg）也佐证了这一过程。

### 1.4 源视频溯源

- `result_test.json` 记录原始输入为 `10240439-uhd_4096_2160_25fps.mp4`——文件命名符合 **Pexels 素材站 UHD 下载命名规则**（`<视频ID>-uhd_4096_2160_25fps.mp4`），即来自 Pexels 的 4K 免费素材，ID 10240439（[https://www.pexels.com/video/10240439/](https://www.pexels.com/video/10240439/)）。该页面临 Cloudflare 验证，无法无头抓取标题，**需浏览器打开确认素材名称与画面描述**（可选动作）。
- Pexels 许可：免费使用、无需署名、可商用，无版权风险。

### 1.5 标注画面内容（`src/utils.py` 代码确认）

标注输出绘制：**骨架关键点连线（draw_skeleton）+ 红色告警文字（draw_alert）+ 底部状态栏（帧号/fps/跟踪人数/跌倒计数，draw_status_bar）** → 画面信息量适合演示"姿态识别 + 检测告警"效果。

### 1.6 结论

- ✅ 内容适合展示：真实跌倒、有"正常 → 跌倒"完整过程、4K 清晰、标注叠加完整、检测成功（conf 1.0）。
- ⚠️ 不足：仅 7.3s、单场景单次跌倒，作为完整演示（尤其"界面录屏 + 结果展示"）时长偏短；2 人同框使画面略杂乱。
- **判定：可用作演示主体，但建议补 1 段"正常行走不告警"对比素材**（见第 3、4 节）。

---

## 2. 补充素材来源（链接均于 2026-09-01 实测）

### 2.1 UR Fall Detection Dataset（✅ 主推，全部链接已验证）

- **官方页**：[https://fenix.ur.edu.pl/mkepski/ds/uf.html](https://fenix.ur.edu.pl/mkepski/ds/uf.html)（HTTP 200）
- **内容**：70 段序列 = **30 段跌倒（fall-01..30）+ 40 段日常生活 ADL（adl-01..40）**；双 Microsoft Kinect（cam0 正面水平、cam1 天花板俯视），含 RGB / 深度图 / 加速度计数据。
- **下载方式**：每段序列提供 ① 小体积 mp4（cam0/cam1）② PNG 图像序列 zip ③ CSV（同步/加速度计）。**无需申请，直接下载。**
- **已验证直链**（HTTP 200/206，大小取 Content-Length）：

| 文件 | 大小 | 状态 |
|---|---|---|
| `data/fall-01-cam0.mp4` | 1.24 MB | ✅ 200 |
| `data/fall-01-cam1.mp4` | 1.26 MB | ✅ 200 |
| `data/fall-30-cam0.mp4` | 0.50 MB | ✅ 200 |
| `data/adl-01-cam0.mp4` | ~1.3 MB | ✅ 206 |
| `data/adl-10-cam0.mp4` | ~1.3 MB | ✅ 206 |
| `data/adl-40-cam0.mp4` | 2.66 MB | ✅ 200 |
| `data/fall-01-cam0-rgb.zip`（PNG 序列） | 55.0 MB | ✅ 200 |

  链接通式：`https://fenix.ur.edu.pl/mkepski/ds/data/<fall|adl>-NN-cam{0,1}.mp4` / `...-cam0-rgb.zip`（NN=01–30 跌倒、01–40 ADL）。

- **许可（页面原文）**：**CC BY-NC-SA 4.0**（署名-非商业-相同方式共享），"intended for non-commercial academic use"；商用需邮件联系 mkepski@ur.edu.pl。**学术演示用途合规，无申请流程。**
- 引用要求：使用需引用 Kwolek & Kepski 论文（页面提供链接）。

### 2.2 Le2i Fall Detection Dataset（⚠️ 官方下载已不可用，慎用）

- **官方页已失效**：`le2i.cnrs.fr/Fall-Detection-Dataset` 无响应。
- **继承实验室 ImViA 页面**：[https://imvia.ube.fr/fall-detection-dataset/](https://imvia.ube.fr/fall-detection-dataset/)（HTTP 200）——当前页面原文为 **"Dowload the data (waiting for new link)"，即官方直链暂缺**。
- **Wayback Machine 无二进制**：CDX 查询显示仅存档了 `acceder_document` 的 **301 跳转页**（484–490B），zip 本体从未被存档 → 无法经 archive.org 下载。
- **数据集构成**（存档页原文）：191 段视频、25fps、**320×240**、5 个场景（Home / Coffee room / Office / Lecture room / Office2）、逐帧 bounding box 人工标注（含跌倒位置真值）。
- **各场景 zip 大小**（存档页原文）：Office 1666MB、Lecture room 1809MB、Home1 950MB、Coffee1 1878MB、Coffee2 1708MB、Home2 1152MB、**Office2 仅 67MB**；总计约 9.2GB。
- **可用替代（需登录）**：Kaggle 镜像 "Fall Detection Dataset"（[https://www.kaggle.com/datasets/uttejkumarkandagatla/fall-detection-dataset](https://www.kaggle.com/datasets/uttejkumarkandagatla/fall-detection-dataset)，页面 200，基于 Le2i 的图像帧+标签，需 Kaggle 账号下载，许可以页面为准）。
- **版权风险**：官方页无明确许可声明、仅要求引用；经第三方镜像获取时受镜像自身条款约束。学生学术演示（非商用）风险低，但**不建议作为首要下载源**。

---

## 3. "正常行走 + 跌倒"对比片段：是否值得、来源

**值得**。演示"正常行走不告警 → 跌倒告警"的对比能直观展示系统判别能力（减少"检测到就告警"的误判质疑），是演示视频加分项。

可行来源（按推荐顺序）：

1. **UR 数据集自带（首选）**：40 段 ADL 序列含行走等日常活动，与 fall 序列**同一拍摄环境、同一设备**，对比说服力最强；单段 mp4 仅 0.5–3MB，直链已验证。注意：官方页未逐段标注活动名称，需**人工预览挑选**哪段是"行走"（cam0 正面视角更接近演示画面）。
2. **Pexels/Pixabay 免费素材**：搜索 "elderly walking" 可找到 4K 行走素材，与现有 test_result.avi 风格（4K 素材）一致，免费免署名；但需要自行确认画面中无跌倒动作、且与检测系统实际跑一遍以证明"不告警"。
3. （如追求监控视角）UR 的 cam1（天花板俯视）mp4，画面更接近 Le2i 式监控场景。

---

## 4. 最终推荐方案

### 推荐：方案 A（主体）+ 方案 B（增强），总下载量 <10MB

- **方案 A — 标注结果视频（零下载）**：以现有 `output/test_result.avi`（或压缩版 `result_test.mp4`）作为"跌倒检测标注结果"演示素材。理由：内容已客观验证（真实跌倒、4K、标注叠加完整、检出 conf 1.0），无需任何下载。
- **方案 B — 对比片段（推荐下载）**：从 UR 下载 2 段小 mp4：
  - `adl-XX-cam0.mp4`（正常行走/日常活动，~1–3MB）→ 展示**不告警**；
  - `fall-XX-cam0.mp4`（跌倒，~0.5–1.5MB）→ 展示**告警**；
  - 剪成 10–15s 对比片段，与标注视频并列放映；注意 UR 为 CC BY-NC-SA 4.0 非商用许可，学术演示合规，建议片尾注明素材来源。
- **可选方案 C**：如需 4K 精细标注视频或监控俯视视角，再考虑 `fall-01-cam0-rgb.zip`（55MB PNG 序列）或 UR cam1 mp4。
- **不建议现在下载 Le2i**：官方直链失效（ImViA 页面标注 waiting for new link）、Wayback 无存档、Kaggle 镜像需登录且单场景 67MB–1.9GB 偏大，对演示性价比低；仅当后续需要"监控场景 + 逐帧标注真值"做标注可视化时才考虑 Office2（67MB 最小包）。

### 后续行动项

1. （可选）浏览器打开 [https://www.pexels.com/video/10240439/](https://www.pexels.com/video/10240439/) 确认现有素材的名称/画面描述，用于演示解说词；
2. 预览挑选 UR 的 ADL 行走片段与 fall 片段，下载（各 <3MB）后用 `detect_falls.py` 实测确认"行走不告警、跌倒告警"；
3. 制作演示时：标注视频（方案 A）→ 对比片段（方案 B）→ 界面录屏（Gradio 界面 + 上述视频），三部分串联成完整演示。

---

### 附：信息来源

- UR Fall Detection Dataset 官方页（含许可声明、下载表）：https://fenix.ur.edu.pl/mkepski/ds/uf.html
- UR 数据直链（实测）：https://fenix.ur.edu.pl/mkepski/ds/data/fall-01-cam0.mp4 等
- Le2i 数据集存档页（Wayback，含构成与各场景 zip 大小）：http://web.archive.org/web/20200811002412/http://le2i.cnrs.fr/Fall-detection-Dataset
- ImViA（Le2i 继承实验室）数据集页：https://imvia.ube.fr/fall-detection-dataset/
- Kaggle Le2i 镜像：https://www.kaggle.com/datasets/uttejkumarkandagatla/fall-detection-dataset
- Pexels 素材页（需浏览器确认标题）：https://www.pexels.com/video/10240439/
- 本地证据：`fall-detection-vison/output/test_result.avi`、`output/result_test.json`、`src/utils.py`、本机 YOLO11-Pose 姿态扫描结果
