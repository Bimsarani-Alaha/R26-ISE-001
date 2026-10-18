const SIZES = ["XS", "S", "M", "L", "XL", "2XL", "3XL", "4XL"];

function normalizeGender(value: unknown): string {
  if (typeof value !== "string") return "";
  switch (value.trim().toLowerCase()) {
    case "men":
    case "male":
      return "Male";
    case "women":
    case "female":
      return "Female";
    case "unisex":
      return "Unisex";
    default:
      return "";
  }
}

function normalizeSize(value: unknown): string {
  if (typeof value !== "string") return "";
  const normalized = value.trim().toUpperCase();
  const size =
    ({ XXL: "2XL", XXXL: "3XL", XXXXL: "4XL" } as Record<string, string>)[
      normalized
    ] ?? normalized;
  return SIZES.includes(size) ? size : "";
}

export function getRecommendationPrefill(values: {
  gender?: unknown;
  predictedSize?: unknown;
  size?: unknown;
  bodyMeasurements?: { gender?: unknown; clothingSize?: unknown } | null;
}) {
  const predictedSize =
    normalizeSize(values.predictedSize) ||
    normalizeSize(values.bodyMeasurements?.clothingSize);
  const gender =
    normalizeGender(values.gender) ||
    normalizeGender(values.bodyMeasurements?.gender);
  return {
    gender,
    size: predictedSize || normalizeSize(values.size),
    predictedGender: predictedSize ? gender : "",
    predictedSize,
  };
}
