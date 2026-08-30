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
import { SiteNav } from "@/app/components/SiteNav";
import { SANS, SERIF } from "@/app/components/typography";
import { Badge } from "@/app/components/ui/badge";
import { Button } from "@/app/components/ui/button";
import { Card } from "@/app/components/ui/card";
import { Separator } from "@/app/components/ui/separator";
import { useAppStore } from "@/app/context/AppStoreContext";
import {
  getStylistTips,
  type GetStylistResponse,
} from "@/app/lib/aiStyleApi";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ||
  "http://localhost:8000";

const colorDots: Record<string, string> = {
  White: "#f8f8f8",
  Beige: "#d4b483",
  "Light Blue": "#93c5fd",
  Black: "#1a1a1a",
  Red: "#ef4444",
  Blue: "#3b82f6",
  Green: "#22c55e",
  Yellow: "#fbbf24",
  Pink: "#f472b6",
  Navy: "#1e3a5f",
  Grey: "#9ca3af",
  Charcoal: "#4b5563",
  Maroon: "#7f1d1d",
  Orange: "#f97316",
  Purple: "#a855f7",
  Teal: "#14b8a6",
  Cream: "#fef3c7",
  Gold: "#f59e0b",
  Silver: "#c0c0c0",
  Peach: "#fed7aa",
  Lavender: "#c4b5fd",
  Coral: "#fb923c",
  Olive: "#65a30d",
  Burgundy: "#881337",
  Ivory: "#fffff0",
};

