import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { cookies } from "next/headers";
import { LanguageProvider } from "@/lib/i18n";
import { LANGUAGE_COOKIE_KEY, type Language } from "@/lib/language";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

function localizedMetadata(language: Language): Metadata {
  return {
    title: language === "tr" ? "PTT AI Şube Performans Danışmanı" : "PTT AI Branch Performance Advisor",
    description: language === "tr"
      ? "PTT şube performansı için veri odaklı karar destek arayüzü"
      : "A data-driven decision-support interface for PTT branch performance",
    icons: { icon: "/ptt-logo.png" },
  };
}

export async function generateMetadata(): Promise<Metadata> {
  const language = (await cookies()).get(LANGUAGE_COOKIE_KEY)?.value === "en" ? "en" : "tr";
  return localizedMetadata(language);
}

export default async function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  const language: Language = (await cookies()).get(LANGUAGE_COOKIE_KEY)?.value === "en" ? "en" : "tr";
  return (
    <html lang={language} className="scroll-smooth">
      <body className={inter.variable}><LanguageProvider initialLanguage={language}>{children}</LanguageProvider></body>
    </html>
  );
}
