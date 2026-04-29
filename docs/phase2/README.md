# Phase 2 — AI Integration Design & Content Adaptation

## Task 2.1 — LLM Ecosystem and Prompt Architecture

### a. Architecture
LangChain + Google Gemini 2.0 Flash with 3 prompt pipelines: companion dialogue, text analysis, explanation generation. Singleton `LLMGateway` with async methods and rule-based fallbacks.

### b. Math/ML
- Text analysis produces 5D behavioral vector: [assertiveness, emotional_depth, specificity, vulnerability, creativity] ∈ [0,1]⁵
- Fallback heuristics: hedge_word_count, emotion_word_count, word_count normalization

### c. Challenges
1. Free tier rate limits (15 RPM, 1500 RPD) — ~10 calls per session × 150 sessions/day max
2. LLM output non-determinism affects scoring consistency
3. Prompt injection risk from user free-text
4. Latency variance (200ms–2s) affects timed interactions

### d. Mitigations
- Request batching + response caching for repeated patterns
- Temperature=0.3 for analysis (determinism) vs 0.7 for dialogue (variety)
- Input sanitization before LLM calls
- Async non-blocking calls with timeout fallback

### e. Linkage
- Upstream: Task 1.1 construct definitions for prompt context
- Downstream: Task 3.3 event pipeline consumes text analysis scores
- Downstream: Task 2.4 explainability uses explanation generation
- Downstream: Task 5.1 UI displays companion responses

### f–j. See `llm_service.py` for implementation.

---

## Task 2.2 — Adaptive Difficulty and Uncertainty Injection

### a. Architecture
Epsilon-greedy difficulty selector (ε=0.15) with ELO-like ability tracking. Thompson Sampling-inspired uncertainty injection based on estimated ability.

### b. Math/ML
**Ability Update (ELO-like):**
```
expected = 1 / (1 + e^(4(difficulty - ability)))
ability += α × (observed - expected),  α = 0.3
```

**Difficulty Selection:**
- Exploit: difficulty ≈ ability_estimate + N(0, 0.1(1-confidence))
- Explore (prob ε): uniform random ∈ [0.2, 0.9]

**Uncertainty Injection:**
```
P(inject) = 0.25 × (0.5 + ability_estimate)
```
Higher ability → more uncertainty probing.

### c–j. See `adaptive_engine.py`.

---

## Task 2.3 — Real-Time Emotion Detection

### a. Architecture
Client-side TensorFlow.js (face-api.js) → emotion labels → valence-arousal mapping → aggregation → behavioral signals. **No video/images leave the client.**

### b. Math/ML
- **Russell's Circumplex Model**: maps discrete emotions to (valence, arousal) coordinates
- **Emotional Stability**: 1 - min(σ²(valence), 1.0)
- **Emotion Diversity**: H(emotions) / log₂(|emotions|) (normalized Shannon entropy)

### c. Key Challenge: Webcam optional — scoring must degrade gracefully without emotion data.

---

## Task 2.4 — Explainable AI Module

### a. Architecture
SHAP-inspired feature attribution: contribution = indicator_weighted_value × sub_facet_weight. Generates evidence chains, confidence descriptions, strength/growth identification.

### b. Math/ML
```
contribution_i = weighted_value_i × w_subfacet
rank indicators by |contribution_i| descending → top 5 = key evidence
```

### c. Key Challenge: Explanation quality depends on LLM availability; fallback narratives are generic.

---

## Tech Stack (Phase 2)

| Technology | Version | Purpose |
|-----------|---------|---------|
| LangChain Core | ≥0.3.0 | LLM orchestration |
| langchain-google-genai | ≥2.0.0 | Gemini integration |
| Google Gemini 2.0 Flash | - | Free-tier LLM (1500 RPD) |
| TensorFlow.js | ≥4.0 | Client-side emotion detection |
| face-api.js | ≥0.22 | Face detection + expression |
