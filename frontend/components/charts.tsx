"use client";

import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { Anomaly, BranchSummary, TrendPoint } from "@/lib/types";
import { useLanguage, type Language } from "@/lib/i18n";

export const branchPalette = [
  "#0b4da2", // mavi
  "#e08b18", // turuncu
  "#d94f4f", // kırmızı
  "#13a89e", // turkuaz
  "#4f9d55", // yeşil
  "#d6a900", // altın
  "#7c4dbe", // mor
  "#d9578d", // pembe
  "#8c6d4f", // kahverengi
  "#47657e", // füme mavi
  "#00a0c6", // camgöbeği
  "#8b9b32", // zeytin
];

export function branchColor(branchCode: string, fallbackIndex = 0) {
  const numericCode = Number(branchCode.match(/\d+/)?.[0]);
  const index = Number.isFinite(numericCode) && numericCode > 0 ? numericCode - 1 : fallbackIndex;
  return branchPalette[index % branchPalette.length];
}

type NumericTrendKey =
  | "toplam_kabul"
  | "genel_basari_puani"
  | "teslim_basarisi_pct"
  | "gecikme_orani_pct"
  | "iade_orani_pct"
  | "sikayet_orani_binde"
  | "personel_verimliligi"
  | "dagitici_is_yuku"
  | "gonderi_basi_gelir"
  | "ortalama_teslim_suresi";

const grid = <CartesianGrid stroke="#e6edf5" strokeDasharray="4 5" vertical={false} />;
const tooltipStyle = { borderRadius: 14, border: "1px solid #dde6f0" };

function formattedValue(
  value: number,
  unit: string,
  language: Language,
  formatNumber: (numberValue: number, digits?: number) => string,
) {
  const formatted = formatNumber(value, 2);
  if (unit === "%") return language === "tr" ? `%${formatted}` : `${formatted}%`;
  return `${formatted}${unit}`;
}

export function SingleMetricTrend({
  data,
  metric,
  label,
  color = "#0b4da2",
  dateKey = "ay",
  unit = "",
  area = false,
}: {
  data: TrendPoint[];
  metric: NumericTrendKey;
  label: string;
  color?: string;
  dateKey?: "tarih" | "ay";
  unit?: string;
  area?: boolean;
}) {
  const { language, monthDate, number, shortDate } = useLanguage();
  const formatter = dateKey === "ay" ? monthDate : shortDate;
  if (area) {
    return (
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 12, right: 12, left: -12, bottom: 0 }}>
          <defs>
            <linearGradient id={`area-${metric}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={color} stopOpacity={0.25} />
              <stop offset="100%" stopColor={color} stopOpacity={0.02} />
            </linearGradient>
          </defs>
          {grid}
          <XAxis dataKey={dateKey} tickFormatter={formatter} axisLine={false} tickLine={false} minTickGap={30} tick={{ fill: "#718096", fontSize: 11 }} />
          <YAxis axisLine={false} tickLine={false} tick={{ fill: "#718096", fontSize: 11 }} />
          <Tooltip labelFormatter={(value) => formatter(String(value))} formatter={(value) => [formattedValue(Number(value), unit, language, number), label]} contentStyle={tooltipStyle} />
          <Area type="monotone" dataKey={metric} name={label} stroke={color} strokeWidth={3} fill={`url(#area-${metric})`} />
        </AreaChart>
      </ResponsiveContainer>
    );
  }
  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart data={data} margin={{ top: 12, right: 16, left: -12, bottom: 0 }}>
        {grid}
        <XAxis dataKey={dateKey} tickFormatter={formatter} axisLine={false} tickLine={false} minTickGap={30} tick={{ fill: "#718096", fontSize: 11 }} />
        <YAxis axisLine={false} tickLine={false} tick={{ fill: "#718096", fontSize: 11 }} />
        <Tooltip labelFormatter={(value) => formatter(String(value))} formatter={(value) => [formattedValue(Number(value), unit, language, number), label]} contentStyle={tooltipStyle} />
        <Line type="monotone" dataKey={metric} name={label} stroke={color} strokeWidth={3} dot={{ r: 3 }} activeDot={{ r: 6 }} />
      </LineChart>
    </ResponsiveContainer>
  );
}

export function DualMetricTrend({
  data,
  first,
  second,
}: {
  data: TrendPoint[];
  first: { key: NumericTrendKey; label: string; color: string; unit?: string };
  second: { key: NumericTrendKey; label: string; color: string; unit?: string };
}) {
  const { language, monthDate, number } = useLanguage();
  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart data={data} margin={{ top: 12, right: 16, left: -12, bottom: 0 }}>
        {grid}
        <XAxis dataKey="ay" tickFormatter={monthDate} axisLine={false} tickLine={false} tick={{ fill: "#718096", fontSize: 11 }} />
        <YAxis axisLine={false} tickLine={false} tick={{ fill: "#718096", fontSize: 11 }} />
        <Tooltip
          labelFormatter={(value) => monthDate(String(value))}
          formatter={(value, name) => {
            const unit = String(name) === first.label ? first.unit : second.unit;
            return [formattedValue(Number(value), unit ?? "", language, number), String(name)];
          }}
          contentStyle={tooltipStyle}
        />
        <Legend />
        <Line type="monotone" dataKey={first.key} name={first.label} stroke={first.color} strokeWidth={3} dot={{ r: 3 }} />
        <Line type="monotone" dataKey={second.key} name={second.label} stroke={second.color} strokeWidth={3} dot={{ r: 3 }} />
      </LineChart>
    </ResponsiveContainer>
  );
}

