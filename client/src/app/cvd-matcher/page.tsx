"use client";

import { useRouter } from "next/navigation";
import { SANS, SERIF, StyleAiWordmark } from "@/app/components/typography";
import ClothingMatcher from "@/app/components/clothingMatcher";
import { SiteNav } from "@/app/components/SiteNav";

export default function ClothMatcherPage() {
  const router = useRouter();

  return (
    <div className="min-h-screen w-full bg-white flex flex-col">
      <SiteNav backHref="/" backLabel="HOME" />
      {/* Page heading */}
      <div className="px-8 md:px-16 pt-14 pb-8 text-center border-b border-[#e8e8e8] bg-[#fafafa]">
        <span
          className="text-[11px] tracking-[0.25em] text-[#aaa] mb-3 block"
          style={SANS}
        >
          COLOUR VISION TOOL
        </span>
        <h1
          className="text-2xl md:text-3xl tracking-[0.15em] text-[#111]"
          style={{ ...SERIF, fontWeight: 400 }}
        >
          CLOTHING MATCHER
        </h1>
      </div>

      {/* Tool */}
      <main className="flex-1 flex items-center justify-center p-6 md:p-16 bg-[#fafafa]">
        <ClothingMatcher />
      </main>
    </div>
  );
}