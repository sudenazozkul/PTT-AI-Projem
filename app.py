"""PTT AI Şube Performans Danışmanı Streamlit uygulaması."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from ptt_ai_projem.data_loader import DataLoadError, load_branch_data
from ptt_ai_projem.kpi import calculate_branch_summary, calculate_daily_kpis
from ptt_ai_projem.validation import validate_branch_data


DATA_PATH = PROJECT_ROOT / "data" / "sube_performans.csv"


class DashboardDataError(Exception):
    """Dashboard verisi hazırlanamadığında oluşan kullanıcı dostu hata."""


@st.cache_data(show_spinner="Şube performans verileri hazırlanıyor...")
def prepare_dashboard_data(
    csv_path: str,
    modified_at: float,
) -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
    """Kaynak CSV'yi okur, doğrular ve dashboard KPI'larını hesaplar."""
    # modified_at, CSV değiştiğinde Streamlit önbelleğinin yenilenmesini sağlar.
    _ = modified_at
    raw_data = load_branch_data(csv_path)
    validation = validate_branch_data(raw_data)

    if not validation.is_valid or validation.cleaned_data is None:
        raise DashboardDataError("\n".join(validation.errors))

    daily_kpis = calculate_daily_kpis(validation.cleaned_data)
    branch_summary = calculate_branch_summary(validation.cleaned_data)
    return daily_kpis, branch_summary, validation.warnings


def format_number(value: float) -> str:
    """Tam sayıları Türkçe binlik ayırıcıyla gösterir."""
    return f"{value:,.0f}".replace(",", ".")


def format_money(value: float) -> str:
    """Para değerlerini milyon TL biçiminde gösterir."""
    return f"{value / 1_000_000:,.1f} Mn TL".replace(",", "X").replace(".", ",").replace("X", ".")


st.set_page_config(
    page_title="PTT AI Şube Performans Danışmanı",
    page_icon="📦",
    layout="wide",
)

st.markdown(
    """
    <style>
        .stApp { background-color: #f4f6f8; }
        .block-container { max-width: 1400px; padding-top: 1.6rem; }
        .ptt-header {
            display: flex;
            align-items: center;
            gap: 1.2rem;
            padding: 1.35rem 1.6rem;
            border-radius: 16px;
            background: linear-gradient(110deg, #14213d 0%, #21345c 100%);
            border-bottom: 6px solid #ffcc00;
            color: white;
            box-shadow: 0 8px 24px rgba(20, 33, 61, 0.16);
        }
        .ptt-mark {
            display: grid;
            place-items: center;
            width: 82px;
            height: 64px;
            border-radius: 12px;
            background: #ffcc00;
            color: #14213d;
            font-size: 1.65rem;
            font-weight: 900;
            letter-spacing: -1px;
        }
        .ptt-header h1 { margin: 0; color: white; font-size: 2rem; }
        .ptt-header p { margin: .3rem 0 0; color: #dce5f3; }
        .section-title {
            margin: 1.7rem 0 .8rem;
            color: #14213d;
            font-size: 1.25rem;
            font-weight: 750;
            border-left: 5px solid #ffcc00;
            padding-left: .7rem;
        }
        .metric-grid {
            display: grid;
            grid-template-columns: repeat(5, minmax(150px, 1fr));
            gap: .85rem;
        }
        .metric-card {
            min-height: 112px;
            padding: 1rem 1.1rem;
            border-radius: 14px;
            background: white;
            border-top: 4px solid #ffcc00;
            box-shadow: 0 4px 15px rgba(20, 33, 61, 0.08);
        }
        .metric-label { color: #607086; font-size: .88rem; font-weight: 650; }
        .metric-value { color: #14213d; font-size: 1.65rem; font-weight: 800; margin-top: .45rem; }
        .data-note {
            margin-top: 1rem;
            padding: .75rem 1rem;
            border-radius: 10px;
            background: #fff8d6;
            color: #4a3c00;
            border: 1px solid #f3d75a;
        }
        @media (max-width: 900px) {
            .metric-grid { grid-template-columns: repeat(2, 1fr); }
            .ptt-header h1 { font-size: 1.45rem; }
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="ptt-header">
        <div class="ptt-mark">PTT</div>
        <div>
            <h1>AI Şube Performans Danışmanı</h1>
            <p>Şube performans analizi ve karar destek sistemi</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

try:
    modified_at = DATA_PATH.stat().st_mtime
    daily_kpis, branch_summary, warnings = prepare_dashboard_data(
        str(DATA_PATH), modified_at
    )
except (OSError, DataLoadError, DashboardDataError) as error:
    st.error(f"Dashboard verisi hazırlanamadı: {error}")
    st.stop()

for warning in warnings:
    st.warning(warning)

total_accepted = daily_kpis["kabul_edilen"].sum()
total_delivered = daily_kpis["teslim_edilen"].sum()
delivery_success = total_delivered / total_accepted * 100 if total_accepted else 0
weighted_delivery_time = (
    (daily_kpis["ortalama_teslim_suresi"] * daily_kpis["teslim_edilen"]).sum()
    / total_delivered
    if total_delivered
    else 0
)
total_complaints = daily_kpis["sikayet_sayisi"].sum()
total_revenue = daily_kpis["toplam_gelir"].sum()

st.markdown('<div class="section-title">Genel Performans Özeti</div>', unsafe_allow_html=True)
st.markdown(
    f"""
    <div class="metric-grid">
        <div class="metric-card">
            <div class="metric-label">Toplam Gönderi</div>
            <div class="metric-value">{format_number(total_accepted)}</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Teslim Başarısı</div>
            <div class="metric-value">%{delivery_success:.2f}</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Ortalama Teslim Süresi</div>
            <div class="metric-value">{weighted_delivery_time:.2f} gün</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Toplam Şikâyet</div>
            <div class="metric-value">{format_number(total_complaints)}</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Toplam Gelir</div>
            <div class="metric-value">{format_money(total_revenue)}</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

first_date = daily_kpis["tarih"].min().strftime("%d.%m.%Y")
last_date = daily_kpis["tarih"].max().strftime("%d.%m.%Y")
st.markdown(
    f"""
    <div class="data-note">
        <strong>Veri bağlantısı aktif:</strong> {format_number(len(daily_kpis))} günlük kayıt,
        {daily_kpis['sube_kodu'].nunique()} şube ve {first_date}–{last_date} dönemi analiz edildi.
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="section-title">Şube Performans Sıralaması</div>', unsafe_allow_html=True)
ranking = branch_summary[
    [
        "sube_adi",
        "toplam_kabul",
        "teslim_basarisi_pct",
        "gecikme_orani_pct",
        "ortalama_teslim_suresi",
        "sikayet_orani_binde",
    ]
].rename(
    columns={
        "sube_adi": "Şube",
        "toplam_kabul": "Toplam Gönderi",
        "teslim_basarisi_pct": "Teslim Başarısı (%)",
        "gecikme_orani_pct": "Gecikme Oranı (%)",
        "ortalama_teslim_suresi": "Teslim Süresi (gün)",
        "sikayet_orani_binde": "Şikâyet Oranı (‰)",
    }
)

st.dataframe(
    ranking,
    hide_index=True,
    width="stretch",
    column_config={
        "Teslim Başarısı (%)": st.column_config.ProgressColumn(
            min_value=0, max_value=100, format="%.2f%%"
        ),
        "Toplam Gönderi": st.column_config.NumberColumn(format="localized"),
    },
)