export function BranchMetricBars({
  data,
  metric,
  label,
  colorMap,
  unit = "",
}: {
  data: BranchSummary[];
  metric: NumericTrendKey;
  label: string;
  colorMap?: Record<string, string>;
  unit?: string;
}) {
  const { language, number } = useLanguage();
  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={data} margin={{ top: 14, right: 10, left: -12, bottom: 30 }}>
        {grid}
        <XAxis dataKey="sube_adi" interval={0} angle={-16} textAnchor="end" tick={{ fill: "#64748b", fontSize: 10 }} axisLine={false} tickLine={false} />
        <YAxis axisLine={false} tickLine={false} tick={{ fill: "#718096", fontSize: 11 }} />
        <Tooltip formatter={(value) => [formattedValue(Number(value), unit, language, number), label]} contentStyle={tooltipStyle} />
        <Bar dataKey={metric} name={label} radius={[8, 8, 0, 0]}>
          {data.map((branch, index) => (
            <Cell key={branch.sube_kodu} fill={colorMap?.[branch.sube_kodu] ?? branchColor(branch.sube_kodu, index)} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

export function MultiBranchTrend({
  data,
  branches,
  metric,
  label,
  colorMap,
  unit = "%",
}: {
  data: TrendPoint[];
  branches: BranchSummary[];
  metric: NumericTrendKey;
  label: string;
  colorMap: Record<string, string>;
  unit?: string;
}) {
  const { language, monthDate, number } = useLanguage();
  const periods = [...new Set(data.map((item) => item.ay).filter(Boolean))] as string[];
  const pivoted = periods.map((period) => {
    const row: Record<string, string | number> = { ay: period };
    data.filter((item) => item.ay === period).forEach((item) => { row[item.sube_kodu] = Number(item[metric]); });
    return row;
  });
  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart data={pivoted} margin={{ top: 12, right: 14, left: -12, bottom: 0 }}>
        {grid}
        <XAxis dataKey="ay" tickFormatter={monthDate} axisLine={false} tickLine={false} tick={{ fill: "#718096", fontSize: 11 }} />
        <YAxis axisLine={false} tickLine={false} tick={{ fill: "#718096", fontSize: 11 }} />
        <Tooltip labelFormatter={(value) => monthDate(String(value))} formatter={(value, name) => [formattedValue(Number(value), unit, language, number), String(name)]} contentStyle={tooltipStyle} />
        <Legend />
        {branches.map((branch) => (
          <Line key={branch.sube_kodu} type="monotone" dataKey={branch.sube_kodu} name={`${branch.sube_adi} · ${label}`} stroke={colorMap[branch.sube_kodu]} strokeWidth={3} dot={{ r: 3 }} />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}

export function VolumeBars({ data }: { data: TrendPoint[] }) {
  const { monthDate, number, text } = useLanguage();
  const acceptedLabel = text("Kabul edilen", "Accepted");
  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={data} margin={{ top: 12, right: 12, left: -6, bottom: 0 }}>
        {grid}
        <XAxis dataKey="ay" tickFormatter={monthDate} axisLine={false} tickLine={false} tick={{ fill: "#718096", fontSize: 11 }} />
        <YAxis axisLine={false} tickLine={false} tick={{ fill: "#718096", fontSize: 11 }} />
        <Tooltip labelFormatter={(value) => monthDate(String(value))} formatter={(value) => [number(Number(value)), acceptedLabel]} contentStyle={tooltipStyle} />
        <Bar dataKey="toplam_kabul" name={acceptedLabel} fill="#002b49" radius={[8, 8, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

export function AnomalyScatter({ data, warningThreshold, highThreshold }: { data: Anomaly[]; warningThreshold: number; highThreshold: number }) {
  const { number, shortDate, text } = useLanguage();
  return (
    <ResponsiveContainer width="100%" height="100%">
      <ScatterChart margin={{ top: 18, right: 18, left: -6, bottom: 8 }}>
        {grid}
        <XAxis type="category" dataKey="date" name={text("Tarih", "Date")} tickFormatter={shortDate} axisLine={false} tickLine={false} tick={{ fill: "#718096", fontSize: 10 }} />
        <YAxis type="number" dataKey="anomaly_score" name={text("Anomali Skoru", "Anomaly Score")} axisLine={false} tickLine={false} tick={{ fill: "#718096", fontSize: 11 }} />
        <Tooltip
          cursor={{ strokeDasharray: "4 4" }}
          labelFormatter={(value) => shortDate(String(value))}
          formatter={(value, name) => [number(Number(value), 2), String(name)]}
          contentStyle={tooltipStyle}
        />
        <ReferenceLine y={warningThreshold} stroke="#d6a900" strokeDasharray="5 5" label={text("Orta eşik", "Medium threshold")} />
        <ReferenceLine y={highThreshold} stroke="#c84b45" strokeDasharray="5 5" label={text("Yüksek eşik", "High threshold")} />
        <Scatter name={text("Orta", "Medium")} data={data.filter((item) => item.severity === "orta")} fill="#d6a900" />
        <Scatter name={text("Yüksek", "High")} data={data.filter((item) => item.severity === "yüksek")} fill="#c84b45" />
        <Legend />
      </ScatterChart>
    </ResponsiveContainer>
  );
}
