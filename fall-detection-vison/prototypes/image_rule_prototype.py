#!/usr/bin/env python3
"""PROTOTYPE — 图片单帧规则式跌倒检测（ticket 01）

目的：回答"单帧图片用什么特征、什么阈值判断跌倒"。
用法：python prototypes/image_rule_prototype.py <图片路径> [<图片路径>...]
输出：打印每个检测到的人的特征状态 + 判断结果；并把标注图保存到 prototypes/out/。

这是 throwaway 原型，验证通过后逻辑会并入正式代码。
"""

import sys
from pathlib import Path

import cv2
from ultralytics import YOLO

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.feature_extraction import FeatureExtractor  # noqa: E402

# ---- 可调阈值（原型标定用）----
ANGLE_FALL_THRESHOLD = 45.0   # 躯干与竖直方向夹角（度），大于此视为"接近水平"
ASPECT_FALL_THRESHOLD = 1.4   # bbox 宽/高比，大于此视为"宽扁（倒地）"
MIN_CONF = 0.3                # 关键点最小置信度

MODEL = YOLO("yolo11n-pose.pt")
FE = FeatureExtractor(confidence_threshold=MIN_CONF)


def judge(fv) -> tuple[str, float, list[str]]:
    """基于单帧特征做规则判断。返回 (标签, 置信度分数, 触发规则列表)。"""
    triggers = []
    angle_deg = fv.body_angle * 180.0  # FeatureExtractor normalize_angle=True → 0-1
    if angle_deg > ANGLE_FALL_THRESHOLD:
        triggers.append(f"角度{angle_deg:.0f}°>{ANGLE_FALL_THRESHOLD}°")
    if fv.bbox_aspect_ratio > ASPECT_FALL_THRESHOLD:
        triggers.append(f"宽高比{fv.bbox_aspect_ratio:.2f}>{ASPECT_FALL_THRESHOLD}")

    if triggers:
        # 简单置信度：0.5 基础 + 每条规则 +0.25，封顶 1.0
        conf = min(1.0, 0.5 + 0.25 * len(triggers))
        return "FALL", conf, triggers
    return "NORMAL", 1.0 - min(0.5, 0.2 * len(triggers)), []


def process_image(img_path: Path):
    img = cv2.imread(str(img_path))
    if img is None:
        print(f"!! 无法读取 {img_path}")
        return
    h, w = img.shape[:2]

    results = MODEL(img, conf=0.3, verbose=False)[0]
    n_persons = len(results.boxes) if results.boxes else 0
    print(f"\n=== {img_path.name} ({w}x{h}) 检测到 {n_persons} 人 ===")

    out = img.copy()
    if results.boxes is None or len(results.boxes) == 0:
        print("   无人")
        cv2.imwrite(str(OUT_DIR / f"{img_path.stem}_out.jpg"), out)
        return

    kps_all = results.keypoints.data.cpu().numpy()  # (N,17,3)
    boxes = results.boxes.xyxy.cpu().numpy()

    for i, (box, kps) in enumerate(zip(boxes, kps_all)):
        bbox = tuple(float(v) for v in box)
        fv = FE.extract(kps, bbox, frame_height=h, prev_cog_height=None)

        label, conf, triggers = judge(fv)
        angle_deg = fv.body_angle * 180.0

        # ---- 状态展示（prototype 要求 surface the state）----
        print(f"  [{i}] 标签={label} 置信度={conf:.2f}")
        print(f"      躯干角度={angle_deg:6.1f}° (站立≈0-15°, 倒地≈60-90°)")
        print(f"      bbox宽高比={fv.bbox_aspect_ratio:.2f} (站立≈0.3-0.5, 倒地≈1.5-3.0)")
        print(f"      重心高度={fv.cog_height:.2f} (0=顶, 1=底)")
        print(f"      关键点置信度均值={fv.keypoint_confidence:.2f}")
        print(f"      触发规则: {triggers if triggers else '无'}")

        # 可视化：画框 + 骨架 + 标签
        x1, y1, x2, y2 = (int(v) for v in bbox)
        color = (0, 0, 255) if label == "FALL" else (0, 255, 0)
        cv2.rectangle(out, (x1, y1), (x2, y2), color, 3)
        label_txt = f"{label} {conf:.0%}"
        cv2.putText(out, label_txt, (x1, max(y1 - 10, 20)),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 3)
        # 骨架
        for j in range(0, 17, 2):
            px, py, pc = kps[j]
            if pc > MIN_CONF:
                cv2.circle(out, (int(px), int(py)), 6, (255, 255, 0), -1)

    OUT_DIR.mkdir(exist_ok=True)
    out_path = OUT_DIR / f"{img_path.stem}_out.jpg"
    cv2.imwrite(str(out_path), out)
    print(f"  标注图: {out_path}")


OUT_DIR = Path(__file__).resolve().parent / "out"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python prototypes/image_rule_prototype.py <图片> [<图片>...]")
        sys.exit(1)
    for p in sys.argv[1:]:
        process_image(Path(p))
