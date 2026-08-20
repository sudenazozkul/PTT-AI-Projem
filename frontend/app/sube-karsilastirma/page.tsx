"use client";

import { useEffect, useMemo, useState } from "react";
import { Check, Clock3, Coins, RefreshCw, Target, Trophy, Users } from "lucide-react";
import { BranchMetricBars, MultiBranchTrend, branchColor } from "@/components/charts";
import { DataTable, type TableColumn } from "@/components/data-table";
import { PageShell, Reveal } from "@/components/page-shell";
import { ErrorState, LoadingState } from "@/components/states";
import { api } from "@/lib/api";
import { useLanguage } from "@/lib/i18n";
import type { Branch, BranchSummary, ComparisonResponse, MetadataResponse } from "@/lib/types";

type ComparisonMetric = "genel_basari_puani" | "teslim_basarisi_pct" | "gecikme_orani_pct" | "iade_orani_pct" | "sikayet_orani_binde" | "personel_verimliligi" | "dagitici_is_yuku" | "gonderi_basi_gelir" | "ortalama_teslim_suresi";

export default function ComparisonPage() {
  const { language, text, number, currency, fullDate } = useLanguage();
  const [branches, setBranches] = useState<Branch[]>([]);
  const [metadata, setMetadata] = useState<MetadataResponse | null>(null);
  const [selected, setSelected] = useState<string[]>([]);
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [metric, setMetric] = useState<ComparisonMetric>("genel_basari_puani");
  const [data, setData] = useState<ComparisonResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const metricLabels = useMemo<Record<ComparisonMetric, { label: string; unit: string }>>(() => ({
    genel_basari_puani: { label: text("Genel Başarı Puanı", "Overall Success Score"), unit: "/100" },
    teslim_basarisi_pct: { label: text("Teslim Başarısı (%)", "Delivery Success (%)"), unit: "%" },
    gecikme_orani_pct: { label: text("Gecikme Oranı (%)", "Delay Rate (%)"), unit: "%" },
    iade_orani_pct: { label: text("İade Oranı (%)", "Return Rate (%)"), unit: "%" },
    sikayet_orani_binde: { label: text("Şikâyet Oranı (‰)", "Complaint Rate (‰)"), unit: "‰" },
    personel_verimliligi: { label: text("Personel Verimliliği", "Staff Productivity"), unit: "" },
    dagitici_is_yuku: { label: text("Dağıtıcı İş Yükü", "Courier Workload"), unit: "" },
    gonderi_basi_gelir: { label: text("Gönderi Başına Gelir (TL)", "Revenue per Shipment (TRY)"), unit: language === "tr" ? " TL" : " TRY" },
    ortalama_teslim_suresi: { label: text("Ortalama Teslim Süresi (gün)", "Average Delivery Time (days)"), unit: text(" gün", " days") },
  }), [language, text]);

  const columns = useMemo<TableColumn<BranchSummary>[]>(() => [
    { label: text("Şube", "Branch"), render: (row) => <strong>{row.sube_adi}</strong> },
    { label: text("Genel Başarı (/100)", "Overall Success (/100)"), align: "right", render: (row) => <strong>{number(row.genel_basari_puani, 2)}</strong> },
    { label: text("Teslim Başarısı (%)", "Delivery Success (%)"), align: "right", render: (row) => number(row.teslim_basarisi_pct, 2) },
    { label: text("Gecikme Oranı (%)", "Delay Rate (%)"), align: "right", render: (row) => number(row.gecikme_orani_pct, 2) },
    { label: text("İade Oranı (%)", "Return Rate (%)"), align: "right", render: (row) => number(row.iade_orani_pct, 2) },
    { label: text("Şikâyet Oranı (‰)", "Complaint Rate (‰)"), align: "right", render: (row) => number(row.sikayet_orani_binde, 2) },
    { label: text("Personel Verimliliği", "Staff Productivity"), align: "right", render: (row) => number(row.personel_verimliligi, 2) },
    { label: text("Dağıtıcı İş Yükü", "Courier Workload"), align: "right", render: (row) => number(row.dagitici_is_yuku, 2) },
    { label: text("Gönderi Başına Gelir", "Revenue per Shipment"), align: "right", render: (row) => `${number(row.gonderi_basi_gelir, 2)} ${text("TL", "TRY")}` },
    { label: text("Teslim Süresi", "Delivery Time"), align: "right", render: (row) => `${number(row.ortalama_teslim_suresi, 2)} ${text("gün", "days")}` },
    { label: text("Toplam Gönderi", "Total Shipments"), align: "right", render: (row) => number(row.toplam_kabul) },
    { label: text("Toplam Gelir", "Total Revenue"), align: "right", render: (row) => currency(row.toplam_gelir) },
  ], [currency, number, text]);

  useEffect(() => {
    Promise.all([api.branches(), api.metadata()]).then(async ([items, meta]) => {
      const initial = items.slice(0, 2).map((item) => item.sube_kodu);
      setBranches(items); setMetadata(meta); setSelected(initial); setStartDate(meta.min_date); setEndDate(meta.max_date);
      setData(await api.comparison(initial, meta.min_date, meta.max_date));
    }).catch((value: Error) => setError(value.message)).finally(() => setLoading(false));
  }, []);

  const colorMap = useMemo(() => Object.fromEntries(selected.map((code, index) => [code, branchColor(code, index)])), [selected]);

  async function loadComparison(codes = selected) {
    if (codes.length < 2) return;
    setLoading(true); setError("");
    try { setData(await api.comparison(codes, startDate, endDate)); }
    catch (value) { setError((value as Error).message); }
    finally { setLoading(false); }
  }

  function toggle(code: string) {
    setSelected((current) => current.includes(code)
      ? (current.length > 2 ? current.filter((item) => item !== code) : current)
      : (current.length < 6 ? [...current, code] : current));
  }

  return (
    <PageShell>
      <section className="page-wrap py-10">
        <div className="mb-8"><p className="eyebrow mb-3">{text("Yan yana performans", "Side-by-side performance")}</p><h1 className="page-title">{text("Şube Performans Karşılaştırması", "Branch Performance Comparison")}</h1><p className="mt-3 text-lg muted">{text("Şubeleri aynı dönem ve sekiz gerçek KPI üzerinden yan yana inceleyin.", "Compare branches side by side over the same period using eight measured KPIs.")}</p></div>
        <div className="filter-panel mb-5">
          <label className="filter-label">{text("Başlangıç", "Start")}<input className="date-control" type="date" min={metadata?.min_date} max={metadata?.max_date} value={startDate} onChange={(event) => setStartDate(event.target.value)} /></label>
          <label className="filter-label">{text("Bitiş", "End")}<input className="date-control" type="date" min={metadata?.min_date} max={metadata?.max_date} value={endDate} onChange={(event) => setEndDate(event.target.value)} /></label>
          <label className="filter-label">{text("Karşılaştırılacak gösterge", "Metric to compare")}<select className="select-control" value={metric} onChange={(event) => setMetric(event.target.value as ComparisonMetric)}>{Object.entries(metricLabels).map(([key, value]) => <option key={key} value={key}>{value.label}</option>)}</select></label>
          <button className="yellow-button" onClick={() => loadComparison()} disabled={loading}><RefreshCw size={18} /> {text("Karşılaştır", "Compare")}</button>
        </div>
        <div className="mb-7 flex flex-wrap gap-3">
          {branches.map((branch) => {
            const active = selected.includes(branch.sube_kodu);
            return <button key={branch.sube_kodu} onClick={() => toggle(branch.sube_kodu)} className={`chip ${active ? "active" : ""}`} style={active ? { borderColor: colorMap[branch.sube_kodu] } : undefined} aria-pressed={active} aria-label={`${branch.sube_adi}: ${active ? text("seçili", "selected") : text("seçili değil", "not selected")}`}><span className="h-3 w-3 rounded-full" style={{ background: active ? colorMap[branch.sube_kodu] : "#cbd5e1" }} />{branch.sube_adi}{active && <Check size={15} />}</button>;
          })}
        </div>
        <p className="mb-6 text-sm font-semibold muted">{text("En az 2, en fazla 6 şube seçilir. Seçili her şubenin rengi tüm grafik ve tablolarda farklı ve sabittir.", "Select between 2 and 6 branches. Each selected branch keeps a distinct, consistent color across all charts and tables.")}</p>
        {error ? <ErrorState message={text("Karşılaştırma verileri alınamadı. Lütfen tekrar deneyin.", "Unable to retrieve comparison data. Please try again.")} /> : loading || !data ? <LoadingState /> : !data.branches.length ? <ErrorState message={text("Seçilen şube ve döneme uygun kayıt bulunamadı.", "No records were found for the selected branches and period.")} /> : (
          <div className="space-y-7">
            <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">
              <Reveal className="surface p-5"><Trophy className="text-amber-500" /><p className="mt-4 text-sm font-bold muted">{text("En Başarılı Şube", "Most Successful Branch")}</p><p className="mt-2 text-xl font-black">{data.highlights?.best_general.sube_adi}</p><p className="mt-2 font-bold text-emerald-600">{number(data.highlights?.best_general.genel_basari_puani ?? 0, 2)}/100</p></Reveal>
              <Reveal delay={.04} className="surface p-5"><Clock3 className="text-red-600" /><p className="mt-4 text-sm font-bold muted">{text("En Riskli Şube", "Riskiest Branch")}</p><p className="mt-2 text-xl font-black">{data.highlights?.risk_general.sube_adi}</p><p className="mt-2 font-bold text-red-600">{number(data.highlights?.risk_general.genel_basari_puani ?? 0, 2)}/100 {text("genel başarı", "overall success")}</p></Reveal>
              <Reveal delay={.08} className="surface p-5"><Users className="text-blue-600" /><p className="mt-4 text-sm font-bold muted">{text("En Yüksek Verimlilik", "Highest Productivity")}</p><p className="mt-2 text-xl font-black">{data.highlights?.highest_productivity.sube_adi}</p><p className="mt-2 font-bold text-blue-600">{number(data.highlights?.highest_productivity.personel_verimliligi ?? 0, 2)}</p></Reveal>
              <Reveal delay={.12} className="surface p-5"><Coins className="text-amber-600" /><p className="mt-4 text-sm font-bold muted">{text("En Yüksek Birim Gelir", "Highest Unit Revenue")}</p><p className="mt-2 text-xl font-black">{data.highlights?.highest_unit_revenue.sube_adi}</p><p className="mt-2 font-bold text-amber-700">{number(data.highlights?.highest_unit_revenue.gonderi_basi_gelir ?? 0, 2)} {text("TL", "TRY")}</p></Reveal>
            </div>

            <Reveal className="surface p-6"><div className="flex flex-wrap items-end justify-between gap-3"><div><h2 className="section-title">{metricLabels[metric].label}</h2><p className="mt-1 text-sm muted">{text("Mevcut", "Outputs from the existing")} <code>calculate_branch_summary</code> {text("çıktıları", "function")}</p></div><span className="text-sm font-bold muted">{data.period && `${fullDate(data.period.start)} – ${fullDate(data.period.end)}`} · {number(data.record_count)} {text("kayıt", "records")}</span></div><div className="mt-4 h-[390px]"><BranchMetricBars data={[...data.branches].sort((a, b) => Number(b[metric]) - Number(a[metric]))} metric={metric} label={metricLabels[metric].label} unit={metricLabels[metric].unit} colorMap={colorMap} /></div></Reveal>

            <div className="grid gap-6 lg:grid-cols-2">
              <Reveal className="surface p-6"><h2 className="section-title">{text("Aylık Teslim Başarısı", "Monthly Delivery Success")}</h2><p className="mt-1 text-sm muted">{text("Şube renkleri seçim sırasına göre sabittir.", "Branch colors remain consistent with the selection order.")}</p><div className="mt-4 h-[350px]"><MultiBranchTrend data={data.monthly} branches={data.branches} metric="teslim_basarisi_pct" label={text("Teslim başarısı", "Delivery success")} colorMap={colorMap} /></div></Reveal>
              <Reveal delay={.06} className="surface p-6"><h2 className="section-title">{text("Aylık Gecikme Oranı", "Monthly Delay Rate")}</h2><p className="mt-1 text-sm muted">{text("Σ geciken / Σ kabul × 100", "Σ delayed / Σ accepted × 100")}</p><div className="mt-4 h-[350px]"><MultiBranchTrend data={data.monthly} branches={data.branches} metric="gecikme_orani_pct" label={text("Gecikme oranı", "Delay rate")} colorMap={colorMap} /></div></Reveal>
            </div>

            <Reveal className="surface p-6"><div className="mb-5 flex items-center gap-3"><Target className="text-[var(--ptt-blue)]" /><div><h2 className="section-title">{text("Ayrıntılı KPI Karşılaştırma Tablosu", "Detailed KPI Comparison Table")}</h2><p className="mt-1 text-sm muted">{text("Orijinal karşılaştırma ekranındaki tüm göstergeler", "All indicators from the original comparison screen")}</p></div></div><DataTable rows={data.branches} columns={columns} rowKey={(row) => row.sube_kodu} /></Reveal>
            <p className="method-note"><strong>{text("Yöntem:", "Method:")}</strong> {text("Genel başarı puanı sekiz KPI'nın gösterilen ağırlıklarıyla, aynı tarih aralığındaki tüm şubelere göre 0–100 arasında hesaplanır. Resmî hedefler tanımlanana kadar bu değer göreli bir puandır.", "The overall success score is calculated from 0 to 100 using the displayed weights of eight KPIs and all branches in the same date range. Until official targets are defined, this is a relative score.")}</p>
          </div>
        )}
      </section>
    </PageShell>
  );
}
