"""Image-based rule fall detection (single frame).

Implements the rule validated in ticket 01: torso angle > 45° OR bbox
aspect ratio > 1.4 → FALL, with confidence = 0.5 + 0.25 × #triggers.
"""

import logging
from dataclasses import dataclass, field

import cv2
import numpy as np
import torch
from ultralytics import YOLO

from src.feature_extraction import FeatureExtractor
from src.utils import COLOR_GREEN, COLOR_RED

logger = logging.getLogger(__name__)

# ---- Validated thresholds (ticket 01) ----
ANGLE_FALL_THRESHOLD = 45.0   # torso angle vs vertical (deg)
ASPECT_FALL_THRESHOLD = 1.4   # bbox width / height
DETECT_CONFIDENCE = 0.3       # YOLO person-detection confidence
MIN_KEYPOINT_CONF = 0.3       # keypoint visibility confidence


@dataclass
class ImageFallResult:
    """Result of single-frame rule fall detection for one image."""

    label: str                      # "FALL" | "NORMAL" | "NO_PERSON"
    confidence: float               # 0.0-1.0
    details: list[str] = field(default_factory=list)  # per-person detail lines
    persons_detected: int = 0
    persons: list[dict] = field(default_factory=list)  # structured per-person info


class ImageFallDetector:
    """YOLO11-Pose single-frame detection + rule-based fall judgment."""

    def __init__(
        self,
        model_name: str = "yolo11n-pose.pt",
        device: str | None = None,
    ):
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = device
        logger.info(f"Loading YOLO model '{model_name}' on device '{device}'")
        self.model = YOLO(model_name)
        self.feature_extractor = FeatureExtractor(
            confidence_threshold=MIN_KEYPOINT_CONF
        )
        logger.info("ImageFallDetector initialized")

    # -------------------------------------------------
    def _judge(self, angle_deg: float, aspect: float) -> tuple[str, float]:
        """Rule judgment. Returns (label, confidence)."""
        triggers = []
        if angle_deg > ANGLE_FALL_THRESHOLD:
            triggers.append(f"躯干角度 {angle_deg:.0f}°")
        if aspect > ASPECT_FALL_THRESHOLD:
            triggers.append(f"宽高比 {aspect:.2f}")
        if triggers:
            conf = min(1.0, 0.5 + 0.25 * len(triggers))
            return "FALL", conf
        return "NORMAL", 1.0

    # -------------------------------------------------
    def detect(
        self, image: np.ndarray
    ) -> tuple[ImageFallResult, np.ndarray]:
        """Detect falls in a single BGR image.

        Returns:
            (result, annotated_image)
        """
        h, w = image.shape[:2]
        out = image.copy()

        results = self.model(image, conf=DETECT_CONFIDENCE, verbose=False)[0]
        if results.boxes is None or len(results.boxes) == 0:
            result = ImageFallResult(
                label="NO_PERSON", confidence=0.0,
                details=["未检测到人"],
            )
            return result, out

        # Normalize to numpy: ultralytics returns torch tensors, tests may
        # hand us plain numpy arrays.
        kps_data = results.keypoints.data
        kps_all = np.asarray(
            kps_data.cpu().numpy() if hasattr(kps_data, "cpu") else kps_data
        )  # (N, 17, 3)
        boxes_xyxy = results.boxes.xyxy
        boxes = np.asarray(
            boxes_xyxy.cpu().numpy() if hasattr(boxes_xyxy, "cpu") else boxes_xyxy
        )
        details: list[str] = []
        persons: list[dict] = []
        any_fall = False
        max_conf = 0.0

        for i, (box, kps) in enumerate(zip(boxes, kps_all)):
            bbox = tuple(float(v) for v in box)
            fv = self.feature_extractor.extract(
                kps, bbox, frame_height=h, prev_cog_height=None
            )
            angle_deg = fv.body_angle * 180.0
            label, conf = self._judge(angle_deg, fv.bbox_aspect_ratio)

            triggers: list[str] = []
            if angle_deg > ANGLE_FALL_THRESHOLD:
                triggers.append("躯干倾斜")
            if fv.bbox_aspect_ratio > ASPECT_FALL_THRESHOLD:
                triggers.append("身体横向展开")

            if label == "FALL":
                any_fall = True
            max_conf = max(max_conf, conf)

            # Draw
            x1, y1, x2, y2 = (int(v) for v in bbox)
            color = COLOR_RED if label == "FALL" else COLOR_GREEN
            cv2.rectangle(out, (x1, y1), (x2, y2), color, 3)
            cv2.putText(
                out, f"{label} {conf:.0%}", (x1, max(y1 - 10, 20)),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 3,
            )
            # Skeleton dots (every other keypoint for visual clarity)
            for j in range(0, 17, 2):
                px, py, pc = kps[j]
                if pc > MIN_KEYPOINT_CONF:
                    cv2.circle(out, (int(px), int(py)), 6, (255, 255, 0), -1)

            details.append(
                f"人{i+1}: {label} 置信度{conf:.0%} | 躯干角度{angle_deg:.0f}° | "
                f"宽高比{fv.bbox_aspect_ratio:.2f} | 重心高度{fv.cog_height:.2f}"
            )
            persons.append({
                "person_id": i + 1,
                "label": label,
                "confidence": conf,
                "angle_deg": angle_deg,
                "aspect_ratio": fv.bbox_aspect_ratio,
                "cog_height": fv.cog_height,
                "triggers": triggers,
            })

        result = ImageFallResult(
            label="FALL" if any_fall else "NORMAL",
            confidence=max_conf,
            details=details,
            persons_detected=len(boxes),
            persons=persons,
        )
        return result, out
