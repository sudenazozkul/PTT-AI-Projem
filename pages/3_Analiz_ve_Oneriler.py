"""Kural tabanlı şube bulgularını ve operasyonel önerileri gösterir."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from ptt_ai_projem.analysis import AnalysisError, analyze_branches
from ptt_ai_projem.data_loader import DataLoadError, load_branch_data
from ptt_ai_projem.recommendations import Recommendation, create_recommendations
from ptt_ai_projem.validation import validate_branch_data


DATA_PATH = PROJECT_ROOT / "data" / "sube_performans.csv"
SEVERITY_ORDER = {"yüksek": 0, "orta": 1, "düşük": 2}


class AnalysisPageError(Exception):
    """Analiz sayfası verisi hazırlanamadığında oluşan kullanıcı dostu hata."""


@st.cache_data(show_spinner="Kural tabanlı analiz hazırlanıyor...")
def load_analysis_data(csv_path: str, modified_at: float) -> pd.DataFrame:
    """Kaynak veriyi okur ve doğrulanmış kayıtları döndürür."""
    _ = modified_at
    raw_data = load_branch_data(csv_path)
    validation = validate_branch_data(raw_data)
    if not validation.is_valid or validation.cleaned_data is None:
        raise AnalysisPageError("\n".join(validation.errors))
    return validation.cleaned_data


def format_evidence(evidence: dict[str, float | int | str]) -> str:
    """Bulgu kanıtlarını kısa ve okunabilir tek satıra dönüştürür."""
    labels = {
        "sube_gecikme_pct": "Şube gecikme (%)",
        "kurum_gecikme_pct": "Kurum gecikme (%)",
        "sube_is_yuku": "Şube iş yükü",
        "kurum_is_yuku": "Kurum iş yükü",
        "korelasyon": "Korelasyon",
        "son_30_gun": "Son 30 gün",
        "onceki_30_gun": "Önceki 30 gün",
        "degisim_pct": "Değişim (%)",
        "ilk_hafta_binde": "İlk hafta (‰)",
        "son_hafta_binde": "Son hafta (‰)",
        "olumsuz_hava_gecikme_pct": "Olumsuz hava (%)",
        "diger_gunler_gecikme_pct": "Diğer günler (%)",
    }
    parts = []
    for key, value in evidence.items():
        shown = f"{value:.2f}" if isinstance(value, float) else str(value)
        parts.append(f"{labels.get(key, key)}: {shown}")
    return " · ".join(parts)


def finding_table(recommendations: list[Recommendation]) -> pd.DataFrame:
    """Bulguları indirilebilir ve sıralanabilir tablo biçimine getirir."""
    return pd.DataFrame([
        {
            "Şube": item.finding.branch_name,
            "Önem": item.finding.severity.capitalize(),
            "Bulgu": item.finding.title,
            "Sayısal Kanıt": format_evidence(item.finding.evidence),
            "Öneri": item.action,
        }
        for item in recommendations
    ])


st.markdown(
    """
    <style>
        .stApp { background-color: #f4f6f8; }
        .block-container { max-width: 1400px; padding-top: 1.5rem; }
        .analysis-header {
            padding: 1.25rem 1.5rem; border-radius: 16px; color: white;
            background: linear-gradient(110deg, #14213d, #21345c);
            border-bottom: 6px solid #ffcc00;
            box-shadow: 0 8px 24px rgba(20, 33, 61, .14);
        }
        .analysis-header h1 { color: white; margin: 0; }
        .analysis-header p { color: #dce5f3; margin: .35rem 0 0; }
        .finding-card {
            margin: .7rem 0 1rem; padding: 1rem 1.2rem; border-radius: 13px;
            background: white; border-left: 6px solid #d6a900;
            box-shadow: 0 4px 14px rgba(20, 33, 61, .08);
        }
        .finding-card.high { border-left-color: #c84b45; }
        .finding-title { color: #14213d; font-size: 1.05rem; font-weight: 800; }
        .finding-detail { color: #33445e; margin-top: .45rem; }
        .finding-evidence { color: #6a7484; font-size: .88rem; margin-top: .45rem; }
        .finding-cause, .finding-action { margin-top: .65rem; color: #33445e; }
        .method-note {
            margin-top: 1rem; padding: .8rem 1rem; border-radius: 10px;
            background: #fff8d6; color: #4a3c00; border: 1px solid #f3d75a;
        }
        section[data-testid="stSidebar"] { background: #14213d; border-right: 4px solid #ffcc00; }
        section[data-testid="stSidebar"] * { color: #f7f9fc; }
        section[data-testid="stSidebar"] [data-baseweb="select"] * { color: #14213d; }
        section[data-testid="stSidebar"] input { color: #14213d; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="analysis-header">
        <h1>Analiz ve Operasyonel Öneriler</h1>
        <p>Şubelerin kurum ortalaması ve kendi geçmişiyle açıklanabilir karşılaştırması</p>
    </div>
    """,
    unsafe_allow_html=True,
)

try:
    data = load_analysis_data(str(DATA_PATH), DATA_PATH.stat().st_mtime)
except (OSError, DataLoadError, AnalysisPageError) as error:
    st.error(f"Analiz verisi hazırlanamadı: {error}")
    st.stop()

minimum_date = data["tarih"].min().date()
maximum_date = data["tarih"].max().date()
branch_names = sorted(data["sube_adi"].unique())

st.sidebar.markdown("## Analiz Filtreleri")
date_range = st.sidebar.date_input(
    "Tarih aralığı", value=(minimum_date, maximum_date),
    min_value=minimum_date, max_value=maximum_date, format="DD.MM.YYYY",
)
selected_branches = st.sidebar.multiselect(
    "Gösterilecek şubeler", options=branch_names, default=branch_names,
)
selected_severities = st.sidebar.multiselect(
    "Önem seviyesi", options=["yüksek", "orta"], default=["yüksek", "orta"],
    format_func=str.capitalize,
)

if not isinstance(date_range, (tuple, list)) or len(date_range) != 2:
    st.warning("Başlangıç ve bitiş tarihini birlikte seçin.")
    st.stop()
if not selected_branches:
    st.warning("En az bir şube seçin.")
    st.stop()

start_date, end_date = date_range
period_data = data[data["tarih"].dt.date.between(start_date, end_date)].copy()
if period_data.empty:
    st.warning("Seçilen dönemde analiz edilecek kayıt bulunamadı.")
    st.stop()

try:
    all_recommendations = create_recommendations(analyze_branches(period_data))
except AnalysisError as error:
    st.error(f"Analiz oluşturulamadı: {error}")
    st.stop()

recommendations = [
    item for item in all_recommendations
    if item.finding.branch_name in selected_branches
    and item.finding.severity in selected_severities
]
recommendations.sort(key=lambda item: (
    SEVERITY_ORDER.get(item.finding.severity, 99),
    item.finding.branch_name,
    item.finding.rule_id,
))

high_count = sum(item.finding.severity == "yüksek" for item in recommendations)
affected_branches = len({item.finding.branch_name for item in recommendations})
cards = st.columns(4)
cards[0].metric("Toplam Bulgu", len(recommendations))
cards[1].metric("Yüksek Önemli", high_count)
cards[2].metric("Etkilenen Şube", affected_branches)
cards[3].metric("İncelenen Gün", period_data["tarih"].nunique())

st.markdown(
    """
    <div class="method-note">
        Bulgular kural tabanlıdır; kurum ortalaması, dönemsel değişim ve korelasyon
        eşiklerine dayanır. Korelasyonlar kesin neden-sonuç ilişkisi göstermez.
    </div>
    """,
    unsafe_allow_html=True,
)

if not recommendations:
    st.info("Seçilen filtrelere uyan bir analiz bulgusu bulunmadı.")
    st.stop()

st.subheader("Şube Bulguları")
for item in recommendations:
    finding = item.finding
    card_class = "finding-card high" if finding.severity == "yüksek" else "finding-card"
    st.markdown(
        f"""
        <div class="{card_class}">
            <div class="finding-title">{finding.branch_name} · {finding.title}</div>
            <div class="finding-detail"><strong>Bulgu:</strong> {finding.detail}</div>
            <div class="finding-evidence"><strong>Kanıt:</strong> {format_evidence(finding.evidence)}</div>
            <div class="finding-cause"><strong>Olası neden:</strong> {finding.possible_cause}</div>
            <div class="finding-action"><strong>Öneri:</strong> {item.action}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.subheader("Toplu Bulgu Tablosu")
table = finding_table(recommendations)
st.dataframe(table, hide_index=True, width="stretch")
st.download_button(
    "Bulguları CSV olarak indir",
    data=table.to_csv(index=False).encode("utf-8-sig"),
    file_name=f"analiz_bulgulari_{start_date}_{end_date}.csv",
    mime="text/csv",
)
