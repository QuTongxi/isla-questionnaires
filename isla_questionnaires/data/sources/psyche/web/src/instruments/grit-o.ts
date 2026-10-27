import type { Instrument } from "./types";
import { registerInstrument } from "./registry";
import { scoreLikert } from "../scoring/engine";

/**
 * Original Grit Scale (Grit-O)
 * 12-item measure of grit: Perseverance of Effort + Consistency of Interest + Overall composite.
 * Source: Duckworth, Peterson, Matthews, & Kelly (2007) — public domain via Duckworth Lab.
 * Extends Grit-S (8 items) with 4 additional items (2 per subscale).
 */

interface GritItem {
  text: string;
  scale: "perseverance" | "interest_consistency";
  reversed: boolean;
}

const ITEMS: GritItem[] = [
  // Consistency of Interest (6 items) — all reverse-scored
  { text: "I often set a goal but later choose to pursue a different one.", scale: "interest_consistency", reversed: true },
  { text: "New ideas and projects sometimes distract me from previous ones.", scale: "interest_consistency", reversed: true },
  { text: "I become interested in new pursuits every few months.", scale: "interest_consistency", reversed: true },
  { text: "My interests change from year to year.", scale: "interest_consistency", reversed: true },
  { text: "I have been obsessed with a certain idea or project for a short time but later lost interest.", scale: "interest_consistency", reversed: true },
  { text: "I have difficulty maintaining my focus on projects that take more than a few months to complete.", scale: "interest_consistency", reversed: true },

  // Perseverance of Effort (6 items) — all forward-scored
  { text: "I have achieved a goal that took years of work.", scale: "perseverance", reversed: false },
  { text: "I have overcome setbacks to conquer an important challenge.", scale: "perseverance", reversed: false },
  { text: "I finish whatever I begin.", scale: "perseverance", reversed: false },
  { text: "Setbacks don't discourage me.", scale: "perseverance", reversed: false },
  { text: "I am a hard worker.", scale: "perseverance", reversed: false },
  { text: "I am diligent.", scale: "perseverance", reversed: false },
];

const gritO: Instrument = {
  id: "grit-o",
  name: "Original Grit Scale (Grit-O)",
  shortName: "Grit (Full)",
  description:
    "Full 12-item grit scale measuring sustained passion and perseverance for long-term goals. Three scores: Perseverance of Effort, Consistency of Interest, and Overall Grit composite.",
  citation:
    "Duckworth, A. L., Peterson, C., Matthews, M. D., & Kelly, D. R. (2007). Grit: Perseverance and passion for long-term goals. Journal of Personality and Social Psychology, 92(6), 1087-1101.",
  itemCount: 12,
  estimatedMinutes: 2,
  scales: [
    { id: "perseverance", name: "Perseverance of Effort", description: "Tendency to work hard and finish what you start" },
    { id: "interest_consistency", name: "Consistency of Interest", description: "Tendency to maintain focus on the same goals over time" },
    { id: "overall", name: "Overall Grit", description: "Composite of perseverance and interest consistency" },
  ],
  items: ITEMS.map((item, idx) => ({
    id: `grit-o-${idx + 1}`,
    text: item.text,
    response: {
      type: "likert" as const,
      min: 1,
      max: 5,
      labels: ["Not at all like me", "Not much like me", "Somewhat like me", "Mostly like me", "Very much like me"],
    },
    scaleId: item.scale,
    reversed: item.reversed,
  })),
};

registerInstrument(gritO, (instrument, session) => {
  const subscaleResult = scoreLikert(instrument, session);

  // Compute overall composite as mean of the two subscales
  const perseverance = subscaleResult.scores.find((s) => s.scaleId === "perseverance");
  const interest = subscaleResult.scores.find((s) => s.scaleId === "interest_consistency");
  const overallNorm = perseverance && interest
    ? (perseverance.normalized + interest.normalized) / 2
    : (perseverance?.normalized ?? interest?.normalized ?? 0);
  const overallRaw = perseverance && interest
    ? (perseverance.raw + interest.raw) / 2
    : (perseverance?.raw ?? interest?.raw ?? 0);

  return {
    instrumentId: instrument.id,
    completedAt: session.completedAt ?? Date.now(),
    scores: [
      ...subscaleResult.scores,
      {
        scaleId: "overall",
        scaleName: "Overall Grit",
        raw: overallRaw,
        normalized: overallNorm,
        itemCount: (perseverance?.itemCount ?? 0) + (interest?.itemCount ?? 0),
      },
    ],
  };
});

export default gritO;
