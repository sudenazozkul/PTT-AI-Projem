"""Günlük KPI anomalilerini açıklanabilir risk sinyalleri olarak gösterir."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from ptt_ai_projem.anomaly import Anomaly, AnomalyDetectionError, detect_anomalies
from ptt_ai_projem.data_loader import DataLoadError, load_branch_data
from ptt_ai_projem.validation import validate_branch_data


DATA_PATH = PROJECT_ROOT / "data" / "sube_performans.csv"


class RiskPageError(Exception):
    """Risk sayfasının verisi güvenli biçimde hazırlanamadığında oluşan hata."""


@st.cache_data(show_spinner="Risk ve anomali kayıtları hazırlanıyor...")
def load_risk_data(csv_path: str, modified_at: float) -> pd.DataFrame:
    """Kaynak CSV'yi okuyup doğrulanmış veriyi döndürür."""
    _ = modified_at
    raw_data = load_branch_data(csv_path)
    validation = validate_branch_data(raw_data)
    if not validation.is_valid or validation.cleaned_data is None:
        raise RiskPageError("\n".join(validation.errors))
    return validation.cleaned_data


def anomalies_to_table(anomalies: list[Anomaly]) -> pd.DataFrame:
    """Anomali nesnelerini kullanıcı dostu tabloya dönüştürür."""
    return pd.DataFrame([
        {
            "Tarih": item.date.date(),
            "Şube": item.branch_name,
            "KPI": item.metric_label,
            "Önem": item.severity.capitalize(),
            "Gerçekleşen": item.actual_value,
            "Olağan Medyan": item.expected_value,
            "Sapma (%)": item.deviation_pct,
            "Anomali Skoru": item.anomaly_score,
            "İncelenecek Alan": item.suggested_check,
        }
        for item in anomalies
    ])


st.markdown(
    """
    <style>
        .stApp { background-color: #f4f6f8; }
        .block-container { max-width: 1400px; padding-top: 1.5rem; }
        .risk-header {
            padding: 1.25rem 1.5rem; border-radius: 16px; color: white;
            background: linear-gradient(110deg, #14213d, #21345c);
            border-bottom: 6px solid #ffcc00;
            box-shadow: 0 8px 24px rgba(20, 33, 61, .14);
        }
        .risk-header h1 { color: white; margin: 0; }
        .risk-header p { color: #dce5f3; margin: .35rem 0 0; }
        .risk-note {
            margin: 1rem 0; padding: .8rem 1rem; border-radius: 10px;
            background: #fff8d6; color: #4a3c00; border: 1px solid #f3d75a;
        }
        .anomaly-card {
            margin: .65rem 0; padding: .9rem 1.1rem; border-radius: 12px;
            background: white; border-left: 6px solid #d6a900;
            box-shadow: 0 4px 14px rgba(20, 33, 61, .08);
        }
        .anomaly-card.high { border-left-color: #c84b45; }
        .anomaly-title { color: #14213d; font-weight: 800; }
        .anomaly-values { color: #4f5f73; margin-top: .4rem; }
        .anomaly-check { color: #33445e; margin-top: .5rem; }
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
    <div class="risk-header">
        <h1>Risk ve Anomali İzleme</h1>
        <p>Şubelerin kendi olağan performansından sapan günlük KPI değerleri</p>
    </div>
    """,
    unsafe_allow_html=True,
)

try:
    data = load_risk_data(str(DATA_PATH), DATA_PATH.stat().st_mtime)
    all_anomalies = detect_anomalies(data)
except (OSError, DataLoadError, RiskPageError, AnomalyDetectionError) as error:
    st.error(f"Anomali verisi hazırlanamadı: {error}")
    st.stop()

minimum_date = data["tarih"].min().date()
maximum_date = data["tarih"].max().date()
branch_names = sorted(data["sube_adi"].unique())
metric_labels = sorted({item.metric_label for item in all_anomalies})

