"use client";

import { AnimatePresence, motion } from "motion/react";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { SiteNav } from "@/app/components/SiteNav";
import { SANS, SERIF } from "@/app/components/typography";
import { Button } from "@/app/components/ui/button";
import { Card } from "@/app/components/ui/card";
import { Progress } from "@/app/components/ui/progress";
import { useAppStore } from "@/app/context/AppStoreContext";
import {
  checkHealth,
  getRecommendations,
  type HealthResponse,
} from "@/app/lib/aiStyleApi";

const PROCESSING_STEPS = [
  "Checking model availability…",
  "Analyzing your requirements…",
  "Matching your preferences…",
  "Curating the perfect wardrobe…",
  "Finalising your looks…",
];

const FASHION_TIPS = [
  "Light colours reflect warmth, keeping you cool and elegant.",
  "Natural fabrics like cotton and linen breathe beautifully.",
  "Layering adds versatility to any refined look.",
  "The right accessory elevates a simple outfit instantly.",
];

export default function RecommendationLoadingPage() {
  const router = useRouter();
  const { requirements, gender, size, setProductResults } = useAppStore();
  const [stepIndex, setStepIndex] = useState(0);
  const [progress, setProgress] = useState(0);
  const [tipIndex, setTipIndex] = useState(0);
  const [error, setError] = useState("");
  const [modelStatus, setModelStatus] = useState<HealthResponse | null>(null);
  const [checkingModel, setCheckingModel] = useState(true);
  const cancelledRef = useRef(false);

  useEffect(() => {
    if (!requirements || !gender || !size) {
      router.replace("/recommendation");
      return;
    }

    cancelledRef.current = false;

    const stepInterval = 650;
    const stepTimer = setInterval(() => {
      setStepIndex((prev) =>
        prev < PROCESSING_STEPS.length - 1 ? prev + 1 : prev,
      );
    }, stepInterval);

    const progressTimer = setInterval(() => {
      setProgress((prev) => (prev >= 92 ? 92 : prev + 2));
    }, 80);

    const tipTimer = setInterval(() => {
      setTipIndex((prev) => (prev + 1) % FASHION_TIPS.length);
    }, 2000);

    const runPipeline = async () => {
      try {
        setError("");
        setCheckingModel(true);

        // Step 1: Check model health
        setStepIndex(0);
        let health: HealthResponse | null = null;
        let retries = 0;
        const maxRetries = 5;

        while (retries < maxRetries && !cancelledRef.current) {
          try {
            health = await checkHealth();
            break;
          } catch {
            retries++;
            if (retries < maxRetries) {
              await new Promise((r) => setTimeout(r, 2000));
            }
          }
        }

        if (cancelledRef.current) return;

        if (!health || !health.ollama_connected) {
          setModelStatus(health);
          setCheckingModel(false);
          setError(
            health
              ? "Ollama is not connected. Please ensure your model is running."
              : "Unable to reach the server. Please check if the backend is running.",
          );
          setProgress(0);
          return;
        }

        setModelStatus(health);
        setCheckingModel(false);

        // Step 2-4: Get recommendations
        setStepIndex(2);
        const result = await getRecommendations({ gender, size, requirements });

        if (cancelledRef.current) return;

        setProductResults(result.recommendations);
        setStepIndex(PROCESSING_STEPS.length - 1);
        setProgress(100);

        setTimeout(() => router.replace("/recommendation/results"), 500);
      } catch (requestError) {
        if (cancelledRef.current) return;

        const message =
          requestError instanceof Error
            ? requestError.message
            : "Unable to reach the recommendation model.";
        setError(message);
        setProgress(0);
      }
    };

    void runPipeline();

    return () => {
      cancelledRef.current = true;
      clearInterval(stepTimer);
      clearInterval(progressTimer);
      clearInterval(tipTimer);
    };
  }, [router, requirements, gender, size, setProductResults]);

  const handleRetry = () => {
    setError("");
    setCheckingModel(true);
    setProgress(0);
    setStepIndex(0);
    // Re-trigger the effect by refreshing
    router.refresh();
  };

  return (
    <div className="min-h-screen w-full bg-white flex flex-col">
      <SiteNav centered />

      {/* Content */}
      <div className="flex-1 flex flex-col items-center justify-center px-6 py-16">
        <div className="max-w-sm w-full text-center">
          {/* Elegant spinner */}
          <div className="relative w-20 h-20 mx-auto mb-12">
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 2.5, repeat: Infinity, ease: "linear" }}
              className="absolute inset-0 rounded-full border border-[#111] border-t-transparent"
            />
            <motion.div
              animate={{ rotate: -360 }}
              transition={{ duration: 3.5, repeat: Infinity, ease: "linear" }}
              className="absolute inset-3 rounded-full border border-[#bbb] border-b-transparent"
            />
            <div className="absolute inset-0 flex items-center justify-center">
              <motion.div
                animate={{ scale: [1, 1.15, 1] }}
                transition={{
                  duration: 2,
                  repeat: Infinity,
                  ease: "easeInOut",
                }}
                className="w-2 h-2 rounded-full bg-[#111]"
              />
            </div>
          </div>

          {/* Title */}
          <h2
            className="text-3xl text-[#111] tracking-wide mb-3"
            style={{ ...SERIF, fontWeight: 300 }}
          >
            {checkingModel ? "Connecting to Model" : "Curating Your Looks"}
          </h2>

          {/* Step text */}
          <AnimatePresence mode="wait">
            <motion.p
              key={stepIndex}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.35 }}
              className="text-sm text-[#999] mb-10 tracking-wide"
              style={SANS}
            >
              {PROCESSING_STEPS[stepIndex]}
            </motion.p>
          </AnimatePresence>

          {/* Model status badge */}
          {modelStatus && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="mb-6"
            >
              <div
                className={`inline-flex items-center gap-2 px-3 py-1.5 text-[10px] tracking-[0.15em] ${
                  modelStatus.ollama_connected
                    ? "text-[#2d7a3a] bg-[#f0faf0] border border-[#c5e8c5]"
                    : "text-[#b33] bg-[#fef0f0] border border-[#e8c5c5]"
                }`}
                style={SANS}
              >
                <span
                  className={`w-1.5 h-1.5 rounded-full ${
                    modelStatus.ollama_connected ? "bg-[#2d7a3a]" : "bg-[#b33]"
                  }`}
                />
                {modelStatus.ollama_connected
                  ? `MODEL CONNECTED · ${modelStatus.product_count} PRODUCTS`
                  : "MODEL OFFLINE"}
              </div>
            </motion.div>
          )}

          {/* Progress bar */}
          <Progress
            value={progress}
            className="h-px w-full overflow-hidden rounded-none bg-[#f0f0f0] [&>div]:bg-[#111]"
          />

          {/* Steps checklist */}
          <Card className="border-0 rounded-none bg-transparent gap-0 mt-10 mb-12 text-left">
            {PROCESSING_STEPS.map((step, i) => (
              <div key={step} className="flex items-center gap-3 py-1.5">
                <div
                  className={`w-4 h-4 flex items-center justify-center flex-shrink-0 transition-all duration-300 border ${
                    i < stepIndex
                      ? "bg-[#111] border-[#111]"
                      : i === stepIndex
                        ? "border-[#111] bg-white"
                        : "border-[#ddd] bg-white"
                  }`}
                >
                  {i < stepIndex && (
                    <svg
                      role="img"
                      aria-label="Completed"
                      className="w-2.5 h-2.5 text-white"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={3}
                        d="M5 13l4 4L19 7"
                      />
                    </svg>
                  )}
                  {i === stepIndex && (
                    <motion.div
                      animate={{ scale: [1, 1.3, 1] }}
                      transition={{ duration: 0.8, repeat: Infinity }}
                      className="w-1.5 h-1.5 bg-[#111]"
                    />
                  )}
                </div>
                <span
                  className={`text-xs tracking-wide transition-colors duration-300 ${
                    i <= stepIndex ? "text-[#333]" : "text-[#ccc]"
                  }`}
                  style={SANS}
                >
                  {step}
                </span>
              </div>
            ))}
          </Card>

          {/* Fashion tip */}
          <AnimatePresence mode="wait">
            <motion.div
              key={tipIndex}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -6 }}
              transition={{ duration: 0.4 }}
            >
              <Card className="border-0 border-t border-[#e8e8e8] rounded-none bg-transparent gap-0 pt-6">
                <p
                  className="text-[10px] tracking-[0.2em] text-[#bbb] mb-2"
                  style={SANS}
                >
                  STYLE NOTE
                </p>
                <p
                  className="text-sm text-[#888] italic"
                  style={{ ...SERIF, fontWeight: 300 }}
                >
                  {FASHION_TIPS[tipIndex]}
                </p>
              </Card>
            </motion.div>
          </AnimatePresence>

          {error && (
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              className="mt-8 text-left"
            >
              <Card className="border border-[#e8e8e8] bg-[#fafafa] rounded-none gap-0 p-4">
                <p
                  className="text-xs tracking-[0.2em] text-[#111] mb-2"
                  style={SANS}
                >
                  MODEL ERROR
                </p>
                <p className="text-sm text-[#666] mb-4" style={SANS}>
                  {error}
                </p>
                <div className="flex gap-3">
                  <Button
                    onClick={handleRetry}
                    variant="outline"
                    className="border border-[#111] px-4 py-2 text-xs tracking-[0.15em] text-[#111] rounded-none h-auto bg-transparent hover:bg-[#111] hover:text-white transition-all duration-200"
                    style={SANS}
                  >
                    RETRY
                  </Button>
                  <Button
                    onClick={() => router.push("/recommendation")}
                    variant="outline"
                    className="border border-[#ddd] px-4 py-2 text-xs tracking-[0.15em] text-[#888] rounded-none h-auto bg-transparent hover:bg-[#111] hover:text-white transition-all duration-200"
                    style={SANS}
                  >
                    GO BACK
                  </Button>
                </div>
              </Card>
            </motion.div>
          )}
        </div>
      </div>
    </div>
  );
}
