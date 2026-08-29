"use client";

import { ArrowUpRight, RotateCcw } from "lucide-react";
import { motion } from "motion/react";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import type { RecommendationLike } from "@/app/components/RecommendationCard";
import {
  normalizeRecommendation,
  RecommendationCard,
} from "@/app/components/RecommendationCard";
import { SiteNav } from "@/app/components/SiteNav";
import { SANS, SERIF } from "@/app/components/typography";
import { Button } from "@/app/components/ui/button";
import { useAppStore } from "@/app/context/AppStoreContext";
import { mockRecommendations } from "@/app/data/recommendations";
import { saveSystemData } from "@/app/lib/systemSaveApi";

export default function ResultsPage() {
  const router = useRouter();
  const store = useAppStore();

  const [liked, setLiked] = useState<string[]>([]);

  useEffect(() => {
    if (!store.requirements && !store.prediction && store.recommendations.length === 0) {
      return;
    }

    const payload = {
      requirements: store.requirements,
      occasion: store.occasion,
      gender: store.gender,
      colorPreference: store.colorPreference,
      prediction: store.prediction,
      recommendations: store.recommendations.map((item) => ({
        id: item.id,
        name: item.name,
        category: item.category,
        description: item.description,
        matchReason: item.matchReason,
        image: item.image,
        price: item.price,
        rating: item.rating,
        tags: item.tags,
        styleTips: item.styleTips,
        colors: item.colors,
        material: item.material,
        occasion: item.occasion,
        weather: item.weather,
      })),
      bodyMeasurements: store.bodyMeasurements,
      metadata: {
        view: "results",
      },
    };

    void saveSystemData(payload).catch(() => undefined);
  }, [store.requirements, store.occasion, store.gender, store.colorPreference, store.prediction, store.recommendations, store.bodyMeasurements]);

  const recommendations = (
    store.recommendations.length > 0
      ? store.recommendations
      : mockRecommendations
  ).map((item) => normalizeRecommendation(item as RecommendationLike));

  const toggleLike = (id: string) => {
    setLiked((prev) =>
      prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id],
    );
  };

  const summary = [
    store.prediction?.color,
    store.prediction?.usage,
    store.prediction?.articleType,
  ]
    .filter(Boolean)
    .join(" · ");

  return (
    <div className="min-h-screen w-full bg-white flex flex-col">
      <SiteNav
        backHref="/input"
        right={
          <Button
            onClick={() => router.push("/input")}
            variant="ghost"
            className="flex items-center gap-1.5 text-[#888] hover:text-[#111] transition-colors h-auto p-0 rounded-none bg-transparent hover:bg-transparent"
            style={SANS}
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span className="text-xs tracking-[0.1em] hidden md:block">
              NEW SEARCH
            </span>
          </Button>
        }
      />

      {/* CONTENT */}
      <div className="max-w-6xl mx-auto w-full px-6 md:px-12 py-12">
        {/* HEADER */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-10 text-center"
        >
          <p
            className="text-[10px] tracking-[0.3em] text-[#aaa] mb-3"
            style={SANS}
          >
            AI ANALYSIS COMPLETE
          </p>

          <h1
            className="text-4xl md:text-5xl text-[#111] tracking-wide mb-4"
            style={{
              ...SERIF,
              fontWeight: 300,
            }}
          >
            Your Curated Looks
          </h1>

          <p
            className="text-sm text-[#888] max-w-lg mx-auto italic mb-2"
            style={{
              ...SERIF,
              fontWeight: 300,
            }}
          >
            "{store.requirements}"
          </p>

          {summary && (
            <p
              className="text-[10px] tracking-[0.2em] text-[#bbb]"
              style={SANS}
            >
              {summary.toUpperCase()}
            </p>
          )}
        </motion.div>

        {/* GRID */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
          {recommendations.map((item, i) => (
            <motion.div
              key={item.id}
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{
                delay: 0.1 + i * 0.08,
              }}
            >
              <RecommendationCard
                item={item}
                liked={liked.includes(item.id)}
                onLike={() => toggleLike(item.id)}
                onView={() => router.push(`/detail/${item.id}`)}
              />
            </motion.div>
          ))}
        </div>

        {/* BUTTON */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="flex justify-center border-t border-[#e8e8e8] pt-10"
        >
          <Button
            onClick={() => router.push("/input")}
            variant="outline"
            className="flex items-center gap-2 border border-[#111] text-[#111] px-8 py-3 text-xs tracking-[0.2em] rounded-none h-auto bg-transparent hover:bg-[#111] hover:text-white transition-all duration-300"
            style={SANS}
          >
            TRY ANOTHER SEARCH
            <ArrowUpRight className="w-3.5 h-3.5" />
          </Button>
        </motion.div>
      </div>
    </div>
  );
}
