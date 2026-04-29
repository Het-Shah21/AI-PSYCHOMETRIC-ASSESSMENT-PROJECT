"""
Task 2.2 — Adaptive Difficulty and Uncertainty Injection

Implements a reinforcement-learning-inspired adaptive engine that:
  1. Adjusts interaction difficulty based on user performance
  2. Injects calibrated uncertainty to probe stress tolerance
  3. Maintains a performance model per-construct for real-time adaptation
  4. Uses epsilon-greedy exploration to balance measurement precision

Based on computerized adaptive testing (CAT) principles with
a simplified Thompson Sampling approach for difficulty selection.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Final


# ---------------------------------------------------------------------------
# Performance Tracking
# ---------------------------------------------------------------------------

@dataclass
class PerformanceState:
    """Tracks user performance within a construct for adaptation."""
    construct_id: str
    ability_estimate: float = 0.5    # Current estimated ability [0, 1]
    confidence: float = 0.1          # Confidence in estimate (increases with data)
    responses_count: int = 0
    correct_count: int = 0
    total_latency_ms: int = 0
    uncertainty_reactions: list[float] = field(default_factory=list)

    @property
    def accuracy(self) -> float:
        return self.correct_count / max(1, self.responses_count)

    @property
    def avg_latency_ms(self) -> float:
        return self.total_latency_ms / max(1, self.responses_count)


# ---------------------------------------------------------------------------
# Adaptive Engine
# ---------------------------------------------------------------------------

class AdaptiveEngine:
    """RL-inspired engine for dynamic difficulty and uncertainty injection."""

    # Target accuracy for optimal measurement (per CAT theory)
    TARGET_ACCURACY: Final[float] = 0.65
    # Epsilon for exploration (probability of random difficulty)
    EPSILON: Final[float] = 0.15
    # Learning rate for ability update
    LEARNING_RATE: Final[float] = 0.3
    # Uncertainty injection probability
    UNCERTAINTY_PROB: Final[float] = 0.25

    def __init__(self):
        self.states: dict[str, PerformanceState] = {}

    def get_state(self, construct_id: str) -> PerformanceState:
        if construct_id not in self.states:
            self.states[construct_id] = PerformanceState(construct_id=construct_id)
        return self.states[construct_id]

    def select_difficulty(self, construct_id: str) -> float:
        """Select difficulty for next interaction using epsilon-greedy.

        Returns difficulty ∈ [0, 1].
        """
        state = self.get_state(construct_id)

        # Exploration: random difficulty
        if random.random() < self.EPSILON:
            return random.uniform(0.2, 0.9)

        # Exploitation: target difficulty matching ability
        # Optimal difficulty = ability level (per CAT, maximizes Fisher information)
        target = state.ability_estimate

        # Add noise proportional to uncertainty in estimate
        noise = random.gauss(0, 0.1 * (1 - state.confidence))
        difficulty = max(0.1, min(0.95, target + noise))

        return round(difficulty, 2)

    def update_performance(
        self,
        construct_id: str,
        was_correct: bool,
        difficulty: float,
        latency_ms: int,
    ) -> None:
        """Update performance model after a response.

        Uses simplified ELO-like update:
          ability += α * (observed - expected)
        where expected = 1 / (1 + e^(4(difficulty - ability)))
        """
        state = self.get_state(construct_id)
        state.responses_count += 1
        state.total_latency_ms += latency_ms

        if was_correct:
            state.correct_count += 1

        # Expected probability of correct answer given current ability and difficulty
        logit = 4.0 * (difficulty - state.ability_estimate)
        expected = 1.0 / (1.0 + math.exp(logit))
        observed = 1.0 if was_correct else 0.0

        # Update ability estimate
        state.ability_estimate += self.LEARNING_RATE * (observed - expected)
        state.ability_estimate = max(0.05, min(0.95, state.ability_estimate))

        # Update confidence (increases with more data, asymptotic)
        state.confidence = 1.0 - (1.0 / (1.0 + 0.3 * state.responses_count))

    def should_inject_uncertainty(self, construct_id: str) -> bool:
        """Decide whether to inject uncertainty into next interaction.

        Uncertainty injection increases when:
        - User has high ability (to probe stress tolerance)
        - Enough baseline data exists (≥2 responses)
        """
        state = self.get_state(construct_id)
        if state.responses_count < 2:
            return False

        # Higher ability = more uncertainty injection
        adjusted_prob = self.UNCERTAINTY_PROB * (0.5 + state.ability_estimate)
        return random.random() < adjusted_prob

    def get_uncertainty_type(self) -> str:
        """Select what type of uncertainty to inject."""
        types = [
            "ambiguous_information",     # Deliberately unclear prompt
            "contradictory_feedback",    # Conflicting info with previous content
            "time_pressure_increase",    # Suddenly reduce time budget
            "missing_context",           # Remove expected context clues
            "social_pressure",           # Introduce observer/evaluator framing
        ]
        return random.choice(types)

    def record_uncertainty_reaction(
        self, construct_id: str, reaction_score: float
    ) -> None:
        """Record how user reacted to uncertainty injection.

        reaction_score ∈ [0, 1]: 0 = avoidant/anxious, 1 = embracing/stable
        """
        state = self.get_state(construct_id)
        state.uncertainty_reactions.append(reaction_score)

    def get_adaptation_summary(self, construct_id: str) -> dict:
        """Get a summary of adaptation state for logging/debugging."""
        state = self.get_state(construct_id)
        return {
            "construct_id": construct_id,
            "ability_estimate": round(state.ability_estimate, 3),
            "confidence": round(state.confidence, 3),
            "accuracy": round(state.accuracy, 3),
            "avg_latency_ms": round(state.avg_latency_ms),
            "responses": state.responses_count,
            "uncertainty_reactions": len(state.uncertainty_reactions),
            "mean_uncertainty_reaction": (
                round(sum(state.uncertainty_reactions) / len(state.uncertainty_reactions), 3)
                if state.uncertainty_reactions else None
            ),
        }
