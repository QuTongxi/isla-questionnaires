import type { Instrument } from "./types";
import { registerInstrument } from "./registry";
import { scoreLikert } from "../scoring/engine";

/**
 * Moral Foundations Questionnaire 2 (MFQ-2)
 * 36-item measure of six moral foundations.
 * Source: Atari, Haidt, Graham, et al. (2023).
 *
 * Six foundations (6 items each):
 * - Care: sensitivity to suffering and cruelty
 * - Equality: fairness as equal treatment
 * - Proportionality: fairness as proportional outcomes
 * - Loyalty: commitment to one's group
 * - Authority: respect for hierarchy and tradition
 * - Purity: concerns about sanctity and contamination
 *
 * All items forward-scored (higher = stronger endorsement of that foundation).
 */

interface MFQItem {
  text: string;
  scale: "care" | "equality" | "proportionality" | "loyalty" | "authority" | "purity";
}

const ITEMS: MFQItem[] = [
  // Care (6 items)
  { text: "Compassion for those who are suffering is the most crucial virtue.", scale: "care" },
  { text: "One of the worst things a person could do is hurt a defenseless animal.", scale: "care" },
  { text: "It can never be right to kill a human being.", scale: "care" },
  { text: "I am empathetic toward those people who have suffered in their lives.", scale: "care" },
  { text: "I believe that the government should do more to help the needy.", scale: "care" },
  { text: "I think caring for people who are weak or vulnerable is an important virtue.", scale: "care" },

  // Equality (6 items)
  { text: "When the government makes laws, the number one principle should be ensuring that everyone is treated fairly.", scale: "equality" },
  { text: "Justice is the most important requirement for a society.", scale: "equality" },
  { text: "I think it's morally wrong that rich children inherit a lot of money while poor children inherit nothing.", scale: "equality" },
  { text: "Everyone should have an equal say in decisions that affect their lives.", scale: "equality" },
  { text: "Discrimination against anyone on the basis of race, gender, or sexual orientation is morally wrong.", scale: "equality" },
  { text: "It is unfair that some people have so much more money than others.", scale: "equality" },

  // Proportionality (6 items)
  { text: "People who work hard deserve to earn more than those who do not.", scale: "proportionality" },
  { text: "The effort a worker puts into a job ought to be reflected in the size of a raise they receive.", scale: "proportionality" },
  { text: "Employees who produce more should be paid more.", scale: "proportionality" },
  { text: "In a fair society, those who work hard should live better lives.", scale: "proportionality" },
  { text: "I believe that merit should determine one's success, not family connections.", scale: "proportionality" },
  { text: "People who contribute more to society should receive more in return.", scale: "proportionality" },

  // Loyalty (6 items)
  { text: "I am proud of my country's history.", scale: "loyalty" },
  { text: "It is more important to be a team player than to express oneself.", scale: "loyalty" },
  { text: "I would never betray a friend, even if I would get rewarded for doing so.", scale: "loyalty" },
  { text: "People should be loyal to their family members, even when they have done something wrong.", scale: "loyalty" },
  { text: "It is important for members of a group to stick together, even when they disagree.", scale: "loyalty" },
  { text: "A group is only strong when its members are unified.", scale: "loyalty" },

  // Authority (6 items)
  { text: "Respect for authority is something all children need to learn.", scale: "authority" },
  { text: "I believe that one of the problems with today's youth is that they don't respect their elders enough.", scale: "authority" },
  { text: "Men and women each have different roles to play in society.", scale: "authority" },
  { text: "If I were a soldier and disagreed with my commanding officer's orders, I would obey anyway because that is my duty.", scale: "authority" },
  { text: "I think the world would be a better place if people showed more respect for tradition.", scale: "authority" },
  { text: "Respect for authority and leadership is an important virtue for children to learn.", scale: "authority" },

  // Purity (6 items)
  { text: "People should not do things that are disgusting, even if no one is harmed.", scale: "purity" },
  { text: "I would call some acts wrong on the grounds that they are unnatural.", scale: "purity" },
  { text: "Chastity is an important and valuable virtue.", scale: "purity" },
  { text: "I think certain acts are wrong even if they do not hurt anyone.", scale: "purity" },
  { text: "When you defile a place of worship, you are doing harm to all who hold it sacred.", scale: "purity" },
  { text: "It is important to maintain one's purity, both in mind and in body.", scale: "purity" },
];

const mfq2: Instrument = {
  id: "mfq-2",
  name: "Moral Foundations Questionnaire 2",
  shortName: "MFQ-2",
  description:
    "Measures endorsement of six moral foundations: Care, Equality, Proportionality, Loyalty, Authority, and Purity. Updated from the original MFQ-30 with improved psychometric properties and the Equality/Proportionality distinction.",
  citation:
    "Atari, M., Haidt, J., Graham, J., Koleva, S., Stevens, S. T., & Dehghani, M. (2023). Morality beyond the WEIRD: How the nomological network of morality varies across cultures. Journal of Personality and Social Psychology, 125(5), 1157-1188.",
  itemCount: 36,
  estimatedMinutes: 7,
  scales: [
    { id: "care", name: "Care", description: "Sensitivity to suffering, cruelty, and harm" },
    { id: "equality", name: "Equality", description: "Fairness as equal treatment and equal outcomes" },
    { id: "proportionality", name: "Proportionality", description: "Fairness as proportional to effort and merit" },
    { id: "loyalty", name: "Loyalty", description: "Commitment to one's group and willingness to sacrifice" },
    { id: "authority", name: "Authority", description: "Respect for hierarchy, tradition, and social order" },
    { id: "purity", name: "Purity", description: "Concerns about sanctity, contamination, and degradation" },
  ],
  items: ITEMS.map((item, idx) => ({
    id: `mfq-${idx + 1}`,
    text: item.text,
    response: {
      type: "likert" as const,
      min: 1,
      max: 5,
      labels: [
        "Strongly Disagree",
        "Disagree",
        "Neither Agree nor Disagree",
        "Agree",
        "Strongly Agree",
      ],
    },
    scaleId: item.scale,
    reversed: false,
  })),
};

registerInstrument(mfq2, scoreLikert);

export default mfq2;
