"use client";

import {
  createContext,
  type ReactNode,
  useContext,
  useMemo,
  useState,
} from "react";
import type { ClothingItem } from "@/app/data/recommendations";
import type { BackendPrediction } from "@/app/lib/recommendationApi";
import type { ProductResult } from "@/app/lib/aiStyleApi";

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
  const [gender, setGender] = useState("");
  const [size, setSize] = useState("");
  const [prediction, setPrediction] = useState<BackendPrediction | null>(null);
  const [recommendations, setRecommendations] = useState<ClothingItem[]>([]);
  const [productResults, setProductResults] = useState<ProductResult[]>([]);
  const [bodyMeasurements, setBodyMeasurements] = useState<BodyMeasurements | null>(null);

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
