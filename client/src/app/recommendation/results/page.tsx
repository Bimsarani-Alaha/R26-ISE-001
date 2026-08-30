"use client";

import { ArrowUpRight, RotateCcw, Star } from "lucide-react";
import { motion } from "motion/react";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { SiteNav } from "@/app/components/SiteNav";
import { SANS, SERIF } from "@/app/components/typography";
import { Badge } from "@/app/components/ui/badge";
import { Button } from "@/app/components/ui/button";
import { Card } from "@/app/components/ui/card";
import { useAppStore } from "@/app/context/AppStoreContext";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ||
  "http://localhost:8000";

export default function RecommendationResultsPage() {
  const router = useRouter();
  const { productResults, requirements, gender, size } = useAppStore();
  const [liked, setLiked] = useState<string[]>([]);

  const toggleLike = (id: string) => {
    setLiked((prev) =>
      prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id],
    );
  };

  const getImageUrl = (imagePath: string) => {
    if (!imagePath) return "";
    if (imagePath.startsWith("http")) return imagePath;
    const cleaned = imagePath.replace("Images/", "").replace("images/", "");
    return `${API_BASE_URL}/fashion-recommendation/images/${cleaned}`;
  };

  if (productResults.length === 0) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="text-center">
          <p className="text-[#888] mb-4" style={SANS}>
            No recommendations found
          </p>
          <button
            type="button"
            onClick={() => router.push("/recommendation")}
            className="text-[#111] underline underline-offset-2 text-sm"
            style={SANS}
          >
            ← Start New Search
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen w-full bg-white flex flex-col">
      <SiteNav
        backHref="/recommendation"
        right={
          <Button
            onClick={() => router.push("/recommendation")}
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
            &quot;{requirements}&quot;
          </p>

          <p
            className="text-[10px] tracking-[0.2em] text-[#bbb]"
            style={SANS}
          >
            {gender.toUpperCase()} · SIZE {size.toUpperCase()} ·{" "}
            {productResults.length} RESULTS
          </p>
        </motion.div>

        {/* GRID */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
          {productResults.map((item, i) => (
            <motion.div
              key={item.product_id}
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{
                delay: 0.1 + i * 0.08,
              }}
            >
              <Card
                className="group cursor-pointer border-0 rounded-none bg-transparent gap-0"
                onClick={() => router.push(`/recommendation/${item.product_id}`)}
              >
                {/* IMAGE */}
                <div className="relative overflow-hidden aspect-[3/4] bg-[#f5f5f5] mb-4">
                  <img
                    src={getImageUrl(item.image_path)}
                    alt={item.article_type}
                    className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105"
                  />

                  {/* LIKE BUTTON */}
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      toggleLike(item.product_id);
                    }}
                    className={`absolute top-3 right-3 w-8 h-8 flex items-center justify-center transition-all duration-200 bg-white/80 backdrop-blur-sm ${
                      liked.includes(item.product_id)
                        ? "opacity-100"
                        : "opacity-0 group-hover:opacity-100"
                    }`}
                  >
                    <span
                      className={`w-4 h-4 transition-colors ${
                        liked.includes(item.product_id)
                          ? "fill-[#111] text-[#111]"
                          : "text-[#555]"
                      }`}
                    >
                      ♥
                    </span>
                  </button>

                  {/* MATCH SCORE */}
                  <div className="absolute top-3 left-3">
                    <Badge
                      variant="outline"
                      className="text-[9px] tracking-[0.2em] text-white bg-black/50 backdrop-blur-sm px-2 py-1 rounded-none border-0"
                      style={SANS}
                    >
                      {Math.round(item.match_score * 100)}% MATCH
                    </Badge>
                  </div>

                  {/* CATEGORY */}
                  <div className="absolute bottom-3 left-3">
                    <Badge
                      variant="outline"
                      className="text-[9px] tracking-[0.2em] text-white bg-black/50 backdrop-blur-sm px-2 py-1 rounded-none border-0"
                      style={SANS}
                    >
                      {item.article_type.toUpperCase()}
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
                      {item.article_type} · {item.base_colour}
                    </h3>

                    <div className="flex items-center gap-0.5 flex-shrink-0 pt-0.5">
                      <Star className="w-3 h-3 fill-[#111] text-[#111]" />
                      <span className="text-xs text-[#555]" style={SANS}>
                        {item.match_score.toFixed(2)}
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
                    {item.style} · {item.base_colour}
                  </p>

                  {/* TAGS */}
                  <div className="flex flex-wrap gap-1.5 mt-2">
                    <Badge
                      variant="outline"
                      className="text-[9px] tracking-[0.15em] text-[#999] border border-[#e5e5e5] px-2 py-0.5 rounded-none"
                      style={SANS}
                    >
                      {item.base_colour.toUpperCase()}
                    </Badge>

                    <Badge
                      variant="outline"
                      className="text-[9px] tracking-[0.15em] text-[#999] border border-[#e5e5e5] px-2 py-0.5 rounded-none"
                      style={SANS}
                    >
                      {item.style.toUpperCase()}
                    </Badge>

                    {item.price && (
                      <Badge
                        variant="outline"
                        className="text-[9px] tracking-[0.15em] text-[#999] border border-[#e5e5e5] px-2 py-0.5 rounded-none"
                        style={SANS}
                      >
                        ${item.price.toFixed(0)}
                      </Badge>
                    )}
                  </div>

                  {/* VIEW */}
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      router.push(`/recommendation/${item.product_id}`);
                    }}
                    className="mt-3 text-[10px] tracking-[0.15em] text-[#888] hover:text-[#111] transition-colors underline underline-offset-2"
                    style={SANS}
                  >
                    VIEW MORE
                  </button>
                </div>
              </Card>
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
            onClick={() => router.push("/recommendation")}
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
