"use client";

import {
  createContext,
  useContext,
  useReducer,
  useCallback,
  type ReactNode,
} from "react";
import type {
  SessionState,
  AssessmentMode,
  SessionPhase,
  ChamberID,
  ConstructScoreResult,
  ExplanationResult,
} from "./types";

// Actions
type Action =
  | { type: "SET_SESSION"; sessionId: string; chamberOrder: ChamberID[] }
  | { type: "SET_MODE"; mode: AssessmentMode }
  | { type: "SET_PHASE"; phase: SessionPhase }
  | { type: "GIVE_CONSENT" }
  | { type: "ADVANCE_CHAMBER" }
  | { type: "SET_SCORES"; scores: Record<string, ConstructScoreResult>; explanations: Record<string, ExplanationResult>; visible: boolean }
  | { type: "RESET" };

const initialState: SessionState = {
  sessionId: "",
  phase: "consent",
  mode: null,
  currentChamberIndex: 0,
  chamberOrder: [],
  elapsedMs: 0,
  isConsentGiven: false,
  scores: null,
  explanations: null,
  scoresVisible: false,
};

function reducer(state: SessionState, action: Action): SessionState {
  switch (action.type) {
    case "SET_SESSION":
      return { ...state, sessionId: action.sessionId, chamberOrder: action.chamberOrder };
    case "SET_MODE":
      return { ...state, mode: action.mode };
    case "SET_PHASE":
      return { ...state, phase: action.phase };
    case "GIVE_CONSENT":
      return { ...state, isConsentGiven: true, phase: "mode_select" };
    case "ADVANCE_CHAMBER":
      return {
        ...state,
        currentChamberIndex: state.currentChamberIndex + 1,
      };
    case "SET_SCORES":
      return {
        ...state,
        scores: action.scores,
        explanations: action.explanations,
        scoresVisible: action.visible,
        phase: "results",
      };
    case "RESET":
      return initialState;
    default:
      return state;
  }
}

const SessionContext = createContext<{
  state: SessionState;
  dispatch: React.Dispatch<Action>;
} | null>(null);

export function SessionProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(reducer, initialState);
  return (
    <SessionContext.Provider value={{ state, dispatch }}>
      {children}
    </SessionContext.Provider>
  );
}

export function useSession() {
  const ctx = useContext(SessionContext);
  if (!ctx) throw new Error("useSession must be used within SessionProvider");
  return ctx;
}
