"use client";

import { useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  Check,
  Download,
  Lightbulb,
  Radar,
  RefreshCw,
  ShieldAlert,
  Target,
} from "lucide-react";
import { AnomalyScatter } from "@/components/charts";
import { DataTable, type TableColumn } from "@/components/data-table";
import { PageShell, Reveal } from "@/components/page-shell";
import { ErrorState, LoadingState } from "@/components/states";
import { api } from "@/lib/api";
import { downloadCsv } from "@/lib/csv";
import { type Language, useLanguage } from "@/lib/i18n";
import type {
  AnalysisResponse,
  Anomaly,
  Branch,
  Finding,
  MetadataResponse,
  MethodologyResponse,
} from "@/lib/types";

type NumberFormatter = (value: number, digits?: number) => string;

const evidenceLabels: Record<string, { tr: string; en: string }> = {
  sube_gecikme_pct: { tr: "Şube gecikme (%)", en: "Branch delay (%)" },
  kurum_gecikme_pct: { tr: "Kurum gecikme (%)", en: "Institution delay (%)" },
  sube_is_yuku: { tr: "Şube iş yükü", en: "Branch workload" },
  kurum_is_yuku: { tr: "Kurum iş yükü", en: "Institution workload" },
  korelasyon: { tr: "Korelasyon", en: "Correlation" },
  son_30_gun: { tr: "Son 30 gün", en: "Last 30 days" },
  onceki_30_gun: { tr: "Önceki 30 gün", en: "Previous 30 days" },
  degisim_pct: { tr: "Değişim (%)", en: "Change (%)" },
  ilk_hafta_binde: { tr: "İlk hafta (‰)", en: "First week (‰)" },
  son_hafta_binde: { tr: "Son hafta (‰)", en: "Last week (‰)" },
  olumsuz_hava_gecikme_pct: { tr: "Olumsuz hava (%)", en: "Adverse weather (%)" },
  diger_gunler_gecikme_pct: { tr: "Diğer günler (%)", en: "Other days (%)" },
};

const anomalyCopy: Record<string, { tr: string; en: string; checkEn: string }> = {
  gecikme_orani_pct: {
    tr: "Gecikme oranı",
    en: "Delay rate",
    checkEn: "Delayed shipments can be reviewed by route and volume.",
  },
  ortalama_teslim_suresi: {
    tr: "Ortalama teslim süresi",
    en: "Average delivery time",
    checkEn: "The day's route, weather and courier-capacity records can be reviewed.",
  },
  sikayet_orani_binde: {
    tr: "Şikâyet oranı",
    en: "Complaint rate",
    checkEn: "Complaint topics and related delivery records can be reviewed.",
  },
  dagitici_is_yuku: {
    tr: "Dağıtıcı iş yükü",
    en: "Courier workload",
    checkEn: "Shipment volume can be compared with active courier capacity.",
  },
  teslim_basarisi_pct: {
    tr: "Teslim başarısı",
    en: "Delivery success",
    checkEn: "Failed deliveries and the day's operating conditions can be reviewed.",
  },
};

function evidenceValue(evidence: Record<string, number | string>, key: string) {
  const value = evidence[key];
  return typeof value === "number" ? value : Number(value ?? 0);
}

function evidenceText(
  evidence: Record<string, number | string>,
  language: Language,
  formatNumber: NumberFormatter,
) {
  return Object.entries(evidence)
    .map(([key, value]) => {
      const label = evidenceLabels[key]?.[language] ?? key;
      return `${label}: ${typeof value === "number" ? formatNumber(value, 2) : value}`;
    })
    .join(" · ");
}

function severityLabel(language: Language, severity: string) {
  if (severity === "yüksek") return language === "tr" ? "Yüksek" : "High";
  if (severity === "orta") return language === "tr" ? "Orta" : "Medium";
  return language === "tr" ? severity : "Unspecified";
}

function anomalyMetricLabel(language: Language, anomaly: Pick<Anomaly, "metric" | "metric_label">) {
  const copy = anomalyCopy[anomaly.metric];
  if (copy) return copy[language];
  return language === "tr" ? anomaly.metric_label : anomaly.metric;
}

