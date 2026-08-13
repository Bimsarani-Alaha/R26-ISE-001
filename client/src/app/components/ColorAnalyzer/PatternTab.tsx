"use client";

import { ImagePlus } from "lucide-react";
import { useState, type ChangeEvent, type FormEvent } from "react";
import { SANS, SERIF } from "@/app/components/typography";
import { Button } from "@/app/components/ui/button";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/";
const API_URL = `${API_BASE.replace(/\/$/, "")}/coloranalyzer`;

interface PatternResult {
  success: boolean;
  colored_pattern?: string;
  dimensions?: { width: number; height: number };
  detail?: string;
}

export function PatternTab() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [result, setResult] = useState<PatternResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFile = (e: ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (!f) return;
    setFile(f);
    setPreview(URL.createObjectURL(f));
    setResult(null);
    setError(null);
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

      const res = await fetch(`${API_URL}/pattern-recognize`, {
        method: "POST",
        body: formData,
      });

      const data = await res.json();
      if (!data.success) throw new Error(data.detail || "Pattern recognition failed");
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Pattern recognition failed");
    } finally {
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
          <label className="flex cursor-pointer items-center gap-3 border border-dashed border-[#d7d7d7] px-4 py-3 transition hover:border-[#111] hover:bg-[#f5f5f5]">
            <ImagePlus className="h-4 w-4 flex-shrink-0 text-[#777]" />
            <span
              className="truncate text-sm text-[#111]"
              style={{ ...SANS, fontWeight: 400 }}
            >
              {file ? file.name : "Select a photo to extract a pattern from"}
            </span>
            <input
              type="file"
              accept="image/*"
              onChange={handleFile}
              className="hidden"
            />
          </label>
        </div>

        <Button
          type="submit"
          disabled={loading || !file}
          className="rounded-none border border-[#111] bg-[#111] px-8 py-2.5 text-[11px] tracking-[0.2em] text-white transition-all hover:bg-[#222] disabled:border-[#ddd] disabled:bg-[#ddd] disabled:text-[#999]"
          style={SANS}
        >
          {loading ? "RECOGNIZING…" : "RECOGNIZE PATTERN"}
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
                The extracted pattern will appear here once you run it.
              </p>
            </div>
          )
        ) : (
          <div>
            <div className="mb-6">
              <h2
                className="text-xl tracking-[0.15em] text-[#111]"
                style={{ ...SERIF, fontWeight: 500 }}
              >
                EXTRACTED PATTERN
              </h2>
              <p className="mt-1 text-xs text-[#888]" style={SANS}>
                {result.dimensions?.width} × {result.dimensions?.height}px
              </p>
            </div>

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
              {result.colored_pattern && (
                <div>
                  <p className="mb-3 text-[10px] tracking-[0.2em] text-[#aaa]" style={SANS}>
                    COLORED PREVIEW
                  </p>
                  <div className="flex min-h-[420px] items-center justify-center border border-[#e8e8e8] bg-white p-4">
                    <img
                      src={`data:image/jpeg;base64,${result.colored_pattern}`}
                      alt="Colored pattern"
                      className="max-h-[560px] w-full object-contain"
                    />
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </form>
  );
}