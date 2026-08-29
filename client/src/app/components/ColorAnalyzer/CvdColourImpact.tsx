"use client";

import { ArrowRight, Info } from "lucide-react";
import { SANS, SERIF } from "@/app/components/typography";
import type { ColorEntry, ColorResult } from "./CvdTab";

export const CVD_LABELS: Record<string, string> = {
  protanopia: "Protanopia — red-blind",
  deuteranopia: "Deuteranopia — green-blind",
  tritanopia: "Tritanopia — blue-blind",
};

const CATEGORY_LABELS: Record<string, string> = {
  single: "single colour",
  dual: "two-tone",
  multi: "multi-colour",
};

type CvdInfoEntry = {
  label: string;
  simpleReason: string;
  confusions: string;
};

const CVD_INFO: Record<string, CvdInfoEntry> = {
  protanopia: {
    label: "protanopia",
    simpleReason:
      "The eye is missing the cells that sense red light. Without them, reds don't look bright anymore — they turn dull and shift toward olive, brown, or dark yellow.",
    confusions: "Reds can be mistaken for black, dark brown, or dark green.",
  },
  deuteranopia: {
    label: "deuteranopia",
    simpleReason:
      "The eye is missing the cells that sense green light. Greens turn pale and shift toward beige or tan, and reds flatten out toward brown too.",
    confusions: "Red and green are often mixed up with each other, and both can look brown.",
  },
  tritanopia: {
    label: "tritanopia",
    simpleReason:
      "The eye is missing the cells that sense blue light. Blues shift toward green or grey, and yellows can end up looking pale pink or light grey.",
    confusions: "Blue and green get confused, and so do yellow and pink/violet.",
  },
};

function rgbToCss(rgb: number[] | undefined): string {
  return Array.isArray(rgb) && rgb.length === 3
    ? `rgb(${rgb[0]}, ${rgb[1]}, ${rgb[2]})`
    : "#cfc8d8";
}

