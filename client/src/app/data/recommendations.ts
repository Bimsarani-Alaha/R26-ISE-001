export interface ClothingItem {
  id: string;
  name: string;
  category: string;
  description: string;
  matchReason: string;
  image: string;
  price: string;
  rating: number;
  tags: string[];
  styleTips: string[];
  colors: string[];
  material: string;
  occasion: string;
  weather: string;
}

export const mockRecommendations: ClothingItem[] = [
  {
    id: "1",
    name: "Light Cotton Linen Shirt",
    category: "Top",
    description:
      "A breathable, relaxed-fit cotton-linen blend shirt perfect for warm days. Features a classic collar with a modern slim cut.",
    matchReason:
      "Matches your need for a casual, breathable outfit in hot weather. The linen fabric wicks moisture and allows air circulation.",
    image:
      "https://images.unsplash.com/photo-1713881587420-113c1c43e28a?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&w=1080",
    price: "$45.99",
    rating: 4.8,
    tags: ["Casual", "Breathable"],
    styleTips: [
      "Pair with light chinos for a smart casual look",
      "Roll up the sleeves for a relaxed vibe",
      "Tuck in slightly for a semi-formal appearance",
    ],
    colors: ["White", "Beige", "Light Blue"],
    material: "65% Cotton, 35% Linen",
    occasion: "Casual",
    weather: "Hot",
  },
  {
    id: "2",
    name: "Flowy Summer Sundress",
    category: "Dress",
    description:
      "A lightweight, floral-print sundress with adjustable straps. Made from 100% rayon for maximum comfort in the heat.",
    matchReason:
      "Ideal for hot weather — the rayon fabric keeps you cool while the flowy silhouette allows air movement around the body.",
    image:
      "https://images.unsplash.com/photo-1661416219270-e7d952c62249?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&w=1080",
    price: "$59.99",
    rating: 4.7,
    tags: ["Casual", "Feminine"],
    styleTips: [
      "Add a wide-brim hat for sun protection",
      "Pair with flat sandals for a beach-ready look",
      "Layer a light denim jacket for evenings",
    ],
    colors: ["Floral Blue", "Floral Pink", "Yellow"],
    material: "100% Rayon",
    occasion: "Casual",
    weather: "Hot",
  },
  {
    id: "4",
    name: "Slim Linen Trousers",
    category: "Bottom",
    description:
      "Lightweight, breathable linen trousers with a tailored slim fit. Elastic waistband for all-day comfort.",
    matchReason:
      "Linen is one of the best fabrics for hot weather — naturally breathable and moisture-wicking, perfect for keeping cool in meetings.",
    image:
      "https://images.unsplash.com/photo-1719650979576-72055a21a658?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&w=1080",
    price: "$79.99",
    rating: 4.6,
    tags: ["Formal", "Breathable"],
    styleTips: [
      "Cuff the hem slightly for a modern look",
      "Pair with a tucked-in shirt for a polished ensemble",
      "Add a leather belt to define the waist",
    ],
    colors: ["Beige", "White", "Light Grey"],
    material: "100% Linen",
    occasion: "Casual / Formal",
    weather: "Hot",
  },
  {
    id: "6",
    name: "Casual Summer Co-ord Set",
    category: "Full Outfit",
    description:
      "A matching two-piece set with a relaxed short-sleeve top and wide-leg shorts. Made from breathable cotton.",
    matchReason:
      "Co-ord sets eliminate the guesswork — this one is specifically designed for hot, casual days with matching breathable pieces.",
    image:
      "https://images.unsplash.com/photo-1658874761235-8d56cbd5da2d?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&w=1080",
    price: "$95.99",
    rating: 4.8,
    tags: ["Casual", "Trendy"],
    styleTips: [
      "Accessorize with a crossbody bag for a complete look",
      "Add sunglasses for a stylish summer vibe",
      "Works perfectly at outdoor events or weekend brunches",
    ],
    colors: ["Sage Green", "Dusty Rose", "Sky Blue"],
    material: "100% Cotton",
    occasion: "Casual",
    weather: "Hot",
  },
];
