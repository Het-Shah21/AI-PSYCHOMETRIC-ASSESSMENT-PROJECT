// ===== Assessment Types =====

export type AssessmentMode = "self-awareness" | "hiring" | "educational" | "therapeutic";

export type ChamberID = "confidence" | "curiosity" | "emotional_safety" | "exploratory_power";

export type SessionPhase =
  | "consent"
  | "mode_select"
  | "onboarding"
  | "chamber_active"
  | "chamber_transition"
  | "scoring"
  | "results"
  | "completed";

export interface SessionState {
  sessionId: string;
  phase: SessionPhase;
  mode: AssessmentMode | null;
  currentChamberIndex: number;
  chamberOrder: ChamberID[];
  elapsedMs: number;
  isConsentGiven: boolean;
  scores: Record<string, ConstructScoreResult> | null;
  explanations: Record<string, ExplanationResult> | null;
  scoresVisible: boolean;
}

export interface ConstructScoreResult {
  scaled_score: number;
  confidence_interval: [number, number];
  evidence_count: number;
  sub_facets: SubFacetResult[];
}

export interface SubFacetResult {
  id: string;
  name: string;
  score: number;
}

export interface ExplanationResult {
  narrative: string;
  strengths: string[];
  growth_areas: string[];
  confidence_description: string;
}

export interface InteractionDef {
  id: string;
  type: string;
  prompt: string;
  options?: string[];
  timeBudgetMs: number;
  hiddenElements?: string[];
  minResponseLength?: number;
}

export interface NarrativeBeat {
  text: string;
  speaker: string;
  duration_ms: number;
}

export interface ChamberInfo {
  id: ChamberID;
  name: string;
  theme: string;
  color: string;
  emoji: string;
}

export const CHAMBER_INFO: Record<ChamberID, ChamberInfo> = {
  confidence: {
    id: "confidence",
    name: "The Decision Forge",
    theme: "forge",
    color: "#ff6b35",
    emoji: "🔥",
  },
  curiosity: {
    id: "curiosity",
    name: "The Archive of Whispers",
    theme: "archive",
    color: "#7b2ff7",
    emoji: "📚",
  },
  emotional_safety: {
    id: "emotional_safety",
    name: "The Mirror Garden",
    theme: "mirror",
    color: "#06d6a0",
    emoji: "🪞",
  },
  exploratory_power: {
    id: "exploratory_power",
    name: "The Uncharted Expanse",
    theme: "expanse",
    color: "#118ab2",
    emoji: "🗺️",
  },
};
