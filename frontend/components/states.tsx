"use client";

import { AlertTriangle, LoaderCircle } from "lucide-react";
import { useLanguage } from "@/lib/i18n";

export function LoadingState({ label }: { label?: string }) {
  const { text } = useLanguage();
  return <div className="surface grid min-h-64 place-items-center"><div className="flex items-center gap-3 font-bold"><LoaderCircle className="animate-spin" />{label ?? text("Veriler hazırlanıyor…", "Preparing data…")}</div></div>;
}

export function ErrorState({ message }: { message: string }) {
  return <div className="surface flex min-h-48 items-center justify-center gap-3 p-8 text-red-600"><AlertTriangle /> <span className="font-bold">{message}</span></div>;
}
