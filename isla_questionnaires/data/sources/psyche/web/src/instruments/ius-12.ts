import type { Instrument } from "./types";
import { registerInstrument } from "./registry";
import { scoreLikert } from "../scoring/engine";

/**
 * Intolerance of Uncertainty Scale — Short Form (IUS-12)
 * 12-item measure of reactions to uncertainty.
 * Source: Carleton, Norton, & Asmundson (2007).
 *
 * Two subscales:
 * - Prospective anxiety (7 items): cognitive reactions to uncertainty about the future
 * - Inhibitory anxiety (5 items): behavioral paralysis under uncertainty
 *
 * All items are forward-scored (higher = more intolerance of uncertainty).
 */

interface IUSItem {
  text: string;
  scale: "prospective" | "inhibitory";
}

const ITEMS: IUSItem[] = [
  // Prospective anxiety (7 items)
  { text: "Unforeseen events upset me greatly.", scale: "prospective" },
  { text: "It frustrates me not having all the information I need.", scale: "prospective" },
  { text: "Uncertainty keeps me from living a full life.", scale: "prospective" },
  { text: "One should always look ahead so as to avoid surprises.", scale: "prospective" },
  { text: "A small unforeseen event can spoil everything, even with the best of planning.", scale: "prospective" },
  { text: "When it's time to act, uncertainty paralyses me.", scale: "prospective" },
  { text: "I always want to know what the future has in store for me.", scale: "prospective" },

  // Inhibitory anxiety (5 items)
  { text: "I can't stand being taken by surprise.", scale: "inhibitory" },
  { text: "The smallest doubt can stop me from acting.", scale: "inhibitory" },
  { text: "I should be able to organize everything in advance.", scale: "inhibitory" },
  { text: "I must get away from all uncertain situations.", scale: "inhibitory" },
  { text: "Uncertainty keeps me from sleeping soundly.", scale: "inhibitory" },
];

const ius12: Instrument = {
  id: "ius-12",
  name: "Intolerance of Uncertainty Scale (Short Form)",
  shortName: "IUS-12",
  description:
    "Measures difficulty tolerating ambiguity and the unknown. Two subscales: Prospective anxiety (worry about future uncertainty) and Inhibitory anxiety (behavioral paralysis under uncertainty).",
  citation:
    "Carleton, R. N., Norton, M. A., & Asmundson, G. J. (2007). Fearing the unknown: A short version of the Intolerance of Uncertainty Scale. Journal of Anxiety Disorders, 21, 105-117.",
  itemCount: 12,
  estimatedMinutes: 2,
  scales: [
    { id: "prospective", name: "Prospective Anxiety", description: "Cognitive apprehension about future uncertainty" },
    { id: "inhibitory", name: "Inhibitory Anxiety", description: "Behavioral paralysis due to uncertainty" },
  ],
  items: ITEMS.map((item, idx) => ({
    id: `ius-${idx + 1}`,
    text: item.text,
    response: {
      type: "likert" as const,
      min: 1,
      max: 5,
      labels: [
        "Not at All Characteristic of Me",
        "A Little Characteristic of Me",
        "Somewhat Characteristic of Me",
        "Very Characteristic of Me",
        "Entirely Characteristic of Me",
      ],
    },
    scaleId: item.scale,
    reversed: false,
  })),
};

registerInstrument(ius12, scoreLikert);

export default ius12;
