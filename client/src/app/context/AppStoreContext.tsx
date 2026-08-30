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
import type { ProductResult } from "@/app/lib/aiStyleApi";

const GENDER_STORAGE_KEY = "styleai-gender";
const BODY_MEASUREMENTS_STORAGE_KEY = "styleai-body-measurements";

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
  setRequirements: (v: string) => void;
  setOccasion: (v: string) => void;
  setGender: (v: string) => void;
  setSize: (v: string) => void;
  setPrediction: (v: BackendPrediction | null) => void;
  setRecommendations: (v: ClothingItem[]) => void;
  setProductResults: (v: ProductResult[]) => void;
  setBodyMeasurements: (v: BodyMeasurements | null) => void;
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
  const [gender, setGenderState] = useState<string>(() =>
    readStorageValue<string>(GENDER_STORAGE_KEY, ""),
  );
  const [size, setSize] = useState("");
  const [colorPreference, setColorPreference] = useState("");
  const [prediction, setPrediction] = useState<BackendPrediction | null>(null);
  const [recommendations, setRecommendations] = useState<ClothingItem[]>([]);
  const [productResults, setProductResults] = useState<ProductResult[]>([]);
  const [bodyMeasurements, setBodyMeasurementsState] = useState<BodyMeasurements | null>(() =>
    readStorageValue<BodyMeasurements | null>(BODY_MEASUREMENTS_STORAGE_KEY, null),
  );

  useEffect(() => {
    if (typeof window !== "undefined") {
      window.localStorage.setItem(GENDER_STORAGE_KEY, JSON.stringify(gender));
    }
  }, [gender]);

  useEffect(() => {
    if (typeof window !== "undefined") {
      window.localStorage.setItem(
        BODY_MEASUREMENTS_STORAGE_KEY,
        JSON.stringify(bodyMeasurements),
      );
    }
  }, [bodyMeasurements]);

  const setGender = (v: string) => {
    setGenderState(v);
  };

  const setBodyMeasurements = (v: BodyMeasurements | null) => {
    setBodyMeasurementsState(v);
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
      setRequirements,
      setOccasion,
      setGender,
      setSize,
      setPrediction,
      setRecommendations,
      setProductResults,
      setBodyMeasurements,
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
