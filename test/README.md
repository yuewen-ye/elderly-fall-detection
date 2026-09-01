# 测试素材与结果说明

本目录用于存放系统验收测试的输入素材与输出结果。

## 目录结构

```
test/
├── images/          # 图片测试输入
├── image_results/   # 图片检测结果（标注图 + Markdown 报告）
├── videos/          # 视频测试输入
└── video_results/   # 视频检测结果（标注视频）
```

## 图片测试

| 文件名 | 来源 | 场景 | 预期结果 | 实际结果 |
|--------|------|------|----------|----------|
| `fall_frame_02s.jpg` | 监控下感人的一幕视频 2s 帧 | 街道人行道，老人倒地 | 跌倒 | 跌倒（躯干倾斜 50°） |
| `fall_frame_04s.jpg` | 监控下感人的一幕视频 4s 帧 | 街道人行道，老人倒地 | 跌倒 | 跌倒（躯干倾斜 46°） |
| `fall_frame_06s.jpg` | 监控下感人的一幕视频 6s 帧 | 街道人行道，老人倒地 | 跌倒 | 跌倒（躯干倾斜 63°） |
| `park_normal_10s.jpg` | 公园老人晨练视频 10s 帧 | 公园，老人正常活动 | 正常 | 正常（5 人） |
| `zebra_fall_05s.jpg` | 老人摔倒在斑马线视频 5s 帧 | 斑马线，老人倒地 | 跌倒 | 未检测到人（画面距离/角度原因） |

结果文件：`image_results/*_annotated.jpg` 与 `image_results/*_result.md`。

## 视频测试

| 文件名 | 场景 | 时长 | 实际结果 | 输出文件 |
|--------|------|------|----------|----------|
| 监控下感人的一幕，老人重重摔倒在地，男子举动让人泪目 - Original.mp4 | 街道人行道 | 103s | 检测到 3 次跌倒，跟踪 10 人 | `result_130832.mp4` |
| 老人摔倒在斑马线上 监控下路人的真实反应 - Original.mp4 | 街道斑马线 | 70s | 检测到 9 次跌倒，跟踪 79 人（存在误报） | `result_zebra_131241.mp4` |
| 公园老人晨练退休生活人文生活4K实拍-src_hd_爱给网_aigei_com.mp4 | 公园晨练 | 48s | 检测到 6 次跌倒，跟踪 17 人（正常活动被误判） | `result_park_131143.mp4` |

> 视频由 CPU 推理，处理时间较长（约 2~4 倍实时）。
> 说明：后两个视频出现了较多误报，说明当前 LSTM 模型在复杂户外场景（多人、弯腰/伸展动作）下 false positive 偏高；本次仅修复 UI 层与 signal 报错，未改动检测模型/阈值。

## 额外素材获取建议

公开渠道中，**真实老年人户外公园/街道 walk-to-fall 监控视频**非常稀缺（隐私/伦理原因）。推荐替代方案：

1. 使用本目录已收集的 3 个真实街道监控视频。
2. 在免费素材站搜索 staged 场景：
   - Pexels：`https://www.pexels.com/search/elderly%20fall/`
   - Pixabay：`https://pixabay.com/videos/search/elderly%20fall/`
3. 自行用手机拍摄模拟场景（公园/街道，老人从走路到跌倒）。
4. 公开数据集（多为室内/年轻志愿者）：
   - UR Fall Detection Dataset
   - Le2i Fall Detection Dataset
   - FallVision (Harvard Dataverse)
