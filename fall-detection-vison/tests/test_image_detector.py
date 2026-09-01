"""Tests for image-based rule fall detection (src/image_detector.py)."""

import numpy as np
import pytest

from src.image_detector import (
    ANGLE_FALL_THRESHOLD,
    ASPECT_FALL_THRESHOLD,
    ImageFallDetector,
)


class FakeBoxes:
    """Minimal fake for ultralytics results.boxes."""

    def __init__(self, boxes: np.ndarray):
        self._boxes = boxes

    @property
    def xyxy(self):
        return self._boxes

    def __len__(self):
        return len(self._boxes)


class FakeKeypoints:
    """Minimal fake for ultralytics results.keypoints."""

    def __init__(self, kps: np.ndarray):
        self._kps = kps

    @property
    def data(self):
        return self._kps


class FakeResult:
    """Minimal fake for a single ultralytics result."""

    def __init__(self, boxes: list[list[float]], kps_list: list[np.ndarray]):
        self.boxes = FakeBoxes(np.array(boxes, dtype=np.float32)) if boxes else None
        self.keypoints = FakeKeypoints(
            np.stack(kps_list) if kps_list else np.zeros((0, 17, 3))
        )


class FakeModel:
    """Fake YOLO model: returns canned results, records the call."""

    def __init__(self, results: list[FakeResult]):
        self._results = results
        self.called_with = None

    def __call__(self, image, conf=None, verbose=None):
        self.called_with = {"conf": conf, "verbose": verbose}
        # Return a list with a single FakeResult with .__getitem__ support
        return _ResultList(self._results)


class _ResultList(list):
    """ultralytics returns a list-like; support [0] indexing."""


# ----------------------------------------------------------------
# Helpers to build keypoints
# ----------------------------------------------------------------

def make_keypoints(torso_angle_deg: float = 0.0, conf: float = 0.9) -> np.ndarray:
    """Synthesize COCO keypoints with a given torso angle from vertical.

    angle 0  → standing upright (nose above hip midpoint, aligned)
    angle 90 → lying horizontal (nose level with hips, offset sideways)
    """
    kps = np.zeros((17, 3), dtype=np.float32)
    for i in range(17):
        kps[i] = [320, 240, conf]

    rad = np.deg2rad(torso_angle_deg)
    # Hip midpoint fixed at (320, 350)
    hip_x, hip_y = 320.0, 350.0
    # Nose offset: dx = sin(angle)*len, dy = cos(angle)*len (screen y down)
    length = 250.0
    nose_x = hip_x + np.sin(rad) * length
    nose_y = hip_y - np.cos(rad) * length
    kps[0] = [nose_x, nose_y, conf]  # nose
    kps[5] = [hip_x - 30, hip_y - 120, conf]  # left shoulder
    kps[6] = [hip_x + 30, hip_y - 120, conf]  # right shoulder
    kps[11] = [hip_x - 25, hip_y, conf]  # left hip
    kps[12] = [hip_x + 25, hip_y, conf]  # right hip
    kps[15] = [hip_x - 20, hip_y + 200, conf]  # left ankle
    kps[16] = [hip_x + 20, hip_y + 200, conf]  # right ankle
    return kps


def bbox_for(angle_deg: float) -> list[float]:
    """Bounding box that matches posture: narrow for standing, wide for lying."""
    if angle_deg > 60:
        # Lying: wide box (x-extent big, y-extent small)
        return [100.0, 300.0, 700.0, 450.0]
    # Standing: narrow tall box
    return [280.0, 50.0, 360.0, 550.0]


def make_detector(results: list[FakeResult]) -> tuple[ImageFallDetector, FakeModel]:
    from src.feature_extraction import FeatureExtractor
    from src.image_detector import MIN_KEYPOINT_CONF

    model = FakeModel(results)
    det = ImageFallDetector.__new__(ImageFallDetector)  # bypass __init__
    det.model = model
    det.feature_extractor = FeatureExtractor(confidence_threshold=MIN_KEYPOINT_CONF)
    return det, model


