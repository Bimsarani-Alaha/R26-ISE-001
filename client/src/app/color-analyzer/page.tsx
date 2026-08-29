"use client";

import { motion } from "motion/react";
import { useState } from "react";
import { SiteNav } from "@/app/components/SiteNav";
import { SANS, SERIF } from "@/app/components/typography";
import { ColorTab } from "../components/ColorAnalyzer/ColorTab";
import { CvdTab } from "../components/ColorAnalyzer/CvdTab";
import { PatternTab } from "../components/ColorAnalyzer/PatternTab";

const TABS = [
  { id: "color", label: "COLOR" },
  { id: "cvd", label: "CVD" },
  { id: "pattern", label: "PATTERN" },
] as const;

type TabId = (typeof TABS)[number]["id"];

export default function ColorAnalyzerPage() {
  const [active, setActive] = useState<TabId>("color");

  return (
    <div className="min-h-screen w-full bg-white">
      <SiteNav backHref="/" backLabel="HOME" />

      <div className="px-8 py-10 md:px-16 md:py-16">
        <motion.div
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, ease: "easeOut" }}
          className="mb-10 text-center"
        >
          <p
            className="text-[10px] tracking-[0.3em] text-[#aaa] mb-3"
            style={SANS}
          >
            GARMENT INTELLIGENCE
          </p>
          <h1
            className="text-4xl md:text-5xl text-[#111] tracking-wide"
            style={{ ...SERIF, fontWeight: 300 }}
          >
            Color &amp; Pattern Analysis
          </h1>
        </motion.div>

        {/* TAB SWITCHER */}
        <div className="mx-auto mb-0 flex max-w-6xl justify-center border-b border-[#e8e8e8]">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActive(tab.id)}
              className={`px-6 py-4 text-xs tracking-[0.2em] transition-colors ${
                active === tab.id
                  ? "border-b border-[#111] text-[#111]"
                  : "text-[#999] hover:text-[#555]"
              }`}
              style={{ ...SANS, marginBottom: "-1px" }}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <motion.div
          key={active}
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="mx-auto max-w-6xl border border-[#e8e8e8]"
        >
          {active === "color" && <ColorTab />}
          {active === "cvd" && <CvdTab />}
          {active === "pattern" && <PatternTab />}
        </motion.div>
      </div>
    </div>
  );
}