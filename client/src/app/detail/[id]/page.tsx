"use client";

import {
  ArrowUpRight,
  CheckCircle,
  Heart,
  Lightbulb,
  Package,
  ShoppingBag,
  Star,
  Tag,
} from "lucide-react";
import { motion } from "motion/react";
import { useParams, useRouter } from "next/navigation";
import { useState } from "react";
import { RelatedItemCard } from "@/app/components/RelatedItemCard";
import { SiteNav } from "@/app/components/SiteNav";
import { SANS, SERIF } from "@/app/components/typography";
import { Badge } from "@/app/components/ui/badge";
import { Button } from "@/app/components/ui/button";
import { Card } from "@/app/components/ui/card";
import { Separator } from "@/app/components/ui/separator";
import { useAppStore } from "@/app/context/AppStoreContext";
import { mockRecommendations } from "@/app/data/recommendations";

const colorDots: Record<string, string> = {
  White: "#f8f8f8",
  Beige: "#d4b483",
  "Light Blue": "#93c5fd",
  "Floral Blue": "#60a5fa",
  "Floral Pink": "#f472b6",
  Yellow: "#fbbf24",
  Navy: "#1e3a5f",
  Charcoal: "#4b5563",
  "Light Grey": "#d1d5db",
  "Sage Green": "#a8b5a0",
  "Dusty Rose": "#d4a5a5",
  "Sky Blue": "#87ceeb",
  Grey: "#9ca3af",
  Black: "#1a1a1a",
};

