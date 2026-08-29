"use client";

import { ImagePlus, ChevronDown, UploadCloud } from "lucide-react";
import { useState, type ChangeEvent, type FormEvent, type DragEvent } from "react";
import { SANS, SERIF } from "@/app/components/typography";
import { Button } from "@/app/components/ui/button";
import defaultPreviewImage from "./images/ColourTab1.png";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/";

const API_URL = `${API_BASE.replace(/\/$/, "")}/coloranalyzer`;

interface ColorEntry {
  name: string;
  rgb: number[];
  percentage: number;
  is_sub_color?: boolean;
}

interface ColorResult {
  success: boolean;
  colors?: ColorEntry[];
  image_preview?: string;
  base_color?: string;
  base_color_confidence?: number;
  color_type?: "single" | "dual" | "multi" | string;
  detail?: string;
}

const CATEGORY_LABELS: Record<string, string> = {
  single: "Single Color T-Shirt",
  dual: "Dual Color T-Shirt",
  multi: "Multi Color T-Shirt",
};

function rgbToCss(rgb: number[]): string {
  return Array.isArray(rgb) && rgb.length === 3
    ? `rgb(${rgb[0]}, ${rgb[1]}, ${rgb[2]})`
    : "#cfc8d8";
}

function pad2(n: number): string {
  return String(n).padStart(2, "0");
}

