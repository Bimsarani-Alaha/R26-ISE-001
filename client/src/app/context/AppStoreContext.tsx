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
const PREDICTED_SIZE_STORAGE_KEY = "styleai-predicted-size";

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
  prediction: BackendPrediction | null;
  recommendations: ClothingItem[];
  bodyMeasurements: BodyMeasurements | null;
  predictedSize: string | null;
  storageLoaded: boolean;
  setRequirements: (v: string) => void;
  setOccasion: (v: string) => void;
  setGender: (v: string) => void;
  setPrediction: (v: BackendPrediction | null) => void;
  setRecommendations: (v: ClothingItem[]) => void;
  setBodyMeasurements: (v: BodyMeasurements | null) => void;
  setPredictedSize: (v: string | null) => void;
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
  const [gender, setGenderState] = useState("");
  const [colorPreference, setColorPreference] = useState("");
  const [prediction, setPrediction] = useState<BackendPrediction | null>(null);
  const [recommendations, setRecommendations] = useState<ClothingItem[]>([]);
  const [bodyMeasurements, setBodyMeasurementsState] =
    useState<BodyMeasurements | null>(null);
  const [predictedSize, setPredictedSizeState] = useState<string | null>(null);
  const [storageLoaded, setStorageLoaded] = useState(false);

  useEffect(() => {
    setGenderState(readStorageValue<string>(GENDER_STORAGE_KEY, ""));
    setBodyMeasurementsState(
      readStorageValue<BodyMeasurements | null>(
        BODY_MEASUREMENTS_STORAGE_KEY,
        null,
      ),
    );
    setPredictedSizeState(
      readStorageValue<string | null>(PREDICTED_SIZE_STORAGE_KEY, null),
    );
    setStorageLoaded(true);
  }, []);

  useEffect(() => {
    if (storageLoaded) {
      window.localStorage.setItem(GENDER_STORAGE_KEY, JSON.stringify(gender));
    }
  }, [gender, storageLoaded]);

  useEffect(() => {
    if (storageLoaded) {
      window.localStorage.setItem(
        BODY_MEASUREMENTS_STORAGE_KEY,
        JSON.stringify(bodyMeasurements),
      );
    }
  }, [bodyMeasurements, storageLoaded]);

  useEffect(() => {
    if (storageLoaded) {
      window.localStorage.setItem(
        PREDICTED_SIZE_STORAGE_KEY,
        JSON.stringify(predictedSize),
      );
    }
  }, [predictedSize, storageLoaded]);

  const setGender = (v: string) => {
    setGenderState(v);
  };

  const setBodyMeasurements = (v: BodyMeasurements | null) => {
    setBodyMeasurementsState(v);
  };

  const setPredictedSize = (v: string | null) => {
    setPredictedSizeState(v);
  };

  const value = useMemo(
    () => ({
      requirements,
      occasion,
      gender,
      prediction,
      recommendations,
      bodyMeasurements,
      predictedSize,
      storageLoaded,
      setRequirements,
      setOccasion,
      setGender,
      setPrediction,
      setRecommendations,
      setBodyMeasurements,
      setPredictedSize,
    }),
    [
      requirements,
      occasion,
      gender,
      prediction,
      recommendations,
      bodyMeasurements,
      predictedSize,
      storageLoaded,
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
