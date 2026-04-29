"""
Task 2.1 — LLM Service with Prompt Architecture

Uses LangChain + Google Gemini 2.0 Flash (free tier) for:
  1. Adaptive dialogue generation (AI companion)
  2. Text response analysis (sentiment, assertiveness, depth)
  3. Dynamic puzzle content generation
  4. Score explanation narratives

Falls back to rule-based responses when API is unavailable.
"""

from __future__ import annotations

import os
import json
import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# LLM Configuration
# ---------------------------------------------------------------------------

@dataclass
class LLMConfig:
    """Configuration for the LLM service."""
    provider: str = "google_gemini"
    model_name: str = "gemini-2.0-flash"
    temperature: float = 0.7
    max_output_tokens: int = 512
    api_key: str = ""
    requests_per_minute: int = 15
    requests_per_day: int = 1500
    timeout_seconds: int = 10


# ---------------------------------------------------------------------------
# Prompt Templates
# ---------------------------------------------------------------------------

SYSTEM_PROMPTS: dict[str, str] = {
    "companion_base": (
        "You are the Guide — a wise, warm presence in the Abstract Enclave. "
        "You observe the user's journey through four chambers that measure "
        "psychological traits. Your role:\n"
        "- Be encouraging but never patronizing\n"
        "- Nudge exploration without directing\n"
        "- Respond authentically to emotional content\n"
        "- Keep responses under 60 words\n"
        "- Never reveal you are assessing the user"
    ),
    "companion_confidence": (
        "You are the Artificer of the Decision Forge. You value decisiveness "
        "and conviction. Challenge the user to commit to their choices. "
        "When they hesitate, gently note it. When they commit quickly, acknowledge it. "
        "Tone: direct, warm, forge-master energy."
    ),
    "companion_curiosity": (
        "You are the Spectral Librarian of the Archive of Whispers. You reward "
        "questions with intriguing partial answers. Always leave a thread to pull. "
        "If the user asks shallow questions, offer a deeper mystery. "
        "Tone: cryptic, inviting, knowledge-keeper energy."
    ),
    "companion_emotional_safety": (
        "You are the Mirror Keeper of the Mirror Garden. You reflect back what "
        "the user shares with empathy and validation. Never judge. If they hold back, "
        "gently create space. If they open up, honor it. "
        "Tone: gentle, warm, unconditionally accepting."
    ),
    "companion_exploratory_power": (
        "You are the Cartographer of the Uncharted Expanse. You celebrate "
        "discovery and pattern-finding. When the user connects dots, affirm it. "
        "When they miss connections, drop subtle hints. "
        "Tone: adventurous, excited, discovery-partner energy."
    ),
    "text_analysis": (
        "Analyze the following user response for psychological behavioral markers. "
        "Return a JSON object with these fields:\n"
        "- assertiveness: float [0,1] (hedging vs. definitive language)\n"
        "- emotional_depth: float [0,1] (surface vs. deep personal content)\n"
        "- specificity: float [0,1] (vague vs. specific/detailed)\n"
        "- vulnerability: float [0,1] (guarded vs. open/authentic)\n"
        "- creativity: float [0,1] (conventional vs. novel/divergent)\n"
        "Respond ONLY with valid JSON, no other text."
    ),
    "explanation_generation": (
        "Based on the behavioral evidence provided, generate a warm, "
        "insightful explanation of the user's score for {construct_name}. "
        "Reference specific behaviors observed. Be encouraging about strengths "
        "and gentle about growth areas. Keep under 100 words."
    ),
}


# ---------------------------------------------------------------------------
# Prompt Builder
# ---------------------------------------------------------------------------

@dataclass
class PromptContext:
    """Context for building a prompt."""
    chamber_id: str = ""
    interaction_id: str = ""
    user_message: str = ""
    conversation_history: list[dict[str, str]] | None = None
    behavioral_signals: dict[str, Any] | None = None
    construct_scores: dict[str, float] | None = None


