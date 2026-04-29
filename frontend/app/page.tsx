"use client";

import dynamic from "next/dynamic";
import { useSession } from "@/src/lib/session-context";
import ConsentAndMode from "@/src/components/ConsentAndMode";
import ChamberView from "@/src/components/ChamberView";
import ResultsDashboard from "@/src/components/ResultsDashboard";
import { motion, AnimatePresence } from "framer-motion";

const BackgroundScene = dynamic(
  () => import("@/src/components/BackgroundScene"),
  { ssr: false }
);

function ScoringScreen() {
  const { state, dispatch } = useSession();

  // Simulate scoring delay then show results with demo scores
  if (state.phase === "scoring") {
    setTimeout(() => {
      dispatch({
        type: "SET_SCORES",
        visible: state.mode === "self-awareness" || state.mode === "educational",
        scores: {
          confidence: {
            scaled_score: 7.2,
            confidence_interval: [5.8, 8.6] as [number, number],
            evidence_count: 9,
            sub_facets: [
              { id: "conf_decisiveness", name: "Decisiveness", score: 7.8 },
              { id: "conf_persistence", name: "Persistence", score: 6.5 },
              { id: "conf_self_assurance", name: "Self-Assurance", score: 7.1 },
              { id: "conf_calibration", name: "Calibration", score: 7.4 },
            ],
          },
          curiosity: {
            scaled_score: 8.1,
            confidence_interval: [6.9, 9.3] as [number, number],
            evidence_count: 9,
            sub_facets: [
              { id: "cur_joyous", name: "Joyous Exploration", score: 8.5 },
              { id: "cur_deprivation", name: "Deprivation Sensitivity", score: 7.2 },
              { id: "cur_stress", name: "Stress Tolerance", score: 8.0 },
              { id: "cur_depth", name: "Depth-Seeking", score: 8.7 },
            ],
          },
          emotional_safety: {
            scaled_score: 6.4,
            confidence_interval: [5.0, 7.8] as [number, number],
            evidence_count: 8,
            sub_facets: [
              { id: "es_vulnerability", name: "Vulnerability", score: 5.8 },
              { id: "es_error", name: "Error Comfort", score: 7.0 },
              { id: "es_help", name: "Help-Seeking", score: 6.2 },
              { id: "es_authentic", name: "Authenticity", score: 6.6 },
            ],
          },
          exploratory_power: {
            scaled_score: 7.8,
            confidence_interval: [6.4, 9.2] as [number, number],
            evidence_count: 8,
            sub_facets: [
              { id: "ep_breadth", name: "Breadth", score: 8.2 },
              { id: "ep_depth", name: "Depth", score: 7.0 },
              { id: "ep_hypothesis", name: "Hypothesis", score: 7.9 },
              { id: "ep_synthesis", name: "Synthesis", score: 8.1 },
            ],
          },
        },
        explanations: {
          confidence: {
            narrative: "Your confidence profile reveals strong decisiveness with quick, committed responses. You show healthy self-assurance in expressing beliefs, with well-calibrated metacognition.",
            strengths: ["Strong decisiveness", "Good calibration"],
            growth_areas: ["Persistence under pressure"],
            confidence_description: "Score: 7.2/10 (moderate confidence). Your true score likely falls between 5.8 and 8.6.",
          },
          curiosity: {
            narrative: "You demonstrated exceptional curiosity — actively exploring optional content and asking deep, probing questions. Your depth-seeking behavior stood out.",
            strengths: ["Joyous exploration", "Depth-seeking behavior"],
            growth_areas: [],
            confidence_description: "Score: 8.1/10 (high confidence). Your true score likely falls between 6.9 and 9.3.",
          },
          emotional_safety: {
            narrative: "You showed moderate emotional safety. You engaged thoughtfully with reflective prompts but may benefit from greater openness in vulnerability-requiring situations.",
            strengths: ["Error comfort"],
            growth_areas: ["Vulnerability willingness"],
            confidence_description: "Score: 6.4/10 (moderate confidence). Your true score likely falls between 5.0 and 7.8.",
          },
          exploratory_power: {
            narrative: "Strong exploratory power with broad coverage and meaningful synthesis of discoveries. You connected insights across different areas effectively.",
            strengths: ["Broad exploration", "Information synthesis"],
            growth_areas: ["Deeper per-area analysis"],
            confidence_description: "Score: 7.8/10 (moderate confidence). Your true score likely falls between 6.4 and 9.2.",
          },
        },
      });
    }, 3000);
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="flex min-h-screen flex-col items-center justify-center p-6"
    >
      <div className="text-center">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
          className="mx-auto mb-6 h-16 w-16 rounded-full border-4 border-white/10 border-t-purple-500"
        />
        <h2 className="mb-2 text-2xl font-bold text-white">Analyzing Your Journey</h2>
        <p className="text-white/50">Processing behavioral patterns across all chambers...</p>
      </div>
    </motion.div>
  );
}

