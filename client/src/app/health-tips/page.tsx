"use client";

import { ArrowLeft, RefreshCw, Sparkles } from "lucide-react";
import { motion } from "motion/react";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { SiteNav } from "@/app/components/SiteNav";
import { SANS, SERIF } from "@/app/components/typography";
import { Button } from "@/app/components/ui/button";
import { useAppStore } from "@/app/context/AppStoreContext";
import { fetchHealthTips } from "@/app/lib/healthTipsApi";

function formatHealthTipsError(message: string): string {
  const normalized = message.trim();

  if (/ollama|qwen2\.5:3b/i.test(normalized)) {
    return "The local Ollama guidance service is unavailable. Please start the qwen2.5:3b model in Ollama to generate your body appearance guide.";
  }

  return normalized || "Unable to generate body guidance.";
}

export default function HealthTipsPage() {
  const router = useRouter();
  const { bodyMeasurements } = useAppStore();
  const [guidance, setGuidance] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!bodyMeasurements) {
      router.replace("/size");
      return;
    }

    let cancelled = false;
    setLoading(true);
    setError("");

    fetchHealthTips({
      shoulder_width: bodyMeasurements.shoulderCm,
      hip_size: bodyMeasurements.hipCm,
      height: bodyMeasurements.heightCm,
      gender: bodyMeasurements.gender,
      clothing_size: bodyMeasurements.clothingSize,
    })
      .then((result) => {
        if (!cancelled) setGuidance(result.guidance);
      })
      .catch((requestError: unknown) => {
        if (!cancelled) {
          const message =
            requestError instanceof Error ? requestError.message : "Unable to generate body guidance.";
          setError(formatHealthTipsError(message));
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [bodyMeasurements, router]);

  const retry = () => {
    if (!bodyMeasurements) return;
    setLoading(true);
    setError("");
    fetchHealthTips({
      shoulder_width: bodyMeasurements.shoulderCm,
      hip_size: bodyMeasurements.hipCm,
      height: bodyMeasurements.heightCm,
      gender: bodyMeasurements.gender,
      clothing_size: bodyMeasurements.clothingSize,
    })
      .then((result) => setGuidance(result.guidance))
      .catch((requestError: unknown) => {
        const message =
          requestError instanceof Error ? requestError.message : "Unable to generate body guidance.";
        setError(formatHealthTipsError(message));
      })
      .finally(() => setLoading(false));
  };

  return (
    <div className="min-h-screen w-full bg-[#f8f7f3] text-[#111]">
      <SiteNav
        backHref="/size"
        right={
          <Button
            type="button"
            variant="ghost"
            onClick={() => router.push("/size")}
            className="flex h-auto items-center gap-1.5 rounded-none bg-transparent p-0 text-[#888] hover:bg-transparent hover:text-[#111]"
            style={SANS}
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            <span className="hidden text-xs tracking-widest md:block">BACK TO MEASUREMENTS</span>
          </Button>
        }
      />

      <main className="mx-auto w-full max-w-5xl px-6 py-14 md:px-12 md:py-20">
        <motion.header
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          className="max-w-2xl"
        >
          <p className="text-[10px] tracking-[0.3em] text-[#999]" style={SANS}>
            PERSONAL BODY GUIDANCE
          </p>
          <h1 className="mt-4 text-5xl leading-[0.95] text-[#111] md:text-7xl" style={{ ...SERIF, fontWeight: 300 }}>
            Understand your proportions.
          </h1>
          <p className="mt-6 max-w-xl text-sm leading-7 text-[#777]" style={SANS}>
            A considered guide to dressing, movement, and everyday wellbeing based on your measured proportions.
          </p>
        </motion.header>

        {bodyMeasurements && (
          <div className="mt-12 grid border-y border-[#ddd] sm:grid-cols-3">
            {[
              ["SHOULDER WIDTH", bodyMeasurements.shoulderCm, "cm"],
              ["HIP SIZE", bodyMeasurements.hipCm, "cm"],
              ["HEIGHT", bodyMeasurements.heightCm, "cm"],
            ].map(([label, value, unit]) => (
              <div key={label} className="border-b border-[#ddd] px-1 py-5 last:border-0 sm:border-b-0 sm:border-r sm:px-6 sm:first:pl-0 sm:last:border-0">
                <p className="text-[10px] tracking-[0.2em] text-[#999]" style={SANS}>{label}</p>
                <p className="mt-2 text-2xl text-[#111]" style={{ ...SERIF, fontWeight: 400 }}>{Number(value).toFixed(1)} <span className="text-sm text-[#888]">{unit}</span></p>
              </div>
            ))}
          </div>
        )}

        <motion.section
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
          className="mt-12 min-h-64 border border-[#ddd] bg-white p-7 md:p-10"
        >
          <div className="flex items-center gap-3 border-b border-[#eee] pb-5">
            <h2 className="text-xs tracking-[0.25em] text-[#333]" style={SANS}>YOUR GUIDANCE</h2>
          </div>
          {loading && <p className="mt-8 text-sm text-[#888]" style={SANS}>Preparing your guidance...</p>}
          {error && (
            <div className="mt-8 flex flex-wrap items-center gap-4">
              <p className="text-sm leading-6 text-[#666]" style={SANS}>{error}</p>
              <Button type="button" onClick={retry} variant="outline" className="h-auto rounded-none border-[#111] px-4 py-2 text-xs tracking-[0.15em]" style={SANS}>
                <RefreshCw className="mr-2 h-3.5 w-3.5" /> RETRY
              </Button>
            </div>
          )}
          {!loading && !error && <p className="mt-8 whitespace-pre-line text-sm leading-8 text-[#555]" style={SANS}>{guidance}</p>}
        </motion.section>
      </main>
    </div>
  );
}