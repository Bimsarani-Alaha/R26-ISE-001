"use client";

import { createContext, type ReactNode, useContext, useState } from "react";
import type { ClothingItem } from "@/app/data/recommendations";
import type { BackendPrediction } from "@/app/lib/recommendationApi";

type AppStore = {
  requirements: string;
  occasion: string;
  gender: string;
  colorPreference: string;
  prediction: BackendPrediction | null;
  recommendations: ClothingItem[];
  setRequirements: (v: string) => void;
  setOccasion: (v: string) => void;
  setGender: (v: string) => void;
  setColorPreference: (v: string) => void;
  setPrediction: (v: BackendPrediction | null) => void;
  setRecommendations: (v: ClothingItem[]) => void;
};

const AppStoreContext = createContext<AppStore | null>(null);

export function AppStoreProvider({ children }: { children: ReactNode }) {
  const [requirements, setRequirements] = useState("");
  const [occasion, setOccasion] = useState("");
  const [gender, setGender] = useState("");
  const [colorPreference, setColorPreference] = useState("");
  const [prediction, setPrediction] = useState<BackendPrediction | null>(null);
  const [recommendations, setRecommendations] = useState<ClothingItem[]>([]);

  return (
    <AppStoreContext.Provider
      value={{
        requirements,
        occasion,
        gender,
        colorPreference,
        prediction,
        recommendations,
        setRequirements,
        setOccasion,
        setGender,
        setColorPreference,
        setPrediction,
        setRecommendations,
      }}
    >
      {children}
    </AppStoreContext.Provider>
  );
}

export function useAppStore() {
  const ctx = useContext(AppStoreContext);
  if (!ctx) throw new Error("useAppStore must be used within AppStoreProvider");
  return ctx;
}
