"use client";

import { ArrowUpRight } from "lucide-react";
import { motion } from "motion/react";
import { useRouter } from "next/navigation";
import { SANS, SERIF, StyleAiWordmark } from "@/app/components/typography";
import { Button } from "@/app/components/ui/button";

export default function HomePage() {
  const router = useRouter();

  return (
    <div className="min-h-screen w-full bg-white flex flex-col">
      {/* Nav */}
      <nav className="flex items-center justify-between px-8 md:px-16 py-6 border-b border-[#e8e8e8]">
        <div className="flex items-center gap-8">
          {["WOMEN", "MEN", "OCCASION"].map((item) => (
            <button
              key={item}
              type="button"
              className="text-[#111] text-xs tracking-[0.15em] hover:text-[#888] transition-colors hidden md:block"
              style={{ ...SANS, fontWeight: 400 }}
            >
              {item}
            </button>
          ))}
        </div>
        <div className="text-center">
          <StyleAiWordmark className="text-2xl" />
        </div>
        <div className="flex items-center gap-6">
          {/* NEW: Color Analyzer button in navigation */}
          <button
            type="button"
            onClick={() => router.push("/color-analyzer")}
            className="text-[#111] text-xs tracking-[0.15em] hover:text-[#888] transition-colors hidden md:block"
            style={{ ...SANS, fontWeight: 400 }}
          >
            ANALYZER
          </button>

          {/* Clothing Matcher */}
          <button
          type="button"
          onClick={() => router.push("/cvd-matcher")}
          className="text-[#111] text-xs tracking-[0.15em] hover:text-[#888] transition-colors hidden md:block"
          style={{ ...SANS, fontWeight: 400 }}
                  >
            CLOTHING MATCHER
          </button>
          <button
            type="button"
            onClick={() => router.push("/input")}
            className="text-[#111] text-xs tracking-[0.15em] hover:text-[#888] transition-colors hidden md:block"
            style={{ ...SANS, fontWeight: 400 }}
          >
            SKIP
          </button>
          <Button
            onClick={() => router.push("/input")}
            variant="ghost"
            size="sm"
            className="text-[#111] text-xs tracking-[0.15em] hover:text-[#888] transition-colors h-auto p-0 rounded-none bg-transparent hover:bg-transparent"
            style={{ ...SANS, fontWeight: 400 }}
          >
            LOGIN
          </Button>
          <Button
            onClick={() => router.push("/size")}
            variant="outline"
            size="sm"
            className="text-[#111] text-xs tracking-[0.15em] rounded-none border-[#111] hover:bg-[#111] hover:text-white transition-colors h-auto py-1.5 px-4"
            style={{ ...SANS, fontWeight: 400 }}
          >
            POSE DETECTION
          </Button>
        </div>
      </nav>

      {/* Hero */}
      <div className="relative flex-1 overflow-hidden">
        <motion.div
          initial={{ scale: 1.04, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 1.2, ease: "easeOut" }}
          className="w-full h-[82vh] relative"
        >
          <img
            src="https://images.unsplash.com/photo-1659522761084-79196b64abe4?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&w=1800"
            alt="Fashion hero"
            className="w-full h-full object-cover object-top"
          />
          {/* Subtle overlay */}
          <div className="absolute inset-0 bg-black/10" />

          {/* Hero text overlay */}
          <div className="absolute inset-0 flex flex-col items-center justify-end pb-16 px-6 text-center">
            <motion.h1
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.9, delay: 0.4 }}
              className="text-white text-4xl md:text-6xl lg:text-7xl mb-8 tracking-wider"
              style={{ ...SERIF, fontWeight: 300 }}
            >
              LOOKS YOU REMEMBER
            </motion.h1>
            <div className="flex flex-col sm:flex-row items-center gap-4">
              <motion.button
                type="button"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.7, delay: 0.7 }}
                onClick={() => router.push("/input")}
                className="flex items-center gap-2 bg-white/90 backdrop-blur-sm text-[#111] px-7 py-3 text-xs tracking-[0.2em] hover:bg-white transition-all duration-300"
                style={{ ...SANS, fontWeight: 400 }}
              >
                START NOW
                <ArrowUpRight className="w-3.5 h-3.5" />
              </motion.button>
              <motion.button
                type="button"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.7, delay: 0.8 }}
                onClick={() => router.push("/size")}
                className="flex items-center gap-2 border border-white/80 text-white px-7 py-3 text-xs tracking-[0.2em] hover:bg-white hover:text-[#111] transition-all duration-300"
                style={{ ...SANS, fontWeight: 400 }}
              >
                POSE DETECTION
                <ArrowUpRight className="w-3.5 h-3.5" />
              </motion.button>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Feature strip - UPDATED with COLOR ANALYZER */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.7, delay: 0.9 }}
        className="border-t border-[#e8e8e8]"
      >
        <div className="grid grid-cols-2 md:grid-cols-5 divide-x divide-y md:divide-y-0 divide-[#e8e8e8]">
          {[
            { icon: "◯", label: "AI OUTFIT CURATION", action: null },
            { icon: "◈", label: "OCCASION MATCHING", action: null },
            { icon: "◻", label: "STYLE INTELLIGENCE", action: null },
            { icon: "⊹", label: "PERSONALIZED PICKS", action: null },
            // NEW: Color Analyzer button in feature strip
            { 
              icon: "●", 
              label: "COLOR ANALYZER", 
              action: () => router.push("/color-analyzer"),
              isClickable: true 
            },
          ].map((feat) => (
            <div
              key={feat.label}
              onClick={feat.action || undefined}
              className={`flex flex-col items-center gap-3 py-8 px-6 transition-colors ${
                feat.isClickable 
                  ? "cursor-pointer hover:bg-[#f5f0eb]" 
                  : "cursor-default hover:bg-[#fafafa]"
              }`}
            >
              <span className="text-lg text-[#999]">{feat.icon}</span>
              <span
                className="text-[10px] tracking-[0.2em] text-[#555]"
                style={{ ...SANS, fontWeight: 400 }}
              >
                {feat.label}
              </span>
            </div>
          ))}
        </div>
      </motion.div>

      {/* Membership-style section */}
      <div className="px-8 md:px-16 py-16 bg-[#fafafa] border-t border-[#e8e8e8]">
        <motion.h2
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 1 }}
          className="text-center text-2xl md:text-3xl tracking-[0.25em] text-[#111] mb-12"
          style={{ ...SERIF, fontWeight: 400 }}
        >
          HOW IT WORKS
        </motion.h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-0 max-w-3xl mx-auto border border-[#e5e5e5]">
          {[
            {
              step: "01",
              title: "DESCRIBE",
              desc: "Tell us your occasion, style, and preferences in your own words.",
            },
            {
              step: "02",
              title: "ANALYSE",
              desc: "Our AI reads your needs and matches them to curated outfit options.",
            },
            {
              step: "03",
              title: "DISCOVER",
              desc: "Browse personalized recommendations crafted just for you.",
            },
          ].map((item, i) => (
            <motion.div
              key={item.step}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 1.1 + i * 0.1 }}
              className={`flex flex-col items-center text-center p-10 ${
                i < 2
                  ? "border-b md:border-b-0 md:border-r border-[#e5e5e5]"
                  : ""
              } bg-white`}
            >
              <span
                className="text-[11px] tracking-[0.25em] text-[#aaa] mb-4"
                style={SANS}
              >
                {item.step}
              </span>
              <span
                className="text-base tracking-[0.2em] text-[#111] mb-3"
                style={{ ...SERIF, fontWeight: 500 }}
              >
                {item.title}
              </span>
              <p
                className="text-xs text-[#888] leading-relaxed"
                style={{ ...SANS, fontWeight: 300 }}
              >
                {item.desc}
              </p>
            </motion.div>
          ))}
        </div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.4 }}
          className="flex justify-center mt-10"
        >
          <Button
            onClick={() => router.push("/input")}
            variant="outline"
            className="flex items-center gap-2 border border-[#111] text-[#111] px-8 py-3 text-xs tracking-[0.2em] rounded-none h-auto bg-transparent hover:bg-[#111] hover:text-white transition-all duration-300"
            style={{ ...SANS, fontWeight: 400 }}
          >
            GET STARTED
            <ArrowUpRight className="w-3.5 h-3.5" />
          </Button>
        </motion.div>
      </div>
    </div>
  );
}