export default function DetailPage() {
  const { id } = useParams();
  const router = useRouter();
  const store = useAppStore();
  const [liked, setLiked] = useState(false);
  const [selectedColor, setSelectedColor] = useState(0);
  const [addedToBag, setAddedToBag] = useState(false);

  const itemId = Array.isArray(id) ? id[0] : id;

  const recommendationSource =
    store.recommendations.length > 0
      ? store.recommendations
      : mockRecommendations;
  const item =
    recommendationSource.find((r) => r.id === itemId) ||
    mockRecommendations.find((r) => r.id === itemId);
  const related = recommendationSource
    .filter((r) => r.id !== itemId)
    .slice(0, 3);

  if (!item) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="text-center">
          <p className="text-[#888] mb-4" style={SANS}>
            Item not found
          </p>
          <button
            type="button"
            onClick={() => router.push("/results")}
            className="text-[#111] underline underline-offset-2 text-sm"
            style={SANS}
          >
            ← Back to Results
          </button>
        </div>
      </div>
    );
  }

  const handleAddToBag = () => {
    setAddedToBag(true);
    setTimeout(() => setAddedToBag(false), 2500);
  };

  const originalPrice = (parseFloat(item.price.replace("$", "")) * 1.3).toFixed(
    2,
  );

  return (
    <div className="min-h-screen w-full bg-white flex flex-col">
      <SiteNav
        backHref="/results"
        backLabel="BACK TO RESULTS"
        right={<div className="w-32" />}
      />

      <div className="max-w-5xl mx-auto w-full px-6 md:px-12 py-12">
        {/* Main Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 mb-16">
          {/* Left: Image */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6 }}
            className="relative"
          >
            <div className="relative aspect-[3/4] overflow-hidden bg-[#f5f5f5]">
              <img
                src={item.image}
                alt={item.name}
                className="w-full h-full object-cover"
              />
              {/* Like */}
              <button
                type="button"
                onClick={() => setLiked(!liked)}
                className="absolute top-4 right-4 w-9 h-9 bg-white/90 backdrop-blur-sm flex items-center justify-center transition-all duration-200 hover:bg-white"
              >
                <Heart
                  className={`w-4 h-4 transition-colors ${liked ? "fill-[#111] text-[#111]" : "text-[#888]"}`}
                />
              </button>

              {/* AI Match badge */}
              <div className="absolute bottom-0 left-0 right-0 bg-white/95 backdrop-blur-sm border-t border-[#e8e8e8] px-4 py-3">
                <div className="flex items-start gap-2">
                  <CheckCircle className="w-4 h-4 text-[#111] flex-shrink-0 mt-0.5" />
                  <p
                    className="text-xs text-[#555] leading-relaxed"
                    style={SANS}
                  >
                    {item.matchReason}
                  </p>
                </div>
              </div>
            </div>
          </motion.div>

          {/* Right: Info */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="flex flex-col"
          >
            {/* Category */}
            <p
              className="text-[10px] tracking-[0.3em] text-[#aaa] mb-3"
              style={SANS}
            >
              {item.category.toUpperCase()}
            </p>

            {/* Name */}
            <h1
              className="text-4xl text-[#111] tracking-wide mb-3 leading-tight"
              style={{ ...SERIF, fontWeight: 300 }}
            >
              {item.name}
            </h1>

            {/* Rating */}
            <div className="flex items-center gap-2 mb-5">
              <div className="flex items-center gap-0.5">
                {[1, 2, 3, 4, 5].map((star) => (
                  <Star
                    key={star}
                    className={`w-3.5 h-3.5 ${
                      star <= Math.floor(item.rating)
                        ? "fill-[#111] text-[#111]"
                        : "text-[#ddd]"
                    }`}
                  />
                ))}
              </div>
              <span className="text-sm text-[#777]" style={SANS}>
                {item.rating} / 5.0
              </span>
            </div>

            {/* Price */}
            <div className="flex items-baseline gap-3 pb-6">
              <span
                className="text-3xl text-[#111]"
                style={{ ...SERIF, fontWeight: 400 }}
              >
                {item.price}
              </span>
              <span className="text-sm text-[#bbb] line-through" style={SANS}>
                ${originalPrice}
              </span>
              <Badge
                variant="outline"
                className="text-xs tracking-[0.1em] text-[#777] border border-[#ddd] px-2 py-0.5 rounded-none"
                style={SANS}
              >
                23% OFF
              </Badge>
            </div>

            <Separator className="bg-[#e8e8e8] mb-6" />

            {/* Description */}
            <p
              className="text-sm text-[#666] leading-relaxed mb-6"
              style={{ ...SANS, fontWeight: 300 }}
            >
              {item.description}
            </p>

            {/* Color */}
            <div className="mb-6">
              <div className="flex items-center justify-between mb-3">
                <span
                  className="text-[10px] tracking-[0.25em] text-[#aaa]"
                  style={SANS}
                >
                  COLOUR
                </span>
                <span className="text-xs text-[#666]" style={SANS}>
                  {item.colors[selectedColor]}
                </span>
              </div>
              <div className="flex gap-2.5">
                {item.colors.map((color, i) => (
                  <button
                    key={color}
                    type="button"
                    onClick={() => setSelectedColor(i)}
                    title={color}
                    className={`w-7 h-7 transition-all duration-200 ${
                      selectedColor === i
                        ? "ring-1 ring-offset-2 ring-[#111]"
                        : "ring-1 ring-[#e5e5e5] hover:ring-[#999]"
                    }`}
                    style={{ backgroundColor: colorDots[color] || "#ccc" }}
                  />
                ))}
              </div>
            </div>

            {/* Details grid */}
            <Card className="grid grid-cols-2 gap-0 border border-[#e8e8e8] rounded-none bg-transparent text-[#555] mb-6">
              {[
                {
                  icon: <Package className="w-3.5 h-3.5 text-[#aaa]" />,
                  label: "MATERIAL",
                  value: item.material,
                },
                {
                  icon: <Tag className="w-3.5 h-3.5 text-[#aaa]" />,
                  label: "OCCASION",
                  value: item.occasion,
                },
              ].map((detail, i) => (
                <div
                  key={detail.label}
                  className={`p-4 ${i === 0 ? "border-r border-[#e8e8e8]" : ""}`}
                >
                  <div className="flex items-center gap-1.5 mb-1.5">
                    {detail.icon}
                    <span
                      className="text-[9px] tracking-[0.2em] text-[#aaa]"
                      style={SANS}
                    >
                      {detail.label}
                    </span>
                  </div>
                  <p className="text-xs text-[#555]" style={SANS}>
                    {detail.value}
                  </p>
                </div>
              ))}
            </Card>

            {/* Style Tips */}
            <Card className="border border-[#e8e8e8] rounded-none bg-transparent gap-0 p-4 mb-8">
              <div className="flex items-center gap-2 mb-3">
                <Lightbulb className="w-3.5 h-3.5 text-[#aaa]" />
                <span
                  className="text-[10px] tracking-[0.25em] text-[#aaa]"
                  style={SANS}
                >
                  STYLE TIPS
                </span>
              </div>
              <ul className="space-y-2">
                {item.styleTips.map((tip) => (
                  <li key={tip} className="flex items-start gap-2">
                    <span className="w-px h-full bg-[#e5e5e5] mt-1.5 flex-shrink-0 self-stretch" />
                    <span
                      className="text-xs text-[#777] leading-relaxed"
                      style={{ ...SANS, fontWeight: 300 }}
                    >
                      {tip}
                    </span>
                  </li>
                ))}
              </ul>
            </Card>

            {/* Actions */}
            <div className="flex gap-3">
              <Button
                type="button"
                onClick={handleAddToBag}
                variant="default"
                className={`flex-1 py-3.5 text-xs tracking-[0.2em] flex items-center justify-center gap-2 transition-all duration-300 rounded-none h-auto ${
                  addedToBag
                    ? "bg-[#555] text-white hover:bg-[#555]"
                    : "bg-[#111] text-white hover:bg-[#333] active:scale-[0.98]"
                }`}
                style={SANS}
              >
                {addedToBag ? (
                  <>
                    <CheckCircle className="w-4 h-4" />
                    ADDED TO BAG
                  </>
                ) : (
                  <>
                    <ShoppingBag className="w-4 h-4" />
                    ADD TO BAG
                  </>
                )}
              </Button>
              <Button
                type="button"
                onClick={() => setLiked(!liked)}
                variant="outline"
                className={`w-14 flex items-center justify-center rounded-none h-auto ${
                  liked
                    ? "border-[#111] bg-[#111] hover:bg-[#111]"
                    : "border-[#ddd] hover:border-[#999] hover:bg-transparent"
                }`}
              >
                <Heart
                  className={`w-4 h-4 ${liked ? "fill-white text-white" : "text-[#888]"}`}
                />
              </Button>
            </div>
          </motion.div>
        </div>

        {/* You Might Also Like */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
        >
          <div className="flex items-center justify-between mb-8 border-t border-[#e8e8e8] pt-10">
            <h2
              className="text-2xl text-[#111] tracking-wide"
              style={{ ...SERIF, fontWeight: 300 }}
            >
              You Might Also Like
            </h2>
            <button
              type="button"
              onClick={() => router.push("/results")}
              className="flex items-center gap-1.5 text-[10px] tracking-[0.2em] text-[#888] hover:text-[#111] transition-colors border-b border-transparent hover:border-[#111] pb-0.5"
              style={SANS}
            >
              VIEW ALL
              <ArrowUpRight className="w-3 h-3" />
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {related.map((rel, i) => (
              <RelatedItemCard key={rel.id} item={rel} delay={0.5 + i * 0.1} />
            ))}
          </div>
        </motion.div>
      </div>
    </div>
  );
}