function anomalySuggestedCheck(language: Language, anomaly: Pick<Anomaly, "metric" | "suggested_check">) {
  if (language === "tr") return anomaly.suggested_check;
  return anomalyCopy[anomaly.metric]?.checkEn
    ?? "The related operating records can be reviewed.";
}

function localizedFinding(
  finding: Finding,
  action: string,
  language: Language,
  formatNumber: NumberFormatter,
) {
  if (language === "tr") {
    return {
      title: finding.title,
      detail: finding.detail,
      possibleCause: finding.possible_cause,
      action,
    };
  }

  const evidence = finding.evidence;
  switch (finding.rule_id) {
    case "high_delay":
      return {
        title: "Delay rate is above the institutional average",
        detail: `${finding.branch_name} delay rate is ${formatNumber(evidenceValue(evidence, "sube_gecikme_pct"), 2)}%; the institution-wide rate is ${formatNumber(evidenceValue(evidence, "kurum_gecikme_pct"), 2)}%.`,
        possibleCause: "Branch-specific capacity, route and volume conditions should be reviewed.",
        action: "Delayed shipments can be reviewed by route, day and volume; capacity plans can be updated for peak periods.",
      };
    case "high_workload":
      return {
        title: "Courier workload is above the institutional average",
        detail: `Workload per courier is ${formatNumber(evidenceValue(evidence, "sube_is_yuku"), 2)}; the institution-wide value is ${formatNumber(evidenceValue(evidence, "kurum_is_yuku"), 2)}.`,
        possibleCause: "Courier capacity may be insufficient for shipment volume.",
        action: "Temporary courier support, shift balancing or route optimization can be considered on busy days.",
      };
    case "leave_delay_relation":
      return {
        title: "Staff leave and delays are increasing together",
        detail: `The correlation between daily staff leave and delay rate is ${formatNumber(evidenceValue(evidence, "korelasyon"), 2)}.`,
        possibleCause: "Staff leave may be associated with delays; this relationship does not establish causation.",
        action: "Leave plans can be reviewed alongside volume forecasts, with backup capacity planned for critical days.",
      };
    case "delivery_time_increase":
      return {
        title: "Delivery time increased over the last 30 days",
        detail: `Average delivery time increased from ${formatNumber(evidenceValue(evidence, "onceki_30_gun"), 2)} days to ${formatNumber(evidenceValue(evidence, "son_30_gun"), 2)} days (${formatNumber(evidenceValue(evidence, "degisim_pct"), 1)}%).`,
        possibleCause: "Recent workload, staffing capacity and route conditions may be associated with the increase.",
        action: "Route, workload and staffing changes over the last 30 days can be compared to identify the source of the increase.",
      };
    case "complaint_trend":
      return {
        title: "Complaint rate has risen steadily in recent weeks",
        detail: `Complaints per 1,000 deliveries rose from ${formatNumber(evidenceValue(evidence, "ilk_hafta_binde"), 2)} to ${formatNumber(evidenceValue(evidence, "son_hafta_binde"), 2)}.`,
        possibleCause: "Delivery quality and delay records should be reviewed together.",
        action: "Recent complaints can be categorized by topic and route, with an owner and deadline assigned for recurring issues.",
      };
    case "weather_delay_relation":
      return {
        title: "Delay rate rises in adverse weather",
        detail: `Delay rate was ${formatNumber(evidenceValue(evidence, "olumsuz_hava_gecikme_pct"), 2)}% on rainy or snowy days and ${formatNumber(evidenceValue(evidence, "diger_gunler_gecikme_pct"), 2)}% on other days.`,
        possibleCause: "Weather conditions may be associated with delays and should be verified by route.",
        action: "Route timings and customer communications can be updated in advance for days with adverse weather forecasts.",
      };
    case "overtime_success_relation":
      return {
        title: "Delivery success falls as overtime rises",
        detail: `The correlation between overtime and delivery success is ${formatNumber(evidenceValue(evidence, "korelasyon"), 2)}.`,
        possibleCause: "High volume or capacity pressure may be associated with both indicators.",
        action: "Work allocation and rest periods can be reviewed in shifts with concentrated overtime.",
      };
    default:
      return {
        title: "Rule-based operational finding",
        detail: `The ${finding.rule_id} rule produced a signal for ${finding.branch_name}.`,
        possibleCause: "The related operating conditions should be reviewed.",
        action: "Review the numeric evidence and the relevant operating records.",
      };
  }
}