function rgbDistance(a: number[], b: number[]): number {
  return Math.sqrt(
    (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2
  );
}

function shiftPhrase(distance: number): string {
  if (distance < 20) return "looks about the same as";
  if (distance < 70) return "shifts noticeably toward";
  return "changes completely, and now looks like";
}

interface Transition {
  originalName: string;
  originalRgb: number[];
  originalPct: number;
  matchedName: string;
  matchedRgb: number[];
  matchedPct: number;
  distance: number;
}

/** For every original main colour, find its nearest colour in the
 * post-CVD breakdown. Straight nearest-neighbour match in RGB space —
 * nothing here is estimated or guessed. */
function buildTransitions(original: ColorEntry[], transformed: ColorEntry[]): Transition[] {
  if (transformed.length === 0) return [];
  return original.map((o) => {
    let best = transformed[0];
    let bestDist = Infinity;
    for (const t of transformed) {
      const d = rgbDistance(o.rgb, t.rgb);
      if (d < bestDist) {
        bestDist = d;
        best = t;
      }
    }
    return {
      originalName: o.name,
      originalRgb: o.rgb,
      originalPct: o.percentage,
      matchedName: best.name,
      matchedRgb: best.rgb,
      matchedPct: best.percentage,
      distance: bestDist,
    };
  });
}

function buildNarrative(
  original: ColorResult,
  transformed: ColorResult,
  cvdType: string
): { paragraphs: string[]; transitions: Transition[]; whyItHappens: string[] } {
  const info = CVD_INFO[cvdType];
  const origMain = (original.colors || []).filter((c) => !c.is_sub_color);
  const transMain = (transformed.colors || []).filter((c) => !c.is_sub_color);
  const transitions = buildTransitions(origMain, transformed.colors || []);

  const paragraphs: string[] = [];

  // 1. Simple intro — what colours are in the garment.
  const origCategory = CATEGORY_LABELS[original.color_type || ""] || "garment";
  const lead = origMain[0];
  if (lead) {
    const others = origMain.slice(1, 3).map((c) => c.name);
    const colourList =
      others.length > 0 ? `${lead.name}, along with ${others.join(" and ")}` : lead.name;
    paragraphs.push(
      `This is a ${origCategory} garment, mainly ${colourList}. To someone with ${
        info?.label || cvdType
      }, those colours don't look the way they do to most people.`
    );
  }

  // 2. Colours that become impossible to tell apart.
  const groups = new Map<string, Transition[]>();
  for (const t of transitions) {
    const arr = groups.get(t.matchedName) || [];
    arr.push(t);
    groups.set(t.matchedName, arr);
  }

  const confused = [...groups.values()].filter((g) => g.length > 1);
  for (const g of confused) {
    const names = g.map((t) => t.originalName);
    const joined =
      names.length === 2
        ? names.join(" and ")
        : `${names.slice(0, -1).join(", ")}, and ${names[names.length - 1]}`;
    paragraphs.push(
      `${joined} end up looking the same — both read as ${g[0].matchedName} to this viewer, even though they're clearly different colours in the original photo.`
    );
  }

  // 3. Individually-tracked shifts for anything not already covered above.
  const confusedNames = new Set(confused.flatMap((g) => g.map((t) => t.originalName)));
  for (const t of transitions) {
    if (confusedNames.has(t.originalName)) continue;
    if (t.originalPct < 3) continue;
    paragraphs.push(
      `${t.originalName} ${shiftPhrase(t.distance)} ${t.matchedName}.`
    );
  }

  // 4. Category-level shift — the single most useful takeaway.
  if (original.color_type && transformed.color_type && original.color_type !== transformed.color_type) {
    const transCategory = CATEGORY_LABELS[transformed.color_type] || transformed.color_type;
    paragraphs.push(
      `Big picture: this started as a ${origCategory} design, but to a ${
        info?.label || cvdType
      } viewer it now reads as ${transCategory}. The colour design isn't coming across the way it was meant to.`
    );
  } else if (transMain.length > 0) {
    paragraphs.push(
      `Good news here: the overall look stays ${origCategory} even after the shift, so the basic colour design still comes through.`
    );
  }

  // 5. Practical closing note.
  if (confused.length > 0) {
    paragraphs.push(
      `Because some colours blend together for this viewer, relying on colour alone (like matching sizes or sets by colour) may not work well. Adding a pattern, texture, or text label would help.`
    );
  }

  // 6. Why this happens — plain explanation of the underlying mechanism.
  const whyItHappens: string[] = [];
  if (info) {
    whyItHappens.push(info.simpleReason);
    whyItHappens.push(info.confusions);
  }

  return { paragraphs, transitions, whyItHappens };
}

interface CvdColourImpactProps {
  cvdType: string;
  analyzing: boolean;
  analysisError: string | null;
  originalAnalysis: ColorResult | null;
  transformedAnalysis: ColorResult | null;
}

export function CvdColourImpact({
  cvdType,
  analyzing,
  analysisError,
  originalAnalysis,
  transformedAnalysis,
}: CvdColourImpactProps) {
  const narrative =
    originalAnalysis && transformedAnalysis
      ? buildNarrative(originalAnalysis, transformedAnalysis, cvdType)
      : null;

  return (
    <div className="border-t border-[#e8e8e8] bg-white p-6 md:p-8">
      <div className="mb-1 flex items-center gap-2">
        <Info className="h-3.5 w-3.5 text-[#aaa]" />
        <p className="text-[10px] tracking-[0.25em] text-[#aaa]" style={SANS}>
          COLOUR VISION IMPACT
        </p>
      </div>
      <h3
        className="mb-6 text-lg text-[#111]"
        style={{ ...SERIF, fontWeight: 500 }}
      >
        How {CVD_LABELS[cvdType]?.split(" — ")[0] || cvdType} changes this garment
      </h3>

      {analyzing && (
        <p className="text-sm text-[#888]" style={SANS}>
          Comparing the original and simulated colours…
        </p>
      )}

      {analysisError && !analyzing && (
        <p
          className="border border-[#f1cfc7] bg-[#fbeae6] px-4 py-3 text-xs leading-6 text-[#9a3b2e]"
          style={SANS}
        >
          {analysisError}
        </p>
      )}

      {narrative && !analyzing && (
        <div>
          {narrative.transitions.length > 0 && (
            <div className="mb-6 border border-[#eee]">
              {narrative.transitions.map((t, i) => (
                <div
                  key={`${t.originalName}-${i}`}
                  className={`grid grid-cols-[1fr_28px_1fr] items-center gap-2 px-4 py-3 ${
                    i !== 0 ? "border-t border-[#eee]" : ""
                  }`}
                >
                  {/* Original colour */}
                  <div className="flex min-w-0 items-center gap-3">
                    <span
                      className="h-7 w-7 flex-shrink-0 border border-[#e5e5e5]"
                      style={{ background: rgbToCss(t.originalRgb) }}
                    />
                    <span
                      className="truncate text-xs text-[#111]"
                      style={SANS}
                      title={t.originalName}
                    >
                      {t.originalName}
                    </span>
                  </div>

                  {/* Arrow, centred in its own column */}
                  <div className="flex justify-center">
                    <ArrowRight className="h-3.5 w-3.5 flex-shrink-0 text-[#ccc]" />
                  </div>

                  {/* Matched colour */}
                  <div className="flex min-w-0 items-center gap-3">
                    <span
                      className="h-7 w-7 flex-shrink-0 border border-[#e5e5e5]"
                      style={{ background: rgbToCss(t.matchedRgb) }}
                    />
                    <span
                      className="truncate text-xs text-[#111]"
                      style={SANS}
                      title={t.matchedName}
                    >
                      {t.matchedName}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}

          <div className="space-y-3">
            {narrative.paragraphs.map((p, i) => (
              <p key={i} className="text-sm leading-7 text-[#444]" style={SANS}>
                {p}
              </p>
            ))}
          </div>

          {narrative.whyItHappens.length > 0 && (
            <div className="mt-8 border-t border-[#eee] pt-6">
              <p
                className="mb-3 text-[10px] tracking-[0.25em] text-[#aaa]"
                style={SANS}
              >
                WHY THIS HAPPENS
              </p>
              <div className="space-y-3">
                {narrative.whyItHappens.map((p, i) => (
                  <p key={i} className="text-sm leading-7 text-[#444]" style={SANS}>
                    {p}
                  </p>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}