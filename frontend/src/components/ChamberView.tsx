"use client";

import { useState, useCallback, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useSession } from "@/src/lib/session-context";
import { CHAMBER_INFO, type ChamberID } from "@/src/lib/types";

// Interaction data keyed by chamber
const INTERACTIONS: Record<ChamberID, { id: string; type: string; prompt: string; options?: string[]; timeBudgetMs: number }[]> = {
  confidence: [
    { id: "conf-1", type: "timed", prompt: "Two paths diverge. One well-lit and familiar. The other descends into shadow, but a faint melody echoes. You have 8 seconds.", options: ["Take the well-lit path", "Descend into the shadow"], timeBudgetMs: 8000 },
    { id: "conf-2", type: "text", prompt: "The Artificer challenges you: 'Defend a belief you hold that others might disagree with. Speak with conviction.'", timeBudgetMs: 25000 },
    { id: "conf-3", type: "choice", prompt: "Identify the true rune sequence. Commit — you cannot change your answer.", options: ["◆▲●◆▲●", "◆●▲◆●▲", "▲◆●▲◆●"], timeBudgetMs: 15000 },
  ],
  curiosity: [
    { id: "cur-1", type: "explore", prompt: "A vast chamber with 6 alcoves. Each contains a different artifact. You have 20 seconds. Explore freely.", timeBudgetMs: 20000 },
    { id: "cur-2", type: "text", prompt: "A spectral librarian appears: 'I have the answer to a question you haven't asked yet.' What would you like to know?", timeBudgetMs: 20000 },
    { id: "cur-3", type: "choice", prompt: "A half-torn page reveals partial information about a hidden treasure. What do you do?", options: ["Search for missing half", "Proceed with partial info", "Ask the librarian", "Ignore and move on"], timeBudgetMs: 12000 },
  ],
  emotional_safety: [
    { id: "es-1", type: "text", prompt: "The mirror shows a moment where you felt truly understood. Describe it — or what it would look like.", timeBudgetMs: 25000 },
    { id: "es-2", type: "choice", prompt: "You solved the last puzzle incorrectly. The guide says: 'That wasn't right, but it showed creative thinking.' How do you feel?", options: ["I'd like to try again differently", "I'd rather move forward"], timeBudgetMs: 10000 },
    { id: "es-3", type: "slider", prompt: "How comfortable are you asking for help when stuck?", timeBudgetMs: 8000 },
  ],
  exploratory_power: [
    { id: "ep-1", type: "explore", prompt: "8 floating islands. Each reveals a clue about a central mystery. Explore strategically.", timeBudgetMs: 25000 },
    { id: "ep-2", type: "text", prompt: "Based on your exploration, what do you think the central mystery is? Form a hypothesis.", timeBudgetMs: 20000 },
    { id: "ep-3", type: "choice", prompt: "New information contradicts your earlier discovery. How do you proceed?", options: ["Revisit with new perspective", "Integrate both pieces", "Discard contradictory info", "Ask for help"], timeBudgetMs: 12000 },
  ],
};

