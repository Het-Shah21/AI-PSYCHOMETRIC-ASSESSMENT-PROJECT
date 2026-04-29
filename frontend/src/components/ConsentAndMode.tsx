"use client";

import { motion } from "framer-motion";
import { useSession } from "@/src/lib/session-context";
import { CHAMBER_INFO, type AssessmentMode, type ChamberID } from "@/src/lib/types";
import { createSession, recordConsent } from "@/src/lib/api";

const MODES: { id: AssessmentMode; label: string; desc: string; icon: string; scoresVisible: boolean }[] = [
  { id: "self-awareness", label: "Self-Awareness", desc: "Explore your behavioral patterns. See your full results.", icon: "🔮", scoresVisible: true },
  { id: "educational", label: "Educational", desc: "Learn about your cognitive and emotional strengths.", icon: "📖", scoresVisible: true },
  { id: "hiring", label: "Hiring", desc: "Assessment for recruitment. Results visible to administrator only.", icon: "💼", scoresVisible: false },
  { id: "therapeutic", label: "Therapeutic", desc: "Clinical assessment. Results shared with your practitioner.", icon: "🌿", scoresVisible: false },
];

export default function ConsentAndMode() {
  const { state, dispatch } = useSession();

  if (state.phase === "consent") {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="flex min-h-screen items-center justify-center p-6"
      >
        <div className="max-w-lg rounded-2xl border border-white/10 bg-black/60 p-8 text-center backdrop-blur-xl">
          <h1 className="mb-2 text-3xl font-bold text-white">The Abstract Enclave</h1>
          <p className="mb-6 text-sm text-white/60">
            AI-Powered Behavioral Assessment
          </p>
          <div className="mb-6 rounded-lg bg-white/5 p-4 text-left text-sm text-white/70">
            <p className="mb-2 font-semibold text-white/90">Before we begin:</p>
            <ul className="list-inside list-disc space-y-1">
              <li>This assessment takes approximately 5 minutes</li>
              <li>Your responses are anonymized and encrypted</li>
              <li>No personal data is stored — only behavioral patterns</li>
              <li>You can exit at any time</li>
              <li>Webcam access is optional and fully client-side</li>
            </ul>
          </div>
          <button
            onClick={() => dispatch({ type: "GIVE_CONSENT" })}
            className="w-full rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 px-8 py-3 font-semibold text-white transition hover:scale-105 hover:shadow-lg hover:shadow-purple-500/20"
          >
            I Understand — Continue
          </button>
        </div>
      </motion.div>
    );
  }

  // Mode Selection
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="flex min-h-screen flex-col items-center justify-center p-6"
    >
      <motion.h2
        initial={{ y: -20 }}
        animate={{ y: 0 }}
        className="mb-2 text-4xl font-bold text-white"
      >
        Choose Your Path
      </motion.h2>
      <p className="mb-8 text-white/50">Select the context for your journey</p>

      <div className="grid max-w-3xl grid-cols-1 gap-4 sm:grid-cols-2">
        {MODES.map((mode, i) => (
          <motion.button
            key={mode.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0, transition: { delay: i * 0.1 } }}
            whileHover={{ scale: 1.03, y: -4 }}
            onClick={async () => {
              dispatch({ type: "SET_MODE", mode: mode.id });
              try {
                const res = await createSession(mode.id);
                dispatch({
                  type: "SET_SESSION",
                  sessionId: res.session_id,
                  chamberOrder: res.chamber_order as ChamberID[],
                });
                await recordConsent(res.session_id, true);
              } catch {
                // Fallback: proceed without backend
                dispatch({
                  type: "SET_SESSION",
                  sessionId: `local-${Date.now()}`,
                  chamberOrder: ["confidence", "curiosity", "emotional_safety", "exploratory_power"],
                });
              }
              dispatch({ type: "SET_PHASE", phase: "onboarding" });
            }}
            className="group rounded-2xl border border-white/10 bg-black/40 p-6 text-left backdrop-blur-lg transition hover:border-white/20 hover:bg-black/50"
          >
            <span className="mb-2 block text-3xl">{mode.icon}</span>
            <span className="block text-lg font-semibold text-white">{mode.label}</span>
            <span className="block text-sm text-white/50">{mode.desc}</span>
            <span className={`mt-3 inline-block rounded-full px-3 py-1 text-xs font-medium ${mode.scoresVisible ? "bg-green-500/20 text-green-400" : "bg-amber-500/20 text-amber-400"}`}>
              {mode.scoresVisible ? "✓ Scores visible to you" : "⚿ Scores visible to admin only"}
            </span>
          </motion.button>
        ))}
      </div>
    </motion.div>
  );
}
