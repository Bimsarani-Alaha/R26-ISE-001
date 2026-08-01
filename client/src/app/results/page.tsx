"use client";

import { ArrowLeft, ArrowUpRight, Heart, RotateCcw, Star } from "lucide-react";
import { motion } from "motion/react";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { Badge } from "@/app/components/ui/badge";
import { Button } from "@/app/components/ui/button";
import { Card } from "@/app/components/ui/card";
import { useAppStore } from "@/app/context/AppStoreContext";
import { mockRecommendations } from "@/app/data/recommendations";

const SERIF = { fontFamily: "'Cormorant Garamond', serif" };
const SANS = { fontFamily: "'Inter', sans-serif" };

type RecommendationViewModel = {
  id: string;
  title: string;
  category: string;
  color: string;
  usage: string;
  image: string;
  similarity: number;
};

type RecommendationLike = {
  id?: string;
  productDisplayName?: string;
  name?: string;
  articleType?: string;
  category?: string;
  baseColour?: string;
  colors?: string[];
  usage?: string;
  occasion?: string;
  weather?: string;
  link?: string;
  image?: string;
  similarity?: number;
  rating?: number;
};

function normalizeRecommendation(
  item: RecommendationLike,
): RecommendationViewModel {
  return {
    id:
      item.id ??
      `${item.productDisplayName ?? item.name ?? "item"}-${Math.random()}`,
    title: item.productDisplayName ?? item.name ?? "Styled Recommendation",
    category: item.articleType ?? item.category ?? "Feature",
    color: item.baseColour ?? item.colors?.[0] ?? "Neutral",
    usage: item.usage ?? item.occasion ?? item.weather ?? "Everyday",
    image: item.link ?? item.image ?? "",
    similarity: item.similarity ?? item.rating ?? 4.8,
  };
}

export default function ResultsPage() {
  const router = useRouter();
  const store = useAppStore();

  const [liked, setLiked] = useState<string[]>([]);

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
      {/* NAVBAR */}
      <nav className="flex items-center justify-between px-8 md:px-16 py-6 border-b border-[#e8e8e8]">
        <button
          type="button"
          onClick={() => router.push("/input")}
          className="flex items-center gap-2 text-[#888] hover:text-[#111] transition-colors"
          style={SANS}
        >
          <ArrowLeft className="w-4 h-4" />
          <span className="text-xs tracking-[0.1em]">BACK</span>
        </button>

        <span
          className="text-xl tracking-widest text-[#111]"
          style={{
            ...SERIF,
            fontWeight: 300,
            letterSpacing: "0.3em",
          }}
        >
          STYLE AI
        </span>

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
      </nav>

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

function RecommendationCard({
  item,
  liked,
  onLike,
  onView,
}: {
  item: RecommendationViewModel;
  liked: boolean;
  onLike: () => void;
  onView: () => void;
}) {
  return (
    <Card
      className="group cursor-pointer border-0 rounded-none bg-transparent gap-0"
      onClick={onView}
    >
      {/* IMAGE */}
      <div className="relative overflow-hidden aspect-[3/4] bg-[#f5f5f5] mb-4">
        <img
          src={item.image}
          alt={item.title}
          className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105"
        />

        {/* LIKE BUTTON */}
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            onLike();
          }}
          className={`absolute top-3 right-3 w-8 h-8 flex items-center justify-center transition-all duration-200 bg-white/80 backdrop-blur-sm ${
            liked ? "opacity-100" : "opacity-0 group-hover:opacity-100"
          }`}
        >
          <Heart
            className={`w-4 h-4 transition-colors ${
              liked ? "fill-[#111] text-[#111]" : "text-[#555]"
            }`}
          />
        </button>

        {/* CATEGORY */}
        <div className="absolute bottom-3 left-3">
          <Badge
            variant="outline"
            className="text-[9px] tracking-[0.2em] text-white bg-black/50 backdrop-blur-sm px-2 py-1 rounded-none border-0"
            style={SANS}
          >
            {item.category.toUpperCase()}
          </Badge>
        </div>
      </div>

      {/* INFO */}
      <div>
        <div className="flex items-start justify-between gap-2 mb-1.5">
          <h3
            className="text-sm tracking-wide text-[#111] leading-snug"
            style={{
              ...SERIF,
              fontWeight: 500,
            }}
          >
            {item.title}
          </h3>

          <div className="flex items-center gap-0.5 flex-shrink-0 pt-0.5">
            <Star className="w-3 h-3 fill-[#111] text-[#111]" />
            <span className="text-xs text-[#555]" style={SANS}>
              {item.similarity.toFixed(2)}
            </span>
          </div>
        </div>

        <p
          className="text-xs text-[#999] mb-2 line-clamp-2 leading-relaxed"
          style={{
            ...SANS,
            fontWeight: 300,
          }}
        >
          {item.color} • {item.usage}
        </p>

        {/* TAGS */}
        <div className="flex flex-wrap gap-1.5 mt-2">
          <Badge
            variant="outline"
            className="text-[9px] tracking-[0.15em] text-[#999] border border-[#e5e5e5] px-2 py-0.5 rounded-none"
            style={SANS}
          >
            {item.color.toUpperCase()}
          </Badge>

          <Badge
            variant="outline"
            className="text-[9px] tracking-[0.15em] text-[#999] border border-[#e5e5e5] px-2 py-0.5 rounded-none"
            style={SANS}
          >
            {item.usage.toUpperCase()}
          </Badge>
        </div>

        {/* VIEW */}
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            onView();
          }}
          className="mt-3 text-[10px] tracking-[0.15em] text-[#888] hover:text-[#111] transition-colors underline underline-offset-2"
          style={SANS}
        >
          VIEW MORE
        </button>
      </div>
    </Card>
  );
}
