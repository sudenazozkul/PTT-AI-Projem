"""Mevcut Python iş mantığını değiştirmeden API biçimine dönüştürür."""

from __future__ import annotations

from dataclasses import asdict
from functools import lru_cache
from pathlib import Path
from typing import Any

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_ROOT / "data" / "sube_performans.csv"


def _configure_import_path() -> None:
    import sys

    source_path = str(PROJECT_ROOT / "src")
    if source_path not in sys.path:
        sys.path.insert(0, source_path)


_configure_import_path()

from ptt_ai_projem.analysis import AnalysisConfig, analyze_branches
from ptt_ai_projem.anomaly import AnomalyConfig, METRIC_RULES, detect_anomalies
from ptt_ai_projem.data_loader import load_branch_data
from ptt_ai_projem.kpi import calculate_branch_summary, calculate_daily_kpis
from ptt_ai_projem.recommendations import create_recommendations
from ptt_ai_projem.validation import validate_branch_data


class IntegrationDataError(RuntimeError):
    """API katmanında doğrulanmış veri üretilemediğinde oluşur."""


GENERAL_SUCCESS_RULES = {
    "teslim_basarisi_pct": {"weight_pct": 30, "direction": "higher"},
    "gecikme_orani_pct": {"weight_pct": 20, "direction": "lower"},
    "ortalama_teslim_suresi": {"weight_pct": 15, "direction": "lower"},
    "iade_orani_pct": {"weight_pct": 10, "direction": "lower"},
    "sikayet_orani_binde": {"weight_pct": 10, "direction": "lower"},
    "personel_verimliligi": {"weight_pct": 5, "direction": "target"},
    "dagitici_is_yuku": {"weight_pct": 5, "direction": "target"},
    "gonderi_basi_gelir": {"weight_pct": 5, "direction": "higher"},
}

DIRECTION_LABELS = {
    "higher": "Yüksek olması iyi",
    "lower": "Düşük olması iyi",
    "target": "Kurum medyanına yakınlık",
}


KPI_FORMULAS = [
    {
        "key": "teslim_basarisi_pct",
        "label": "Teslim Başarısı",
        "formula": "teslim_edilen / kabul_edilen × 100",
        "summary_formula": "Σ teslim_edilen / Σ kabul_edilen × 100",
        "unit": "%",
        "description": "Kabul edilen gönderilerin teslim edilen bölümünü gösterir.",
        **GENERAL_SUCCESS_RULES["teslim_basarisi_pct"],
    },
    {
        "key": "gecikme_orani_pct",
        "label": "Gecikme Oranı",
        "formula": "geciken / kabul_edilen × 100",
        "summary_formula": "Σ geciken / Σ kabul_edilen × 100",
        "unit": "%",
        "description": "Kabul edilen gönderiler içindeki geciken gönderi payıdır.",
        **GENERAL_SUCCESS_RULES["gecikme_orani_pct"],
    },
    {
        "key": "iade_orani_pct",
        "label": "İade Oranı",
        "formula": "iade_edilen / kabul_edilen × 100",
        "summary_formula": "Σ iade_edilen / Σ kabul_edilen × 100",
        "unit": "%",
        "description": "Kabul edilen gönderiler içindeki iade edilen gönderi payıdır.",
        **GENERAL_SUCCESS_RULES["iade_orani_pct"],
    },
    {
        "key": "sikayet_orani_binde",
        "label": "Şikâyet Oranı",
        "formula": "sikayet_sayisi / teslim_edilen × 1000",
        "summary_formula": "Σ sikayet_sayisi / Σ teslim_edilen × 1000",
        "unit": "‰",
        "description": "Her 1.000 teslimattaki şikâyet sayısını gösterir.",
        **GENERAL_SUCCESS_RULES["sikayet_orani_binde"],
    },
    {
        "key": "personel_verimliligi",
        "label": "Personel Verimliliği",
        "formula": "teslim_edilen / toplam_personel",
        "summary_formula": "Σ teslim_edilen / Σ personel-gün",
        "unit": "teslim/personel-gün",
        "description": "Personel başına günlük teslimat üretimini gösterir.",
        **GENERAL_SUCCESS_RULES["personel_verimliligi"],
    },
    {
        "key": "dagitici_is_yuku",
        "label": "Dağıtıcı İş Yükü",
        "formula": "kabul_edilen / dagitici_sayisi",
        "summary_formula": "Σ kabul_edilen / Σ dağıtıcı-gün",
        "unit": "gönderi/dağıtıcı-gün",
        "description": "Dağıtıcı başına düşen gönderi hacmini gösterir.",
        **GENERAL_SUCCESS_RULES["dagitici_is_yuku"],
    },
    {
        "key": "gonderi_basi_gelir",
        "label": "Gönderi Başına Gelir",
        "formula": "toplam_gelir / kabul_edilen",
        "summary_formula": "Σ toplam_gelir / Σ kabul_edilen",
        "unit": "TL/gönderi",
        "description": "Kabul edilen gönderi başına oluşan geliri gösterir.",
        **GENERAL_SUCCESS_RULES["gonderi_basi_gelir"],
    },
    {
        "key": "ortalama_teslim_suresi",
        "label": "Ağırlıklı Ortalama Teslim Süresi",
        "formula": "Σ (ortalama_teslim_suresi × teslim_edilen) / Σ teslim_edilen",
        "summary_formula": "Teslimat hacmine göre ağırlıklı ortalama",
        "unit": "gün",
        "description": "Şube ve kurum özetinde teslimat hacmini ağırlık olarak kullanır.",
        **GENERAL_SUCCESS_RULES["ortalama_teslim_suresi"],
    },
]

