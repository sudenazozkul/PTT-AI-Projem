"""Şube verilerinden açıklanabilir, kural tabanlı operasyonel bulgular üretir."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from ptt_ai_projem.kpi import (
    KPI_SOURCE_COLUMNS,
    calculate_branch_summary,
    calculate_daily_kpis,
)


ANALYSIS_SOURCE_COLUMNS = KPI_SOURCE_COLUMNS | {
    "tarih", "sube_kodu", "sube_adi", "kabul_edilen", "teslim_edilen",
    "geciken", "ortalama_teslim_suresi", "dagitici_sayisi",
    "izinli_personel", "sikayet_sayisi", "hava_durumu",
    "fazla_mesai_saati",
}
ADVERSE_WEATHER = {"Yağmurlu", "Karlı"}


class AnalysisError(Exception):
    """Analiz için gerekli veri yapısı sağlanmadığında oluşan hata."""


@dataclass(frozen=True)
class Finding:
    """Bir şube için sayısal kanıtla desteklenen tek analiz bulgusu."""

    rule_id: str
    branch_code: str
    branch_name: str
    title: str
    detail: str
    possible_cause: str
    evidence: dict[str, float | int | str]
    severity: str = "orta"


@dataclass(frozen=True)
class AnalysisConfig:
    """Kuralların hassasiyetini belirleyen, açıklanabilir eşikler."""

    institution_gap_ratio: float = 0.10
    period_change_ratio: float = 0.08
    minimum_correlation: float = 0.30
    complaint_trend_weeks: int = 4
    minimum_period_days: int = 20


def _weighted_rate(data: pd.DataFrame, numerator: str, denominator: str) -> float:
    denominator_total = float(data[denominator].sum())
    return float(data[numerator].sum()) / denominator_total * 100 if denominator_total else 0.0


def _weighted_average(data: pd.DataFrame, value: str, weight: str) -> float:
    weight_total = float(data[weight].sum())
    if not weight_total:
        return 0.0
    return float((data[value] * data[weight]).sum()) / weight_total


def _relative_change(current: float, previous: float) -> float:
    return (current - previous) / abs(previous) if previous else 0.0


def _correlation(data: pd.DataFrame, first: str, second: str) -> float | None:
    pairs = data[[first, second]].dropna()
    if len(pairs) < 10 or pairs[first].nunique() < 2 or pairs[second].nunique() < 2:
        return None
    value = pairs[first].corr(pairs[second])
    return None if pd.isna(value) else float(value)


def _finding(
    branch: pd.DataFrame,
    rule_id: str,
    title: str,
    detail: str,
    possible_cause: str,
    evidence: dict[str, float | int | str],
    severity: str = "orta",
) -> Finding:
    return Finding(
        rule_id=rule_id,
        branch_code=str(branch["sube_kodu"].iloc[0]),
        branch_name=str(branch["sube_adi"].iloc[0]),
        title=title,
        detail=detail,
        possible_cause=possible_cause,
        evidence=evidence,
        severity=severity,
    )


def analyze_branches(
    data: pd.DataFrame, config: AnalysisConfig | None = None
) -> list[Finding]:
    """Tüm şubeleri kurum geneli ve kendi geçmişleriyle karşılaştırır."""
    missing = sorted(ANALYSIS_SOURCE_COLUMNS - set(data.columns))
    if missing:
        raise AnalysisError("Analiz için gerekli sütunlar eksik: " + ", ".join(missing))
    if data.empty:
        return []

    config = config or AnalysisConfig()
    working = data.copy()
    working["tarih"] = pd.to_datetime(working["tarih"], errors="coerce")
    if working["tarih"].isna().any():
        raise AnalysisError("Analiz verisinde geçersiz tarih bulundu.")
    daily = calculate_daily_kpis(working)
    institution = calculate_branch_summary(working.assign(
        sube_kodu="KURUM", sube_adi="Kurum Geneli", il="Tümü",
        ilce="Tümü", sube_tipi="Tümü",
    )).iloc[0]
    findings: list[Finding] = []

    for _, branch in daily.groupby("sube_kodu", sort=False):
        branch = branch.sort_values("tarih")
        name = str(branch["sube_adi"].iloc[0])
        summary = calculate_branch_summary(branch).iloc[0]

        delay_limit = institution["gecikme_orani_pct"] * (1 + config.institution_gap_ratio)
        if summary["gecikme_orani_pct"] > delay_limit:
            findings.append(_finding(
                branch, "high_delay", "Gecikme oranı kurum ortalamasının üzerinde",
                f"{name} gecikme oranı %{summary['gecikme_orani_pct']:.2f}; kurum geneli %{institution['gecikme_orani_pct']:.2f}.",
                "Şubeye özgü kapasite, rota ve yoğunluk koşulları incelenmelidir.",
                {"sube_gecikme_pct": summary["gecikme_orani_pct"], "kurum_gecikme_pct": institution["gecikme_orani_pct"]},
                "yüksek",
            ))

        workload_limit = institution["dagitici_is_yuku"] * (1 + config.institution_gap_ratio)
        if summary["dagitici_is_yuku"] > workload_limit:
            findings.append(_finding(
                branch, "high_workload", "Dağıtıcı iş yükü kurum ortalamasının üzerinde",
                f"Dağıtıcı başına iş yükü {summary['dagitici_is_yuku']:.2f}; kurum geneli {institution['dagitici_is_yuku']:.2f}.",
                "Dağıtıcı kapasitesi gönderi hacmine göre yetersiz kalıyor olabilir.",
                {"sube_is_yuku": summary["dagitici_is_yuku"], "kurum_is_yuku": institution["dagitici_is_yuku"]},
            ))

        leave_corr = _correlation(branch, "izinli_personel", "gecikme_orani_pct")
        if leave_corr is not None and leave_corr >= config.minimum_correlation:
            findings.append(_finding(
                branch, "leave_delay_relation", "İzinli personel ile gecikme birlikte artıyor",
                f"Günlük izinli personel ve gecikme oranı arasındaki korelasyon {leave_corr:.2f}.",
                "Personel izinleri gecikmeyle ilişkili olabilir; ilişki nedensellik göstermez.",
                {"korelasyon": round(leave_corr, 3)},
            ))

        last_date = branch["tarih"].max()
        recent = branch[branch["tarih"] > last_date - pd.Timedelta(days=30)]
        previous = branch[(branch["tarih"] > last_date - pd.Timedelta(days=60)) & (branch["tarih"] <= last_date - pd.Timedelta(days=30))]
        if len(recent) >= config.minimum_period_days and len(previous) >= config.minimum_period_days:
            recent_time = _weighted_average(
                recent, "ortalama_teslim_suresi", "teslim_edilen"
            )
            previous_time = _weighted_average(
                previous, "ortalama_teslim_suresi", "teslim_edilen"
            )
            time_change = _relative_change(recent_time, previous_time)
            if time_change >= config.period_change_ratio:
                findings.append(_finding(
                    branch, "delivery_time_increase", "Teslim süresi son 30 günde arttı",
                    f"Ortalama teslim süresi {previous_time:.2f} günden {recent_time:.2f} güne çıktı (%{time_change * 100:.1f}).",
                    "Son dönemdeki iş yükü, personel kapasitesi ve rota koşulları artışla ilişkili olabilir.",
                    {"son_30_gun": round(recent_time, 3), "onceki_30_gun": round(previous_time, 3), "degisim_pct": round(time_change * 100, 2)},
                    "yüksek",
                ))

        weekly = branch.set_index("tarih").resample("W").agg(
            sikayet=("sikayet_sayisi", "sum"), teslim=("teslim_edilen", "sum")
        )
        weekly["oran"] = weekly["sikayet"].div(weekly["teslim"].replace(0, pd.NA)).mul(1000)
        recent_weeks = weekly["oran"].dropna().tail(config.complaint_trend_weeks)
        if len(recent_weeks) == config.complaint_trend_weeks and recent_weeks.is_monotonic_increasing and recent_weeks.iloc[-1] > recent_weeks.iloc[0]:
            findings.append(_finding(
                branch, "complaint_trend", "Şikâyet oranı son haftalarda düzenli yükseliyor",
                f"Her bin teslimattaki şikâyet {recent_weeks.iloc[0]:.2f} düzeyinden {recent_weeks.iloc[-1]:.2f} düzeyine yükseldi.",
                "Teslimat kalitesi ve gecikmeye ilişkin kayıtlar birlikte incelenmelidir.",
                {"ilk_hafta_binde": round(float(recent_weeks.iloc[0]), 3), "son_hafta_binde": round(float(recent_weeks.iloc[-1]), 3)},
            ))

        bad_weather = branch["hava_durumu"].isin(ADVERSE_WEATHER)
        if bad_weather.any() and (~bad_weather).any():
            bad_delay = _weighted_rate(branch[bad_weather], "geciken", "kabul_edilen")
            normal_delay = _weighted_rate(branch[~bad_weather], "geciken", "kabul_edilen")
            if _relative_change(bad_delay, normal_delay) >= config.period_change_ratio:
                findings.append(_finding(
                    branch, "weather_delay_relation", "Olumsuz havada gecikme oranı yükseliyor",
                    f"Yağmurlu/karlı günlerde gecikme %{bad_delay:.2f}; diğer günlerde %{normal_delay:.2f}.",
                    "Hava koşulları gecikmeyle ilişkili olabilir; rota bazında doğrulanmalıdır.",
                    {"olumsuz_hava_gecikme_pct": round(bad_delay, 3), "diger_gunler_gecikme_pct": round(normal_delay, 3)},
                ))

        overtime_corr = _correlation(branch, "fazla_mesai_saati", "teslim_basarisi_pct")
        if overtime_corr is not None and overtime_corr <= -config.minimum_correlation:
            findings.append(_finding(
                branch, "overtime_success_relation", "Fazla mesai artarken teslim başarısı düşüyor",
                f"Fazla mesai ile teslim başarısı arasındaki korelasyon {overtime_corr:.2f}.",
                "Yüksek yoğunluk veya kapasite baskısı her iki göstergeyle ilişkili olabilir.",
                {"korelasyon": round(overtime_corr, 3)},
            ))

    return sorted(findings, key=lambda item: (item.branch_name, item.rule_id))
