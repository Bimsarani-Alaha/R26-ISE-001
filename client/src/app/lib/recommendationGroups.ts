import type { ProductResult } from "./aiStyleApi";

type ResultGroup = { title: string; items: ProductResult[] };
const occasionOrder = ["Wedding", "Party", "Casual", "Formal"];
const unknownOccasions = new Set(["", "unknown", "n/a", "na", "none", "null", "nan"]);

function byOccasion(items: ProductResult[]): ResultGroup[] {
  const groups = new Map<string, ProductResult[]>();
  for (const item of items) {
    const rawOccasion = (item.occasion ?? "").trim().toLowerCase();
    const occasions = new Set(
      (unknownOccasions.has(rawOccasion) ? "" : rawOccasion)
        .split(/[,/;]|\band\b|&/i)
        .map((value) => value.trim().toLowerCase())
        .filter((value) => !unknownOccasions.has(value))
        .map((value) => value.replace(/\b\w/g, (letter) => letter.toUpperCase())),
    );
    if (!occasions.size) occasions.add("Occasion unspecified");
    for (const occasion of occasions) {
      const group = groups.get(occasion) ?? [];
      group.push(item);
      groups.set(occasion, group);
    }
  }
  const order = (occasion: string) => {
    const index = occasionOrder.indexOf(occasion);
    return index >= 0 ? index : occasion === "Occasion unspecified" ? 100 : 10;
  };
  return [...groups.entries()]
    .sort(([a], [b]) => order(a) - order(b) || a.localeCompare(b))
    .map(([title, products]) => ({ title, items: products }));
}

export function buildRecommendationGroups(
  products: ProductResult[],
  occasionUsed: string[] | null,
): ResultGroup[] {
  const primary = products.filter((item) => item.match_category === "exact");
  if (!occasionUsed?.length) {
    return byOccasion(primary);
  }
  return [
    { title: "Primary Recommendations", items: primary },
  ].filter((group) => group.items.length > 0);
}
