"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { useSession } from "@/src/lib/session-context";
import { CHAMBER_INFO, type ChamberID, type ConstructScoreResult, type ExplanationResult } from "@/src/lib/types";

export default function ResultsDashboard() {
  const { state, dispatch } = useSession();

  // If scores not visible (hiring/therapeutic), show confirmation
  if (!state.scoresVisible) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="flex min-h-screen items-center justify-center p-6"
      >
        <div className="max-w-md rounded-2xl border border-white/10 bg-black/60 p-8 text-center backdrop-blur-xl">
          <span className="mb-4 block text-5xl">🔒</span>
          <h2 className="mb-2 text-2xl font-bold text-white">Assessment Complete</h2>
          <p className="mb-6 text-white/60">
            Your results have been securely recorded and are available to your
            {state.mode === "hiring" ? " administrator" : " practitioner"} only.
          </p>
          <div className="rounded-lg bg-white/5 p-4 text-sm text-white/50">
            <p>Session: {state.sessionId.slice(0, 8)}...</p>
            <p>Mode: {state.mode}</p>
            <p>Status: Completed ✓</p>
          </div>
          <button
            onClick={() => dispatch({ type: "RESET" })}
            className="mt-6 rounded-xl bg-white/10 px-6 py-2.5 text-sm text-white/70 transition hover:bg-white/20"
          >
            Return to Start
          </button>
        </div>
      </motion.div>
    );
  }

  const scores = (state.scores || {}) as Record<string, ConstructScoreResult>;
  const explanations = (state.explanations || {}) as Record<string, ExplanationResult>;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="flex min-h-screen flex-col items-center justify-center p-6"
    >
      <h2 className="mb-2 text-3xl font-bold text-white">Your Assessment Profile</h2>
      <p className="mb-8 text-white/50">Based on behavioral patterns observed during your journey</p>

      <div className="grid w-full max-w-4xl grid-cols-1 gap-6 md:grid-cols-2">
        {Object.entries(scores).map(([cid, score]: [string, ConstructScoreResult]) => {
          const chamber = CHAMBER_INFO[cid as ChamberID];
          const explanation = explanations[cid];
          if (!chamber) return null;

          return (
            <motion.div
              key={cid}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="rounded-2xl border border-white/10 bg-black/50 p-6 backdrop-blur-xl"
            >
              <div className="mb-4 flex items-center gap-3">
                <span className="text-2xl">{chamber.emoji}</span>
                <div>
                  <h3 className="font-semibold text-white">{chamber.name.replace("The ", "")}</h3>
                  <p className="text-xs text-white/40">{cid.replace(/_/g, " ")}</p>
                </div>
              </div>

              {/* Score display */}
              <div className="mb-4 flex items-end gap-2">
                <span className="text-5xl font-bold text-white">{score.scaled_score}</span>
                <span className="mb-1 text-lg text-white/40">/10</span>
              </div>

              {/* Score bar */}
              <div className="mb-2 h-2.5 w-full overflow-hidden rounded-full bg-white/10">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${(score.scaled_score / 10) * 100}%` }}
                  transition={{ duration: 1, ease: "easeOut" }}
                  className="h-full rounded-full"
                  style={{ backgroundColor: chamber.color }}
                />
              </div>

              {/* Confidence interval */}
              <p className="mb-4 text-xs text-white/30">
                95% CI: [{score.confidence_interval[0]} – {score.confidence_interval[1]}]
                · {score.evidence_count} signals
              </p>

              {/* Sub-facets */}
              {score.sub_facets.length > 0 && (
                <div className="mb-4 space-y-2">
                  {score.sub_facets.map((sf) => (
                    <div key={sf.id} className="flex items-center justify-between text-sm">
                      <span className="text-white/60">{sf.name}</span>
                      <div className="flex items-center gap-2">
                        <div className="h-1.5 w-16 overflow-hidden rounded-full bg-white/10">
                          <div
                            className="h-full rounded-full"
                            style={{ width: `${(sf.score / 10) * 100}%`, backgroundColor: chamber.color }}
                          />
                        </div>
                        <span className="w-8 text-right text-xs text-white/50">{sf.score}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Explanation */}
              {explanation && (
                <div className="rounded-lg bg-white/5 p-3 text-sm text-white/60">
                  <p>{explanation.narrative}</p>
                  {explanation.strengths.length > 0 && (
                    <p className="mt-2 text-green-400/70">
                      ✦ {explanation.strengths.join(" · ")}
                    </p>
                  )}
                  {explanation.growth_areas.length > 0 && (
                    <p className="mt-1 text-amber-400/70">
                      ◇ {explanation.growth_areas.join(" · ")}
                    </p>
                  )}
                </div>
              )}
            </motion.div>
          );
        })}
      </div>

      <button
        onClick={() => dispatch({ type: "RESET" })}
        className="mt-8 rounded-xl bg-white/10 px-8 py-3 text-white/70 transition hover:bg-white/20"
      >
        Start New Assessment
      </button>
    </motion.div>
  );
}
