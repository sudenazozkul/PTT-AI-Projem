"""Şubelerin günlük KPI değerlerinde açıklanabilir anomali sinyalleri üretir."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from ptt_ai_projem.kpi import KPI_SOURCE_COLUMNS, calculate_daily_kpis


ANOMALY_SOURCE_COLUMNS = KPI_SOURCE_COLUMNS | {"tarih"}
METRIC_RULES = {
    "gecikme_orani_pct": (
        "Gecikme oranı", 1,
        "Geciken gönderilerin rota ve yoğunluk kırılımı incelenebilir.",
    ),
    "ortalama_teslim_suresi": (
        "Ortalama teslim süresi", 1,
        "Günün rota, hava ve dağıtıcı kapasitesi kayıtları incelenebilir.",
    ),
    "sikayet_orani_binde": (
        "Şikâyet oranı", 1,
        "Şikâyet konuları ve ilgili teslimat kayıtları incelenebilir.",
    ),
    "dagitici_is_yuku": (
        "Dağıtıcı iş yükü", 1,
        "Gönderi hacmi ile aktif dağıtıcı kapasitesi karşılaştırılabilir.",
    ),
    "teslim_basarisi_pct": (
        "Teslim başarısı", -1,
        "Başarısız teslimatlar ve o güne özgü operasyon koşulları incelenebilir.",
    ),
}


class AnomalyDetectionError(Exception):
    """Anomali tespiti için veri yapısı uygun olmadığında oluşan hata."""


@dataclass(frozen=True)
class AnomalyConfig:
    """Dayanıklı sapma yönteminin veri ve önem eşikleri."""

    warning_threshold: float = 3.5
    high_threshold: float = 4.5
    minimum_observations: int = 30


@dataclass(frozen=True)
class Anomaly:
    """Tek bir şube-gün-KPI için açıklanabilir anomali kaydı."""

    branch_code: str
    branch_name: str
    date: pd.Timestamp
    metric: str
    metric_label: str
    actual_value: float
    expected_value: float
    deviation_pct: float
    anomaly_score: float
    severity: str
    suggested_check: str


def _robust_scale(values: pd.Series, median: float) -> float | None:
    """MAD'yi ölçek olarak kullanır; değişkenlik yoksa güvenli alternatif dener."""
    mad = float((values - median).abs().median())
    if mad > 0:
        return mad / 0.6745

    standard_deviation = float(values.std(ddof=0))
    return standard_deviation if standard_deviation > 0 else None


def _deviation_percent(actual: float, expected: float) -> float:
    """Gerçekleşen değerin medyandan göreli sapmasını yüzde olarak döndürür."""
    return (actual - expected) / abs(expected) * 100 if expected else 0.0


def detect_anomalies(
    data: pd.DataFrame,
    config: AnomalyConfig | None = None,
) -> list[Anomaly]:
    """Her şubenin günlük KPI'larını kendi olağan dağılımıyla karşılaştırır."""
    missing = sorted(ANOMALY_SOURCE_COLUMNS - set(data.columns))
    if missing:
        raise AnomalyDetectionError(
            "Anomali analizi için gerekli sütunlar eksik: " + ", ".join(missing)
        )
    if data.empty:
        return []

    config = config or AnomalyConfig()
    if config.warning_threshold <= 0 or config.high_threshold < config.warning_threshold:
        raise AnomalyDetectionError("Anomali eşikleri pozitif ve birbiriyle uyumlu olmalıdır.")
    if config.minimum_observations < 2:
        raise AnomalyDetectionError("Minimum gözlem sayısı en az 2 olmalıdır.")

    working = data.copy()
    working["tarih"] = pd.to_datetime(working["tarih"], errors="coerce")
    if working["tarih"].isna().any():
        raise AnomalyDetectionError("Anomali verisinde geçersiz tarih bulundu.")

    daily = calculate_daily_kpis(working)
    anomalies: list[Anomaly] = []

    for _, branch in daily.groupby("sube_kodu", sort=False):
        if len(branch) < config.minimum_observations:
            continue

        for metric, (label, adverse_direction, suggested_check) in METRIC_RULES.items():
            values = branch[metric].astype(float)
            median = float(values.median())
            scale = _robust_scale(values, median)
            if scale is None:
                continue

            scores = ((values - median) / scale) * adverse_direction
            detected = scores[scores >= config.warning_threshold]
            for index, score in detected.items():
                actual = float(values.loc[index])
                anomalies.append(Anomaly(
                    branch_code=str(branch.loc[index, "sube_kodu"]),
                    branch_name=str(branch.loc[index, "sube_adi"]),
                    date=pd.Timestamp(branch.loc[index, "tarih"]),
                    metric=metric,
                    metric_label=label,
                    actual_value=round(actual, 3),
                    expected_value=round(median, 3),
                    deviation_pct=round(_deviation_percent(actual, median), 2),
                    anomaly_score=round(float(score), 2),
                    severity="yüksek" if score >= config.high_threshold else "orta",
                    suggested_check=suggested_check,
                ))

    return sorted(
        anomalies,
        key=lambda item: (item.date, item.anomaly_score),
        reverse=True,
    )
