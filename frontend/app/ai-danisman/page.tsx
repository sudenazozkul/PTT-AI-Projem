"use client";

import { Bot, Braces, Database, LockKeyhole, Send } from "lucide-react";
import { PageShell, Reveal } from "@/components/page-shell";
import { useLanguage } from "@/lib/i18n";

export default function AdvisorPage() {
  const { text } = useLanguage();

  return (
    <PageShell>
      <section className="page-wrap py-10">
        <div className="mb-8">
          <p className="eyebrow mb-3">{text("Gelecek entegrasyon alanı", "Future integration area")}</p>
          <h1 className="page-title">{text("AI Danışman", "AI Advisor")}</h1>
          <p className="mt-3 max-w-3xl text-lg leading-8 muted">
            {text(
              "Bu alan, daha sonra bağlanacak LLM için bilinçli olarak boş bırakılmıştır. Şu anda yapay zekâ yanıtı, örnek sohbet veya sahte içgörü üretilmez.",
              "This area is intentionally reserved for a future LLM connection. It currently produces no AI responses, sample conversations or fabricated insights.",
            )}
          </p>
        </div>
        <Reveal className="ai-placeholder grid min-h-[620px] gap-8 p-7 lg:grid-cols-[1.35fr_.65fr]">
          <div className="flex flex-col rounded-[22px] border border-slate-200 bg-white/90 p-6 shadow-sm">
            <div className="flex items-center gap-4 border-b border-slate-100 pb-5">
              <div className="grid h-12 w-12 place-items-center rounded-full bg-[var(--ptt-yellow)]"><Bot /></div>
              <div><p className="font-extrabold">{text("LLM bağlantısı bekleniyor", "Awaiting LLM connection")}</p><p className="mt-1 text-sm muted">{text("Henüz bir model veya sağlayıcı yapılandırılmadı.", "No model or provider has been configured yet.")}</p></div>
            </div>
            <div className="grid flex-1 place-items-center py-16 text-center">
              <div>
                <div className="mx-auto grid h-28 w-28 place-items-center rounded-full border border-dashed border-slate-300 bg-slate-50"><LockKeyhole size={42} className="text-slate-400" /></div>
                <h2 className="mt-6 text-2xl font-black">{text("Sohbet alanı boş", "Chat area is empty")}</h2>
                <p className="mx-auto mt-3 max-w-xl leading-7 muted">
                  {text(
                    "LLM entegrasyonu tamamlandığında mesajlar ve model yanıtları burada gösterilebilir. Mevcut KPI, analiz ve anomali API’leri bağlam kaynağı olarak kullanılabilir.",
                    "Once the LLM integration is complete, messages and model responses can appear here. The existing KPI, analysis and anomaly APIs can provide context.",
                  )}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3 rounded-2xl border border-slate-200 bg-slate-50 p-2 opacity-60">
              <input className="min-w-0 flex-1 bg-transparent px-4 py-3 outline-none" placeholder={text("LLM entegrasyonundan sonra kullanılacak…", "Available after LLM integration…")} disabled />
              <button className="yellow-button" disabled aria-label={text("Gönder", "Send")}><Send size={19} /></button>
            </div>
          </div>
          <aside className="space-y-4">
            <h2 className="section-title">{text("Entegrasyon İçin Hazır Yapı", "Integration-Ready Structure")}</h2>
            <div className="surface p-5"><Database className="text-blue-600" /><p className="mt-4 font-extrabold">{text("Veri Bağlamı", "Data Context")}</p><p className="mt-2 text-sm leading-6 muted">{text("KPI, bulgu, öneri ve anomali endpoint’leri LLM bağlamına eklenebilir.", "KPI, finding, recommendation and anomaly endpoints can be added to the LLM context.")}</p></div>
            <div className="surface p-5"><Braces className="text-amber-600" /><p className="mt-4 font-extrabold">{text("Backend Alanı", "Backend Extension Point")}</p><p className="mt-2 text-sm leading-6 muted">{text("AI endpoint’i eklemek için ", "An explanatory TODO for adding an AI endpoint is included in ")}<code>backend/main.py</code>{text(" içinde açıklayıcı TODO bırakıldı.", ".")}</p></div>
            <div className="surface p-5"><LockKeyhole className="text-emerald-600" /><p className="mt-4 font-extrabold">{text("Anahtar Güvenliği", "API Key Security")}</p><p className="mt-2 text-sm leading-6 muted">{text("Model API anahtarı yalnızca backend ortam değişkeninde tutulmalıdır; frontend koduna yazılmamalıdır.", "The model API key must be kept only in a backend environment variable and must never be added to frontend code.")}</p></div>
          </aside>
        </Reveal>
      </section>
    </PageShell>
  );
}
