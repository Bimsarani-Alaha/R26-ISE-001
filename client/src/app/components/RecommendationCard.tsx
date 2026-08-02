import { Heart, Star } from "lucide-react";
import { SANS, SERIF } from "@/app/components/typography";
import { Badge } from "@/app/components/ui/badge";
import { Card } from "@/app/components/ui/card";

export type RecommendationViewModel = {
  id: string;
  title: string;
  category: string;
  color: string;
  usage: string;
  image: string;
  similarity: number;
};

export type RecommendationLike = {
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

export function normalizeRecommendation(
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

export function RecommendationCard({
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