function OnboardingScreen() {
  const { dispatch } = useSession();
  const steps = [
    { emoji: "🏛️", title: "The Abstract Enclave", text: "You are about to enter a liminal space between thought and feeling." },
    { emoji: "🔥", title: "Four Chambers Await", text: "Each chamber takes ~60 seconds. Interact naturally — there are no wrong answers." },
    { emoji: "🤖", title: "Your AI Guide", text: "A luminous guide accompanies you. Ask questions anytime." },
    { emoji: "⏱️", title: "5 Minutes Total", text: "Let your instincts guide you. Ready?" },
  ];
  const [step, setStep] = useState(0);

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="flex min-h-screen flex-col items-center justify-center p-6"
    >
      <AnimatePresence mode="wait">
        <motion.div
          key={step}
          initial={{ opacity: 0, x: 40 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -40 }}
          className="max-w-md text-center"
        >
          <span className="mb-4 block text-5xl">{steps[step].emoji}</span>
          <h2 className="mb-2 text-2xl font-bold text-white">{steps[step].title}</h2>
          <p className="mb-8 text-white/60">{steps[step].text}</p>
        </motion.div>
      </AnimatePresence>

      <div className="flex gap-2 mb-6">
        {steps.map((_, i) => (
          <div
            key={i}
            className={`h-1.5 w-8 rounded-full transition-colors ${i <= step ? "bg-purple-500" : "bg-white/15"}`}
          />
        ))}
      </div>

      <button
        onClick={() => {
          if (step < steps.length - 1) {
            setStep(step + 1);
          } else {
            dispatch({ type: "SET_PHASE", phase: "chamber_active" });
          }
        }}
        className="rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 px-8 py-3 font-semibold text-white transition hover:scale-105"
      >
        {step < steps.length - 1 ? "Continue" : "Enter the Enclave"}
      </button>
    </motion.div>
  );
}

import { useState } from "react";

export default function Home() {
  const { state } = useSession();

  return (
    <>
      <BackgroundScene />
      <main className="relative z-10 flex flex-1 flex-col">
        <AnimatePresence mode="wait">
          {(state.phase === "consent" || state.phase === "mode_select") && (
            <motion.div key="consent" exit={{ opacity: 0 }}>
              <ConsentAndMode />
            </motion.div>
          )}

          {state.phase === "onboarding" && (
            <motion.div key="onboarding" exit={{ opacity: 0 }}>
              <OnboardingScreen />
            </motion.div>
          )}

          {(state.phase === "chamber_active" || state.phase === "chamber_transition") && (
            <motion.div key="chamber" exit={{ opacity: 0 }}>
              <ChamberView />
            </motion.div>
          )}

          {state.phase === "scoring" && (
            <motion.div key="scoring" exit={{ opacity: 0 }}>
              <ScoringScreen />
            </motion.div>
          )}

          {state.phase === "results" && (
            <motion.div key="results" exit={{ opacity: 0 }}>
              <ResultsDashboard />
            </motion.div>
          )}
        </AnimatePresence>
      </main>
    </>
  );
}
