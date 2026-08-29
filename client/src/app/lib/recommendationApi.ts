import type { ClothingItem } from "../data/recommendations";

export interface BackendPrediction {
  color: string;
  usage: string;
  articleType: string;
}

export interface BackendRecommendationRecord {
  productDisplayName: string;
  baseColour: string;
  usage: string;
  articleType: string;
  link?: string;
  score?: number;
}

export interface RecommendationResponse {
  prediction: BackendPrediction;
  recommendations: ClothingItem[];
}

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ||
  "http://localhost:8000";

const IMAGE_BY_CATEGORY: Record<string, string> = {
  Top: "https://images.unsplash.com/photo-1523398002811-999ca8dec234?auto=format&fit=crop&w=1080&q=80",
  Bottom:
    "https://images.unsplash.com/photo-1542272604-787c3835535d?auto=format&fit=crop&w=1080&q=80",
  Dress:
    "https://images.unsplash.com/photo-1496747611176-843222e1e57c?auto=format&fit=crop&w=1080&q=80",
  "Full Outfit":
    "https://images.unsplash.com/photo-1483985988355-763728e1935b?auto=format&fit=crop&w=1080&q=80",
};

function inferCategory(articleType: string) {
  const normalized = articleType.toLowerCase();

  if (/(dress|kurta|gown|saree|jumpsuit)/.test(normalized)) {
    return "Dress";
  }

  if (/(jean|pant|trouser|short|skirt|legging|bottom)/.test(normalized)) {
    return "Bottom";
  }

  if (/(set|coord|co-?ord|full outfit)/.test(normalized)) {
    return "Full Outfit";
  }

  return "Top";
}

function createMatchReason(
  record: BackendRecommendationRecord,
  prediction: BackendPrediction,
) {
  return `The model ranked this ${record.articleType.toLowerCase()} because it aligns with ${prediction.color}, ${prediction.usage}, and ${prediction.articleType}.`;
}

function createPrice(rank: number) {
  return `$${(49 + rank * 12).toFixed(2)}`;
}

export function toClothingItem(
  record: BackendRecommendationRecord,
  index: number,
  prediction: BackendPrediction,
): ClothingItem {
  const category = inferCategory(record.articleType);
  const color = record.baseColour || prediction.color;
  const image =
    record.link || IMAGE_BY_CATEGORY[category] || IMAGE_BY_CATEGORY.Top;

  return {
    id: `${record.productDisplayName}-${index}`,
    name: record.productDisplayName,
    category,
    description: `A ${color.toLowerCase()} ${record.articleType.toLowerCase()} suited for ${record.usage.toLowerCase()} wear.`,
    matchReason: createMatchReason(record, prediction),
    image,
    price: createPrice(index),
    rating: Math.max(4.2, 4.9 - index * 0.1),
    tags: [record.baseColour, record.usage, record.articleType].filter(Boolean),
    styleTips: [
      `Use this ${record.articleType.toLowerCase()} to build a polished ${record.usage.toLowerCase()} look.`,
      "Pair it with neutral accessories to keep the outfit balanced.",
      "Layer with a lightweight outerwear piece if you want more versatility.",
    ],
    colors: [color],
    material: "Model-curated recommendation",
    occasion: record.usage,
    weather: "All-Season",
  };
}

export async function fetchRecommendations(
  text: string,
): Promise<RecommendationResponse> {
  const response = await fetch(`${API_BASE_URL}/predict`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ text }),
  });

  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`);
  }

  const data = (await response.json()) as {
    prediction: BackendPrediction;
    recommendations: BackendRecommendationRecord[];
  };

  return {
    prediction: data.prediction,
    recommendations: data.recommendations.map((record, index) =>
      toClothingItem(record, index, data.prediction),
    ),
  };
}
