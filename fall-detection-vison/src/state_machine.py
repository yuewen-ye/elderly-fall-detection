"""Per-person temporal action state machine for fall detection.

States: UPRIGHT → BENDING → SITTING → FALLING → FALLEN → RECOVERED

Each state transition requires N consecutive frames of evidence (temporal
smoothing) to eliminate single-frame noise. The state machine runs
independently per track_id so multiple persons are tracked in isolation.
"""

import logging
import time
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class ActionState(str, Enum):
    UPRIGHT = "upright"
    BENDING = "bending"
    SITTING = "sitting"
    FALLING = "falling"
    FALLEN = "fallen"
    RECOVERED = "recovered"
    UNKNOWN = "unknown"


# Alert levels mapped from states
STATE_ALERT = {
    ActionState.UPRIGHT: "NONE",
    ActionState.BENDING: "NONE",
    ActionState.SITTING: "NONE",
    ActionState.FALLING: "WARNING",
    ActionState.FALLEN: "CRITICAL",
    ActionState.RECOVERED: "NONE",
    ActionState.UNKNOWN: "NONE",
}


@dataclass
class StateTransition:
    """Record of a single state change."""

    from_state: ActionState
    to_state: ActionState
    frame_num: int
    timestamp: float
    confidence: float
    features: dict  # snapshot of key features at transition
    reason: str  # human-readable trigger explanation


@dataclass
class PersonStateMachine:
    """State machine for one tracked person."""

    track_id: int
    current_state: ActionState = ActionState.UNKNOWN
    state_history: list[StateTransition] = field(default_factory=list)
    candidate_state: ActionState | None = None
    candidate_count: int = 0

    # Configurable thresholds
    smooth_frames: int = 3  # consecutive frames to confirm transition
    fallen_timeout_s: float = 30.0  # seconds in FALLEN before EMERGENCY

    # Runtime
    fallen_since: float | None = None
    last_update_frame: int = 0

    def classify_frame(
        self,
        body_angle: float,
        aspect_ratio: float,
        cog_height: float,
        vertical_velocity: float,
    ) -> ActionState:
        """Classify a single frame into a raw action state based on features."""
        # Features are normalized: body_angle 0-1 (0.5=90°), CoG 0-1 (1=bottom of frame)
        if aspect_ratio > 1.4 and cog_height > 0.65:
            return ActionState.FALLEN
        if vertical_velocity > 0.04 and (aspect_ratio > 0.9 or cog_height > 0.6):
            return ActionState.FALLING
        if aspect_ratio > 1.0 and cog_height > 0.55 and abs(vertical_velocity) < 0.03:
            return ActionState.SITTING
        if body_angle > 0.15:
            return ActionState.BENDING
        return ActionState.UPRIGHT

    def update(
        self,
        frame_num: int,
        body_angle: float,
        aspect_ratio: float,
        cog_height: float,
        vertical_velocity: float,
        confidence: float = 0.0,
    ) -> StateTransition | None:
        """Update with one frame's features. Returns transition if state changed."""
        raw = self.classify_frame(body_angle, aspect_ratio, cog_height, vertical_velocity)
        self.last_update_frame = frame_num

        # Temporal smoothing: require N consecutive frames
        if raw == self.current_state:
            self.candidate_state = None
            self.candidate_count = 0
            self._check_fallen_timeout()
            return None

        if raw == self.candidate_state:
            self.candidate_count += 1
        else:
            self.candidate_state = raw
            self.candidate_count = 1

        if self.candidate_count >= self.smooth_frames:
            return self._transition(raw, frame_num, confidence, body_angle, aspect_ratio, cog_height, vertical_velocity)

        self._check_fallen_timeout()
        return None

    def _transition(
        self,
        new_state: ActionState,
        frame_num: int,
        confidence: float,
        body_angle: float,
        aspect_ratio: float,
        cog_height: float,
        vertical_velocity: float,
    ) -> StateTransition:
        transition = StateTransition(
            from_state=self.current_state,
            to_state=new_state,
            frame_num=frame_num,
            timestamp=time.time(),
            confidence=confidence,
            features={
                "body_angle": round(body_angle, 1),
                "aspect_ratio": round(aspect_ratio, 2),
                "cog_height": round(cog_height, 2),
                "vertical_velocity": round(vertical_velocity, 3),
            },
            reason=self._explain(new_state, body_angle, aspect_ratio, cog_height, vertical_velocity),
        )
        self.state_history.append(transition)
        self.current_state = new_state
        self.candidate_state = None
        self.candidate_count = 0

        if new_state == ActionState.FALLEN:
            self.fallen_since = time.time()
        elif new_state in (ActionState.UPRIGHT, ActionState.RECOVERED):
            self.fallen_since = None

        logger.info(
            "Track %d: %s → %s (frame %d, %.1f°, AR %.2f, CoG %.2f)",
            self.track_id,
            transition.from_state.value,
            new_state.value,
            frame_num,
            body_angle,
            aspect_ratio,
            cog_height,
        )
        return transition

    def _explain(
        self,
        state: ActionState,
        body_angle: float,
        aspect_ratio: float,
        cog_height: float,
        vertical_velocity: float,
    ) -> str:
        parts = [f"angle={body_angle:.0f}°", f"AR={aspect_ratio:.2f}", f"CoG={cog_height:.2f}", f"v={vertical_velocity:.3f}"]
        if state == ActionState.FALLING:
            return f"FALLING: {' | '.join(parts)}"
        if state == ActionState.FALLEN:
            return f"FALLEN: {' | '.join(parts)}"
        if state == ActionState.SITTING:
            return f"SITTING: {' | '.join(parts)}"
        return f"{state.value}: {' | '.join(parts)}"

    def _check_fallen_timeout(self) -> bool:
        """Check if person has been in FALLEN state past the timeout. Returns True if EMERGENCY."""
        if self.current_state == ActionState.FALLEN and self.fallen_since is not None:
            elapsed = time.time() - self.fallen_since
            return elapsed >= self.fallen_timeout_s
        return False

    @property
    def alert_level(self) -> str:
        """Current alert level: NONE / WARNING / CRITICAL / EMERGENCY."""
        if self._check_fallen_timeout():
            return "EMERGENCY"
        return STATE_ALERT.get(self.current_state, "NONE")

    @property
    def fallen_duration_s(self) -> float:
        if self.fallen_since is None:
            return 0.0
        return time.time() - self.fallen_since


