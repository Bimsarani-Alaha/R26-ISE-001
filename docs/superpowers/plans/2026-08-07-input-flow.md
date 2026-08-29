# Refined Recommendation Input Flow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restructure the recommendation input flow into two progressive steps (occasion, then free-text description) while keeping the backend, results, and detail pages unchanged.

**Architecture:** Frontend-only change to the Next.js client. The `/input` page becomes a two-step progressive reveal (Step 1: occasion chips; Step 2: free-text textarea). The shared store drops `gender`/`colorPreference`. `/processing` composes a prompt of `Occasion: <occasion>. <free text>` and sends it to the existing `/predict` endpoint. The model extracts color/usage/articleType as before.

**Tech Stack:** Next.js 16 (App Router, client components), React 19, motion, lucide-react, Tailwind CSS 4, Biome (lint/format), shared React context store.

## Global Constraints

- No new routes. Only `/input`, `AppStoreContext.tsx`, and `/processing` change.
- No backend/model changes. `/predict` still receives `{ text: string }`.
- Remove `gender` and `colorPreference` from the store and all their usages.
- Step 1 (occasion) and Step 2 (free text) are both required before submit.
- Prompt format sent to `/predict`: `Occasion: <occasion>. <free text>`.
- Existing visual language must be preserved: `SANS`/`SERIF` from `typography`, `FilterChip` styling, `motion` entrance animations, `SiteNav`.
- No test runner is configured in `client/`. Verification is `npm run lint` (Biome) and `npm run build`. Follow existing patterns; do not add a test framework.

---

### Task 1: Remove gender and colorPreference from the shared store

**Files:**
- Modify: `client/src/app/context/AppStoreContext.tsx`

**Interfaces:**
- Consumes: `BackendPrediction` (from `client/src/app/lib/recommendationApi`), `ClothingItem` (from `client/src/app/data/recommendations`).
- Produces: `AppStore` context retaining `requirements`, `occasion`, `prediction`, `recommendations` and their setters; deleting `gender`, `colorPreference`, `setGender`, `setColorPreference`.

- [ ] **Step 1: Remove the four deleted members from the type**

In `client/src/app/context/AppStoreContext.tsx`, edit the `AppStore` type (lines 13-26):

```tsx
type AppStore = {
  requirements: string;
  occasion: string;
  prediction: BackendPrediction | null;
  recommendations: ClothingItem[];
  setRequirements: (v: string) => void;
  setOccasion: (v: string) => void;
  setPrediction: (v: BackendPrediction | null) => void;
  setRecommendations: (v: ClothingItem[]) => void;
};
```

- [ ] **Step 2: Remove the deleted state and value members**

Remove these four lines from the provider (currently lines 33-34 and 42-49):

```tsx
const [gender, setGender] = useState("");
const [colorPreference, setColorPreference] = useState("");
```

and remove `gender,`, `colorPreference,`, `setGender,`, `setColorPreference,` from the `value` object (lines 42-49) and its dependency array (lines 56-57).

- [ ] **Step 3: Verify the store no longer references removed members**

Run: `npm run lint` in `client/`
Expected: no errors (Biome reports nothing for this file).

- [ ] **Step 4: Commit**

```bash
git add client/src/app/context/AppStoreContext.tsx
git commit -m "refactor: remove gender and colorPreference from app store"
```

---

### Task 2: Restructure the input page into two progressive steps

**Files:**
- Modify: `client/src/app/input/page.tsx` (full rewrite of the component body)

**Interfaces:**
- Consumes: `useAppStore()` from `client/src/app/context/AppStoreContext` (now without `gender`/`colorPreference`); `SiteNav`, `SANS`, `SERIF`, `Badge`, `Button`, `Textarea` — all unchanged.
- Produces: On submit, sets `occasion` and `requirements` on the store, clears `prediction` and `recommendations`, then routes to `/processing`.

- [ ] **Step 1: Write the new input page**

Replace the entire contents of `client/src/app/input/page.tsx` with:

