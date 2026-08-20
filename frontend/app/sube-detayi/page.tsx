"use client";

import { useEffect, useMemo, useState } from "react";
import { BarChart3, Clock3, MapPin, PackageCheck, RefreshCw, Truck, Users } from "lucide-react";
import { DualMetricTrend, SingleMetricTrend, VolumeBars } from "@/components/charts";
import { DataTable, type TableColumn } from "@/components/data-table";
import { MetricCard } from "@/components/metric-card";
import { PageShell, Reveal } from "@/components/page-shell";
import { ErrorState, LoadingState } from "@/components/states";
import { api } from "@/lib/api";
import { useLanguage } from "@/lib/i18n";
import type { Branch, BranchDetailResponse, MetadataResponse, MethodologyResponse, TrendPoint } from "@/lib/types";

export default function BranchDetailPage() {
  const { language, text, number, currency, fullDate } = useLanguage();
  const [branches, setBranches] = useState<Branch[]>([]);
  const [metadata, setMetadata] = useState<MetadataResponse | null>(null);
  const [methodology, setMethodology] = useState<MethodologyResponse | null>(null);
  const [code, setCode] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [data, setData] = useState<BranchDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const dailyColumns = useMemo<TableColumn<TrendPoint>[]>(() => [
    { label: text("Tarih", "Date"), render: (row) => row.tarih ? fullDate(row.tarih) : "—" },
    { label: text("Kabul Edilen", "Accepted"), align: "right", render: (row) => number(row.kabul_edilen ?? row.toplam_kabul) },
    { label: text("Teslim Edilen", "Delivered"), align: "right", render: (row) => number(row.teslim_edilen ?? row.toplam_teslim) },
    { label: text("Teslim Başarısı (%)", "Delivery Success (%)"), align: "right", render: (row) => number(row.teslim_basarisi_pct, 2) },
    { label: text("Gecikme Oranı (%)", "Delay Rate (%)"), align: "right", render: (row) => number(row.gecikme_orani_pct, 2) },
    { label: text("Teslim Süresi (gün)", "Delivery Time (days)"), align: "right", render: (row) => number(row.ortalama_teslim_suresi, 2) },
    { label: text("Personel Verimliliği", "Staff Productivity"), align: "right", render: (row) => number(row.personel_verimliligi, 2) },
    { label: text("Dağıtıcı İş Yükü", "Courier Workload"), align: "right", render: (row) => number(row.dagitici_is_yuku, 2) },
    { label: text("Şikâyet", "Complaints"), align: "right", render: (row) => number(row.sikayet_sayisi ?? row.toplam_sikayet) },
  ], [fullDate, number, text]);

  const percent = (value: number) => language === "tr" ? `%${number(value, 2)}` : `${number(value, 2)}%`;
  const deltaText = (value: number | null, turkishSuffix: string, englishSuffix: string) => value === null
    ? text("Karşılaştırılabilir önceki dönem yok", "No comparable previous period")
    : `${text("Önceki 30 güne göre", "Compared with the previous 30 days")} ${value >= 0 ? "+" : ""}${number(value, 2)} ${text(turkishSuffix, englishSuffix)}`;
  const branchType = (value: string) => language === "tr" ? value : (({ Merkez: "Central", "Büyük": "Large", Orta: "Medium" } as Record<string, string>)[value] ?? value);
  const englishFormulaLabels: Record<string, string> = {
    teslim_basarisi_pct: "Delivery Success",
    gecikme_orani_pct: "Delay Rate",
    iade_orani_pct: "Return Rate",
    sikayet_orani_binde: "Complaint Rate",
    personel_verimliligi: "Staff Productivity",
    dagitici_is_yuku: "Courier Workload",
    gonderi_basi_gelir: "Revenue per Shipment",
    ortalama_teslim_suresi: "Weighted Average Delivery Time",
  };
  const formulaLabel = (key: string, fallback: string) => language === "tr" ? fallback : (englishFormulaLabels[key] ?? fallback);

  useEffect(() => {
    Promise.all([api.branches(), api.metadata(), api.methodology()]).then(async ([items, meta, methods]) => {
      const initialCode = items[0]?.sube_kodu ?? "";
      setBranches(items); setMetadata(meta); setMethodology(methods); setCode(initialCode); setStartDate(meta.min_date); setEndDate(meta.max_date);
      if (initialCode) setData(await api.branchDetail(initialCode, meta.min_date, meta.max_date));
    }).catch((value: Error) => setError(value.message)).finally(() => setLoading(false));
  }, []);

  async function loadDetail(nextCode = code) {
    if (!nextCode) return;
    setLoading(true); setError("");
    try { setData(await api.branchDetail(nextCode, startDate, endDate)); }
    catch (value) { setError((value as Error).message); }
    finally { setLoading(false); }
  }

  async function changeBranch(nextCode: string) { setCode(nextCode); await loadDetail(nextCode); }

  return (
    <PageShell>
      <section className="page-wrap py-10">
        <div className="mb-8"><p className="eyebrow mb-3">{text("Tek şube analizi", "Single-branch analysis")}</p><h1 className="page-title">{text("Şube Performans Detayı", "Branch Performance Details")}</h1><p className="mt-3 text-lg muted">{text("Seçilen şubenin KPI, iş yükü, personel ve kalite eğilimleri.", "KPI, workload, staff, and quality trends for the selected branch.")}</p></div>
        <div className="filter-panel mb-7">
          <label className="filter-label">{text("Şube", "Branch")}<select className="select-control" value={code} onChange={(event) => changeBranch(event.target.value)}>{branches.map((branch) => <option key={branch.sube_kodu} value={branch.sube_kodu}>{branch.sube_adi}</option>)}</select></label>
          <label className="filter-label">{text("Başlangıç", "Start")}<input className="date-control" type="date" min={metadata?.min_date} max={metadata?.max_date} value={startDate} onChange={(event) => setStartDate(event.target.value)} /></label>
          <label className="filter-label">{text("Bitiş", "End")}<input className="date-control" type="date" min={metadata?.min_date} max={metadata?.max_date} value={endDate} onChange={(event) => setEndDate(event.target.value)} /></label>
          <button className="yellow-button" onClick={() => loadDetail()} disabled={loading}><RefreshCw size={18} /> {text("Dönemi Uygula", "Apply Period")}</button>
        </div>
        {error ? <ErrorState message={text("Şube detayları alınamadı. Lütfen tekrar deneyin.", "Unable to retrieve branch details. Please try again.")} /> : loading || !data ? <LoadingState /> : (
          <div className="space-y-7">
            <Reveal className="surface flex flex-wrap items-center justify-between gap-6 p-7">
              <div><p className="eyebrow">{data.branch.sube_kodu}</p><h2 className="mt-2 text-3xl font-black">{data.branch.sube_adi} — {branchType(data.branch.sube_tipi)} {text("Şube", "Branch")}</h2><p className="mt-3 flex items-center gap-2 muted"><MapPin size={18} /> {data.branch.il} / {data.branch.ilce} · {fullDate(data.period.start)}–{fullDate(data.period.end)}</p></div>
              <div className="grid min-w-[260px] grid-cols-2 gap-3"><div className="soft-surface p-4"><p className="text-xs font-bold muted">{text("Genel Başarı Sırası", "Overall Success Rank")}</p><p className="mt-1 text-3xl font-black">{number(data.rank)} <span className="text-base muted">/ {number(data.branch_count)}</span></p><p className="mt-1 text-xs font-bold text-emerald-700">{number(data.branch.genel_basari_puani, 2)}/100 {text("puan", "points")}</p></div><div className="soft-surface p-4"><p className="text-xs font-bold muted">{text("Günlük Kayıt", "Daily Records")}</p><p className="mt-1 text-3xl font-black">{number(data.record_count)}</p></div></div>
            </Reveal>

            <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-5">
              <MetricCard icon={PackageCheck} label={text("Teslim Başarısı", "Delivery Success")} value={percent(data.metrics.teslim_basarisi_pct)} detail={deltaText(data.deltas.teslim_basarisi_pct, "puan", "points")} tone="green" />
              <MetricCard icon={Clock3} label={text("Gecikme Oranı", "Delay Rate")} value={percent(data.metrics.gecikme_orani_pct)} detail={deltaText(data.deltas.gecikme_orani_pct, "puan", "points")} tone="red" delay={.04} />
              <MetricCard icon={Clock3} label={text("Teslim Süresi", "Delivery Time")} value={`${number(data.metrics.ortalama_teslim_suresi, 2)} ${text("gün", "days")}`} detail={deltaText(data.deltas.ortalama_teslim_suresi, "gün", "days")} tone="yellow" delay={.08} />
              <MetricCard icon={Users} label={text("Personel Verimliliği", "Staff Productivity")} value={number(data.metrics.personel_verimliligi, 2)} detail={text("Σ teslim / Σ personel-gün", "Σ deliveries / Σ staff-days")} tone="blue" delay={.12} />
              <MetricCard icon={Truck} label={text("Dağıtıcı İş Yükü", "Courier Workload")} value={number(data.metrics.dagitici_is_yuku, 2)} detail={text("Σ kabul / Σ dağıtıcı-gün", "Σ accepted / Σ courier-days")} tone="yellow" delay={.16} />
            </div>

            <Reveal className="surface p-6"><h2 className="section-title">{text("Tüm Şube KPI Özeti", "Complete Branch KPI Summary")}</h2><div className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-4"><div className="soft-surface p-4"><p className="text-xs font-bold muted">{text("İade Oranı", "Return Rate")}</p><p className="mt-2 text-2xl font-black">{percent(data.metrics.iade_orani_pct)}</p></div><div className="soft-surface p-4"><p className="text-xs font-bold muted">{text("Şikâyet Oranı", "Complaint Rate")}</p><p className="mt-2 text-2xl font-black">{number(data.metrics.sikayet_orani_binde, 2)}‰</p></div><div className="soft-surface p-4"><p className="text-xs font-bold muted">{text("Gönderi Başına Gelir", "Revenue per Shipment")}</p><p className="mt-2 text-2xl font-black">{currency(data.metrics.gonderi_basi_gelir)}</p></div><div className="soft-surface p-4"><p className="text-xs font-bold muted">{text("Toplam Gönderi", "Total Shipments")}</p><p className="mt-2 text-2xl font-black">{number(data.metrics.toplam_gonderi)}</p></div></div></Reveal>

            {methodology && <Reveal className="surface p-6">
              <div className="flex flex-wrap items-end justify-between gap-3"><div><h2 className="section-title">{text("Genel Başarı Puanı Dağılımı", "Overall Success Score Breakdown")}</h2><p className="mt-1 text-sm muted">{text("Her KPI'nın alt puanı, sabit ağırlığı ve genel puana gerçek katkısı", "Each KPI's subscore, fixed weight, and actual contribution to the overall score")}</p></div><p className="text-3xl font-black text-emerald-700">{number(data.branch.genel_basari_puani, 2)}<span className="text-base muted">/100</span></p></div>
              <div className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                {methodology.kpi_formulas.map((formula) => {
                  const subscore = data.branch.genel_basari_alt_puanlari[formula.key] ?? 0;
                  const contribution = data.branch.genel_basari_katkilari[formula.key] ?? 0;
                  return <div key={formula.key} className="parameter-card soft-surface p-4"><div className="flex items-start justify-between gap-3"><p className="font-extrabold">{formulaLabel(formula.key, formula.label)}</p><span className="rounded-full bg-amber-100 px-2 py-1 text-xs font-extrabold text-amber-800">{language === "tr" ? `%${number(formula.weight_pct)}` : `${number(formula.weight_pct)}%`}</span></div><div className="mt-4 h-2 overflow-hidden rounded-full bg-slate-200"><div className="h-full rounded-full bg-[var(--ptt-blue)]" style={{ width: `${Math.max(0, Math.min(100, subscore))}%` }} /></div><div className="mt-3 flex justify-between gap-2 text-xs font-bold"><span className="muted">{text("Alt puan", "Subscore")}: {number(subscore, 2)}</span><span className="text-[var(--ptt-blue)]">{text("Katkı", "Contribution")}: {number(contribution, 2)}</span></div></div>;
                })}
              </div>
            </Reveal>}

            <div className="grid gap-6 lg:grid-cols-2">
              <Reveal className="surface p-6"><h3 className="section-title">{text("Aylık Başarı ve Gecikme Eğilimi", "Monthly Success and Delay Trend")}</h3><p className="mt-1 text-sm muted">{text("İki gösterge de ağırlıklı dönem oranıdır.", "Both indicators are weighted rates for the period.")}</p><div className="mt-4 h-[350px]"><DualMetricTrend data={data.monthly} first={{ key: "teslim_basarisi_pct", label: text("Teslim başarısı", "Delivery success"), color: "#237a57", unit: "%" }} second={{ key: "gecikme_orani_pct", label: text("Gecikme oranı", "Delay rate"), color: "#c84b45", unit: "%" }} /></div></Reveal>
              <Reveal delay={.06} className="surface p-6"><h3 className="section-title">{text("İş Yükü ve Personel Verimliliği", "Workload and Staff Productivity")}</h3><p className="mt-1 text-sm muted">{text("Dağıtıcı-gün ve personel-gün hesapları", "Courier-day and staff-day calculations")}</p><div className="mt-4 h-[350px]"><DualMetricTrend data={data.monthly} first={{ key: "dagitici_is_yuku", label: text("Dağıtıcı iş yükü", "Courier workload"), color: "#d6a900" }} second={{ key: "personel_verimliligi", label: text("Personel verimliliği", "Staff productivity"), color: "#2878b5" }} /></div></Reveal>
              <Reveal className="surface p-6"><h3 className="section-title">{text("Ortalama Teslim Süresi", "Average Delivery Time")}</h3><p className="mt-1 text-sm muted">{text("Teslimat hacmine göre ağırlıklı", "Weighted by delivery volume")}</p><div className="mt-4 h-[300px]"><SingleMetricTrend data={data.monthly} metric="ortalama_teslim_suresi" label={text("Teslim süresi", "Delivery time")} color="#c84b45" unit={text(" gün", " days")} /></div></Reveal>
              <Reveal delay={.06} className="surface p-6"><h3 className="section-title">{text("Aylık Gönderi Hacmi", "Monthly Shipment Volume")}</h3><p className="mt-1 text-sm muted">{text("Kabul edilen toplam gönderi", "Total accepted shipments")}</p><div className="mt-4 h-[300px]"><VolumeBars data={data.monthly} /></div></Reveal>
            </div>

            <Reveal className="surface p-6"><div className="mb-5 flex items-center gap-3"><BarChart3 className="text-[var(--ptt-blue)]" /><div><h3 className="section-title">{text("Günlük KPI Kayıtları", "Daily KPI Records")}</h3><p className="mt-1 text-sm muted">{text("Orijinal Şube Detayı ekranındaki günlük tablo", "Daily table from the original Branch Details screen")}</p></div></div><DataTable rows={[...data.trend].reverse()} columns={dailyColumns} rowKey={(row, index) => row.tarih ?? String(index)} /></Reveal>
            <p className="method-note"><strong>{text("Hesaplama notu:", "Calculation note:")}</strong> {text("Kartlardaki değişimler son 30 günün önceki 30 güne teslimat ağırlıklı farkını gösterir. Şube özeti de günlük yüzdelerin basit ortalamasıyla değil, mevcut", "Changes on the cards show the delivery-weighted difference between the latest 30 days and the preceding 30 days. The branch summary is calculated with the weighted method in the existing")} <code>calculate_branch_summary</code> {text("fonksiyonunun ağırlıklı yöntemiyle hesaplanır.", "function, not by taking a simple average of daily percentages.")}</p>
          </div>
        )}
      </section>
    </PageShell>
  );
}
