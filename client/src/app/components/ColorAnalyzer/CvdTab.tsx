"use client";

import { ImagePlus } from "lucide-react";
import { useState, type ChangeEvent, type FormEvent, type DragEvent } from "react";
import { SANS, SERIF } from "@/app/components/typography";
import { Button } from "@/app/components/ui/button";
import { CvdColourImpact, CVD_LABELS } from "./CvdColourImpact";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/";
const API_URL = `${API_BASE.replace(/\/$/, "")}/coloranalyzer`;

interface CvdResult {
  success: boolean;
  cvd_type: string;
  cvd_image: string;
  detail?: string;
}

export interface ColorEntry {
  name: string;
  rgb: number[];
  percentage: number;
  is_sub_color?: boolean;
}

export interface ColorResult {
  success: boolean;
  colors?: ColorEntry[];
  base_color?: string;
  base_color_confidence?: number;
  color_type?: "single" | "dual" | "multi" | string;
  detail?: string;
}

function base64ToFile(base64: string, filename: string, mime = "image/jpeg"): File {
  const byteChars = atob(base64);
  const byteNumbers = new Array(byteChars.length);
  for (let i = 0; i < byteChars.length; i++) {
    byteNumbers[i] = byteChars.charCodeAt(i);
  }
  const byteArray = new Uint8Array(byteNumbers);
  return new File([byteArray], filename, { type: mime });
}

async function analyzeColors(imageFile: File): Promise<ColorResult> {
  const formData = new FormData();
  formData.append("image", imageFile);
  formData.append("has_person", "false");
  const res = await fetch(`${API_URL}/analyze`, {
    method: "POST",
    body: formData,
  });
  const data = await res.json();
  if (!data.success) throw new Error(data.detail || "Color analysis failed");
  return data as ColorResult;
}

