"use client";

import { Star } from "lucide-react";
import { motion } from "motion/react";
import { useRouter } from "next/navigation";
import { SANS, SERIF } from "@/app/components/typography";
import type { ClothingItem } from "@/app/data/recommendations";

export function RelatedItemCard({
  item,
  delay,
}: {
  item: ClothingItem;
  delay: number;
}) {
  const router = useRouter();

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay }}
      onClick={() => router.push(`/detail/${item.id}`)}
      className="group cursor-pointer"
    >
      <div className="relative aspect-[3/4] overflow-hidden bg-[#f5f5f5] mb-3">
        <img
          src={item.image}
          alt={item.name}
          className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105"
        />
        <div className="absolute inset-0 bg-black/0 group-hover:bg-black/10 transition-colors duration-300" />
      </div>
      <div className="flex items-start justify-between">
        <div>
          <p
            className="text-sm text-[#111] tracking-wide mb-1"
            style={{ ...SERIF, fontWeight: 500 }}
          >
            {item.name}
          </p>
          <p className="text-xs text-[#888]" style={SANS}>
            {item.price}
          </p>
        </div>
        <div className="flex items-center gap-0.5 mt-0.5">
          <Star className="w-3 h-3 fill-[#111] text-[#111]" />
          <span className="text-xs text-[#888]" style={SANS}>
            {item.rating}
          </span>
        </div>
      </div>
    </motion.div>
  );
}
