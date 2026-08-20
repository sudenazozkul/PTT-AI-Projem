"use client";

import { Calculator } from "lucide-react";
import type { FormulaItem } from "@/lib/types";
import { useLanguage } from "@/lib/i18n";

const englishFormulas: Record<string, Partial<FormulaItem>> = {
  teslim_basarisi_pct: { label: "Delivery Success", formula: "delivered / accepted × 100", summary_formula: "Σ delivered / Σ accepted × 100", description: "Share of accepted shipments that were delivered." },
  gecikme_orani_pct: { label: "Delay Rate", formula: "delayed / accepted × 100", summary_formula: "Σ delayed / Σ accepted × 100", description: "Share of accepted shipments recorded as delayed." },
  iade_orani_pct: { label: "Return Rate", formula: "returned / accepted × 100", summary_formula: "Σ returned / Σ accepted × 100", description: "Share of accepted shipments that were returned." },
  sikayet_orani_binde: { label: "Complaint Rate", formula: "complaints / delivered × 1000", summary_formula: "Σ complaints / Σ delivered × 1000", description: "Number of complaints per 1,000 deliveries." },
  personel_verimliligi: { label: "Staff Productivity", formula: "delivered / total_staff", summary_formula: "Σ delivered / Σ staff-days", unit: "deliveries/staff-day", description: "Daily delivery output per staff member." },
  dagitici_is_yuku: { label: "Courier Workload", formula: "accepted / courier_count", summary_formula: "Σ accepted / Σ courier-days", unit: "shipments/courier-day", description: "Shipment volume assigned to each courier." },
  gonderi_basi_gelir: { label: "Revenue per Shipment", formula: "total_revenue / accepted", summary_formula: "Σ total_revenue / Σ accepted", unit: "TRY/shipment", description: "Revenue generated per accepted shipment." },
  ortalama_teslim_suresi: { label: "Weighted Average Delivery Time", formula: "Σ (average_delivery_time × delivered) / Σ delivered", summary_formula: "Weighted by delivered shipment volume", unit: "days", description: "Uses delivered shipment volume as the weight in branch and institution summaries." },
};

export function FormulaGrid({ formulas }: { formulas: FormulaItem[] }) {
  const { language, number, text } = useLanguage();
  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      {formulas.map((item) => {
        const localized = language === "en" ? { ...item, ...englishFormulas[item.key] } : item;
        const direction = item.direction === "higher"
          ? text("Yüksek olması iyi", "Higher is better")
          : item.direction === "lower"
            ? text("Düşük olması iyi", "Lower is better")
            : text("Kurum medyanına yakınlık", "Closeness to institution median");
        return (
          <article key={item.key} className="formula-card">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="font-extrabold">{localized.label}</p>
                <p className="mt-1 text-xs font-bold text-[var(--ptt-blue)]">{text("Birim", "Unit")}: {localized.unit}</p>
              </div>
              <div className="flex shrink-0 flex-col items-end gap-2">
                <Calculator className="text-amber-500" size={20} />
                <span className="rounded-full bg-amber-100 px-2.5 py-1 text-xs font-extrabold text-amber-800">
                  {text(`Ağırlık: %${number(item.weight_pct)}`, `Weight: ${number(item.weight_pct)}%`)}
                </span>
              </div>
            </div>
            <code className="formula-code mt-4">{localized.formula}</code>
            <p className="mt-3 text-sm leading-6 muted">{localized.description}</p>
            <p className="mt-2 text-xs font-bold text-[var(--ptt-blue)]">{text("Puan yönü", "Scoring direction")}: {direction}</p>
            <p className="mt-3 border-t border-slate-100 pt-3 text-xs font-semibold muted">{text("Dönem özeti", "Period summary")}: {localized.summary_formula}</p>
          </article>
        );
      })}
    </div>
  );
}
