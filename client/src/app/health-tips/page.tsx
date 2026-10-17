"use client";

import { ArrowLeft, RefreshCw } from "lucide-react";
import { motion } from "motion/react";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { SiteNav } from "@/app/components/SiteNav";
import { SANS, SERIF } from "@/app/components/typography";
import { Button } from "@/app/components/ui/button";
import { useAppStore } from "@/app/context/AppStoreContext";
import { fetchHealthTips } from "@/app/lib/healthTipsApi";

function formatHealthTipsError(message: string): string {
  const normalized = message.trim();

  if (/ollama|qwen2\.5:3b/i.test(normalized)) {
    return "The local Ollama guidance service is unavailable. Please start the qwen2.5:3b model in Ollama to generate your wellness guidance.";
  }

  return normalized || "Unable to generate body guidance.";
}

export default function HealthTipsPage() {
  const router = useRouter();
  const { bodyMeasurements, predictedSize, hydrated } = useAppStore();
  const healthTipsRequest = useMemo(
    () =>
      predictedSize
        ? {
            clothing_size: predictedSize,
            height_cm: bodyMeasurements?.heightCm,
            shoulder_cm: bodyMeasurements?.shoulderCm,
            hip_cm: bodyMeasurements?.hipCm,
          }
        : null,
    [bodyMeasurements, predictedSize],
  );
  const [guidance, setGuidance] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!hydrated) return;

    if (!predictedSize || !healthTipsRequest) {
      router.replace("/size");
      return;
    }

    let cancelled = false;
    setLoading(true);
    setError("");

    fetchHealthTips(healthTipsRequest)
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
  }, [healthTipsRequest, hydrated, predictedSize, router]);

  const retry = () => {
    if (!healthTipsRequest) return;
    setLoading(true);
    setError("");
    fetchHealthTips(healthTipsRequest)
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
            <span className="hidden text-sm tracking-widest md:block">BACK TO MEASUREMENTS</span>
          </Button>
        }
      />

      <main className="mx-auto w-full max-w-5xl px-6 py-14 md:px-12 md:py-20">
        <motion.header
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          className="max-w-2xl"
        >
          <p className="text-xs tracking-[0.2em] text-[#777]" style={SANS}>
            PERSONAL WELLNESS GUIDANCE
          </p>
          <h1 className="mt-4 text-5xl leading-[0.95] text-[#111] md:text-7xl" style={{ ...SERIF, fontWeight: 300 }}>
            Everyday wellbeing, at your pace.
          </h1>
          <p className="mt-6 max-w-xl text-base leading-7 text-[#666]" style={SANS}>
            General wellness and appearance suggestions informed by your clothing size and available measurements. Measurements are not a measure of health.
          </p>
        </motion.header>

        {predictedSize && (
          <div className="mt-12 border-y border-[#ddd] px-1 py-5">
            <p className="text-xs tracking-[0.15em] text-[#777]" style={SANS}>PREDICTED CLOTHING SIZE</p>
            <p className="mt-2 text-2xl text-[#111]" style={{ ...SERIF, fontWeight: 400 }}>{predictedSize}</p>
            {bodyMeasurements && (
              <div className="mt-5 grid grid-cols-3 border-y border-[#ddd]">
                <div className="px-2 py-4 sm:px-4">
                  <p className="text-xs tracking-[0.08em] text-[#777]" style={SANS}>SHOULDER WIDTH</p>
                  <p className="mt-2 text-lg text-[#111]" style={{ ...SERIF, fontWeight: 400 }}>
                    {bodyMeasurements.shoulderCm.toFixed(1)} <span className="text-xs text-[#777]">cm</span>
                  </p>
                </div>
                <div className="border-l border-[#ddd] px-2 py-4 sm:px-4">
                  <p className="text-xs tracking-[0.08em] text-[#777]" style={SANS}>HIP SIZE</p>
                  <p className="mt-2 text-lg text-[#111]" style={{ ...SERIF, fontWeight: 400 }}>
                    {bodyMeasurements.hipCm.toFixed(1)} <span className="text-xs text-[#777]">cm</span>
                  </p>
                </div>
                <div className="border-l border-[#ddd] px-2 py-4 sm:px-4">
                  <p className="text-xs tracking-[0.08em] text-[#777]" style={SANS}>HEIGHT</p>
                  <p className="mt-2 text-lg text-[#111]" style={{ ...SERIF, fontWeight: 400 }}>
                    {bodyMeasurements.heightCm.toFixed(1)} <span className="text-xs text-[#777]">cm</span>
                  </p>
                </div>
              </div>
            )}
          </div>
        )}

        <motion.section
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
          className="mt-12 min-h-64 border border-[#ddd] bg-white p-7 md:p-10"
        >
          <div className="flex items-center gap-3 border-b border-[#eee] pb-5">
            <h2 className="text-sm tracking-[0.15em] text-[#333]" style={SANS}>YOUR GUIDANCE</h2>
          </div>
          {loading && <p className="mt-8 text-base text-[#666]" style={SANS}>Preparing your guidance...</p>}
          {error && (
            <div className="mt-8 flex flex-wrap items-center gap-4">
              <p className="text-base leading-6 text-[#555]" style={SANS}>{error}</p>
              <Button type="button" onClick={retry} variant="outline" className="h-auto rounded-none border-[#111] px-4 py-2 text-sm tracking-[0.1em]" style={SANS}>
                <RefreshCw className="mr-2 h-3.5 w-3.5" /> RETRY
              </Button>
            </div>
          )}
          {!loading && !error && <p className="mt-8 whitespace-pre-line text-base leading-8 text-[#444]" style={SANS}>{guidance}</p>}
        </motion.section>
      </main>
    </div>
  );
}