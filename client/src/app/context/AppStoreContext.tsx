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
  colorPreference: string;
  prediction: BackendPrediction | null;
  recommendations: ClothingItem[];
  bodyMeasurements: BodyMeasurements | null;
  setRequirements: (v: string) => void;
  setOccasion: (v: string) => void;
  setGender: (v: string) => void;
  setColorPreference: (v: string) => void;
  setPrediction: (v: BackendPrediction | null) => void;
  setRecommendations: (v: ClothingItem[]) => void;
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
  const [colorPreference, setColorPreference] = useState("");
  const [prediction, setPrediction] = useState<BackendPrediction | null>(null);
  const [recommendations, setRecommendations] = useState<ClothingItem[]>([]);
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
      colorPreference,
      prediction,
      recommendations,
      bodyMeasurements,
      setRequirements,
      setOccasion,
      setGender,
      setColorPreference,
      setPrediction,
      setRecommendations,
      setBodyMeasurements,
    }),
    [
      requirements,
      occasion,
      gender,
      colorPreference,
      prediction,
      recommendations,
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
