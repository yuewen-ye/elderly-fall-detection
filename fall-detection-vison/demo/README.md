# 演示素材清单（ticket 05）

## 1. 标注结果视频（主演示）

| 文件 | 内容 | 检测结果 |
|---|---|---|
| `demo_fall_detection_result.mp4` | 4K 户外场景人物跌倒（源为 Pexels 素材），7.3s | ✅ 检出 1 次跌倒（00:00:04.080 → 00:00:07.240，conf 1.0） |
| `fall_event_annotated.mp4` | UR Fall Detection Dataset (fall-01-cam0)，室内场景，5.3s | ✅ 检出 1 次跌倒（00:00:03.300 → 00:00:05.300，conf 1.0） |

标注内容：骨骼关键点 + 边界框（绿=正常，红=跌倒）+ 状态栏告警（PERSON FALLEN + 时长）。

## 2. 原始素材（对比用）

| 文件 | 内容 |
|---|---|
| `fall_event.mp4` | UR 数据集原始视频（未标注），用于展示"检测前/后"对比 |
| `test_events.json` / `fall_event_events.json` | 检测事件日志（时间戳、置信度、track id） |

## 3. 演示建议

- **系统演示**：启动 `./venv/bin/python app/app.py`（Gradio 界面，会输出 localhost + share 公网链接），浏览器打开后：
  - 图片 Tab：上传跌倒/正常图片 → 显示规则判断结果
  - 视频 Tab：上传 `demo/fall_event.mp4`（640x240 处理快）或 `output/test_result.avi`（4K 处理约 30s）→ 显示标注视频 + 事件
- **成果展示**：直接播放 `demo_fall_detection_result.mp4` 展示检测能力

## 4. 来源与许可

- `demo_fall_detection_result.mp4` 源自项目自带测试视频（Pexels 4K 素材 ID 10240439）
- `fall_event.mp4` 来自 UR Fall Detection Dataset（https://fenix.ur.edu.pl/mkepski/ds/uf.html），许可 CC BY-NC-SA 4.0，非商业学术用途