```tsx
"use client";

import { ArrowUpRight } from "lucide-react";
import { motion } from "motion/react";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { SiteNav } from "@/app/components/SiteNav";
import { SANS, SERIF } from "@/app/components/typography";
import { Badge } from "@/app/components/ui/badge";
import { Button } from "@/app/components/ui/button";
import { Textarea } from "@/app/components/ui/textarea";
import { useAppStore } from "@/app/context/AppStoreContext";

const OCCASIONS = [
  "Casual",
  "Formal",
  "Party",
  "Sports",
  "Date Night",
  "Business",
];

const EXAMPLE_PROMPTS = [
  "A formal outfit for an office meeting in hot weather",
  "A casual summer outfit for a beach day with friends",
  "Party look for a rooftop event in the evening",
];

export default function InputPage() {
  const router = useRouter();
  const store = useAppStore();
  const [step, setStep] = useState(1);
  const [occasion, setOccasion] = useState(store.occasion || "");
  const [requirements, setRequirements] = useState(store.requirements || "");
  const [charCount, setCharCount] = useState(requirements.length);

  const handleTextChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setRequirements(e.target.value);
    setCharCount(e.target.value.length);
  };

  const handleSubmit = () => {
    if (!occasion || !requirements.trim()) return;
    store.setOccasion(occasion);
    store.setRequirements(requirements);
    store.setPrediction(null);
    store.setRecommendations([]);
    router.push("/processing");
  };

  const isValidStep1 = occasion.length > 0;
  const isValidStep2 = requirements.trim().length > 0;

  const FilterChip = ({
    label,
    active,
    onClick,
  }: {
    label: string;
    active: boolean;
    onClick: () => void;
  }) => (
    <Button
      type="button"
      onClick={onClick}
      variant="outline"
      size="sm"
      className={`px-4 py-2 text-xs tracking-[0.12em] transition-all duration-200 border rounded-none h-auto ${
        active
          ? "bg-[#111] text-white border-[#111] hover:bg-[#111] hover:text-white"
          : "bg-white text-[#555] border-[#ddd] hover:border-[#999] hover:text-[#111] hover:bg-white"
      }`}
      style={SANS}
    >
      {label.toUpperCase()}
    </Button>
  );

  return (
    <div className="min-h-screen w-full bg-white flex flex-col">
      <SiteNav backHref="/" />

      <div className="flex-1 max-w-2xl mx-auto w-full px-6 py-14">
        {/* HEADER */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="mb-12 text-center"
        >
          <p className="text-xs tracking-[0.3em] text-[#aaa] mb-4" style={SANS}>
            STEP {step} OF 2
          </p>
          <h1
            className="text-4xl md:text-5xl text-[#111] tracking-wide mb-4"
            style={{ ...SERIF, fontWeight: 300 }}
          >
            {step === 1 ? "What's the Occasion?" : "Describe Your Outfit"}
          </h1>
          <p className="text-sm text-[#888] tracking-wide" style={SANS}>
            {step === 1
              ? "Select the occasion you're dressing for."
              : "Mention the color, dress type, and any other requirements."}
          </p>
        </motion.div>

        {step === 1 ? (
          /* STEP 1: OCCASION */
          <motion.div
            key="step1"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.15 }}
            className="mb-12"
          >
            <div className="flex flex-wrap gap-2">
              {OCCASIONS.map((o) => (
                <FilterChip
                  key={o}
                  label={o}
                  active={occasion === o}
                  onClick={() => setOccasion(occasion === o ? "" : o)}
                />
              ))}
            </div>

            <Button
              type="button"
              onClick={() => setStep(2)}
              disabled={!isValidStep1}
              variant="default"
              className={`w-full mt-10 py-4 text-xs tracking-[0.25em] flex items-center justify-center gap-3 transition-all duration-300 rounded-none h-auto ${
                isValidStep1
                  ? "bg-[#111] text-white hover:bg-[#333] active:scale-[0.98]"
                  : "bg-[#f0f0f0] text-[#ccc] cursor-not-allowed hover:bg-[#f0f0f0]"
              }`}
              style={SANS}
            >
              CONTINUE
              {isValidStep1 && <ArrowUpRight className="w-4 h-4" />}
            </Button>
          </motion.div>
        ) : (
          /* STEP 2: FREE TEXT */
          <motion.div
            key="step2"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.15 }}
          >
            {/* Selected occasion summary */}
            <div className="mb-8 text-center">
              <span
                className="text-[10px] tracking-[0.25em] text-[#888]"
                style={SANS}
              >
                OCCASION: {occasion.toUpperCase()}
              </span>
            </div>

            <label
              htmlFor="outfit-needs"
              className="block text-[10px] tracking-[0.25em] text-[#aaa] mb-3"
              style={SANS}
            >
              DESCRIBE YOUR OUTFIT NEEDS
            </label>
            <div
              className={`relative border transition-colors duration-200 ${
                isValidStep2 ? "border-[#111]" : "border-[#ddd]"
              } focus-within:border-[#111]`}
            >
              <Textarea
                id="outfit-needs"
                value={requirements}
                onChange={handleTextChange}
                placeholder={
                  "Describe your outfit needs…\n\nE.g. I need a formal outfit for an office meeting in hot weather"
                }
                maxLength={500}
                rows={6}
                className="w-full bg-white text-[#111] placeholder-[#ccc] px-5 pt-5 pb-10 text-sm resize-none outline-none leading-relaxed border-0 rounded-none shadow-none focus-visible:ring-0 min-h-0"
                style={SANS}
              />
              <div className="absolute bottom-3 left-5 right-5 flex items-center justify-between">
                <span className="text-[#ccc] text-xs" style={SANS}>
                  {charCount}/500
                </span>
                {isValidStep2 && (
                  <Badge
                    variant="outline"
                    className="text-[10px] tracking-[0.15em] text-[#111] border-0 bg-transparent px-0 py-0"
                    style={SANS}
                  >
                    READY ✓
                  </Badge>
                )}
              </div>
            </div>

            {/* Example prompts */}
            <div className="mt-4">
              <p
                className="text-[10px] tracking-[0.2em] text-[#bbb] mb-3"
                style={SANS}
              >
                TRY AN EXAMPLE
              </p>
              <div className="flex flex-col gap-2">
                {EXAMPLE_PROMPTS.map((prompt) => (
                  <button
                    key={prompt}
                    type="button"
                    onClick={() => {
                      setRequirements(prompt);
                      setCharCount(prompt.length);
                    }}
                    className="text-left text-xs text-[#888] hover:text-[#111] border border-[#eee] hover:border-[#bbb] px-4 py-2.5 transition-all duration-200 bg-[#fafafa] hover:bg-white"
                    style={SANS}
                  >
                    "{prompt}"
                  </button>
                ))}
              </div>
            </div>

            {/* Back + Submit */}
            <div className="mt-10 flex flex-col gap-4">
              <Button
                type="button"
                onClick={handleSubmit}
                disabled={!isValidStep2}
                variant="default"
                className={`w-full py-4 text-xs tracking-[0.25em] flex items-center justify-center gap-3 transition-all duration-300 rounded-none h-auto ${
                  isValidStep2
                    ? "bg-[#111] text-white hover:bg-[#333] active:scale-[0.98]"
                    : "bg-[#f0f0f0] text-[#ccc] cursor-not-allowed hover:bg-[#f0f0f0]"
                }`}
                style={SANS}
              >
                GET RECOMMENDATIONS
                {isValidStep2 && <ArrowUpRight className="w-4 h-4" />}
              </Button>
              <button
                type="button"
                onClick={() => setStep(1)}
                className="text-xs tracking-[0.15em] text-[#888] hover:text-[#111] transition-colors underline underline-offset-2 self-center"
                style={SANS}
              >
                ← BACK TO OCCASION
              </button>
            </div>
          </motion.div>
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Run lint**

Run: `npm run lint` in `client/`
Expected: no errors.

- [ ] **Step 3: Run build**

Run: `npm run build` in `client/`
Expected: build succeeds.

- [ ] **Step 4: Commit**

```bash
git add client/src/app/input/page.tsx
git commit -m "feat: two-step input flow (occasion, then free-text description)"
```

---

### Task 3: Update processing page prompt composition

**Files:**
- Modify: `client/src/app/processing/page.tsx`

**Interfaces:**
- Consumes: `useAppStore()` (now without `gender`/`colorPreference`); `fetchRecommendations(text)` from `client/src/app/lib/recommendationApi`.
- Produces: calls `fetchRecommendations` with the composed prompt, then `setPrediction`/`setRecommendations` and routes to `/results`.

- [ ] **Step 1: Update the store destructuring**

In `client/src/app/processing/page.tsx`, change line 31 from:

```tsx
  const { requirements, occasion, gender, colorPreference, setPrediction, setRecommendations } =
    useAppStore();
```

to:

```tsx
  const { requirements, occasion, setPrediction, setRecommendations } =
    useAppStore();
```

- [ ] **Step 2: Update prompt composition**

Replace the `filters`/`prompt` block (currently lines 66-73):

```tsx
        const filters = [
          occasion && `Occasion: ${occasion}`,
          gender && `Gender: ${gender}`,
          colorPreference && `Colour preference: ${colorPreference}`,
        ].filter(Boolean);
        const prompt = filters.length
          ? `${requirements}. ${filters.join(". ")}.`
          : requirements;
```

with:

```tsx
        const prompt = occasion
          ? `Occasion: ${occasion}. ${requirements}`
          : requirements;
```

- [ ] **Step 3: Update the effect dependency array**

Replace line 110:

```tsx
  }, [router, requirements, occasion, gender, colorPreference, setPrediction, setRecommendations]);
```

with:

```tsx
  }, [router, requirements, occasion, setPrediction, setRecommendations]);
```

- [ ] **Step 4: Run lint**

Run: `npm run lint` in `client/`
Expected: no errors.

- [ ] **Step 5: Run build**

Run: `npm run build` in `client/`
Expected: build succeeds.

- [ ] **Step 6: Commit**

```bash
git add client/src/app/processing/page.tsx
git commit -m "feat: compose occasion-first prompt in processing page"
```

---

### Task 4: Verify no stale references and manual flow check

**Files:**
- Inspect: `client/src/app/results/page.tsx`, `client/src/app/detail/[id]/page.tsx` (should not reference `gender`/`colorPreference`).

- [ ] **Step 1: Grep for stale references**

Run in repo root: `rg "colorPreference|setColorPreference|setGender|\bgender\b" client/src`
Expected: no matches.

- [ ] **Step 2: Final lint and build**

Run: `npm run lint` then `npm run build` in `client/`
Expected: both pass.

- [ ] **Step 3: Manual flow check (with backend running, if available)**

1. Start the FastAPI backend (`uvicorn src.api.app:app --reload` from `styleRecommendationEngine/`).
2. Start the client (`npm run dev` in `client/`).
3. Open `/input`: Confirm the Continue button is disabled until an occasion is selected.
4. Select an occasion → Continue. Confirm Step 2 shows the occasion summary.
5. Type a description → "Get Recommendations". Confirm the prompt sent is `Occasion: <occasion>. <description>` (inspect the network tab).
6. Confirm navigation to `/processing`, then `/results`, and that `/detail/[id]` renders description, color, occasion, and style tips.

- [ ] **Step 4: Commit any follow-up fixes**

If any fix was needed, commit it with a descriptive message.

---

## Self-Review Notes

- Spec coverage: occasion-first step (Task 2), free-text extraction via existing model (Task 3 prompt), remove gender/color chips (Tasks 1-2), results/detail unchanged (Task 4 inspection), error handling unchanged (no code path touched in Task 3 beyond prompt).
- No placeholders: all code blocks are complete.
- Type consistency: `useAppStore()` signature after Task 1 matches Tasks 2-3 usages.
