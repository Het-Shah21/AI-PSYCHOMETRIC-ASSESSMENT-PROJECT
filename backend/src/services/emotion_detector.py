"""
Task 2.3 — Real-Time Emotion Detection via Webcam (Client-Side)

This module provides the TypeScript component spec and Python
signal processing for webcam-based emotion detection.

Architecture:
  - TensorFlow.js face-api runs ENTIRELY client-side (privacy-first)
  - Only aggregated emotion labels + valence/arousal are sent to backend
  - No images or video are transmitted or stored
  - User consent is required before activation
  - Graceful fallback when webcam is unavailable or declined

Emotion Model: 7 basic emotions (Ekman) → valence-arousal mapping
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Final


class EmotionLabel(str, Enum):
    """Ekman's 7 basic emotions + neutral."""
    NEUTRAL = "neutral"
    HAPPY = "happy"
    SAD = "sad"
    ANGRY = "angry"
    FEARFUL = "fearful"
    DISGUSTED = "disgusted"
    SURPRISED = "surprised"


@dataclass(frozen=True)
class EmotionReading:
    """A single emotion detection reading from webcam."""
    timestamp_ms: int
    dominant_emotion: EmotionLabel
    confidence: float         # Detection confidence [0, 1]
    valence: float           # Positive/negative [-1, 1]
    arousal: float           # Calm/excited [0, 1]
    face_detected: bool = True


# Valence-Arousal mapping for each emotion (Russell's circumplex model)
EMOTION_VA_MAP: Final[dict[EmotionLabel, tuple[float, float]]] = {
    EmotionLabel.NEUTRAL:   (0.0,  0.2),
    EmotionLabel.HAPPY:     (0.8,  0.6),
    EmotionLabel.SAD:       (-0.7, 0.2),
    EmotionLabel.ANGRY:     (-0.5, 0.8),
    EmotionLabel.FEARFUL:   (-0.6, 0.7),
    EmotionLabel.DISGUSTED: (-0.6, 0.5),
    EmotionLabel.SURPRISED: (0.2,  0.9),
}


def emotion_to_valence_arousal(
    emotion: EmotionLabel,
) -> tuple[float, float]:
    """Map discrete emotion to valence-arousal coordinates."""
    return EMOTION_VA_MAP.get(emotion, (0.0, 0.2))


@dataclass
class EmotionAggregator:
    """Aggregates emotion readings over a time window for scoring."""
    readings: list[EmotionReading]

    @property
    def dominant_emotion(self) -> EmotionLabel:
        if not self.readings:
            return EmotionLabel.NEUTRAL
        counts: dict[EmotionLabel, int] = {}
        for r in self.readings:
            counts[r.dominant_emotion] = counts.get(r.dominant_emotion, 0) + 1
        return max(counts, key=counts.get)  # type: ignore

    @property
    def avg_valence(self) -> float:
        if not self.readings:
            return 0.0
        return sum(r.valence for r in self.readings) / len(self.readings)

    @property
    def avg_arousal(self) -> float:
        if not self.readings:
            return 0.5
        return sum(r.arousal for r in self.readings) / len(self.readings)

    @property
    def emotional_stability(self) -> float:
        """Measure of how stable emotions are over the window.
        Low variance = high stability. Returns [0, 1].
        """
        if len(self.readings) < 2:
            return 0.5
        valences = [r.valence for r in self.readings]
        mean_v = sum(valences) / len(valences)
        variance = sum((v - mean_v) ** 2 for v in valences) / len(valences)
        # Map variance to stability (inverse, capped)
        return max(0.0, min(1.0, 1.0 - min(variance, 1.0)))

    @property
    def emotion_diversity(self) -> float:
        """Shannon entropy of emotion distribution, normalized to [0, 1]."""
        if not self.readings:
            return 0.0
        import math
        counts: dict[EmotionLabel, int] = {}
        for r in self.readings:
            counts[r.dominant_emotion] = counts.get(r.dominant_emotion, 0) + 1
        total = len(self.readings)
        entropy = -sum(
            (c / total) * math.log2(c / total)
            for c in counts.values()
            if c > 0
        )
        max_entropy = math.log2(len(EmotionLabel))
        return entropy / max_entropy if max_entropy > 0 else 0.0

    def to_behavioral_signals(self) -> dict[str, float]:
        """Convert aggregated emotions to behavioral signal values."""
        return {
            "emotion_stability": round(self.emotional_stability, 3),
            "emotion_valence": round(self.avg_valence, 3),
            "emotion_arousal": round(self.avg_arousal, 3),
            "emotion_diversity": round(self.emotion_diversity, 3),
        }


# ---------------------------------------------------------------------------
# Client-side component spec (for frontend implementation in Task 5.1)
# ---------------------------------------------------------------------------

EMOTION_DETECTOR_SPEC: Final[dict] = {
    "component": "EmotionDetector",
    "library": "@vladmandic/face-api or face-api.js",
    "models_required": [
        "tinyFaceDetector",        # Lightweight face detection
        "faceExpressionNet",       # 7-emotion classification
    ],
    "inference_frequency_hz": 2,   # 2 FPS to save CPU
    "privacy": {
        "video_stored": False,
        "images_stored": False,
        "data_sent": "aggregated emotion labels + valence/arousal only",
        "consent_required": True,
        "camera_indicator": "visible green dot when active",
    },
    "fallback": {
        "no_camera": "Skip emotion signals; score using behavioral data only",
        "consent_denied": "Same as no_camera",
        "detection_failure": "Use last valid reading; degrade gracefully",
    },
}
