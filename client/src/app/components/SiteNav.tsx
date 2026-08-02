"use client";

import { ArrowLeft } from "lucide-react";
import { useRouter } from "next/navigation";
import type { ReactNode } from "react";
import { SANS, StyleAiWordmark } from "./typography";

type SiteNavProps = {
  backHref?: string;
  backLabel?: string;
  right?: ReactNode;
  centered?: boolean;
};

export function SiteNav({
  backHref,
  backLabel = "BACK",
  right,
  centered = false,
}: SiteNavProps) {
  const router = useRouter();

  if (centered) {
    return (
      <nav className="flex items-center justify-center px-8 py-6 border-b border-[#e8e8e8]">
        <StyleAiWordmark />
      </nav>
    );
  }

  return (
    <nav className="flex items-center justify-between px-8 md:px-16 py-6 border-b border-[#e8e8e8]">
      {backHref ? (
        <button
          type="button"
          onClick={() => router.push(backHref)}
          className="flex items-center gap-2 text-[#888] hover:text-[#111] transition-colors"
          style={SANS}
        >
          <ArrowLeft className="w-4 h-4" />
          <span className="text-xs tracking-[0.1em]">{backLabel}</span>
        </button>
      ) : (
        <div className="w-16" />
      )}
      <StyleAiWordmark />
      {right ?? <div className="w-16" />}
    </nav>
  );
}