export function CvdTab() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [cvdType, setCvdType] = useState("protanopia");
  const [result, setResult] = useState<CvdResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  const [analyzing, setAnalyzing] = useState(false);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [originalAnalysis, setOriginalAnalysis] = useState<ColorResult | null>(null);
  const [transformedAnalysis, setTransformedAnalysis] = useState<ColorResult | null>(null);

  const applyFile = (f: File | null | undefined) => {
    if (!f) return;
    if (!f.type.startsWith("image/")) {
      setError("Please select a valid image file");
      return;
    }
    setFile(f);
    setPreview(URL.createObjectURL(f));
    setResult(null);
    setError(null);
    setOriginalAnalysis(null);
    setTransformedAnalysis(null);
    setAnalysisError(null);
  };

  const handleFile = (e: ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    applyFile(f);
  };

  const handleDragOver = (e: DragEvent<HTMLLabelElement>) => {
    e.preventDefault();
    e.stopPropagation();
    if (!isDragging) setIsDragging(true);
  };

  const handleDragEnter = (e: DragEvent<HTMLLabelElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: DragEvent<HTMLLabelElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e: DragEvent<HTMLLabelElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    const f = e.dataTransfer.files?.[0];
    applyFile(f);
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!file) {
      setError("Please select an image first");
      return;
    }

    setLoading(true);
    setResult(null);
    setError(null);
    setOriginalAnalysis(null);
    setTransformedAnalysis(null);
    setAnalysisError(null);

    try {
      const formData = new FormData();
      formData.append("image", file);
      formData.append("cvd_type", cvdType);

      const res = await fetch(`${API_URL}/generate-cvd`, {
        method: "POST",
        body: formData,
      });

      const data = await res.json();
      if (!data.success) throw new Error(data.detail || "CVD generation failed");
      setResult(data);
      setLoading(false);

      setAnalyzing(true);
      try {
        const cvdFile = base64ToFile(data.cvd_image, `cvd-${cvdType}.jpg`);
        const [origColors, transColors] = await Promise.all([
          analyzeColors(file),
          analyzeColors(cvdFile),
        ]);
        setOriginalAnalysis(origColors);
        setTransformedAnalysis(transColors);
      } catch (analysisErr) {
        setAnalysisError(
          analysisErr instanceof Error ? analysisErr.message : "Colour impact analysis failed"
        );
      } finally {
        setAnalyzing(false);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Simulation failed");
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      {/* CONTROLS BAR */}
      <div className="flex flex-wrap items-end gap-5 border-b border-[#e8e8e8] p-6 md:p-8">
        <div className="min-w-[240px] flex-1">
          <p className="mb-2 text-[10px] tracking-[0.25em] text-[#aaa]" style={SANS}>
            PHOTO
          </p>
          <label
            onDragOver={handleDragOver}
            onDragEnter={handleDragEnter}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            className={`flex cursor-pointer items-center gap-3 border border-dashed px-4 py-3 transition ${
              isDragging
                ? "border-[#111] bg-[#f0f0f0]"
                : "border-[#d7d7d7] hover:border-[#111] hover:bg-[#f5f5f5]"
            }`}
          >
            <ImagePlus className="h-4 w-4 flex-shrink-0 text-[#777]" />
            <span
              className="truncate text-sm text-[#111]"
              style={{ ...SANS, fontWeight: 400 }}
            >
              {file
                ? file.name
                : isDragging
                ? "Drop the photo here"
                : "Select a photo to simulate, or drag & drop it here"}
            </span>
            <input
              type="file"
              accept="image/*"
              onChange={handleFile}
              className="hidden"
            />
          </label>
        </div>

        <div className="min-w-[220px]">
          <p className="mb-2 text-[10px] tracking-[0.25em] text-[#aaa]" style={SANS}>
            CVD TYPE
          </p>
          <select
            value={cvdType}
            onChange={(e) => setCvdType(e.target.value)}
            className="w-full border border-[#d7d7d7] bg-white px-3 py-2.5 text-sm text-[#111] outline-none focus:border-[#111]"
            style={SANS}
          >
            {Object.entries(CVD_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </div>

        <Button
          type="submit"
          disabled={loading || !file}
          className="rounded-none border border-[#111] bg-[#111] px-8 py-2.5 text-[11px] tracking-[0.2em] text-white transition-all hover:bg-[#222] disabled:border-[#ddd] disabled:bg-[#ddd] disabled:text-[#999]"
          style={SANS}
        >
          {loading ? "SIMULATING…" : "SIMULATE CVD"}
        </Button>
      </div>

      {error && (
        <p
          className="mx-6 mt-6 border border-[#f1cfc7] bg-[#fbeae6] px-4 py-3 text-xs leading-6 text-[#9a3b2e] md:mx-8"
          style={SANS}
        >
          {error}
        </p>
      )}

      {/* PREVIEW / RESULTS */}
      <div className="bg-[#fafafa] p-6 md:p-8">
        {!result ? (
          preview ? (
            <div className="mx-auto max-w-2xl border border-[#e8e8e8] bg-white p-4">
              <img
                src={preview}
                alt="Preview"
                className="mx-auto max-h-[560px] w-full object-contain"
              />
            </div>
          ) : (
            <div
              className="flex min-h-80 flex-col items-center justify-center gap-3 text-center text-[#999]"
              style={SANS}
            >
              <div className="h-1.5 w-1.5 bg-[#111]" />
              <p className="text-sm">
                Simulated vision will appear here once you run it.
              </p>
            </div>
          )
        ) : (
          <div>
            <h2
              className="mb-6 text-xl capitalize tracking-[0.15em] text-[#111]"
              style={{ ...SERIF, fontWeight: 500 }}
            >
              {result.cvd_type}
            </h2>
            <div className="grid gap-6 md:grid-cols-2">
              <div>
                <p className="mb-3 text-[10px] tracking-[0.2em] text-[#aaa]" style={SANS}>
                  ORIGINAL
                </p>
                <div className="flex min-h-[420px] items-center justify-center border border-[#e8e8e8] bg-white p-4">
                  {preview && (
                    <img
                      src={preview}
                      alt="Original"
                      className="max-h-[560px] w-full object-contain"
                    />
                  )}
                </div>
              </div>
              <div>
                <p className="mb-3 text-[10px] tracking-[0.2em] text-[#aaa]" style={SANS}>
                  SIMULATED
                </p>
                <div className="flex min-h-[420px] items-center justify-center border border-[#e8e8e8] bg-white p-4">
                  <img
                    src={`data:image/jpeg;base64,${result.cvd_image}`}
                    alt="CVD simulation"
                    className="max-h-[560px] w-full object-contain"
                  />
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* COLOUR VISION IMPACT — logic + UI live in CvdColourImpact.tsx */}
      {result && (
        <CvdColourImpact
          cvdType={cvdType}
          analyzing={analyzing}
          analysisError={analysisError}
          originalAnalysis={originalAnalysis}
          transformedAnalysis={transformedAnalysis}
        />
      )}
    </form>
  );
}