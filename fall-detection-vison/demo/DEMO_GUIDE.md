# 老年人跌倒检测系统 - 操作手册 (SOP)

## 1. 环境要求

- macOS / Linux（CPU 即可，无需 GPU）
- Python 3.10+
- 磁盘空间 ≥ 5GB（含虚拟环境）

## 2. 安装（首次使用）

```bash
cd fall-detection-vison

# 创建虚拟环境
python3 -m venv venv

# 安装依赖（PyTorch CPU 版）
./venv/bin/pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
./venv/bin/pip install ultralytics opencv-python numpy gradio flask pyyaml tqdm scikit-learn matplotlib seaborn
```

验证安装：

```bash
./venv/bin/python -c "import torch; print('OK')"
# 输出: OK
```

## 3. 启动系统

```bash
cd fall-detection-vison

# 设置 Ultralytics 配置目录（避免写入用户 Home）
export YOLO_CONFIG_DIR=/tmp/ultralytics_config

# 启动 Dashboard
./venv/bin/python app/dashboard.py
```

启动成功后，浏览器打开：

```
http://127.0.0.1:5001
```

看到深色监控界面即表示系统就绪。

## 4. 功能操作

### 4.1 图片检测

1. 打开浏览器 → http://127.0.0.1:5001
2. 默认选中「📷 图片检测」Tab
3. 点击虚线框区域，选择一张图片（支持 jpg/png）
4. 点击后自动检测，结果区显示：
   - 标注图（骨架叠加 + 跌倒红色框）
   - 每人状态标签（🚨 跌倒 / ✅ 正常）+ 置信度条
   - 特征数值（躯干角度、宽高比、重心高度）
5. 如果检出跌倒，顶部弹出红色 CRITICAL 警报横幅

**测试素材**（`demo/media/` 目录）：

| 文件 | 预期结果 |
|---|---|
| fall_frame_04s.jpg | 🚨 跌倒，触发 CRITICAL 警报 |
| park_normal_10s.jpg | ✅ 正常 |

### 4.2 视频检测

1. 切换到「🎬 视频检测」Tab
2. 点击虚线框区域，选择一段视频（支持 mp4/avi/mov）
3. 点击后开始处理（CPU 推理，视频越长耗时越久）
4. 结果区显示：
   - 标注结果视频（可在线播放）
   - 检出跌倒次数 + 跟踪人数 + 耗时
   - 状态流转列表（如 upright → bending → fallen）
5. 事件自动写入右侧时间线 + 统计面板更新

**测试素材**：

| 文件 | 预期结果 |
|---|---|
| ur_fall_01.mp4 | 1 次跌倒（conf 1.0），6 个状态转换 |

### 4.3 事件管理

- **事件时间线**（右侧面板）：显示所有历史事件，按时间倒序
  - 每条事件包含：状态标签、track ID、触发原因（角度/宽高比/重心高度/速度）
  - fallen 事件用红色标记，bending 用黄色
- **警报弹窗**：检出跌倒时顶部显示红色横幅
  - 点击「确认」按钮关闭弹窗
- **统计面板**（左下方）：
  - 总事件 / 跌倒次数 / 危急 / 紧急
  - 每 10 秒自动刷新

### 4.4 关闭警报

点击警报横幅右侧的「确认」按钮，横幅消失，警报标记为已确认（SQLite 更新）。

## 5. 配置调整

编辑 `configs/system.yaml`：

```yaml
detection:
  device: "cpu"           # 改为 "cuda" 使用 GPU（如有）
  confidence_threshold: 0.3  # YOLO 检测置信度阈值

state_machine:
  smooth_frames: 3         # 状态切换需连续 N 帧确认（越大越保守）
  fallen_timeout_s: 30.0   # 倒地超过 N 秒 → EMERGENCY

features:
  angle_fall_threshold: 45.0   # 躯干角度阈值（度）
  aspect_fall_threshold: 1.4   # 宽高比阈值
```

修改后重启 Dashboard 生效。

## 6. 数据管理

| 路径 | 说明 |
|---|---|
| `data/events.db` | SQLite 事件数据库（所有历史记录） |
| `data/screenshots/` | 跌倒事件关键帧截图 |
| `data/logs/` | 系统日志 |

清空所有历史事件：

```bash
rm -rf data/events.db data/screenshots/ data/logs/
```

重启 Dashboard 后自动重建空数据库。

## 7. 故障排查

| 问题 | 原因 | 解决 |
|---|---|---|
| 启动报错 `ModuleNotFoundError` | venv 未激活或依赖未装 | 重新执行第 2 步安装 |
| 端口 5001 被占用 | 其他程序占用了端口 | `lsof -i :5001` 找到进程后 kill，或修改 dashboard.py 的 port |
| 视频处理很慢 | CPU 推理，正常现象 | 缩短视频或使用更短的测试片段 |
| 页面显示「无法连接」 | 服务未启动或已崩溃 | 重新执行第 3 步启动 |
| Ultralytics 配置报错 | 写入权限受限 | 确保 `YOLO_CONFIG_DIR=/tmp/ultralytics_config` 已设置 |

## 8. 系统架构

```
视频/图片输入
    │
    ▼
[1] YOLO11-Pose      → 人体检测 + 17 个 COCO 骨架关键点
    │
    ▼
[2] BoT-SORT         → 跨帧多人跟踪（Re-ID 遮挡恢复）
    │
    ▼
[3] 特征提取          → 5 维特征：躯干角度 / 重心高度 / 垂直速度 / 宽高比 / 关键点置信度
    │
    ├──▼
    │   [3a] LSTM 分类器  → 30 帧时序分类（normal / falling / fallen）
    │
    ├──▼
    │   [3b] 状态机       → 时序平滑 + 动作状态流转
    │                      UPRIGHT → BENDING → SITTING → FALLING → FALLEN
    │                      （连续 N 帧确认，消除单帧噪声）
    │
    ▼
[4] 分级预警          → WARNING（疑似）→ CRITICAL（确认）→ EMERGENCY（超时）
    │
    ▼
[5] SQLite 事件存储    → 时间 / 人员 / 置信度 / 触发规则 / 状态流转
    │
    ▼
[6] Flask Dashboard   → 深色监控 UI + 实时时间线 + 统计面板
```

## 9. API 接口

| 端点 | 方法 | 说明 |
|---|---|---|
| `/api/detect/image` | POST | 上传图片进行检测（multipart/form-data, field: image） |
| `/api/detect/video` | POST | 上传视频进行检测（multipart/form-data, field: video） |
| `/api/events` | GET | 获取最近 50 条事件 |
| `/api/alerts` | GET | 获取未确认警报 |
| `/api/alerts/ack` | POST | 确认警报（JSON body: `{"alert_id": N}`） |
| `/api/stats` | GET | 获取统计信息 |
