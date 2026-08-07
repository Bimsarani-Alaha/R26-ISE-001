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

type AppStore = {
  requirements: string;
  occasion: string;
  prediction: BackendPrediction | null;
  recommendations: ClothingItem[];
  setRequirements: (v: string) => void;
  setOccasion: (v: string) => void;
  setPrediction: (v: BackendPrediction | null) => void;
  setRecommendations: (v: ClothingItem[]) => void;
};

const AppStoreContext = createContext<AppStore | null>(null);

export function AppStoreProvider({ children }: { children: ReactNode }) {
  const [requirements, setRequirements] = useState("");
  const [occasion, setOccasion] = useState("");
  const [prediction, setPrediction] = useState<BackendPrediction | null>(null);
  const [recommendations, setRecommendations] = useState<ClothingItem[]>([]);

  const value = useMemo(
    () => ({
      requirements,
      occasion,
      prediction,
      recommendations,
      setRequirements,
      setOccasion,
      setPrediction,
      setRecommendations,
    }),
    [
      requirements,
      occasion,
      prediction,
      recommendations,
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
