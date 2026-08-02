import type { CSSProperties } from "react";

export const SERIF: CSSProperties = {
  fontFamily: "'Cormorant Garamond', serif",
};

export const SANS: CSSProperties = {
  fontFamily: "'Inter', sans-serif",
};

export function StyleAiWordmark({ className = "" }: { className?: string }) {
  return (
    <span
      className={`text-xl tracking-widest text-[#111] ${className}`}
      style={{ ...SERIF, fontWeight: 300, letterSpacing: "0.3em" }}
    >
      STYLE AI
    </span>
  );
}
