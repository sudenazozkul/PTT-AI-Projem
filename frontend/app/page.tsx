"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import {
  ArrowRight, BarChart3, Box, Calculator, CalendarDays, CircleDollarSign,
  Clock3, MessageCircle, RefreshCw, ShieldCheck, Target, Users,
} from "lucide-react";
import { motion } from "motion/react";
import { BranchMetricBars, SingleMetricTrend } from "@/components/charts";
import { DataTable, type TableColumn } from "@/components/data-table";
import { FormulaGrid } from "@/components/formula-grid";
import { MetricCard } from "@/components/metric-card";
import { PageShell, Reveal } from "@/components/page-shell";
import { ErrorState, LoadingState } from "@/components/states";
import { api } from "@/lib/api";
import { useLanguage } from "@/lib/i18n";
import type { Branch, BranchSummary, MetadataResponse, MethodologyResponse, OverviewResponse } from "@/lib/types";

export default function OverviewPage() {
  const { currency, fullDate, language, number, text } = useLanguage();
  const [data, setData] = useState<OverviewResponse | null>(null);
  const [metadata, setMetadata] = useState<MetadataResponse | null>(null);
  const [methodology, setMethodology] = useState<MethodologyResponse | null>(null);
  const [branches, setBranches] = useState<Branch[]>([]);
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [province, setProvince] = useState("");
  const [branchType, setBranchType] = useState("");
  const [branchCode, setBranchCode] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const shortcuts = [
    [CalendarDays, text("Genel Performans", "Overall Performance"), "#performans"],
    [BarChart3, text("Şube Performansı", "Branch Performance"), "/sube-detayi"],
    [Users, text("Karşılaştırma", "Comparison"), "/sube-karsilastirma"],
    [ShieldCheck, text("Risk ve Bulgular", "Risks & Findings"), "/analiz-oneriler"],
    [Calculator, text("KPI Formülleri", "KPI Formulas"), "#formuller"],
  ] as const;

  const rankingColumns: TableColumn<BranchSummary>[] = [
    { label: text("Sıra", "Rank"), render: (row) => row.siralama ?? "—" },
    { label: text("Şube", "Branch"), render: (row) => <strong>{row.sube_adi}</strong> },
    { label: text("Genel Başarı (/100)", "Overall Success (/100)"), align: "right", render: (row) => <strong>{number(row.genel_basari_puani, 2)}</strong> },
    { label: text("Toplam Gönderi", "Total Shipments"), align: "right", render: (row) => number(row.toplam_kabul) },
    { label: text("Teslim Başarısı (%)", "Delivery Success (%)"), align: "right", render: (row) => number(row.teslim_basarisi_pct, 2) },
    { label: text("Gecikme Oranı (%)", "Delay Rate (%)"), align: "right", render: (row) => number(row.gecikme_orani_pct, 2) },
    { label: text("Teslim Süresi (gün)", "Delivery Time (days)"), align: "right", render: (row) => number(row.ortalama_teslim_suresi, 2) },
    { label: text("Şikâyet Oranı (‰)", "Complaint Rate (‰)"), align: "right", render: (row) => number(row.sikayet_orani_binde, 2) },
  ];

  function localizedBranchType(value: string) {
    if (language === "tr") return value;
    return ({ Merkez: "Central", Büyük: "Large", Orta: "Medium" } as Record<string, string>)[value] ?? value;
  }

  function percentage(value: number, digits = 2) {
    const formatted = number(value, digits);
    return language === "tr" ? `%${formatted}` : `${formatted}%`;
  }

  useEffect(() => {
    Promise.all([api.metadata(), api.methodology(), api.branches(), api.overview()])
      .then(([meta, methods, branchItems, overview]) => {
        setMetadata(meta); setMethodology(methods); setBranches(branchItems); setData(overview);
        setStartDate(meta.min_date); setEndDate(meta.max_date);
      })
      .catch((value: Error) => setError(value.message))
      .finally(() => setLoading(false));
  }, []);

  const availableBranches = useMemo(() => branches.filter((branch) =>
    (!province || branch.il === province) && (!branchType || branch.sube_tipi === branchType),
  ), [branches, province, branchType]);

  async function applyFilters() {
    setLoading(true); setError("");
    try {
      setData(await api.overview({
        startDate, endDate,
        provinces: province ? [province] : [],
        branchTypes: branchType ? [branchType] : [],
        branchCodes: branchCode ? [branchCode] : [],
      }));
    } catch (value) { setError((value as Error).message); }
    finally { setLoading(false); }
  }

  const metrics = data?.metrics;
  return (
    <PageShell>
      <section className="border-y border-slate-100 bg-white">
        <div className="page-wrap grid min-h-[420px] items-center gap-10 py-10 lg:grid-cols-[1fr_.9fr]">
          <motion.div initial={{ opacity: 0, x: -24 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: .6 }}>
            <p className="eyebrow mb-4">{text("Doğrulanmış veri • açıklanabilir hesaplama", "Verified data • explainable calculation")}</p>
            <h1 className="display max-w-[760px]">{text("Veriden Karara,", "From Data to Decisions,")}<br />{text("Şubeden Geleceğe", "From Branches to the Future")}</h1>
            <p className="mt-6 max-w-[650px] text-lg leading-8 muted">{text(
              "PTT şubelerinin gerçek CSV kayıtlarını; mevcut KPI, kural tabanlı analiz ve anomali kodlarıyla inceleyen karar destek ekranı.",
              "A decision-support dashboard that analyzes actual CSV records from PTT branches using the existing KPIs, rule-based analysis and anomaly code.",
            )}</p>
            <div className="mt-8 flex flex-wrap gap-4"><a href="#performans" className="yellow-button"><BarChart3 size={20} /> {text("Performansı İncele", "Review Performance")}</a><a href="#formuller" className="outline-button border-0">{text("Formülleri Gör", "View Formulas")} <ArrowRight size={18} /></a></div>
          </motion.div>
          <motion.div className="hero-visual surface grid content-center gap-5 p-8" initial={{ opacity: 0, scale: .97 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: .7, delay: .1 }}>
            <div className="relative z-10 grid grid-cols-2 gap-4">
              <div className="soft-surface p-5"><p className="text-xs font-bold muted">{text("Doğrulanmış Kayıt", "Verified Records")}</p><p className="mt-2 text-4xl font-black">{metadata ? number(metadata.record_count) : "—"}</p></div>
              <div className="soft-surface p-5"><p className="text-xs font-bold muted">{text("Şube Sayısı", "Branch Count")}</p><p className="mt-2 text-4xl font-black">{metadata ? number(metadata.branch_count) : "—"}</p></div>
              <div className="soft-surface p-5"><p className="text-xs font-bold muted">{text("Teslim Başarısı", "Delivery Success")}</p><p className="mt-2 text-4xl font-black text-emerald-600">{metrics ? percentage(metrics.teslim_basarisi_pct) : "—"}</p></div>
              <div className="soft-surface p-5"><p className="text-xs font-bold muted">{text("Analiz Dönemi", "Analysis Period")}</p><p className="mt-2 text-lg font-black">{data?.period ? `${fullDate(data.period.start)} – ${fullDate(data.period.end)}` : "—"}</p></div>
            </div>
            <p className="relative z-10 text-center text-xs font-bold muted">{text(
              "KPI formülleri yeniden yazılmaz; mevcut Python modülü doğrudan çağrılır.",
              "KPI formulas are not reimplemented; the existing Python module is called directly.",
            )}</p>
          </motion.div>
        </div>
      </section>

      <div className="page-wrap relative -mt-2 grid grid-cols-2 overflow-hidden rounded-[22px] border border-slate-200 bg-white shadow-[0_18px_45px_rgba(0,43,73,.1)] md:grid-cols-5">
        {shortcuts.map(([Icon, label, href]) => <Link key={label} href={href} className="flex min-h-24 items-center justify-center gap-3 border-r border-slate-200 px-3 font-bold transition hover:bg-amber-50"><Icon className="text-[var(--ptt-blue)]" /><span>{label}</span></Link>)}
      </div>

      <section id="performans" className="page-wrap py-14">
        <div className="mb-7"><p className="eyebrow mb-2">{text("Rapor filtreleri", "Report filters")}</p><h2 className="section-title text-[28px]">{text("Genel Performans Özeti", "Overall Performance Summary")}</h2></div>
        <div className="filter-panel mb-7">
          <label className="filter-label">{text("Başlangıç", "Start")}<input className="date-control" type="date" min={metadata?.min_date} max={metadata?.max_date} value={startDate} onChange={(event) => setStartDate(event.target.value)} /></label>
          <label className="filter-label">{text("Bitiş", "End")}<input className="date-control" type="date" min={metadata?.min_date} max={metadata?.max_date} value={endDate} onChange={(event) => setEndDate(event.target.value)} /></label>
          <label className="filter-label">{text("İl", "Province")}<select className="select-control" value={province} onChange={(event) => { setProvince(event.target.value); setBranchCode(""); }}><option value="">{text("Tüm İller", "All Provinces")}</option>{metadata?.provinces.map((item) => <option key={item}>{item}</option>)}</select></label>
          <label className="filter-label">{text("Şube tipi", "Branch type")}<select className="select-control" value={branchType} onChange={(event) => { setBranchType(event.target.value); setBranchCode(""); }}><option value="">{text("Tüm Tipler", "All Types")}</option>{metadata?.branch_types.map((item) => <option key={item} value={item}>{localizedBranchType(item)}</option>)}</select></label>
          <label className="filter-label">{text("Şube", "Branch")}<select className="select-control" value={branchCode} onChange={(event) => setBranchCode(event.target.value)}><option value="">{text("Tüm Uygun Şubeler", "All Eligible Branches")}</option>{availableBranches.map((item) => <option key={item.sube_kodu} value={item.sube_kodu}>{item.sube_adi}</option>)}</select></label>
          <button className="yellow-button" onClick={applyFilters} disabled={loading}><RefreshCw size={18} /> {text("Uygula", "Apply")}</button>
        </div>
        {error ? <ErrorState message={text("Veriler alınamadı. Lütfen tekrar deneyin.", "Unable to retrieve data. Please try again.")} /> : loading || !data ? <LoadingState /> : !metrics ? <ErrorState message={text("Seçilen filtrelere uygun performans kaydı bulunamadı.", "No performance records match the selected filters.")} /> : (
          <div className="space-y-7">
            <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-5">
              <MetricCard icon={Box} label={text("Toplam Gönderi", "Total Shipments")} value={number(metrics.toplam_gonderi)} detail={text("Σ kabul_edilen", "Σ accepted shipments")} tone="blue" />
              <MetricCard icon={Target} label={text("Teslim Başarısı", "Delivery Success")} value={percentage(metrics.teslim_basarisi_pct)} detail={text("Ağırlıklı oran", "Weighted rate")} tone="green" delay={.04} />
              <MetricCard icon={Clock3} label={text("Ortalama Teslim Süresi", "Average Delivery Time")} value={`${number(metrics.ortalama_teslim_suresi, 2)} ${text("gün", "days")}`} detail={text("Teslimat ağırlıklı", "Delivery weighted")} tone="yellow" delay={.08} />
              <MetricCard icon={MessageCircle} label={text("Toplam Şikâyet", "Total Complaints")} value={number(metrics.toplam_sikayet)} detail={`${number(metrics.sikayet_orani_binde, 2)}‰`} tone="red" delay={.12} />
              <MetricCard icon={CircleDollarSign} label={text("Toplam Gelir", "Total Revenue")} value={currency(metrics.toplam_gelir)} detail={text("Σ toplam_gelir", "Σ total revenue")} tone="yellow" delay={.16} />
            </div>
            <div className="grid gap-5 md:grid-cols-2">
              <Reveal className="surface border-l-[6px] border-l-emerald-500 p-6"><p className="text-sm font-bold muted">{text("En Başarılı Şube", "Top-Performing Branch")}</p><p className="mt-2 text-2xl font-black">{data.highlights?.best_branch.sube_adi}</p><p className="mt-2 font-bold text-emerald-600">{text("Genel başarı puanı", "Overall success score")}: {number(data.highlights?.best_branch.genel_basari_puani ?? 0, 2)}/100</p></Reveal>
              <Reveal delay={.06} className="surface border-l-[6px] border-l-red-500 p-6"><p className="text-sm font-bold muted">{text("En Riskli Şube", "Highest-Risk Branch")}</p><p className="mt-2 text-2xl font-black">{data.highlights?.risk_branch.sube_adi}</p><p className="mt-2 font-bold text-red-600">{text("Genel başarı puanı", "Overall success score")}: {number(data.highlights?.risk_branch.genel_basari_puani ?? 0, 2)}/100</p></Reveal>
            </div>
            <div className="grid gap-6 lg:grid-cols-2">
              <Reveal className="surface p-6"><h3 className="section-title">{text("Şube Genel Başarı Karşılaştırması", "Branch Overall Success Comparison")}</h3><p className="mt-1 text-sm muted">{text("Sekiz KPI'nın ağırlıklı ve göreli birleşik puanı", "Weighted, relative composite score across eight KPIs")}</p><div className="mt-4 h-[380px]"><BranchMetricBars data={[...data.branches].reverse()} metric="genel_basari_puani" label={text("Genel başarı puanı", "Overall success score")} unit="/100" /></div></Reveal>
              <Reveal delay={.06} className="surface p-6"><h3 className="section-title">{text("Aylık Teslim Başarısı Trendi", "Monthly Delivery Success Trend")}</h3><p className="mt-1 text-sm muted">{text("Σ teslim / Σ kabul × 100", "Σ delivered / Σ accepted × 100")}</p><div className="mt-4 h-[380px]"><SingleMetricTrend data={data.monthly} metric="teslim_basarisi_pct" label={text("Teslim başarısı", "Delivery success")} unit="%" /></div></Reveal>
              <Reveal className="surface p-6"><h3 className="section-title">{text("Aylık Gecikme Oranı", "Monthly Delay Rate")}</h3><p className="mt-1 text-sm muted">{text("Σ geciken / Σ kabul × 100", "Σ delayed / Σ accepted × 100")}</p><div className="mt-4 h-[310px]"><SingleMetricTrend data={data.monthly} metric="gecikme_orani_pct" label={text("Gecikme oranı", "Delay rate")} color="#c84b45" unit="%" area /></div></Reveal>
              <Reveal delay={.06} className="surface p-6"><h3 className="section-title">{text("Her 1.000 Teslimattaki Şikâyet", "Complaints per 1,000 Deliveries")}</h3><p className="mt-1 text-sm muted">{text("Σ şikâyet / Σ teslim × 1000", "Σ complaints / Σ delivered × 1,000")}</p><div className="mt-4 h-[310px]"><SingleMetricTrend data={data.monthly} metric="sikayet_orani_binde" label={text("Şikâyet oranı", "Complaint rate")} color="#d6a900" unit="‰" /></div></Reveal>
            </div>
            <Reveal className="surface p-6"><div className="mb-5 flex flex-wrap items-end justify-between gap-3"><div><h3 className="section-title">{text("Genel Başarı Sıralaması", "Overall Success Ranking")}</h3><p className="mt-1 text-sm muted">{number(data.record_count)} {text("günlük kayıt", "daily records")} • {number(data.branch_count)} {text("şube", "branches")} • {text("aynı dönem kurum geneline göre", "compared with the institution-wide result for the same period")}</p></div><span className="text-sm font-bold muted">{data.period && `${fullDate(data.period.start)} – ${fullDate(data.period.end)}`}</span></div><DataTable rows={data.branches} columns={rankingColumns} rowKey={(row) => row.sube_kodu} /></Reveal>
          </div>
        )}
      </section>

      <section id="formuller" className="border-y border-slate-200 bg-white py-14">
        <div className="page-wrap">
          <p className="eyebrow mb-2">{text("Mevcut kpi.py kaynaklı", "Sourced from the existing kpi.py")}</p>
          <h2 className="section-title text-[28px]">{text("KPI Formülleri ve Matematiksel İfadeler", "KPI Formulas and Mathematical Expressions")}</h2>
          <p className="mb-7 mt-3 max-w-4xl leading-7 muted">{text(
            "Günlük hesaplarda oranlar satır bazında; şube ve kurum özetlerinde günlük yüzdelerin basit ortalaması yerine toplamlar üzerinden ağırlıklı yöntem kullanılır. Her karttaki ağırlık, ilgili KPI'nın genel başarı puanına ayırdığı payı gösterir.",
            "Daily ratios are calculated row by row; branch and institution summaries use weighted aggregation over totals instead of a simple average of daily percentages. The weight on each card shows that KPI's share of the overall success score.",
          )}</p>
          {methodology ? <>
            <div className="method-note mb-6"><strong>{text(methodology.general_success.label, "Overall Success Score")}:</strong> <code>{text(methodology.general_success.formula, "Σ (KPI subscore × KPI weight)")}</code> • {text(methodology.general_success.method, "Relative percentile scoring against all branches in the same date range")}</div>
            <FormulaGrid formulas={methodology.kpi_formulas} />
            <p className="method-note mt-6"><strong>{text("Önemli", "Important")}:</strong> {text(
              methodology.scoring_note,
              "Until official institutional targets are defined, the overall success score is a relative composite performance score calculated against branches in the same period; it is not an actual probability of success or a causal effect.",
            )}</p>
          </> : <LoadingState />}
        </div>
      </section>
    </PageShell>
  );
}