st.sidebar.markdown("## Anomali Filtreleri")
date_range = st.sidebar.date_input(
    "Anomali tarihi", value=(minimum_date, maximum_date),
    min_value=minimum_date, max_value=maximum_date, format="DD.MM.YYYY",
)
selected_branches = st.sidebar.multiselect(
    "Şubeler", options=branch_names, default=branch_names,
)
selected_metrics = st.sidebar.multiselect(
    "KPI'lar", options=metric_labels, default=metric_labels,
)
selected_severities = st.sidebar.multiselect(
    "Önem seviyesi", options=["yüksek", "orta"], default=["yüksek", "orta"],
    format_func=str.capitalize,
)

if not isinstance(date_range, (tuple, list)) or len(date_range) != 2:
    st.warning("Başlangıç ve bitiş tarihini birlikte seçin.")
    st.stop()
if not selected_branches or not selected_metrics or not selected_severities:
    st.warning("Şube, KPI ve önem filtrelerinde en az bir seçenek bırakın.")
    st.stop()

start_date, end_date = date_range
filtered = [
    item for item in all_anomalies
    if start_date <= item.date.date() <= end_date
    and item.branch_name in selected_branches
    and item.metric_label in selected_metrics
    and item.severity in selected_severities
]

high_count = sum(item.severity == "yüksek" for item in filtered)
affected_branches = len({item.branch_name for item in filtered})
latest_date = max((item.date for item in filtered), default=None)
cards = st.columns(4)
cards[0].metric("Toplam Anomali", len(filtered))
cards[1].metric("Yüksek Önemli", high_count)
cards[2].metric("Etkilenen Şube", affected_branches)
cards[3].metric("Son Anomali", latest_date.strftime("%d.%m.%Y") if latest_date else "—")

st.markdown(
    """
    <div class="risk-note">
        Olağan değerler şubenin tüm tarihsel kayıtlarından medyan–MAD yöntemiyle
        hesaplanır; tarih filtresi yalnızca gösterilecek anomalileri sınırlar.
        Anomali, mutlaka operasyonel hata veya kesin neden anlamına gelmez.
    </div>
    """,
    unsafe_allow_html=True,
)

if not filtered:
    st.info("Seçilen filtrelere uyan bir anomali bulunmadı.")
    st.stop()

table = anomalies_to_table(filtered)
figure = px.scatter(
    table, x="Tarih", y="Anomali Skoru", color="Önem", symbol="KPI",
    hover_name="Şube", hover_data=["Gerçekleşen", "Olağan Medyan", "Sapma (%)"],
    title="Anomalilerin Zaman Dağılımı",
    color_discrete_map={"Yüksek": "#c84b45", "Orta": "#d6a900"},
)
figure.add_hline(y=3.5, line_dash="dash", line_color="#d6a900", annotation_text="Orta eşik")
figure.add_hline(y=4.5, line_dash="dash", line_color="#c84b45", annotation_text="Yüksek eşik")
figure.update_layout(
    height=430, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    legend_title_text="Gösterge",
)
st.plotly_chart(figure, width="stretch")

st.subheader("En Güncel Anomaliler")
for item in filtered[:10]:
    card_class = "anomaly-card high" if item.severity == "yüksek" else "anomaly-card"
    st.markdown(
        f"""
        <div class="{card_class}">
            <div class="anomaly-title">
                {item.date:%d.%m.%Y} · {item.branch_name} · {item.metric_label}
            </div>
            <div class="anomaly-values">
                Gerçekleşen: <strong>{item.actual_value:.2f}</strong> ·
                Olağan medyan: <strong>{item.expected_value:.2f}</strong> ·
                Skor: <strong>{item.anomaly_score:.2f}</strong> ·
                Önem: <strong>{item.severity.capitalize()}</strong>
            </div>
            <div class="anomaly-check"><strong>İnceleme:</strong> {item.suggested_check}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.subheader("Tüm Anomali Kayıtları")
st.dataframe(table, hide_index=True, width="stretch")
st.download_button(
    "Anomalileri CSV olarak indir",
    data=table.to_csv(index=False).encode("utf-8-sig"),
    file_name=f"anomali_kayitlari_{start_date}_{end_date}.csv",
    mime="text/csv",
)