export function ColorTab() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [result, setResult] = useState<ColorResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasPerson, setHasPerson] = useState(false);
  const [showSubColors, setShowSubColors] = useState(false);
  const [isDragging, setIsDragging] = useState(false);

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
    setShowSubColors(false);
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

    try {
      const formData = new FormData();
      formData.append("image", file);
      formData.append("has_person", String(hasPerson));

      const res = await fetch(`${API_URL}/analyze`, {
        method: "POST",
        body: formData,
      });

      const data = await res.json();
      if (!data.success) throw new Error(data.detail || "Color analysis failed");
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis failed");
    } finally {
      setLoading(false);
    }
  };

  const sortedColors = result?.colors
    ? [...result.colors].sort((a, b) => b.percentage - a.percentage)
    : [];


  const mainColors = sortedColors.filter((c) => !c.is_sub_color);
  const subColors = sortedColors.filter((c) => c.is_sub_color);

  const categoryLabel = result?.color_type
    ? CATEGORY_LABELS[result.color_type] ?? null
    : null;

  return (
    <form onSubmit={handleSubmit}>
      
      <div className="grid grid-cols-1 items-stretch gap-6 border-b border-[#e8e8e8] p-6 md:grid-cols-2 md:p-8">
        
        <div className="flex h-full min-h-[280px] items-center justify-center border border-[#e8e8e8] bg-[#fafafa] p-4">
          <img
            src={defaultPreviewImage.src}
            alt="Color analyzer"
            className="max-h-[420px] w-full object-contain"
          />
        </div>

        
        <div className="flex h-full min-h-[280px] flex-col justify-between border border-[#e8e8e8] bg-white p-6">
          <div>
            <p className="mb-2 text-[10px] tracking-[0.25em] text-[#aaa]" style={SANS}>
              OPTIONS
            </p>
            <p className="mb-4 text-sm leading-7 text-[#666]" style={SANS}>
              Upload a clear photo of the garment — drag &amp; drop it below,
              or click to browse. Once you&apos;re ready, hit Analyze Colors
              to get a full colour breakdown of the cloth.
            </p>

            <label
              onDragOver={handleDragOver}
              onDragEnter={handleDragEnter}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              className={`flex min-h-[120px] w-full cursor-pointer flex-col items-center justify-center gap-2 border border-dashed px-4 py-6 text-center transition ${
                isDragging
                  ? "border-[#111] bg-[#f0f0f0]"
                  : "border-[#d7d7d7] hover:border-[#111]"
              }`}
            >
              {isDragging || !file ? (
                <ImagePlus className="h-6 w-6 text-[#777]" />
              ) : (
                <UploadCloud className="h-6 w-6 text-[#777]" />
              )}
              <span
                className="max-w-full truncate text-sm text-[#111]"
                style={{ ...SANS, fontWeight: 400 }}
              >
                {isDragging
                  ? "Drop the photo here"
                  : file
                  ? "Drag & drop or click to replace"
                  : "Select a photo to analyze, or drag & drop it here"}
              </span>

              <input
                type="file"
                accept="image/*"
                onChange={handleFile}
                className="hidden"
              />
            </label>

            {file && (
              <div className="mt-4 flex items-center gap-3">
                <img
                  src={preview ?? undefined}
                  alt="Selected preview"
                  className="h-14 w-14 flex-shrink-0 border border-[#e8e8e8] object-cover"
                />
                <span className="truncate text-xs text-[#888]" style={SANS}>
                  {file.name}
                </span>
              </div>
            )}
          </div>

          <div className="mt-6 flex flex-wrap items-center justify-between gap-4">
            <label
              className="flex items-center gap-2.5 text-xs text-[#666]"
              style={SANS}
            >
              <input
                type="checkbox"
                checked={hasPerson}
                onChange={(e) => setHasPerson(e.target.checked)}
                className="accent-[#111]"
              />
              Person is wearing the shirt (excludes skin tone)
            </label>

            <Button
              type="submit"
              disabled={loading || !file}
              className="rounded-none border border-[#111] bg-[#111] px-8 py-2.5 text-[11px] tracking-[0.2em] text-white transition-all hover:bg-[#222] disabled:border-[#ddd] disabled:bg-[#ddd] disabled:text-[#999]"
              style={SANS}
            >
              {loading ? "ANALYZING…" : "ANALYZE COLORS"}
            </Button>
          </div>
        </div>
      </div>

      {error && (
        <p
          className="mx-6 mt-6 border border-[#f1cfc7] bg-[#fbeae6] px-4 py-3 text-xs leading-6 text-[#9a3b2e] md:mx-8"
          style={SANS}
        >
          {error}
        </p>
      )}

      {/* RESULTS: full width, below both boxes */}
      {result && (
        <div className="w-full bg-[#fafafa] p-6 md:p-8">
          <div className="grid gap-8 md:grid-cols-[0.9fr_1.1fr] items-start">
            {/* Photo */}
            <div className="border border-[#e8e8e8] bg-white p-4">
              <p
                className="mb-3 text-[10px] tracking-[0.25em] text-[#aaa]"
                style={SANS}
              >
                {result.image_preview ? "PROCESSED PHOTO" : "PHOTO"}
              </p>
              <div className="flex aspect-[4/5] items-center justify-center overflow-hidden bg-[#f5f5f5]">
                {result.image_preview ? (
                  <img
                    src={`data:image/jpeg;base64,${result.image_preview}`}
                    alt="Processed garment"
                    className="h-full w-full object-contain"
                  />
                ) : preview ? (
                  <img
                    src={preview}
                    alt="Garment"
                    className="h-full w-full object-contain"
                  />
                ) : (
                  <span className="text-xs text-[#999]" style={SANS}>
                    No image
                  </span>
                )}
              </div>
            </div>

            {/* Breakdown */}
            <div className="border border-[#e8e8e8] bg-white p-6 md:p-8">
              <div className="mb-1 flex items-center justify-between gap-3">
                <p
                  className="text-[10px] tracking-[0.25em] text-[#aaa]"
                  style={SANS}
                >
                  COLOR BREAKDOWN
                </p>
                {categoryLabel && (
                  <span
                    className="border border-[#111] px-3 py-1 text-[10px] tracking-[0.15em] text-[#111]"
                    style={SANS}
                  >
                    {categoryLabel.toUpperCase()}
                  </span>
                )}
              </div>

              {mainColors.length === 0 ? (
                <p className="mt-4 text-sm text-[#888]" style={SANS}>
                  No dominant colours detected — try a clearer, closer photo.
                </p>
              ) : (
                <>
                  <p className="mb-6 text-xs text-[#888]" style={SANS}>
                    {mainColors.length}{" "}
                    {mainColors.length === 1 ? "colour" : "colours"} detected
                  </p>
                  <div className="space-y-6">
                    {mainColors.map((c, i) => (
                      <div key={`${c.name}-${i}`} className="flex items-center gap-5">
                        <span className="w-5 text-[11px] text-[#bbb]" style={SANS}>
                          {pad2(i + 1)}
                        </span>
                        <span
                          className="h-10 w-10 flex-shrink-0 border border-[#e5e5e5]"
                          style={{ background: rgbToCss(c.rgb) }}
                        />
                        <div className="min-w-0 flex-1">
                          <div className="mb-2 flex items-baseline justify-between gap-2">
                            <span
                              className="truncate text-base text-[#111]"
                              style={{ ...SERIF, fontWeight: 500 }}
                            >
                              {c.name}
                            </span>
                            <span
                              className="flex-shrink-0 text-xs text-[#999]"
                              style={SANS}
                            >
                              {c.percentage.toFixed(1)}%
                            </span>
                          </div>
                          <div className="h-2 w-full bg-[#eee]">
                            <div
                              className="h-full bg-[#111] transition-all duration-700"
                              style={{ width: `${Math.min(100, c.percentage)}%` }}
                            />
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>

                  {subColors.length > 0 && (
                    <div className="mt-6 border-t border-[#eee] pt-4">
                      <button
                        type="button"
                        onClick={() => setShowSubColors((v) => !v)}
                        className="flex w-full items-center justify-between text-[11px] tracking-[0.15em] text-[#888] transition-colors hover:text-[#111]"
                        style={SANS}
                      >
                        <span>
                          {showSubColors ? "HIDE" : "SHOW"} {subColors.length}{" "}
                          SUB {subColors.length === 1 ? "COLOUR" : "COLOURS"}
                        </span>
                        <ChevronDown
                          className={`h-4 w-4 transition-transform ${
                            showSubColors ? "rotate-180" : ""
                          }`}
                        />
                      </button>

                      {showSubColors && (
                        <div className="mt-4 space-y-4">
                          {subColors.map((c, i) => (
                            <div
                              key={`sub-${c.name}-${i}`}
                              className="flex items-center gap-4 opacity-70"
                            >
                              <span
                                className="h-7 w-7 flex-shrink-0 border border-[#e5e5e5]"
                                style={{ background: rgbToCss(c.rgb) }}
                              />
                              <div className="min-w-0 flex-1">
                                <div className="flex items-baseline justify-between gap-2">
                                  <span
                                    className="truncate text-sm text-[#555]"
                                    style={{ ...SERIF, fontWeight: 500 }}
                                  >
                                    {c.name}
                                  </span>
                                  <span
                                    className="flex-shrink-0 text-[11px] text-[#999]"
                                    style={SANS}
                                  >
                                    {c.percentage.toFixed(1)}%
                                  </span>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </form>
  );
}