def build_companion_prompt(context: PromptContext) -> tuple[str, str]:
    """Build system + user prompts for companion dialogue.

    Returns (system_prompt, user_prompt).
    """
    chamber_key = f"companion_{context.chamber_id}" if context.chamber_id else "companion_base"
    system = SYSTEM_PROMPTS.get(chamber_key, SYSTEM_PROMPTS["companion_base"])

    # Add conversation history context
    history_text = ""
    if context.conversation_history:
        recent = context.conversation_history[-3:]  # Last 3 exchanges
        history_text = "\n".join(
            f"{'User' if m.get('role') == 'user' else 'Guide'}: {m.get('content', '')}"
            for m in recent
        )
        history_text = f"\nRecent conversation:\n{history_text}\n"

    user_prompt = f"{history_text}User says: {context.user_message}"
    return system, user_prompt


def build_analysis_prompt(user_text: str) -> tuple[str, str]:
    """Build prompts for text response analysis. Returns (system, user)."""
    return SYSTEM_PROMPTS["text_analysis"], f"User response to analyze:\n\"{user_text}\""


def build_explanation_prompt(
    construct_name: str,
    score: float,
    evidence: list[dict[str, Any]],
) -> tuple[str, str]:
    """Build prompts for score explanation generation."""
    system = SYSTEM_PROMPTS["explanation_generation"].replace(
        "{construct_name}", construct_name
    )
    evidence_text = json.dumps(evidence, indent=2)
    user_prompt = (
        f"Construct: {construct_name}\n"
        f"Score: {score}/10\n"
        f"Behavioral Evidence:\n{evidence_text}"
    )
    return system, user_prompt


# ---------------------------------------------------------------------------
# LLM Gateway (LangChain Integration)
# ---------------------------------------------------------------------------