class StateMachineManager:
    """Manages state machines for multiple tracked persons."""

    def __init__(self, smooth_frames: int = 3, fallen_timeout_s: float = 30.0):
        self.smooth_frames = smooth_frames
        self.fallen_timeout_s = fallen_timeout_s
        self.machines: dict[int, PersonStateMachine] = {}

    def get_or_create(self, track_id: int) -> PersonStateMachine:
        if track_id not in self.machines:
            self.machines[track_id] = PersonStateMachine(
                track_id=track_id,
                smooth_frames=self.smooth_frames,
                fallen_timeout_s=self.fallen_timeout_s,
            )
        return self.machines[track_id]

    def update(
        self,
        track_id: int,
        frame_num: int,
        body_angle: float,
        aspect_ratio: float,
        cog_height: float,
        vertical_velocity: float,
        confidence: float = 0.0,
    ) -> StateTransition | None:
        sm = self.get_or_create(track_id)
        return sm.update(frame_num, body_angle, aspect_ratio, cog_height, vertical_velocity, confidence)

    def all_alerts(self) -> list[dict]:
        """Get all persons currently in an alert state."""
        alerts = []
        for tid, sm in self.machines.items():
            if sm.alert_level != "NONE":
                alerts.append({
                    "track_id": tid,
                    "state": sm.current_state.value,
                    "alert_level": sm.alert_level,
                    "fallen_duration_s": round(sm.fallen_duration_s, 1),
                })
        return alerts