export default function RecommendationDetailPage() {
  const { id } = useParams();
  const router = useRouter();
  const { productResults, requirements, gender, size } = useAppStore();
  const [liked, setLiked] = useState(false);
  const [addedToBag, setAddedToBag] = useState(false);
  const [stylistTips, setStylistTips] = useState<GetStylistResponse | null>(
    null,
  );
  const [loadingTips, setLoadingTips] = useState(false);
  const [tipsError, setTipsError] = useState("");

  const itemId = Array.isArray(id) ? id[0] : id;

  const item = productResults.find((r) => r.product_id === itemId);

  if (!item) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="text-center">
          <p className="text-[#888] mb-4" style={SANS}>
            Item not found
          </p>
          <button
            type="button"
            onClick={() => router.push("/recommendation/results")}
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

  const handleGetStylistTips = async () => {
    if (stylistTips) {
      setStylistTips(null);
      return;
    }

    setLoadingTips(true);
    setTipsError("");

    try {
      const tips = await getStylistTips({
        gender,
        size,
        requirements,
        product_id: itemId,
      });
      setStylistTips(tips);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Failed to load styling tips";
      setTipsError(message);
    } finally {
      setLoadingTips(false);
    }
  };

  const getImageUrl = (imagePath: string) => {
    if (!imagePath) return "";
    if (imagePath.startsWith("http")) return imagePath;
    const cleaned = imagePath.replace("Images/", "").replace("images/", "");
    return `${API_BASE_URL}/fashion-recommendation/images/${cleaned}`;
  };

  const originalPrice = item.price
    ? (item.price * 1.3).toFixed(2)
    : null;

  return (
    <div className="min-h-screen w-full bg-white flex flex-col">
      <SiteNav
        backHref="/recommendation/results"
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
                src={getImageUrl(item.image_path)}
                alt={item.article_type}
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
                    {item.explanation}
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
              {item.article_type}
            </h1>

            {/* Match Score */}
            <div className="flex items-center gap-2 mb-5">
              <div className="flex items-center gap-0.5">
                {[1, 2, 3, 4, 5].map((star) => (
                  <Star
                    key={star}
                    className={`w-3.5 h-3.5 ${
                      star <= Math.floor(item.match_score * 5)
                        ? "fill-[#111] text-[#111]"
                        : "text-[#ddd]"
                    }`}
                  />
                ))}
              </div>
              <span className="text-sm text-[#777]" style={SANS}>
                {(item.match_score * 5).toFixed(1)} / 5.0
              </span>
            </div>

            {/* Price */}
            {item.price && (
              <div className="flex items-baseline gap-3 pb-6">
                <span
                  className="text-3xl text-[#111]"
                  style={{ ...SERIF, fontWeight: 400 }}
                >
                  ${item.price.toFixed(2)}
                </span>
                {originalPrice && (
                  <span
                    className="text-sm text-[#bbb] line-through"
                    style={SANS}
                  >
                    ${originalPrice}
                  </span>
                )}
              </div>
            )}

            <Separator className="bg-[#e8e8e8] mb-6" />

            {/* Description */}
            <p
              className="text-sm text-[#666] leading-relaxed mb-6"
              style={{ ...SANS, fontWeight: 300 }}
            >
              {item.description}
            </p>

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
                  value: item.occasion || "N/A",
                },
                {
                  icon: <Tag className="w-3.5 h-3.5 text-[#aaa]" />,
                  label: "PATTERN",
                  value: item.pattern,
                },
                {
                  icon: <Tag className="w-3.5 h-3.5 text-[#aaa]" />,
                  label: "SIZE",
                  value: item.selected_size,
                },
              ].map((detail, i) => (
                <div
                  key={detail.label}
                  className={`p-4 ${i % 2 === 0 ? "border-r border-[#e8e8e8]" : ""} ${i < 2 ? "border-b border-[#e8e8e8]" : ""}`}
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

            {/* AI Stylist Tips Button */}
            <div className="mb-8">
              <Button
                type="button"
                onClick={handleGetStylistTips}
                disabled={loadingTips}
                variant="outline"
                className={`w-full py-3.5 text-xs tracking-[0.2em] flex items-center justify-center gap-2 transition-all duration-300 rounded-none h-auto ${
                  loadingTips
                    ? "bg-[#f0f0f0] text-[#ccc] border-[#ddd] cursor-not-allowed"
                    : stylistTips
                      ? "bg-[#111] text-white border-[#111] hover:bg-[#333]"
                      : "bg-white text-[#111] border-[#111] hover:bg-[#111] hover:text-white"
                }`}
                style={SANS}
              >
                {loadingTips ? (
                  <>
                    <motion.div
                      animate={{ rotate: 360 }}
                      transition={{
                        duration: 1,
                        repeat: Infinity,
                        ease: "linear",
                      }}
                      className="w-4 h-4 border-2 border-[#ccc] border-t-transparent rounded-full"
                    />
                    LOADING AI TIPS…
                  </>
                ) : stylistTips ? (
                  <>
                    <Lightbulb className="w-4 h-4" />
                    HIDE AI STYLING TIPS
                  </>
                ) : (
                  <>
                    <Lightbulb className="w-4 h-4" />
                    GET AI STYLING TIPS
                  </>
                )}
              </Button>
            </div>

            {/* AI Stylist Tips Display */}
            {stylistTips && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="mb-8"
              >
                <Card className="border border-[#e8e8e8] rounded-none bg-[#fafafa] gap-0 p-5">
                  <div className="flex items-center gap-2 mb-4">
                    <Lightbulb className="w-4 h-4 text-[#111]" />
                    <span
                      className="text-[10px] tracking-[0.25em] text-[#111]"
                      style={SANS}
                    >
                      AI STYLING TIPS
                    </span>
                  </div>

                  {/* Summary */}
                  {stylistTips.summary && (
                    <p
                      className="text-sm text-[#555] leading-relaxed mb-4 italic"
                      style={{ ...SERIF, fontWeight: 300 }}
                    >
                      &quot;{stylistTips.summary}&quot;
                    </p>
                  )}

                  {/* Accessories */}
                  {stylistTips.accessories.length > 0 && (
                    <div className="mb-4">
                      <p
                        className="text-[9px] tracking-[0.2em] text-[#aaa] mb-2"
                        style={SANS}
                      >
                        ACCESSORIES
                      </p>
                      <ul className="space-y-1">
                        {stylistTips.accessories.map((tip) => (
                          <li
                            key={tip}
                            className="text-xs text-[#666] flex items-start gap-2"
                            style={SANS}
                          >
                            <span className="text-[#ccc]">·</span>
                            {tip}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Footwear */}
                  {stylistTips.footwear.length > 0 && (
                    <div className="mb-4">
                      <p
                        className="text-[9px] tracking-[0.2em] text-[#aaa] mb-2"
                        style={SANS}
                      >
                        FOOTWEAR
                      </p>
                      <ul className="space-y-1">
                        {stylistTips.footwear.map((tip) => (
                          <li
                            key={tip}
                            className="text-xs text-[#666] flex items-start gap-2"
                            style={SANS}
                          >
                            <span className="text-[#ccc]">·</span>
                            {tip}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Color Combinations */}
                  {stylistTips.color_combinations.length > 0 && (
                    <div className="mb-4">
                      <p
                        className="text-[9px] tracking-[0.2em] text-[#aaa] mb-2"
                        style={SANS}
                      >
                        COLOR COMBINATIONS
                      </p>
                      <div className="flex flex-wrap gap-1.5">
                        {stylistTips.color_combinations.map((color) => (
                          <Badge
                            key={color}
                            variant="outline"
                            className="text-[9px] tracking-[0.1em] text-[#666] border border-[#ddd] px-2 py-0.5 rounded-none"
                            style={SANS}
                          >
                            {color}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Layering */}
                  {stylistTips.layering.length > 0 && (
                    <div className="mb-4">
                      <p
                        className="text-[9px] tracking-[0.2em] text-[#aaa] mb-2"
                        style={SANS}
                      >
                        LAYERING
                      </p>
                      <ul className="space-y-1">
                        {stylistTips.layering.map((tip) => (
                          <li
                            key={tip}
                            className="text-xs text-[#666] flex items-start gap-2"
                            style={SANS}
                          >
                            <span className="text-[#ccc]">·</span>
                            {tip}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Occasion Tip */}
                  {stylistTips.occasion_tip && (
                    <div className="mb-4">
                      <p
                        className="text-[9px] tracking-[0.2em] text-[#aaa] mb-2"
                        style={SANS}
                      >
                        OCCASION TIP
                      </p>
                      <p
                        className="text-xs text-[#666] italic"
                        style={{ ...SERIF, fontWeight: 300 }}
                      >
                        {stylistTips.occasion_tip}
                      </p>
                    </div>
                  )}

                  {/* Complementary Items */}
                  {stylistTips.complementary_items.length > 0 && (
                    <div>
                      <p
                        className="text-[9px] tracking-[0.2em] text-[#aaa] mb-2"
                        style={SANS}
                      >
                        COMPLEMENTARY ITEMS
                      </p>
                      <div className="flex flex-wrap gap-1.5">
                        {stylistTips.complementary_items.map((item) => (
                          <Badge
                            key={item}
                            variant="outline"
                            className="text-[9px] tracking-[0.1em] text-[#666] border border-[#ddd] px-2 py-0.5 rounded-none"
                            style={SANS}
                          >
                            {item}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </Card>
              </motion.div>
            )}

            {/* Tips Error */}
            {tipsError && (
              <motion.div
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                className="mb-8"
              >
                <Card className="border border-[#e8e8e8] bg-[#fafafa] rounded-none gap-0 p-4">
                  <p
                    className="text-xs tracking-[0.2em] text-[#b33] mb-1"
                    style={SANS}
                  >
                    TIPS UNAVAILABLE
                  </p>
                  <p className="text-xs text-[#888]" style={SANS}>
                    {tipsError}
                  </p>
                </Card>
              </motion.div>
            )}

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
      </div>
    </div>
  );
}