# ----------------------------------------------------------------
# _judge: pure rule logic
# ----------------------------------------------------------------

class TestJudge:
    def test_standing_is_normal(self):
        det = ImageFallDetector.__new__(ImageFallDetector)
        label, conf = det._judge(angle_deg=10.0, aspect=0.4)
        assert label == "NORMAL"
        assert conf == 1.0

    def test_lying_angle_triggers_fall(self):
        det = ImageFallDetector.__new__(ImageFallDetector)
        label, conf = det._judge(angle_deg=70.0, aspect=0.8)
        assert label == "FALL"
        assert conf == pytest.approx(0.75)  # 0.5 + 1*0.25

    def test_wide_bbox_triggers_fall(self):
        det = ImageFallDetector.__new__(ImageFallDetector)
        label, conf = det._judge(angle_deg=20.0, aspect=2.5)
        assert label == "FALL"
        assert conf == pytest.approx(0.75)

    def test_both_triggers_give_max_confidence(self):
        det = ImageFallDetector.__new__(ImageFallDetector)
        label, conf = det._judge(angle_deg=80.0, aspect=3.0)
        assert label == "FALL"
        assert conf == 1.0  # capped

    def test_boundary_angle_just_below_threshold_is_normal(self):
        det = ImageFallDetector.__new__(ImageFallDetector)
        label, _ = det._judge(angle_deg=ANGLE_FALL_THRESHOLD - 1.0, aspect=0.5)
        assert label == "NORMAL"

    def test_boundary_aspect_just_below_threshold_is_normal(self):
        det = ImageFallDetector.__new__(ImageFallDetector)
        label, _ = det._judge(angle_deg=10.0, aspect=ASPECT_FALL_THRESHOLD - 0.01)
        assert label == "NORMAL"


# ----------------------------------------------------------------
# detect: end-to-end with fake model
# ----------------------------------------------------------------

class TestDetect:
    def test_no_person(self):
        det, _ = make_detector([FakeResult(boxes=[], kps_list=[])])
        image = np.zeros((480, 640, 3), dtype=np.uint8)
        result, annotated = det.detect(image)
        assert result.label == "NO_PERSON"
        assert result.persons_detected == 0
        assert annotated.shape == image.shape

    def test_standing_person_normal(self):
        kps = make_keypoints(torso_angle_deg=5.0)
        det, model = make_detector(
            [FakeResult(boxes=[bbox_for(0.0)], kps_list=[kps])]
        )
        image = np.zeros((480, 640, 3), dtype=np.uint8)
        result, annotated = det.detect(image)
        assert result.label == "NORMAL"
        assert result.persons_detected == 1
        assert result.confidence == 1.0
        assert model.called_with["conf"] == 0.3  # detection confidence
        assert annotated.shape == image.shape

    def test_fallen_person_fall(self):
        kps = make_keypoints(torso_angle_deg=75.0)
        det, _ = make_detector(
            [FakeResult(boxes=[bbox_for(75.0)], kps_list=[kps])]
        )
        image = np.zeros((480, 640, 3), dtype=np.uint8)
        result, annotated = det.detect(image)
        assert result.label == "FALL"
        assert result.persons_detected == 1
        assert result.confidence >= 0.75
        assert len(result.details) == 1

    def test_multiple_persons_any_fall_wins(self):
        standing = make_keypoints(torso_angle_deg=5.0)
        fallen = make_keypoints(torso_angle_deg=80.0)
        det, _ = make_detector(
            [
                FakeResult(
                    boxes=[bbox_for(0.0), bbox_for(80.0)],
                    kps_list=[standing, fallen],
                )
            ]
        )
        image = np.zeros((480, 640, 3), dtype=np.uint8)
        result, _ = det.detect(image)
        assert result.label == "FALL"
        assert result.persons_detected == 2
        assert len(result.details) == 2
