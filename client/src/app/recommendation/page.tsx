"use client";

import { ArrowUpRight } from "lucide-react";
import { motion } from "motion/react";
import { useRouter } from "next/navigation";
import { Suspense, useEffect, useRef, useState } from "react";
import { SiteNav } from "@/app/components/SiteNav";
import { SANS, SERIF } from "@/app/components/typography";
import { Badge } from "@/app/components/ui/badge";
import { Button } from "@/app/components/ui/button";
import { Textarea } from "@/app/components/ui/textarea";
import { useAppStore } from "@/app/context/AppStoreContext";
import { getRecommendationPrefill } from "@/app/lib/recommendationPrefill";

const GENDERS = ["Male", "Female", "Unisex"];
const SIZES = ["XS", "S", "M", "L", "XL", "2XL", "3XL", "4XL" ,"Free Size"];

const EXAMPLE_PROMPTS = [
  "A black dress for casual wear",
  "A blue frock for a formal event",
  "Party look for a rooftop event in the evening",
  "A blue saree for a wedding",
  "Red cotton kurta for party",
];

export default function RecommendationPage() {
  return (
    <Suspense fallback={<div role="status">Loading recommendations…</div>}>
      <RecommendationForm />
    </Suspense>
  );
}

function RecommendationForm() {
  const router = useRouter();
  const store = useAppStore();
  const [gender, setGender] = useState("");
  const [size, setSize] = useState("");
  const initialized = useRef(false);
  const [requirements, setRequirements] = useState("");
  const [charCount, setCharCount] = useState(0);

  // AppStore hydrates styleai-gender and styleai-predicted-size after mount.
  const prefill = getRecommendationPrefill(store);

  useEffect(() => {
    if (!store.hydrated || initialized.current) return;
    initialized.current = true;
    setGender(prefill.gender);
    setSize(prefill.size);
  }, [store.hydrated, prefill.gender, prefill.size]);

  const genderFromPrediction = !!prefill.predictedGender && gender === prefill.predictedGender;
  const sizeFromPrediction = !!prefill.predictedSize && size === prefill.predictedSize;

  const handleTextChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setRequirements(e.target.value);
    setCharCount(e.target.value.length);
  };

  const handleSubmit = () => {
    if (!gender || !size || !requirements.trim()) return;
    store.setGender(gender);
    store.setSize(size);
    store.setRequirements(requirements);
    store.setProductResults([]);
    router.push("/recommendation/loading");
  };

  const isValid = gender.length > 0 && size.length > 0 && requirements.trim().length > 0;

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
      aria-pressed={active}
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
          className="mb-10 text-center"
        >
          <h1
            className="text-4xl md:text-5xl text-[#111] tracking-wide mb-4"
            style={{ ...SERIF, fontWeight: 300 }}
          >
            Describe Your Outfit
          </h1>
          <p className="text-sm text-[#888] tracking-wide" style={SANS}>
            Choose gender, size and describe your outfit in one place.
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.12 }}
          className="space-y-8"
        >
          {/* Gender + Size on same page — prefilled from size prediction if available */}
          <div>
            <div className="flex items-center gap-2 mb-3">
              <p className="block text-[10px] tracking-[0.25em] text-[#aaa]" style={SANS}>
                GENDER
              </p>
              {genderFromPrediction && (
                <span className="text-[9px] tracking-[0.15em] bg-[#fef9e7] border border-[#f0d97a] px-2 py-0.5 text-[#6b5900]" style={SANS}>
                  FROM SIZE PREDICTION
                </span>
              )}
            </div>
            <div className="flex flex-wrap gap-2">
              {GENDERS.map((g) => (
                <FilterChip
                  key={g}
                  label={g}
                  active={gender === g}
                  onClick={() => setGender(gender === g ? "" : g)}
                />
              ))}
            </div>
          </div>

          <div>
            <div className="flex items-center gap-2 mb-3">
              <p className="block text-[10px] tracking-[0.25em] text-[#aaa]" style={SANS}>
                SIZE
              </p>
              {sizeFromPrediction && (
                <span className="text-[9px] tracking-[0.15em] bg-[#fef9e7] border border-[#f0d97a] px-2 py-0.5 text-[#6b5900]" style={SANS}>
                  FROM SIZE PREDICTION
                </span>
              )}
            </div>
            <div className="flex flex-wrap gap-2">
              {SIZES.map((s) => (
                <FilterChip
                  key={s}
                  label={s}
                  active={size === s}
                  onClick={() => setSize(size === s ? "" : s)}
                />
              ))}
            </div>
          </div>

          <div>
            <label
              htmlFor="outfit-needs"
              className="block text-[10px] tracking-[0.25em] text-[#aaa] mb-3"
              style={SANS}
            >
              DESCRIBE YOUR OUTFIT NEEDS
            </label>
            <div
              className={`relative border transition-colors duration-200 ${
                requirements.trim().length > 0 ? "border-[#111]" : "border-[#ddd]"
              } focus-within:border-[#111]`}
            >
              <Textarea
                id="outfit-needs"
                value={requirements}
                onChange={handleTextChange}
                placeholder={
                  "Describe your outfit needs…\n\nE.g. I need A black dress for casual wear"
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
                {requirements.trim().length > 0 && (
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
                    &quot;{prompt}&quot;
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Submit */}
          <Button
            type="button"
            onClick={handleSubmit}
            disabled={!isValid}
            variant="default"
            className={`w-full py-4 text-xs tracking-[0.25em] flex items-center justify-center gap-3 transition-all duration-300 rounded-none h-auto ${
              isValid
                ? "bg-[#111] text-white hover:bg-[#333] active:scale-[0.98]"
                : "bg-[#f0f0f0] text-[#ccc] cursor-not-allowed hover:bg-[#f0f0f0]"
            }`}
            style={SANS}
          >
            GET RECOMMENDATIONS
            {isValid && <ArrowUpRight className="w-4 h-4" />}
          </Button>
          {!isValid && (
            <p className="text-[10px] tracking-[0.15em] text-[#bbb] text-center" style={SANS}>
              {!gender ? "Select gender" : !size ? "Select size" : "Describe your outfit"}
            </p>
          )}
        </motion.div>
      </div>
    </div>
  );
}
