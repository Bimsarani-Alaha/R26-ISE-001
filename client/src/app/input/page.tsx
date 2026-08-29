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