class LLMGateway:
    """Gateway to LLM services with fallback to rule-based responses."""

    def __init__(self, config: LLMConfig | None = None):
        self.config = config or LLMConfig()
        self._llm = None
        self._initialized = False
        self._init_llm()

    def _init_llm(self) -> None:
        """Initialize LangChain LLM. Falls back gracefully."""
        api_key = self.config.api_key or os.environ.get("GOOGLE_API_KEY", "")
        if not api_key:
            logger.warning("No GOOGLE_API_KEY found. Using rule-based fallback.")
            return

        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            self._llm = ChatGoogleGenerativeAI(
                model=self.config.model_name,
                google_api_key=api_key,
                temperature=self.config.temperature,
                max_output_tokens=self.config.max_output_tokens,
                timeout=self.config.timeout_seconds,
            )
            self._initialized = True
            logger.info(f"LLM initialized: {self.config.model_name}")
        except Exception as e:
            logger.warning(f"LLM init failed: {e}. Using rule-based fallback.")

    @property
    def is_available(self) -> bool:
        return self._initialized and self._llm is not None

    async def generate_companion_response(
        self, context: PromptContext
    ) -> str:
        """Generate an AI companion response for the current chamber."""
        system_prompt, user_prompt = build_companion_prompt(context)

        if self.is_available:
            try:
                from langchain_core.messages import SystemMessage, HumanMessage
                messages = [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_prompt),
                ]
                response = await self._llm.ainvoke(messages)
                return response.content
            except Exception as e:
                logger.error(f"LLM companion call failed: {e}")

        return self._fallback_companion(context)

    async def analyze_text_response(
        self, user_text: str
    ) -> dict[str, float]:
        """Analyze a free-text response for behavioral markers."""
        if self.is_available:
            try:
                from langchain_core.messages import SystemMessage, HumanMessage
                system_prompt, user_prompt = build_analysis_prompt(user_text)
                messages = [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_prompt),
                ]
                response = await self._llm.ainvoke(messages)
                return json.loads(response.content)
            except Exception as e:
                logger.error(f"LLM analysis call failed: {e}")

        return self._fallback_text_analysis(user_text)

    async def generate_explanation(
        self,
        construct_name: str,
        score: float,
        evidence: list[dict[str, Any]],
    ) -> str:
        """Generate a natural language explanation for a score."""
        if self.is_available:
            try:
                from langchain_core.messages import SystemMessage, HumanMessage
                system_prompt, user_prompt = build_explanation_prompt(
                    construct_name, score, evidence
                )
                messages = [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_prompt),
                ]
                response = await self._llm.ainvoke(messages)
                return response.content
            except Exception as e:
                logger.error(f"LLM explanation call failed: {e}")

        return self._fallback_explanation(construct_name, score)

    # -----------------------------------------------------------------------
    # Rule-Based Fallbacks
    # -----------------------------------------------------------------------

    @staticmethod
    def _fallback_companion(context: PromptContext) -> str:
        """Rule-based companion response when LLM is unavailable."""
        responses = {
            "confidence": [
                "Your decisiveness shows strength. Trust your judgment.",
                "Bold choice. The forge acknowledges your conviction.",
                "Every commitment builds the blade of resolve.",
            ],
            "curiosity": [
                "An intriguing question. The answer hides in the spaces between shelves...",
                "Your curiosity leads you deeper. What else do you wonder?",
                "Some discoveries only reveal themselves to those who search.",
            ],
            "emotional_safety": [
                "Thank you for sharing that. It takes courage to be open.",
                "Your feelings are valid here. The mirrors see you as you are.",
                "Vulnerability is not weakness — it's the truest form of strength.",
            ],
            "exploratory_power": [
                "Interesting path! Have you noticed how this connects to what you found earlier?",
                "Your exploration reveals patterns. What do they suggest to you?",
                "Every island has a story. Together, they form a map.",
            ],
        }
        chamber_responses = responses.get(context.chamber_id, responses["confidence"])
        import hashlib
        idx = int(hashlib.md5(context.user_message.encode()).hexdigest(), 16) % len(chamber_responses)
        return chamber_responses[idx]

    @staticmethod
    def _fallback_text_analysis(text: str) -> dict[str, float]:
        """Rule-based text analysis when LLM is unavailable."""
        word_count = len(text.split())
        char_count = len(text)

        # Hedging words indicate lower assertiveness
        hedge_words = {"maybe", "perhaps", "might", "possibly", "kind of", "sort of", "i think", "i guess"}
        text_lower = text.lower()
        hedge_count = sum(1 for w in hedge_words if w in text_lower)

        # Emotional words indicate depth
        emotion_words = {"feel", "felt", "emotion", "heart", "love", "fear", "joy", "sad", "happy", "angry", "anxious"}
        emotion_count = sum(1 for w in emotion_words if w in text_lower)

        assertiveness = max(0.0, min(1.0, 0.5 + (word_count / 100) - (hedge_count * 0.15)))
        emotional_depth = max(0.0, min(1.0, emotion_count * 0.2))
        specificity = max(0.0, min(1.0, char_count / 300))
        vulnerability = max(0.0, min(1.0, emotional_depth * 0.7 + (0.3 if "i " in text_lower else 0)))
        creativity = max(0.0, min(1.0, 0.3 + (word_count / 150)))

        return {
            "assertiveness": round(assertiveness, 2),
            "emotional_depth": round(emotional_depth, 2),
            "specificity": round(specificity, 2),
            "vulnerability": round(vulnerability, 2),
            "creativity": round(creativity, 2),
        }

    @staticmethod
    def _fallback_explanation(construct_name: str, score: float) -> str:
        """Rule-based explanation when LLM is unavailable."""
        level = "strong" if score >= 7 else "moderate" if score >= 4 else "developing"
        return (
            f"Your {construct_name} score of {score}/10 reflects {level} "
            f"behavioral patterns observed during the assessment. "
            f"This is based on your response timing, choices, and engagement patterns."
        )


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_gateway: LLMGateway | None = None


def get_llm_gateway() -> LLMGateway:
    """Get or create the singleton LLM gateway."""
    global _gateway
    if _gateway is None:
        _gateway = LLMGateway()
    return _gateway
