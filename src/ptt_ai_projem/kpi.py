"""Şube performansına ait günlük ve özet KPI hesaplamaları."""

from __future__ import annotations

import pandas as pd


KPI_SOURCE_COLUMNS = {
    "sube_kodu", "sube_adi", "il", "ilce", "sube_tipi",
    "kabul_edilen", "teslim_edilen", "geciken", "iade_edilen",
    "ortalama_teslim_suresi", "toplam_personel", "dagitici_sayisi",
    "sikayet_sayisi", "toplam_gelir",
}


class KpiCalculationError(Exception):
    """KPI hesaplaması güvenli biçimde yapılamadığında oluşan hata."""


def _safe_divide(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    """Sıfıra bölmeden oran hesaplar; payda sıfırsa sonucu 0 kabul eder."""
    result = pd.Series(0.0, index=numerator.index)
    valid = denominator > 0
    result.loc[valid] = numerator.loc[valid] / denominator.loc[valid]
    return result


def _check_columns(data: pd.DataFrame) -> None:
    """KPI için gerekli kaynak sütunların bulunduğunu kontrol eder."""
    missing = sorted(KPI_SOURCE_COLUMNS - set(data.columns))
    if missing:
        raise KpiCalculationError(
            "KPI hesaplamak için gerekli sütunlar eksik: " + ", ".join(missing)
        )


def calculate_daily_kpis(data: pd.DataFrame) -> pd.DataFrame:
    """Her şube-gün kaydına temel performans göstergelerini ekler."""
    _check_columns(data)
    kpi_data = data.copy()

    kpi_data["teslim_basarisi_pct"] = (
        _safe_divide(kpi_data["teslim_edilen"], kpi_data["kabul_edilen"]) * 100
    )
    kpi_data["gecikme_orani_pct"] = (
        _safe_divide(kpi_data["geciken"], kpi_data["kabul_edilen"]) * 100
    )
    kpi_data["iade_orani_pct"] = (
        _safe_divide(kpi_data["iade_edilen"], kpi_data["kabul_edilen"]) * 100
    )
    kpi_data["sikayet_orani_binde"] = (
        _safe_divide(kpi_data["sikayet_sayisi"], kpi_data["teslim_edilen"])
        * 1000
    )
    kpi_data["personel_verimliligi"] = _safe_divide(
        kpi_data["teslim_edilen"], kpi_data["toplam_personel"]
    )
    kpi_data["dagitici_is_yuku"] = _safe_divide(
        kpi_data["kabul_edilen"], kpi_data["dagitici_sayisi"]
    )
    kpi_data["gonderi_basi_gelir"] = _safe_divide(
        kpi_data["toplam_gelir"], kpi_data["kabul_edilen"]
    )

    kpi_columns = [
        "teslim_basarisi_pct", "gecikme_orani_pct", "iade_orani_pct",
        "sikayet_orani_binde", "personel_verimliligi", "dagitici_is_yuku",
        "gonderi_basi_gelir",
    ]
    kpi_data[kpi_columns] = kpi_data[kpi_columns].round(2)
    return kpi_data


def calculate_branch_summary(data: pd.DataFrame) -> pd.DataFrame:
    """Tüm dönem için şube bazında ağırlıklı KPI özeti oluşturur."""
    _check_columns(data)
    working = data.copy()
    working["teslim_suresi_agirlikli"] = (
        working["ortalama_teslim_suresi"] * working["teslim_edilen"]
    )

    summary = (
        working.groupby(
            ["sube_kodu", "sube_adi", "il", "ilce", "sube_tipi"],
            as_index=False,
        )
        .agg(
            toplam_kabul=("kabul_edilen", "sum"),
            toplam_teslim=("teslim_edilen", "sum"),
            toplam_geciken=("geciken", "sum"),
            toplam_iade=("iade_edilen", "sum"),
            toplam_sikayet=("sikayet_sayisi", "sum"),
            toplam_gelir=("toplam_gelir", "sum"),
            toplam_personel_gun=("toplam_personel", "sum"),
            toplam_dagitici_gun=("dagitici_sayisi", "sum"),
            teslim_suresi_agirlikli=("teslim_suresi_agirlikli", "sum"),
        )
    )

    summary["teslim_basarisi_pct"] = (
        _safe_divide(summary["toplam_teslim"], summary["toplam_kabul"]) * 100
    )
    summary["gecikme_orani_pct"] = (
        _safe_divide(summary["toplam_geciken"], summary["toplam_kabul"]) * 100
    )
    summary["iade_orani_pct"] = (
        _safe_divide(summary["toplam_iade"], summary["toplam_kabul"]) * 100
    )
    summary["sikayet_orani_binde"] = (
        _safe_divide(summary["toplam_sikayet"], summary["toplam_teslim"]) * 1000
    )
    summary["personel_verimliligi"] = _safe_divide(
        summary["toplam_teslim"], summary["toplam_personel_gun"]
    )
    summary["dagitici_is_yuku"] = _safe_divide(
        summary["toplam_kabul"], summary["toplam_dagitici_gun"]
    )
    summary["gonderi_basi_gelir"] = _safe_divide(
        summary["toplam_gelir"], summary["toplam_kabul"]
    )
    summary["ortalama_teslim_suresi"] = _safe_divide(
        summary["teslim_suresi_agirlikli"], summary["toplam_teslim"]
    )

    summary = summary.drop(
        columns=["teslim_suresi_agirlikli", "toplam_personel_gun", "toplam_dagitici_gun"]
    )
    numeric_columns = summary.select_dtypes(include="number").columns
    summary[numeric_columns] = summary[numeric_columns].round(2)
    return summary.sort_values("teslim_basarisi_pct", ascending=False).reset_index(drop=True)
