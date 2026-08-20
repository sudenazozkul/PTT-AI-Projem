"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { LANGUAGE_COOKIE_KEY, LANGUAGE_STORAGE_KEY, type Language } from "@/lib/language";

export type { Language } from "@/lib/language";

type LanguageContextValue = {
  language: Language;
  locale: "tr-TR" | "en-GB";
  setLanguage: (language: Language) => void;
  text: (turkish: string, english: string) => string;
  number: (value: number, digits?: number) => string;
  currency: (value: number) => string;
  shortDate: (value: string) => string;
  monthDate: (value: string) => string;
  fullDate: (value: string) => string;
};

const LanguageContext = createContext<LanguageContextValue | null>(null);

function updateDocument(language: Language) {
  if (typeof document === "undefined") return;
  document.documentElement.lang = language;
  document.title = language === "tr"
    ? "PTT AI Şube Performans Danışmanı"
    : "PTT AI Branch Performance Advisor";
  const description = document.querySelector<HTMLMetaElement>('meta[name="description"]');
  if (description) {
    description.content = language === "tr"
      ? "PTT şube performansı için doğrulanabilir karar destek arayüzü"
      : "A verifiable decision-support interface for PTT branch performance";
  }
}

export function LanguageProvider({
  children,
  initialLanguage = "tr",
}: {
  children: React.ReactNode;
  initialLanguage?: Language;
}) {
  const [language, setLanguageState] = useState<Language>(initialLanguage);

  const setLanguage = useCallback((nextLanguage: Language) => {
    setLanguageState(nextLanguage);
    updateDocument(nextLanguage);
    if (typeof window !== "undefined") {
      try {
        window.localStorage.setItem(LANGUAGE_STORAGE_KEY, nextLanguage);
      } catch {
        // Cross-tab synchronization is optional when storage is unavailable.
      }
      try {
        document.cookie = `${LANGUAGE_COOKIE_KEY}=${nextLanguage}; Path=/; Max-Age=31536000; SameSite=Lax`;
      } catch {
        // The language still changes for this tab when cookies are unavailable.
      }
    }
  }, []);

  useEffect(() => {
    updateDocument(language);
  }, [language]);

  useEffect(() => {
    const syncLanguage = (event: StorageEvent) => {
      if (event.key !== LANGUAGE_STORAGE_KEY) return;
      const nextLanguage: Language = event.newValue === "en" ? "en" : "tr";
      setLanguageState(nextLanguage);
      updateDocument(nextLanguage);
    };
    window.addEventListener("storage", syncLanguage);
    return () => window.removeEventListener("storage", syncLanguage);
  }, []);

  const value = useMemo<LanguageContextValue>(() => {
    const locale = language === "tr" ? "tr-TR" : "en-GB";
    return {
      language,
      locale,
      setLanguage,
      text: (turkish, english) => language === "tr" ? turkish : english,
      number: (numberValue, digits = 0) => new Intl.NumberFormat(locale, {
        maximumFractionDigits: digits,
        minimumFractionDigits: digits,
      }).format(numberValue),
      currency: (numberValue) => new Intl.NumberFormat(locale, {
        style: "currency",
        currency: "TRY",
        maximumFractionDigits: 0,
      }).format(numberValue),
      shortDate: (dateValue) => new Intl.DateTimeFormat(locale, {
        day: "2-digit",
        month: "short",
      }).format(new Date(dateValue)),
      monthDate: (dateValue) => new Intl.DateTimeFormat(locale, {
        month: "short",
        year: "numeric",
      }).format(new Date(dateValue)),
      fullDate: (dateValue) => new Intl.DateTimeFormat(locale, {
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
      }).format(new Date(dateValue)),
    };
  }, [language, setLanguage]);

  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
}

export function useLanguage() {
  const context = useContext(LanguageContext);
  if (!context) throw new Error("useLanguage must be used inside LanguageProvider");
  return context;
}