for _formula in KPI_FORMULAS:
    _formula["direction_label"] = DIRECTION_LABELS[str(_formula["direction"])]

if sum(int(rule["weight_pct"]) for rule in GENERAL_SUCCESS_RULES.values()) != 100:
    raise RuntimeError("Genel başarı ağırlıkları toplamı 100 olmalıdır.")


@lru_cache(maxsize=1)
def _validated_payload() -> tuple[pd.DataFrame, tuple[str, ...]]:
    """Orijinal yükleyici ve doğrulayıcı üzerinden veriyi hazırlar."""
    raw_data = load_branch_data(DATA_PATH)
    validation = validate_branch_data(raw_data)
    if not validation.is_valid or validation.cleaned_data is None:
        raise IntegrationDataError("; ".join(validation.errors))
    return validation.cleaned_data, tuple(validation.warnings)


def load_validated_data() -> pd.DataFrame:
    return _validated_payload()[0]


def _json_value(value: Any) -> Any:
    if isinstance(value, pd.Timestamp):
        return value.date().isoformat()
    if isinstance(value, dict):
        return {key: _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        return value.item()
    return value


def _records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    return [_json_value(record) for record in frame.to_dict(orient="records")]


def _peer_score(value: float, reference: pd.Series, direction: str) -> float:
    """Bir değeri aynı dönemdeki şubelere göre 0–100 arası puanlar."""
    numeric = pd.to_numeric(reference, errors="coerce").dropna().astype(float)
    if numeric.empty:
        return 50.0

    numeric_value = float(value)
    if direction == "target":
        target = float(numeric.median())
        numeric_value = abs(numeric_value - target)
        numeric = (numeric - target).abs()
        direction = "lower"

    if len(numeric) == 1:
        return 50.0

    below = int((numeric < numeric_value).sum())
    equal = int((numeric == numeric_value).sum())
    zero_based_rank = below + max(equal - 1, 0) / 2
    higher_score = max(0.0, min(100.0, zero_based_rank / (len(numeric) - 1) * 100))
    return 100.0 - higher_score if direction == "lower" else higher_score


def _score_branch_summaries(
    summaries: pd.DataFrame,
    reference: pd.DataFrame,
) -> pd.DataFrame:
    """Sekiz KPI'yı ağırlıklandırarak açıklanabilir genel başarı puanı ekler."""
    scored = summaries.copy()
    if scored.empty:
        return scored

    if reference.empty:
        reference = summaries

    all_subscores: list[dict[str, float]] = []
    all_contributions: list[dict[str, float]] = []
    totals: list[float] = []
    for _, row in scored.iterrows():
        subscores: dict[str, float] = {}
        contributions: dict[str, float] = {}
        for metric, rule in GENERAL_SUCCESS_RULES.items():
            subscore = _peer_score(
                float(row[metric]), reference[metric], str(rule["direction"])
            )
            contribution = subscore * float(rule["weight_pct"]) / 100
            subscores[metric] = round(subscore, 2)
            contributions[metric] = round(contribution, 2)
        total = round(sum(contributions.values()), 2)
        all_subscores.append(subscores)
        all_contributions.append(contributions)
        totals.append(total)

    scored["genel_basari_alt_puanlari"] = all_subscores
    scored["genel_basari_katkilari"] = all_contributions
    scored["genel_basari_puani"] = totals
    return scored.sort_values(
        ["genel_basari_puani", "teslim_basarisi_pct", "sube_adi"],
        ascending=[False, False, True],
    ).reset_index(drop=True)


def _scored_scope(
    data: pd.DataFrame,
    reference_data: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Görünür şubeleri ve kurum referansını aynı puan ölçeğinde hazırlar."""
    reference = calculate_branch_summary(reference_data)
    scored_reference = _score_branch_summaries(reference, reference)
    scored_reference["siralama"] = range(1, len(scored_reference) + 1)

    summaries = calculate_branch_summary(data)
    scored = _score_branch_summaries(summaries, reference)
    rank_lookup = scored_reference.set_index("sube_kodu")["siralama"].to_dict()
    scored["siralama"] = scored["sube_kodu"].map(rank_lookup)
    return scored, scored_reference


def _apply_filters(
    data: pd.DataFrame,
    start_date: str | None = None,
    end_date: str | None = None,
    provinces: list[str] | None = None,
    branch_types: list[str] | None = None,
    branch_codes: list[str] | None = None,
) -> pd.DataFrame:
    filtered = data.copy()
    if start_date:
        filtered = filtered[filtered["tarih"] >= pd.Timestamp(start_date)]
    if end_date:
        filtered = filtered[filtered["tarih"] <= pd.Timestamp(end_date)]
    if provinces:
        filtered = filtered[filtered["il"].isin(provinces)]
    if branch_types:
        filtered = filtered[filtered["sube_tipi"].isin(branch_types)]
    if branch_codes:
        filtered = filtered[filtered["sube_kodu"].isin(branch_codes)]
    return filtered


def _metrics_from_summary(summary: pd.Series | dict[str, Any]) -> dict[str, float | int]:
    values = dict(summary)
    return {
        "toplam_islem_hacmi": int(values["toplam_kabul"]),
        "toplam_gonderi": int(values["toplam_kabul"]),
        "toplam_teslim": int(values["toplam_teslim"]),
        "toplam_geciken": int(values["toplam_geciken"]),
        "toplam_iade": int(values["toplam_iade"]),
        "toplam_sikayet": int(values["toplam_sikayet"]),
        "toplam_gelir": round(float(values["toplam_gelir"]), 2),
        "teslim_basarisi_pct": float(values["teslim_basarisi_pct"]),
        "gecikme_orani_pct": float(values["gecikme_orani_pct"]),
        "iade_orani_pct": float(values["iade_orani_pct"]),
        "sikayet_orani_binde": float(values["sikayet_orani_binde"]),
        "personel_verimliligi": float(values["personel_verimliligi"]),
        "dagitici_is_yuku": float(values["dagitici_is_yuku"]),
        "gonderi_basi_gelir": float(values["gonderi_basi_gelir"]),
        "ortalama_teslim_suresi": float(values["ortalama_teslim_suresi"]),
    }


def _institution_summary(data: pd.DataFrame) -> pd.Series:
    institution = data.assign(
        sube_kodu="KURUM",
        sube_adi="Kurum Geneli",
        il="Tümü",
        ilce="Tümü",
        sube_tipi="Tümü",
    )
    return calculate_branch_summary(institution).iloc[0]


def _summary_trend(
    data: pd.DataFrame,
    frequency: str,
    by_branch: bool = False,
) -> list[dict[str, Any]]:
    if data.empty:
        return []
    working = data.copy()
    period_column = "tarih" if frequency == "D" else "ay"
    if frequency == "D":
        working[period_column] = working["tarih"].dt.normalize()
    else:
        working[period_column] = working["tarih"].dt.to_period("M").dt.to_timestamp()
    group_columns = [period_column]
    if by_branch:
        group_columns.append("sube_kodu")

    records: list[dict[str, Any]] = []
    for keys, group in working.groupby(group_columns, sort=True):
        period_value = keys[0] if isinstance(keys, tuple) else keys
        summary = (
            calculate_branch_summary(group).iloc[0]
            if by_branch
            else _institution_summary(group)
        ).to_dict()
        summary[period_column] = period_value
        records.append(_json_value(summary))
    return records


def _period_delta(daily: pd.DataFrame, column: str) -> float | None:
    if daily.empty:
        return None
    last_date = daily["tarih"].max()
    recent = daily[daily["tarih"] > last_date - pd.Timedelta(days=30)]
    previous = daily[
        (daily["tarih"] > last_date - pd.Timedelta(days=60))
        & (daily["tarih"] <= last_date - pd.Timedelta(days=30))
    ]
    if recent.empty or previous.empty:
        return None
    recent_value = float(calculate_branch_summary(recent).iloc[0][column])
    previous_value = float(calculate_branch_summary(previous).iloc[0][column])
    return round(recent_value - previous_value, 2)


def _period_payload(data: pd.DataFrame) -> dict[str, Any] | None:
    if data.empty:
        return None
    return {
        "start": data["tarih"].min().date().isoformat(),
        "end": data["tarih"].max().date().isoformat(),
    }


def get_metadata() -> dict[str, Any]:
    data, warnings = _validated_payload()
    return {
        "min_date": data["tarih"].min().date().isoformat(),
        "max_date": data["tarih"].max().date().isoformat(),
        "record_count": int(len(data)),
        "branch_count": int(data["sube_kodu"].nunique()),
        "provinces": sorted(data["il"].astype(str).unique().tolist()),
        "branch_types": sorted(data["sube_tipi"].astype(str).unique().tolist()),
        "validation_warnings": list(warnings),
    }


def get_methodology() -> dict[str, Any]:
    analysis_config = AnalysisConfig()
    anomaly_config = AnomalyConfig()
    return {
        "kpi_formulas": KPI_FORMULAS,
        "analysis": {
            "institution_gap_ratio": analysis_config.institution_gap_ratio,
            "period_change_ratio": analysis_config.period_change_ratio,
            "minimum_correlation": analysis_config.minimum_correlation,
            "complaint_trend_weeks": analysis_config.complaint_trend_weeks,
            "minimum_period_days": analysis_config.minimum_period_days,
            "note": "Korelasyonlar kesin neden-sonuç ilişkisi göstermez.",
        },
        "anomaly": {
            "method": "Medyan–MAD dayanıklı sapma yöntemi",
            "median_formula": "medyan(x)",
            "mad_formula": "MAD = medyan(|xᵢ − medyan(x)|)",
            "scale_formula": "dayanıklı ölçek = MAD / 0,6745",
            "score_formula": "anomali skoru = (gerçekleşen − medyan) / dayanıklı ölçek × olumsuz yön",
            "warning_threshold": anomaly_config.warning_threshold,
            "high_threshold": anomaly_config.high_threshold,
            "minimum_observations": anomaly_config.minimum_observations,
            "metrics": [
                {"key": key, "label": value[0], "adverse_direction": value[1]}
                for key, value in METRIC_RULES.items()
            ],
        },
        "general_success": {
            "label": "Genel Başarı Puanı",
            "formula": "Σ (KPI alt puanı × KPI ağırlığı)",
            "range": "0–100",
            "method": "Aynı tarih aralığındaki tüm şubelere göre göreli yüzdelik puanlama",
            "reference_scope": "İl, şube tipi ve tek şube filtrelerinden bağımsız kurum geneli",
            "target_rule": "Personel verimliliği ve dağıtıcı iş yükünde kurum medyanına yakınlık",
            "weights": {
                key: int(rule["weight_pct"])
                for key, rule in GENERAL_SUCCESS_RULES.items()
            },
        },
        "scoring_note": (
            "Genel başarı puanı, resmî kurumsal hedefler tanımlanana kadar aynı dönemdeki "
            "şubelere göre hesaplanan göreli bir birleşik performans puanıdır; gerçek bir "
            "başarı olasılığı veya nedensel etki değildir."
        ),
    }


def get_branches() -> list[dict[str, str]]:
    columns = ["sube_kodu", "sube_adi", "il", "ilce", "sube_tipi"]
    branches = load_validated_data()[columns].drop_duplicates().sort_values("sube_adi")
    return _records(branches)


def get_overview(
    start_date: str | None = None,
    end_date: str | None = None,
    provinces: list[str] | None = None,
    branch_types: list[str] | None = None,
    branch_codes: list[str] | None = None,
) -> dict[str, Any]:
    all_data = load_validated_data()
    filtered = _apply_filters(
        all_data, start_date, end_date, provinces, branch_types, branch_codes
    )
    if filtered.empty:
        return {
            "metrics": None, "trend": [], "monthly": [], "branches": [],
            "highlights": None, "period": None, "record_count": 0, "branch_count": 0,
        }

    reference_data = _apply_filters(all_data, start_date, end_date)
    summaries, _ = _scored_scope(filtered, reference_data)
    best = summaries.iloc[0]
    risk = summaries.sort_values(
        ["genel_basari_puani", "teslim_basarisi_pct"],
        ascending=[True, True],
    ).iloc[0]
    return {
        "metrics": _metrics_from_summary(_institution_summary(filtered)),
        "trend": _summary_trend(filtered, "D"),
        "monthly": _summary_trend(filtered, "M"),
        "branches": _records(summaries),
        "highlights": {"best_branch": _json_value(best.to_dict()), "risk_branch": _json_value(risk.to_dict())},
        "period": _period_payload(filtered),
        "record_count": int(len(filtered)),
        "branch_count": int(filtered["sube_kodu"].nunique()),
    }


def get_branch_detail(
    branch_code: str,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict[str, Any] | None:
    all_data = load_validated_data()
    branch = _apply_filters(all_data, start_date, end_date, branch_codes=[branch_code])
    if branch.empty:
        return None

    reference_data = _apply_filters(all_data, start_date, end_date)
    _, ranked = _scored_scope(reference_data, reference_data)
    summary = ranked[ranked["sube_kodu"].eq(branch_code)].iloc[0]
    rank_lookup = {code: index + 1 for index, code in enumerate(ranked["sube_kodu"].tolist())}
    daily = calculate_daily_kpis(branch).sort_values("tarih")
    return {
        "branch": _json_value(summary.to_dict()),
        "metrics": _metrics_from_summary(summary),
        "deltas": {
            "teslim_basarisi_pct": _period_delta(daily, "teslim_basarisi_pct"),
            "gecikme_orani_pct": _period_delta(daily, "gecikme_orani_pct"),
            "ortalama_teslim_suresi": _period_delta(daily, "ortalama_teslim_suresi"),
        },
        "rank": rank_lookup.get(branch_code),
        "branch_count": int(ranked["sube_kodu"].nunique()),
        "trend": _records(daily),
        "monthly": _summary_trend(branch, "M"),
        "period": _period_payload(branch),
        "record_count": int(len(branch)),
    }


def get_comparison(
    branch_codes: list[str],
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict[str, Any]:
    all_data = load_validated_data()
    selected = _apply_filters(
        all_data, start_date, end_date, branch_codes=branch_codes or None
    )
    if selected.empty:
        return {"branches": [], "monthly": [], "highlights": None, "period": None, "record_count": 0}

    reference_data = _apply_filters(all_data, start_date, end_date)
    summaries, _ = _scored_scope(selected, reference_data)
    highlights = {
        "best_general": _json_value(summaries.iloc[0].to_dict()),
        "risk_general": _json_value(
            summaries.sort_values("genel_basari_puani").iloc[0].to_dict()
        ),
        "best_success": _json_value(
            summaries.sort_values("teslim_basarisi_pct", ascending=False).iloc[0].to_dict()
        ),
        "lowest_delay": _json_value(summaries.sort_values("gecikme_orani_pct").iloc[0].to_dict()),
        "highest_productivity": _json_value(summaries.sort_values("personel_verimliligi", ascending=False).iloc[0].to_dict()),
        "highest_unit_revenue": _json_value(summaries.sort_values("gonderi_basi_gelir", ascending=False).iloc[0].to_dict()),
    }
    return {
        "branches": _records(summaries),
        "monthly": _summary_trend(selected, "M", by_branch=True),
        "highlights": highlights,
        "period": _period_payload(selected),
        "record_count": int(len(selected)),
    }


def get_analysis(
    start_date: str | None = None,
    end_date: str | None = None,
    branch_codes: list[str] | None = None,
) -> dict[str, Any]:
    full_scope = _apply_filters(load_validated_data(), branch_codes=branch_codes)
    period_scope = _apply_filters(full_scope, start_date, end_date)
    findings = analyze_branches(period_scope) if not period_scope.empty else []
    recommendations = create_recommendations(findings)

    anomalies = detect_anomalies(full_scope) if not full_scope.empty else []
    if start_date:
        minimum = pd.Timestamp(start_date).date()
        anomalies = [item for item in anomalies if item.date.date() >= minimum]
    if end_date:
        maximum = pd.Timestamp(end_date).date()
        anomalies = [item for item in anomalies if item.date.date() <= maximum]

    latest_anomaly = max((item.date for item in anomalies), default=None)
    return {
        "findings": [
            {"finding": _json_value(asdict(item.finding)), "action": item.action}
            for item in recommendations
        ],
        "anomalies": [_json_value(asdict(item)) for item in anomalies],
        "summary": {
            "finding_count": len(recommendations),
            "high_findings": sum(item.finding.severity == "yüksek" for item in recommendations),
            "affected_finding_branches": len({item.finding.branch_code for item in recommendations}),
            "studied_days": int(period_scope["tarih"].nunique()) if not period_scope.empty else 0,
            "anomaly_count": len(anomalies),
            "high_anomalies": sum(item.severity == "yüksek" for item in anomalies),
            "affected_anomaly_branches": len({item.branch_code for item in anomalies}),
            "latest_anomaly": latest_anomaly.date().isoformat() if latest_anomaly is not None else None,
            "recommendation_count": len(recommendations),
        },
        "period": _period_payload(period_scope),
    }
