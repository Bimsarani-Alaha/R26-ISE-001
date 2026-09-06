"use client";

import {
  createContext,
  type ReactNode,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import type { ClothingItem } from "@/app/data/recommendations";
import type { BackendPrediction } from "@/app/lib/recommendationApi";
import type { GetStylistResponse, ProductResult } from "@/app/lib/aiStyleApi";

const GENDER_STORAGE_KEY = "styleai-gender";
const BODY_MEASUREMENTS_STORAGE_KEY = "styleai-body-measurements";
const REQUIREMENTS_STORAGE_KEY = "styleai-requirements";
const OCCASION_STORAGE_KEY = "styleai-occasion";
const SIZE_STORAGE_KEY = "styleai-size";
const PRODUCT_RESULTS_STORAGE_KEY = "styleai-product-results";
const PREDICTION_STORAGE_KEY = "styleai-prediction";
const RECOMMENDATIONS_STORAGE_KEY = "styleai-recommendations";
const COLOR_PREF_STORAGE_KEY = "styleai-color-pref";
const STYLIST_TIPS_STORAGE_KEY = "styleai-stylist-tips";

const readStorageValue = <T,>(key: string, fallback: T): T => {
  if (typeof window === "undefined") {
    return fallback;
  }

  try {
    const rawValue = window.localStorage.getItem(key);
    if (!rawValue) {
      return fallback;
    }

    return JSON.parse(rawValue) as T;
  } catch {
    return fallback;
  }
};

type AppStore = {
  requirements: string;
  occasion: string;
  gender: string;
  size: string;
  prediction: BackendPrediction | null;
  recommendations: ClothingItem[];
  productResults: ProductResult[];
  bodyMeasurements: BodyMeasurements | null;
  colorPreference: string;
  stylistTipsCache: Record<string, GetStylistResponse>;
  hydrated: boolean;
  setRequirements: (v: string) => void;
  setOccasion: (v: string) => void;
  setGender: (v: string) => void;
  setSize: (v: string) => void;
  setPrediction: (v: BackendPrediction | null) => void;
  setRecommendations: (v: ClothingItem[]) => void;
  setProductResults: (v: ProductResult[]) => void;
  setBodyMeasurements: (v: BodyMeasurements | null) => void;
  setColorPreference: (v: string) => void;
  setStylistTipsCache: (v: Record<string, GetStylistResponse>) => void;
  setStylistTip: (productId: string, tip: GetStylistResponse | null) => void;
};

export type BodyMeasurements = {
  shoulderCm: number;
  hipCm: number;
  heightCm: number;
  gender: string;
  clothingSize: string;
};

const AppStoreContext = createContext<AppStore | null>(null);

export function AppStoreProvider({ children }: { children: ReactNode }) {
  const [requirements, setRequirements] = useState("");
  const [occasion, setOccasion] = useState("");
  const [gender, setGenderState] = useState<string>("");
  const [size, setSize] = useState("");
  const [colorPreference, setColorPreference] = useState("");
  const [prediction, setPrediction] = useState<BackendPrediction | null>(null);
  const [recommendations, setRecommendations] = useState<ClothingItem[]>([]);
  const [productResults, setProductResults] = useState<ProductResult[]>([]);
  const [bodyMeasurements, setBodyMeasurementsState] = useState<BodyMeasurements | null>(null);
  const [stylistTipsCache, setStylistTipsCache] = useState<Record<string, GetStylistResponse>>({});
  const [hydrated, setHydrated] = useState(false);

  // Hydrate from localStorage after mount to avoid SSR mismatch
  useEffect(() => {
    setGenderState(readStorageValue<string>(GENDER_STORAGE_KEY, ""));
    setBodyMeasurementsState(readStorageValue<BodyMeasurements | null>(BODY_MEASUREMENTS_STORAGE_KEY, null));
    setRequirements(readStorageValue<string>(REQUIREMENTS_STORAGE_KEY, ""));
    setOccasion(readStorageValue<string>(OCCASION_STORAGE_KEY, ""));
    setSize(readStorageValue<string>(SIZE_STORAGE_KEY, ""));
    setColorPreference(readStorageValue<string>(COLOR_PREF_STORAGE_KEY, ""));
    setPrediction(readStorageValue<BackendPrediction | null>(PREDICTION_STORAGE_KEY, null));
    setRecommendations(readStorageValue<ClothingItem[]>(RECOMMENDATIONS_STORAGE_KEY, []));
    setProductResults(readStorageValue<ProductResult[]>(PRODUCT_RESULTS_STORAGE_KEY, []));
    setStylistTipsCache(readStorageValue<Record<string, GetStylistResponse>>(STYLIST_TIPS_STORAGE_KEY, {}));
    setHydrated(true);
  }, []);

  useEffect(() => {
    if (!hydrated) return;
    if (typeof window !== "undefined") {
      window.localStorage.setItem(GENDER_STORAGE_KEY, JSON.stringify(gender));
    }
  }, [gender, hydrated]);

  useEffect(() => {
    if (!hydrated) return;
    if (typeof window !== "undefined") {
      window.localStorage.setItem(
        BODY_MEASUREMENTS_STORAGE_KEY,
        JSON.stringify(bodyMeasurements),
      );
    }
  }, [bodyMeasurements, hydrated]);

  useEffect(() => {
    if (!hydrated) return;
    window.localStorage.setItem(REQUIREMENTS_STORAGE_KEY, JSON.stringify(requirements));
  }, [requirements, hydrated]);

  useEffect(() => {
    if (!hydrated) return;
    window.localStorage.setItem(OCCASION_STORAGE_KEY, JSON.stringify(occasion));
  }, [occasion, hydrated]);

  useEffect(() => {
    if (!hydrated) return;
    window.localStorage.setItem(SIZE_STORAGE_KEY, JSON.stringify(size));
  }, [size, hydrated]);

  useEffect(() => {
    if (!hydrated) return;
    window.localStorage.setItem(COLOR_PREF_STORAGE_KEY, JSON.stringify(colorPreference));
  }, [colorPreference, hydrated]);

  useEffect(() => {
    if (!hydrated) return;
    window.localStorage.setItem(PREDICTION_STORAGE_KEY, JSON.stringify(prediction));
  }, [prediction, hydrated]);

  useEffect(() => {
    if (!hydrated) return;
    window.localStorage.setItem(RECOMMENDATIONS_STORAGE_KEY, JSON.stringify(recommendations));
  }, [recommendations, hydrated]);

  useEffect(() => {
    if (!hydrated) return;
    window.localStorage.setItem(PRODUCT_RESULTS_STORAGE_KEY, JSON.stringify(productResults));
  }, [productResults, hydrated]);

  useEffect(() => {
    if (!hydrated) return;
    window.localStorage.setItem(STYLIST_TIPS_STORAGE_KEY, JSON.stringify(stylistTipsCache));
  }, [stylistTipsCache, hydrated]);

  const setGender = (v: string) => {
    setGenderState(v);
  };

  const setBodyMeasurements = (v: BodyMeasurements | null) => {
    setBodyMeasurementsState(v);
  };

  const setStylistTip = (productId: string, tip: GetStylistResponse | null) => {
    setStylistTipsCache((prev) => {
      if (tip === null) {
        const { [productId]: _, ...rest } = prev;
        return rest;
      }
      return { ...prev, [productId]: tip };
    });
  };

  const value = useMemo(
    () => ({
      requirements,
      occasion,
      gender,
      size,
      prediction,
      recommendations,
      productResults,
      bodyMeasurements,
      colorPreference,
      stylistTipsCache,
      hydrated,
      setRequirements,
      setOccasion,
      setGender,
      setSize,
      setPrediction,
      setRecommendations,
      setProductResults,
      setBodyMeasurements,
      setColorPreference,
      setStylistTipsCache,
      setStylistTip,
    }),
    [
      requirements,
      occasion,
      gender,
      size,
      prediction,
      recommendations,
      productResults,
      bodyMeasurements,
      colorPreference,
      stylistTipsCache,
      hydrated,
    ],
  );

  return (
    <AppStoreContext.Provider value={value}>
      {children}
    </AppStoreContext.Provider>
  );
}

export function useAppStore() {
  const ctx = useContext(AppStoreContext);
  if (!ctx) throw new Error("useAppStore must be used within AppStoreProvider");
  return ctx;
}
