# 02 - 演示素材调研

Type: research
Status: resolved
Blocked by:

## Question

演示视频用什么素材？现有 `output/test_result.avi`（7.3s 4K，检出 1 次跌倒）够不够？是否需要补充素材（如 UR Fall Detection Dataset 的视频片段、Le2i 公开视频），从哪里可靠获取（版权/下载链接可用性）？是否需要一个"正常行走+跌倒"对比片段做演示更有说服力？

## 背景

交付物包含"标注结果视频 + 界面录屏"（Q8-C）。素材决定演示效果，且需确认公开素材的下载可用性与许可。

## Answer

调研结论（详见 `research/02-demo-material-findings.md`）：

1. **现有 `output/test_result.avi` 可作为演示主体**：经姿态量化验证（帧10-70躯干近竖直 1-14° → 帧90过渡 43° → 帧105-180近水平 67-83° + bbox 变宽扁），与 `result_test.json` 的 fall 事件（帧102-181, conf 1.0）吻合，确认真实跌倒场景。4K/7.28s，标注含骨架+红字告警+状态栏。源为 Pexels 4K 素材（ID 10240439）。
2. **UR Fall Detection Dataset 可靠**：官方页 HTTP 200，直链 `https://fenix.ur.edu.pl/mkepski/ds/data/<fall|adl>-NN-cam0.mp4` 逐条验证可用，单段 0.5-3MB（fall-01-cam0.mp4 1.24MB、adl-40-cam0.mp4 2.66MB），zip 55MB；许可 CC BY-NC-SA 4.0，非商业学术用途、无需申请。
3. **Le2i 官方下载已失效**（le2i.cnrs.fr 无响应，ImViA 页显示 "waiting for new link"），仅 Kaggle 镜像可用（需登录），不建议现在下载。
4. **推荐方案**：A) 用现有 `test_result.avi` 做标注结果视频（零下载）；B) 从 UR 下载 1-2 段小 mp4（ADL 行走 + fall 跌倒，<10MB）做"不告警→告警"对比片段。不下载 Le2i。

→ 素材策略：主体用现有 test_result.avi；对比片段可选下载 UR 小片段（总量 <10MB，磁盘允许）。
