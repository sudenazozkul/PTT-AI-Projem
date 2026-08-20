"use client";

import type { LucideIcon } from "lucide-react";
import { motion } from "motion/react";

export function MetricCard({ icon: Icon, label, value, detail, tone = "blue", delay = 0 }: {
  icon: LucideIcon; label: string; value: string; detail: string; tone?: "blue" | "green" | "red" | "yellow"; delay?: number;
}) {
  const tones = {
    blue: "bg-blue-50 text-blue-700",
    green: "bg-emerald-50 text-emerald-600",
    red: "bg-red-50 text-red-600",
    yellow: "bg-amber-50 text-amber-600",
  };
  return (
    <motion.div className="surface flex items-center gap-4 p-5" initial={{ opacity: 0, y: 22 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: .45, delay }} whileHover={{ y: -4 }}>
      <div className={`grid h-14 w-14 shrink-0 place-items-center rounded-2xl ${tones[tone]}`}><Icon size={26} /></div>
      <div><p className="mb-1 text-sm font-bold muted">{label}</p><p className="metric-value">{value}</p><p className="mt-2 text-xs font-semibold muted">{detail}</p></div>
    </motion.div>
  );
}