export default function AnalysisPage() {
  const { language, text, number, fullDate } = useLanguage();
  const [branches, setBranches] = useState<Branch[]>([]);
  const [metadata, setMetadata] = useState<MetadataResponse | null>(null);
  const [methodology, setMethodology] = useState<MethodologyResponse | null>(null);
  const [selectedBranches, setSelectedBranches] = useState<string[]>([]);
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [severities, setSeverities] = useState(["yüksek", "orta"]);
  const [metrics, setMetrics] = useState<string[]>([]);
  const [data, setData] = useState<AnalysisResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([api.branches(), api.metadata(), api.methodology()])
      .then(async ([branchItems, meta, methods]) => {
        setBranches(branchItems);
        setMetadata(meta);
        setMethodology(methods);
        setStartDate(meta.min_date);
        setEndDate(meta.max_date);
        setMetrics(methods.anomaly.metrics.map((item) => item.key));
        setData(await api.analysis([], meta.min_date, meta.max_date));
      })
      .catch((value: Error) => setError(value.message))
      .finally(() => setLoading(false));
  }, []);

  async function loadAnalysis() {
    setLoading(true);
    setError("");
    try {
      setData(await api.analysis(selectedBranches, startDate, endDate));
    } catch (value) {
      setError((value as Error).message);
    } finally {
      setLoading(false);
    }
  }

  const findings = useMemo(
    () => data?.findings.filter((item) => severities.includes(item.finding.severity)) ?? [],
    [data, severities],
  );
  const anomalies = useMemo(
    () => data?.anomalies.filter((item) => severities.includes(item.severity) && metrics.includes(item.metric)) ?? [],
    [data, severities, metrics],
  );
  const highFindings = findings.filter((item) => item.finding.severity === "yüksek").length;
  const findingBranches = new Set(findings.map((item) => item.finding.branch_code)).size;
  const highAnomalies = anomalies.filter((item) => item.severity === "yüksek").length;
  const anomalyBranches = new Set(anomalies.map((item) => item.branch_code)).size;
  const latestAnomaly = anomalies.length
    ? [...anomalies].sort((a, b) => b.date.localeCompare(a.date))[0].date
    : null;

  const anomalyColumns = useMemo<TableColumn<Anomaly>[]>(() => [
    { label: text("Tarih", "Date"), render: (row) => fullDate(row.date) },
    { label: text("Şube", "Branch"), render: (row) => <strong>{row.branch_name}</strong> },
    { label: "KPI", render: (row) => anomalyMetricLabel(language, row) },
    {
      label: text("Önem", "Severity"),
      render: (row) => (
        <span className={`rounded-full px-3 py-1 text-xs font-extrabold ${row.severity === "yüksek" ? "bg-red-50 text-red-600" : "bg-amber-50 text-amber-700"}`}>
          {severityLabel(language, row.severity).toUpperCase()}
        </span>
      ),
    },
    { label: text("Gerçekleşen", "Actual"), align: "right", render: (row) => number(row.actual_value, 2) },
    { label: text("Olağan Medyan", "Typical Median"), align: "right", render: (row) => number(row.expected_value, 2) },
    { label: text("Sapma (%)", "Deviation (%)"), align: "right", render: (row) => number(row.deviation_pct, 2) },
    { label: text("Anomali Skoru", "Anomaly Score"), align: "right", render: (row) => number(row.anomaly_score, 2) },
    { label: text("İncelenecek Alan", "Area to Review"), render: (row) => anomalySuggestedCheck(language, row) },
  ], [fullDate, language, number, text]);

  function toggleBranch(code: string) {
    setSelectedBranches((current) => current.includes(code)
      ? current.filter((item) => item !== code)
      : [...current, code]);
  }

  function toggleSeverity(value: string) {
    setSeverities((current) => current.includes(value)
      ? (current.length > 1 ? current.filter((item) => item !== value) : current)
      : [...current, value]);
  }

  function toggleMetric(value: string) {
    setMetrics((current) => current.includes(value)
      ? (current.length > 1 ? current.filter((item) => item !== value) : current)
      : [...current, value]);
  }

  function exportFindings() {
    const rows = findings.map(({ finding, action }) => {
      const copy = localizedFinding(finding, action, language, number);
      return [
        finding.branch_name,
        severityLabel(language, finding.severity),
        copy.title,
        evidenceText(finding.evidence, language, number),
        copy.possibleCause,
        copy.action,
      ];
    });
    downloadCsv(
      `${language === "tr" ? "analiz_bulgulari" : "analysis_findings"}_${startDate}_${endDate}.csv`,
      language === "tr"
        ? ["Şube", "Önem", "Bulgu", "Sayısal Kanıt", "Olası Neden", "Öneri"]
        : ["Branch", "Severity", "Finding", "Numeric Evidence", "Possible Cause", "Recommendation"],
      rows,
    );
  }

  function exportAnomalies() {
    downloadCsv(
      `${language === "tr" ? "anomali_kayitlari" : "anomaly_records"}_${startDate}_${endDate}.csv`,
      language === "tr"
        ? ["Tarih", "Şube", "KPI", "Önem", "Gerçekleşen", "Olağan Medyan", "Sapma (%)", "Anomali Skoru", "İncelenecek Alan"]
        : ["Date", "Branch", "KPI", "Severity", "Actual", "Typical Median", "Deviation (%)", "Anomaly Score", "Area to Review"],
      anomalies.map((item) => [
        item.date,
        item.branch_name,
        anomalyMetricLabel(language, item),
        severityLabel(language, item.severity),
        number(item.actual_value, 2),
        number(item.expected_value, 2),
        number(item.deviation_pct, 2),
        number(item.anomaly_score, 2),
        anomalySuggestedCheck(language, item),
      ]),
    );
  }

  return (
    <PageShell>
      <section className="page-wrap py-10">
        <div className="mb-8">
          <p className="eyebrow mb-3">{text("Açıklanabilir karar desteği", "Explainable decision support")}</p>
          <h1 className="page-title">{text("Analiz, Öneriler ve Anomaliler", "Analysis, Recommendations and Anomalies")}</h1>
          <p className="mt-3 text-lg muted">
            {text(
              "Şubelerin kurum ortalaması, kendi geçmişi ve olağan dağılımıyla açıklanabilir karşılaştırması.",
              "An explainable comparison of branches against the institutional average, their own history and typical distribution.",
            )}
          </p>
        </div>

        <div className="filter-panel mb-5">
          <label className="filter-label">
            {text("Başlangıç", "Start")}
            <input className="date-control" type="date" min={metadata?.min_date} max={metadata?.max_date} value={startDate} onChange={(event) => setStartDate(event.target.value)} />
          </label>
          <label className="filter-label">
            {text("Bitiş", "End")}
            <input className="date-control" type="date" min={metadata?.min_date} max={metadata?.max_date} value={endDate} onChange={(event) => setEndDate(event.target.value)} />
          </label>
          <button className="yellow-button" onClick={loadAnalysis} disabled={loading}>
            <RefreshCw size={18} /> {text("Analizi Yenile", "Refresh Analysis")}
          </button>
        </div>

        <div className="mb-4">
          <p className="mb-3 text-xs font-extrabold uppercase tracking-[.12em] muted">
            {text("Gösterilecek şubeler · seçim yoksa tümü", "Branches to display · all if none are selected")}
          </p>
          <div className="flex flex-wrap gap-2">
            {branches.map((branch) => (
              <button type="button" key={branch.sube_kodu} aria-pressed={selectedBranches.includes(branch.sube_kodu)} className={`chip ${selectedBranches.includes(branch.sube_kodu) ? "active" : ""}`} onClick={() => toggleBranch(branch.sube_kodu)}>
                {selectedBranches.includes(branch.sube_kodu) && <Check size={14} />}
                {branch.sube_adi}
              </button>
            ))}
          </div>
        </div>

        <div className="mb-7 flex flex-wrap items-start gap-8">
          <div>
            <p className="mb-3 text-xs font-extrabold uppercase tracking-[.12em] muted">{text("Önem seviyesi", "Severity")}</p>
            <div className="flex gap-2">
              {["yüksek", "orta"].map((item) => (
                <button type="button" key={item} aria-pressed={severities.includes(item)} className={`chip ${severities.includes(item) ? "active" : ""}`} onClick={() => toggleSeverity(item)}>
                  {severityLabel(language, item).toUpperCase()}
                </button>
              ))}
            </div>
          </div>
          <div>
            <p className="mb-3 text-xs font-extrabold uppercase tracking-[.12em] muted">{text("Anomali KPI’ları", "Anomaly KPIs")}</p>
            <div className="flex flex-wrap gap-2">
              {methodology?.anomaly.metrics.map((item) => (
                <button type="button" key={item.key} aria-pressed={metrics.includes(item.key)} className={`chip ${metrics.includes(item.key) ? "active" : ""}`} onClick={() => toggleMetric(item.key)}>
                  {language === "tr" ? item.label : anomalyCopy[item.key]?.en ?? item.key}
                </button>
              ))}
            </div>
          </div>
        </div>

        {error ? (
          <ErrorState message={text("Analiz verileri alınamadı. Lütfen tekrar deneyin.", "Analysis data could not be retrieved. Please try again.")} />
        ) : loading || !data || !methodology ? (
          <LoadingState label={text("Kural ve anomali analizleri hazırlanıyor…", "Preparing rule and anomaly analyses…")} />
        ) : (
          <div className="space-y-10">
            <section className="space-y-6">
              <div>
                <p className="eyebrow mb-2">analysis.py + recommendations.py</p>
                <h2 className="section-title text-[28px]">
                  {text("Kural Tabanlı Bulgular ve Operasyonel Öneriler", "Rule-Based Findings and Operational Recommendations")}
                </h2>
              </div>
              <div className="grid gap-5 sm:grid-cols-2 xl:grid-cols-4">
                {[
                  [AlertTriangle, findings.length, text("Toplam Bulgu", "Total Findings"), "text-red-600 bg-red-50"],
                  [ShieldAlert, highFindings, text("Yüksek Önemli", "High Severity"), "text-red-600 bg-red-50"],
                  [Target, findingBranches, text("Etkilenen Şube", "Affected Branches"), "text-blue-600 bg-blue-50"],
                  [Lightbulb, data.summary.studied_days, text("İncelenen Gün", "Days Reviewed"), "text-amber-700 bg-amber-50"],
                ].map(([Icon, value, label, tone], index) => {
                  const Component = Icon as typeof AlertTriangle;
                  return (
                    <Reveal key={String(label)} delay={index * 0.04} className="surface flex items-center gap-5 p-6">
                      <div className={`grid h-14 w-14 place-items-center rounded-2xl ${tone}`}><Component size={26} /></div>
                      <div><p className="text-3xl font-black">{number(Number(value))}</p><p className="mt-1 text-sm font-bold muted">{String(label)}</p></div>
                    </Reveal>
                  );
                })}
              </div>
              <p className="method-note">
                <strong>{text("Yöntem:", "Method:")}</strong>{" "}
                {text(
                  `Bulgular kurum ortalaması, dönemsel değişim ve korelasyon eşiklerine dayanır. Kurum farkı %${number(methodology.analysis.institution_gap_ratio * 100)}, dönem değişimi %${number(methodology.analysis.period_change_ratio * 100)}, minimum korelasyon ${number(methodology.analysis.minimum_correlation, 2)} ve minimum dönem ${number(methodology.analysis.minimum_period_days)} gündür. Korelasyonlar kesin neden-sonuç ilişkisi göstermez.`,
                  `Findings use institutional-average, period-change and correlation thresholds. The institution gap is ${number(methodology.analysis.institution_gap_ratio * 100)}%, the period change is ${number(methodology.analysis.period_change_ratio * 100)}%, the minimum correlation is ${number(methodology.analysis.minimum_correlation, 2)}, and the minimum period is ${number(methodology.analysis.minimum_period_days)} days. Correlations do not establish causation.`,
                )}
              </p>
              <div className="space-y-4">
                {findings.length ? findings.map(({ finding, action }) => {
                  const copy = localizedFinding(finding, action, language, number);
                  return (
                    <Reveal key={`${finding.branch_code}-${finding.rule_id}`} className={`surface border-l-[6px] p-6 ${finding.severity === "yüksek" ? "border-l-red-500" : "border-l-amber-500"}`}>
                      <div className="flex flex-wrap items-start justify-between gap-3">
                        <div>
                          <p className="text-lg font-extrabold">{finding.branch_name} · {copy.title}</p>
                          <p className="mt-1 text-xs font-bold text-[var(--ptt-blue)]">{text("Kural", "Rule")}: {finding.rule_id}</p>
                        </div>
                        <span className={`rounded-full px-3 py-1 text-xs font-extrabold ${finding.severity === "yüksek" ? "bg-red-50 text-red-600" : "bg-amber-50 text-amber-700"}`}>
                          {severityLabel(language, finding.severity).toUpperCase()}
                        </span>
                      </div>
                      <div className="mt-5 grid gap-4 lg:grid-cols-2">
                        <div className="rounded-2xl bg-slate-50 p-4"><p className="text-xs font-extrabold uppercase tracking-wide muted">{text("Bulgu", "Finding")}</p><p className="mt-2 leading-7">{copy.detail}</p></div>
                        <div className="rounded-2xl bg-blue-50 p-4"><p className="text-xs font-extrabold uppercase tracking-wide text-blue-700">{text("Sayısal Kanıt", "Numeric Evidence")}</p><p className="mt-2 leading-7">{evidenceText(finding.evidence, language, number)}</p></div>
                        <div className="rounded-2xl bg-amber-50 p-4"><p className="text-xs font-extrabold uppercase tracking-wide text-amber-700">{text("Olası Neden", "Possible Cause")}</p><p className="mt-2 leading-7">{copy.possibleCause}</p></div>
                        <div className="rounded-2xl bg-emerald-50 p-4"><p className="text-xs font-extrabold uppercase tracking-wide text-emerald-700">{text("Öneri", "Recommendation")}</p><p className="mt-2 leading-7">{copy.action}</p></div>
                      </div>
                    </Reveal>
                  );
                }) : (
                  <div className="surface p-6 font-bold text-emerald-700">
                    {text("Seçili filtrelere uyan bir analiz bulgusu bulunmadı.", "No analysis findings match the selected filters.")}
                  </div>
                )}
              </div>
              <button className="outline-button" onClick={exportFindings} disabled={!findings.length}>
                <Download size={18} /> {text("Bulguları CSV Olarak İndir", "Download Findings as CSV")}
              </button>
            </section>

            <section className="space-y-6 border-t border-slate-200 pt-10">
              <div>
                <p className="eyebrow mb-2">anomaly.py</p>
                <h2 className="section-title text-[28px]">{text("Risk ve Anomali İzleme", "Risk and Anomaly Monitoring")}</h2>
                <p className="mt-2 muted">{text("Şubelerin kendi olağan performansından sapan günlük KPI değerleri.", "Daily KPI values that deviate from each branch's typical performance.")}</p>
              </div>
              <div className="grid gap-5 sm:grid-cols-2 xl:grid-cols-4">
                {[
                  [Radar, anomalies.length, text("Toplam Anomali", "Total Anomalies"), "text-amber-600 bg-amber-50"],
                  [ShieldAlert, highAnomalies, text("Yüksek Önemli", "High Severity"), "text-red-600 bg-red-50"],
                  [Target, anomalyBranches, text("Etkilenen Şube", "Affected Branches"), "text-blue-600 bg-blue-50"],
                  [AlertTriangle, latestAnomaly ? fullDate(latestAnomaly) : "—", text("Son Anomali", "Latest Anomaly"), "text-violet-600 bg-violet-50"],
                ].map(([Icon, value, label, tone], index) => {
                  const Component = Icon as typeof AlertTriangle;
                  return (
                    <Reveal key={String(label)} delay={index * 0.04} className="surface flex items-center gap-5 p-6">
                      <div className={`grid h-14 w-14 place-items-center rounded-2xl ${tone}`}><Component size={26} /></div>
                      <div><p className="text-2xl font-black">{typeof value === "number" ? number(value) : String(value)}</p><p className="mt-1 text-sm font-bold muted">{String(label)}</p></div>
                    </Reveal>
                  );
                })}
              </div>
              <p className="method-note">
                {language === "tr" ? (
                  <><strong>{methodology.anomaly.method}:</strong> {methodology.anomaly.mad_formula}; {methodology.anomaly.scale_formula}; {methodology.anomaly.score_formula}. Orta eşik {number(methodology.anomaly.warning_threshold, 1)}, yüksek eşik {number(methodology.anomaly.high_threshold, 1)}, minimum gözlem {number(methodology.anomaly.minimum_observations)}. Tarih filtresi yalnızca gösterilecek anomalileri sınırlar.</>
                ) : (
                  <><strong>Robust Median–MAD deviation method:</strong> MAD = median(|xᵢ − median(x)|); robust scale = MAD / 0.6745; anomaly score = (actual − median) / robust scale × adverse direction. Medium threshold {number(methodology.anomaly.warning_threshold, 1)}, high threshold {number(methodology.anomaly.high_threshold, 1)}, minimum observations {number(methodology.anomaly.minimum_observations)}. The date filter only limits the anomalies displayed.</>
                )}
              </p>
              {anomalies.length ? (
                <>
                  <Reveal className="surface p-6">
                    <h3 className="section-title">{text("Anomalilerin Zaman Dağılımı", "Anomaly Distribution Over Time")}</h3>
                    <p className="mt-1 text-sm muted">{text("Gerçek anomali skorları ve kodda tanımlı eşikler", "Actual anomaly scores and the thresholds defined in code")}</p>
                    <div className="mt-4 h-[420px]"><AnomalyScatter data={anomalies} warningThreshold={methodology.anomaly.warning_threshold} highThreshold={methodology.anomaly.high_threshold} /></div>
                  </Reveal>
                  <div className="space-y-3">
                    <h3 className="section-title">{text("En Güncel Anomaliler", "Most Recent Anomalies")}</h3>
                    {[...anomalies].sort((a, b) => b.date.localeCompare(a.date)).slice(0, 10).map((item) => (
                      <article key={`${item.branch_code}-${item.date}-${item.metric}`} className={`surface border-l-[6px] p-5 ${item.severity === "yüksek" ? "border-l-red-500" : "border-l-amber-500"}`}>
                        <p className="font-extrabold">{fullDate(item.date)} · {item.branch_name} · {anomalyMetricLabel(language, item)}</p>
                        <p className="mt-3 leading-7 muted">
                          {text("Gerçekleşen", "Actual")}: <strong>{number(item.actual_value, 2)}</strong> · {text("Olağan medyan", "Typical median")}: <strong>{number(item.expected_value, 2)}</strong> · {text("Sapma", "Deviation")}: <strong>{number(item.deviation_pct, 2)}%</strong> · {text("Skor", "Score")}: <strong>{number(item.anomaly_score, 2)}</strong>
                        </p>
                        <p className="mt-2"><strong>{text("İnceleme", "Review")}:</strong> {anomalySuggestedCheck(language, item)}</p>
                      </article>
                    ))}
                  </div>
                  <Reveal className="surface p-6">
                    <h3 className="section-title">{text("Tüm Anomali Kayıtları", "All Anomaly Records")}</h3>
                    <div className="mt-5"><DataTable rows={anomalies} columns={anomalyColumns} rowKey={(row, index) => `${row.branch_code}-${row.date}-${row.metric}-${index}`} /></div>
                  </Reveal>
                  <button className="outline-button" onClick={exportAnomalies}>
                    <Download size={18} /> {text("Anomalileri CSV Olarak İndir", "Download Anomalies as CSV")}
                  </button>
                </>
              ) : (
                <div className="surface p-6 font-bold text-emerald-700">
                  {text("Seçilen filtrelere uyan bir anomali bulunmadı.", "No anomalies match the selected filters.")}
                </div>
              )}
              <p className="method-note">
                <strong>{text("Yorum sınırı:", "Interpretation limit:")}</strong>{" "}
                {text(
                  `Anomali, mutlaka operasyonel hata veya kesin neden anlamına gelmez. ${methodology.scoring_note}`,
                  "An anomaly does not necessarily mean an operational error or a confirmed cause. The general success score is a relative composite performance score calculated against branches in the same period until official institutional targets are defined; it is neither a probability of success nor a causal effect.",
                )}
              </p>
            </section>
          </div>
        )}
      </section>
    </PageShell>
  );
}