export default function ChamberView() {
  const { state, dispatch } = useSession();
  const [interactionIdx, setInteractionIdx] = useState(0);
  const [showEntry, setShowEntry] = useState(true);
  const [textValue, setTextValue] = useState("");
  const [sliderValue, setSliderValue] = useState(50);
  const [selectedOption, setSelectedOption] = useState<number | null>(null);
  const [timeLeft, setTimeLeft] = useState(0);
  const [exploredAreas, setExploredAreas] = useState<Set<number>>(new Set());
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  const chamberId = state.chamberOrder[state.currentChamberIndex] as ChamberID;
  const chamber = CHAMBER_INFO[chamberId];
  const interactions = INTERACTIONS[chamberId] || [];
  const current = interactions[interactionIdx];

  // Timer for timed interactions
  useEffect(() => {
    if (!current || showEntry) return;
    setTimeLeft(current.timeBudgetMs);
    timerRef.current = setInterval(() => {
      setTimeLeft((t) => {
        if (t <= 100) {
          handleSubmit();
          return 0;
        }
        return t - 100;
      });
    }, 100);
    return () => { if (timerRef.current) clearInterval(timerRef.current); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [interactionIdx, showEntry]);

  // Entry animation
  useEffect(() => {
    setShowEntry(true);
    const t = setTimeout(() => setShowEntry(false), 3000);
    return () => clearTimeout(t);
  }, [state.currentChamberIndex]);

  const handleSubmit = useCallback(() => {
    if (timerRef.current) clearInterval(timerRef.current);
    setSelectedOption(null);
    setTextValue("");
    setSliderValue(50);
    setExploredAreas(new Set());

    if (interactionIdx >= interactions.length - 1) {
      // Chamber complete
      if (state.currentChamberIndex >= state.chamberOrder.length - 1) {
        dispatch({ type: "SET_PHASE", phase: "scoring" });
      } else {
        dispatch({ type: "ADVANCE_CHAMBER" });
        setInteractionIdx(0);
      }
    } else {
      setInteractionIdx((i) => i + 1);
    }
  }, [interactionIdx, interactions.length, state, dispatch]);

  if (!chamber || !current) return null;

  return (
    <div className="flex min-h-screen flex-col items-center justify-center p-6">
      {/* Chamber Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-4 text-center"
      >
        <span className="text-3xl">{chamber.emoji}</span>
        <h2 className="text-2xl font-bold text-white">{chamber.name}</h2>
        <div className="mt-2 flex items-center gap-2">
          {interactions.map((_, i) => (
            <div
              key={i}
              className="h-1.5 w-8 rounded-full transition-colors"
              style={{ backgroundColor: i <= interactionIdx ? chamber.color : "rgba(255,255,255,0.15)" }}
            />
          ))}
        </div>
      </motion.div>

      {/* Entry Narrative */}
      <AnimatePresence>
        {showEntry && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 z-50 flex items-center justify-center bg-black/80"
          >
            <motion.p
              initial={{ scale: 0.9 }}
              animate={{ scale: 1 }}
              className="max-w-md text-center text-xl text-white/90"
            >
              {chamber.name === "The Decision Forge" && "Heat washes over you. An ancient forge pulses with molten light..."}
              {chamber.name === "The Archive of Whispers" && "Infinite shelves stretch in every direction. Knowledge hides in unexpected places..."}
              {chamber.name === "The Mirror Garden" && "Mirrors surround you. They reflect feelings, not faces — colors pulse with your emotions..."}
              {chamber.name === "The Uncharted Expanse" && "An endless landscape unfolds. Islands of knowledge float in a sea of fog..."}
            </motion.p>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Interaction Card */}
      {!showEntry && (
        <motion.div
          key={current.id}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="w-full max-w-xl rounded-2xl border border-white/10 bg-black/50 p-6 backdrop-blur-xl"
        >
          {/* Timer bar */}
          <div className="mb-4 h-1 w-full overflow-hidden rounded-full bg-white/10">
            <motion.div
              className="h-full rounded-full"
              style={{ backgroundColor: chamber.color, width: `${(timeLeft / current.timeBudgetMs) * 100}%` }}
            />
          </div>

          <p className="mb-6 text-lg text-white/90">{current.prompt}</p>

          {/* Choice interaction */}
          {(current.type === "choice" || current.type === "timed") && current.options && (
            <div className="space-y-3">
              {current.options.map((opt, i) => (
                <button
                  key={i}
                  onClick={() => { setSelectedOption(i); setTimeout(handleSubmit, 300); }}
                  className="w-full rounded-xl border border-white/10 bg-white/5 p-4 text-left text-white/80 transition hover:border-white/30 hover:bg-white/10"
                  style={selectedOption === i ? { borderColor: chamber.color, backgroundColor: `${chamber.color}20` } : {}}
                >
                  {opt}
                </button>
              ))}
            </div>
          )}

          {/* Text interaction */}
          {current.type === "text" && (
            <div>
              <textarea
                value={textValue}
                onChange={(e) => setTextValue(e.target.value)}
                placeholder="Type your response..."
                className="w-full rounded-xl border border-white/10 bg-white/5 p-4 text-white/90 placeholder-white/30 focus:border-white/30 focus:outline-none"
                rows={4}
              />
              <button
                onClick={handleSubmit}
                disabled={textValue.length < 10}
                className="mt-3 w-full rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 py-3 font-semibold text-white transition hover:scale-[1.02] disabled:opacity-40"
              >
                Submit
              </button>
            </div>
          )}

          {/* Slider interaction */}
          {current.type === "slider" && (
            <div>
              <input
                type="range"
                min={0}
                max={100}
                value={sliderValue}
                onChange={(e) => setSliderValue(Number(e.target.value))}
                className="w-full accent-purple-500"
              />
              <div className="mt-2 flex justify-between text-xs text-white/40">
                <span>Not at all</span>
                <span className="text-lg text-white/80">{sliderValue}%</span>
                <span>Completely</span>
              </div>
              <button onClick={handleSubmit} className="mt-4 w-full rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 py-3 font-semibold text-white transition hover:scale-[1.02]">
                Confirm
              </button>
            </div>
          )}

          {/* Exploration interaction */}
          {current.type === "explore" && (
            <div>
              <div className="grid grid-cols-3 gap-3">
                {Array.from({ length: current.id.startsWith("ep") ? 8 : 6 }, (_, i) => (
                  <button
                    key={i}
                    onClick={() => setExploredAreas((prev) => new Set(prev).add(i))}
                    className="aspect-square rounded-xl border border-white/10 bg-white/5 text-2xl transition hover:scale-105 hover:bg-white/10"
                    style={exploredAreas.has(i) ? { borderColor: chamber.color, backgroundColor: `${chamber.color}20` } : {}}
                  >
                    {exploredAreas.has(i) ? "✨" : `${i + 1}`}
                  </button>
                ))}
              </div>
              <p className="mt-3 text-center text-sm text-white/40">
                {exploredAreas.size} areas explored
              </p>
              <button onClick={handleSubmit} className="mt-3 w-full rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 py-3 font-semibold text-white transition hover:scale-[1.02]">
                Continue
              </button>
            </div>
          )}
        </motion.div>
      )}
    </div>
  );
}
