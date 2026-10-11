import { requestJson } from "./apiClient";

export interface HealthResponse {
  status: string;
  model_available: boolean;
  ollama_connected: boolean;
  model_name: string;
  products_loaded: boolean;
  product_count: number;
}

export interface ProductResult {
  match_category?: "exact" | "alternative";
  unmatched_requirements?: string[];
  product_id: string;
  image_path: string;
  article_type: string;
  base_colour: string;
  occasion: string | null;
  style: string;
  price: number | null;
  selected_size: string;
  match_score: number;
  explanation: string;
  category: string;
  pattern: string;
  material: string;
  sleeve_type: string;
  neck_type: string;
  description: string;
}

export interface GetRecommendationsRequest {
  gender: string;
  size: string;
  requirements: string;
}

export interface GetRecommendationsResponse {
  recommendations: ProductResult[];
  alternatives: ProductResult[];
  occasion_used: string[] | null;
  total_candidates: number;
  message: string | null;
}

export interface GetStylistRequest extends GetRecommendationsRequest {
  product_id: string;
}

export interface GetStylistResponse {
  summary: string;
  accessories: string[];
  footwear: string[];
  color_combinations: string[];
  layering: string[];
  occasion_tip: string;
  complementary_items: string[];
}

const API_PREFIX = "/fashion-recommendation/api";

export function checkHealth(): Promise<HealthResponse> {
  return requestJson(`${API_PREFIX}/health`);
}

export function getRecommendations(
  request: GetRecommendationsRequest,
): Promise<GetRecommendationsResponse> {
  return requestJson(`${API_PREFIX}/recommendations`, request);
}

export function getStylistTips(
  request: GetStylistRequest,
): Promise<GetStylistResponse> {
  return requestJson(`${API_PREFIX}/stylist`, request);
}
