"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { CircleCheck, Database, Languages } from "lucide-react";
import { motion } from "motion/react";
import { useLanguage, type Language } from "@/lib/i18n";

const links = [
  ["/", "Genel Bakış", "Overview"],
  ["/sube-detayi", "Şube Detayı", "Branch Detail"],
  ["/sube-karsilastirma", "Şube Karşılaştırma", "Branch Comparison"],
  ["/analiz-oneriler", "Analiz & Öneriler", "Analysis & Recommendations"],
  ["/ai-danisman", "AI Danışman", "AI Advisor"],
] as const;

export function SiteHeader() {
  const pathname = usePathname();
  const { language, setLanguage, text } = useLanguage();
  const languageButton = (value: Language, label: string, accessibleLabel: string) => (
    <button
      type="button"
      onClick={() => setLanguage(value)}
      aria-pressed={language === value}
      aria-label={accessibleLabel}
      className={`min-h-11 min-w-11 rounded-full px-3 py-2 text-xs font-black transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--ptt-navy)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--ptt-yellow)] ${language === value ? "bg-[var(--ptt-navy)] text-white shadow-sm" : "text-[var(--ptt-navy)] hover:bg-white/60"}`}
    >
      {label}
    </button>
  );
  return (
    <header className="sticky top-0 z-50 bg-white/95 shadow-[0_4px_18px_rgba(0,43,73,.06)] backdrop-blur-xl">
      <div className="bg-[var(--ptt-yellow)]">
        <div className="page-wrap flex h-[70px] items-center gap-2 sm:gap-5">
          <div className="relative h-[54px] w-[120px] shrink-0 overflow-hidden sm:w-[150px]" aria-label="PTT">
            <Image src="/ptt-logo.png" alt={text("PTT logosu", "PTT logo")} fill className="object-cover" priority sizes="150px" />
          </div>
          <span className="header-divider h-9 w-px bg-[var(--ptt-navy)]/35" />
          <span className="header-title text-[18px] font-extrabold tracking-[-.02em]">{text("AI Şube Performans Danışmanı", "AI Branch Performance Advisor")}</span>
          <div className="ml-auto flex shrink-0 items-center gap-1 rounded-full border border-[var(--ptt-navy)]/25 bg-white/35 p-1" role="group" aria-label={text("Dil seçimi", "Language selection")}>
            <Languages size={16} className="language-icon ml-2 text-[var(--ptt-navy)]" aria-hidden="true" />
            {languageButton("tr", "TR", "Türkçe")}
            <span className="text-xs font-black text-[var(--ptt-navy)]/45" aria-hidden="true">|</span>
            {languageButton("en", "EN", "English")}
          </div>
        </div>
      </div>
      <div className="page-wrap flex min-h-[72px] items-center gap-5">
        <nav className="desktop-nav flex flex-1 items-center justify-center gap-3" aria-label={text("Ana navigasyon", "Main navigation")}>
          {links.map(([href, turkishLabel, englishLabel]) => {
            const active = pathname === href;
            return (
              <Link key={href} href={href} aria-current={active ? "page" : undefined} className="relative rounded-xl px-4 py-3 text-sm font-bold text-[var(--ptt-navy)]">
                {active && <motion.span layoutId="active-nav" className="absolute inset-0 -z-10 rounded-xl bg-[var(--ptt-yellow)]" transition={{ type: "spring", stiffness: 420, damping: 34 }} />}
                {text(turkishLabel, englishLabel)}
              </Link>
            );
          })}
        </nav>
        <div className="header-actions flex items-center gap-2 rounded-full border border-emerald-100 bg-emerald-50 px-4 py-2 text-xs font-extrabold text-emerald-700">
          <Database size={16} /><span>{text("CSV bağlantısı aktif", "CSV connection active")}</span><CircleCheck size={16} />
        </div>
      </div>
    </header>
  );
}
