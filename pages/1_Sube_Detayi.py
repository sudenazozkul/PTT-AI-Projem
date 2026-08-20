"""Tek bir PTT şubesinin ayrıntılı performans ekranı."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from ptt_ai_projem.data_loader import DataLoadError, load_branch_data
from ptt_ai_projem.kpi import calculate_branch_summary, calculate_daily_kpis
from ptt_ai_projem.validation import validate_branch_data


DATA_PATH = PROJECT_ROOT / "data" / "sube_performans.csv"

@st.cache_data(show_spinner="Şube detayları hazırlanıyor...")
def load_dashboard_data(csv_path: str, modified_at: float) -> pd.DataFrame:
    """Kaynak veriyi okuyup doğruladıktan sonra günlük KPI'ları döndürür."""
    _ = modified_at
    raw_data = load_branch_data(csv_path)
    validation = validate_branch_data(raw_data)
    if not validation.is_valid or validation.cleaned_data is None:
        raise ValueError("\n".join(validation.errors))
    return calculate_daily_kpis(validation.cleaned_data)


def weighted_delivery_success(data: pd.DataFrame) -> float:
    """Toplam teslim ve kabul sayılarını kullanarak başarı oranı hesaplar."""
    accepted = data["kabul_edilen"].sum()
    return data["teslim_edilen"].sum() / accepted * 100 if accepted else 0.0


def period_delta(data: pd.DataFrame, column: str) -> float | None:
    """Son 30 gün ile önceki 30 günün ağırlıklı KPI farkını döndürür."""
    last_date = data["tarih"].max()
    recent = data[data["tarih"] > last_date - pd.Timedelta(days=30)]
    previous = data[
        (data["tarih"] > last_date - pd.Timedelta(days=60))
        & (data["tarih"] <= last_date - pd.Timedelta(days=30))
    ]
    if recent.empty or previous.empty:
        return None
    recent_value = float(calculate_branch_summary(recent).iloc[0][column])
    previous_value = float(calculate_branch_summary(previous).iloc[0][column])
    return recent_value - previous_value


st.markdown(
    """
    <style>
        .stApp { background-color: #f4f6f8; }
        .block-container { max-width: 1400px; padding-top: 1.5rem; }
        .detail-header {
            padding: 1.2rem 1.5rem;
            border-radius: 16px;
            color: white;
            background: linear-gradient(110deg, #14213d, #21345c);
            border-bottom: 6px solid #ffcc00;
        }
        .detail-header h1 { color: white; margin: 0; }
        .detail-header p { color: #dce5f3; margin: .35rem 0 0; }
        section[data-testid="stSidebar"] {
            background: #14213d;
            border-right: 4px solid #ffcc00;
        }
        section[data-testid="stSidebar"] * { color: #f7f9fc; }
        section[data-testid="stSidebar"] [data-baseweb="select"] * { color: #14213d; }
        section[data-testid="stSidebar"] input { color: #14213d; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="detail-header">
        <h1>Şube Performans Detayı</h1>
        <p>Seçilen şubenin KPI, iş yükü, personel ve kalite eğilimleri</p>
    </div>
    """,
    unsafe_allow_html=True,
)

try:
    daily_data = load_dashboard_data(str(DATA_PATH), DATA_PATH.stat().st_mtime)
except (OSError, DataLoadError, ValueError) as error:
    st.error(f"Şube verisi hazırlanamadı: {error}")
    st.stop()

st.sidebar.markdown("## Şube Seçimi")
selected_branch = st.sidebar.selectbox(
    "Şube",
    sorted(daily_data["sube_adi"].unique()),
)
minimum_date = daily_data["tarih"].min().date()
maximum_date = daily_data["tarih"].max().date()
date_range = st.sidebar.date_input(
    "Tarih aralığı",
    value=(minimum_date, maximum_date),
    min_value=minimum_date,
    max_value=maximum_date,
    format="DD.MM.YYYY",
)
if not isinstance(date_range, (tuple, list)) or len(date_range) != 2:
    st.warning("Başlangıç ve bitiş tarihini birlikte seçin.")
    st.stop()

start_date, end_date = date_range
branch_data = daily_data[
    daily_data["sube_adi"].eq(selected_branch)
    & daily_data["tarih"].dt.date.between(start_date, end_date)
].copy()
if branch_data.empty:
    st.warning("Seçilen dönem için şube kaydı bulunamadı.")
    st.stop()

summary = calculate_branch_summary(branch_data).iloc[0]
st.subheader(f"{selected_branch} — {summary['sube_tipi']} Şube")
st.caption(
    f"{summary['il']} / {summary['ilce']} · "
    f"{start_date.strftime('%d.%m.%Y')}–{end_date.strftime('%d.%m.%Y')}"
)

success_delta = period_delta(branch_data, "teslim_basarisi_pct")
delay_delta = period_delta(branch_data, "gecikme_orani_pct")
time_delta = period_delta(branch_data, "ortalama_teslim_suresi")

cards = st.columns(5)
cards[0].metric(
    "Teslim Başarısı",
    f"%{summary['teslim_basarisi_pct']:.2f}",
    None if success_delta is None else f"{success_delta:+.2f} puan",
)
cards[1].metric(
    "Gecikme Oranı",
    f"%{summary['gecikme_orani_pct']:.2f}",
    None if delay_delta is None else f"{delay_delta:+.2f} puan",
    delta_color="inverse",
)
cards[2].metric(
    "Teslim Süresi",
    f"{summary['ortalama_teslim_suresi']:.2f} gün",
    None if time_delta is None else f"{time_delta:+.2f} gün",
    delta_color="inverse",
)
cards[3].metric("Personel Verimliliği", f"{summary['personel_verimliligi']:.2f}")
cards[4].metric("Dağıtıcı İş Yükü", f"{summary['dagitici_is_yuku']:.2f}")
st.caption("Kartlardaki değişimler son 30 günün önceki 30 güne farkını gösterir.")

monthly = branch_data.assign(
    ay=branch_data["tarih"].dt.to_period("M").dt.to_timestamp(),
    teslim_suresi_agirlikli=(
        branch_data["ortalama_teslim_suresi"] * branch_data["teslim_edilen"]
    ),
).groupby("ay", as_index=False).agg(
    kabul_edilen=("kabul_edilen", "sum"),
    teslim_edilen=("teslim_edilen", "sum"),
    geciken=("geciken", "sum"),
    sikayet_sayisi=("sikayet_sayisi", "sum"),
    teslim_suresi_agirlikli=("teslim_suresi_agirlikli", "sum"),
    personel_verimliligi=("personel_verimliligi", "mean"),
    dagitici_is_yuku=("dagitici_is_yuku", "mean"),
)
monthly["teslim_basarisi_pct"] = (
    monthly["teslim_edilen"] / monthly["kabul_edilen"] * 100
)
monthly["gecikme_orani_pct"] = monthly["geciken"] / monthly["kabul_edilen"] * 100
monthly["ortalama_teslim_suresi"] = (
    monthly["teslim_suresi_agirlikli"]
    .div(monthly["teslim_edilen"].replace(0, pd.NA))
    .fillna(0)
)

left_chart, right_chart = st.columns(2)
performance_figure = go.Figure()
performance_figure.add_trace(go.Scatter(
    x=monthly["ay"], y=monthly["teslim_basarisi_pct"],
    name="Teslim başarısı", mode="lines+markers", line=dict(color="#237a57"),
))
performance_figure.add_trace(go.Scatter(
    x=monthly["ay"], y=monthly["gecikme_orani_pct"],
    name="Gecikme oranı", mode="lines+markers", line=dict(color="#c84b45"),
))
performance_figure.update_layout(
    title="Aylık Başarı ve Gecikme Eğilimi", height=410,
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    yaxis_ticksuffix="%", hovermode="x unified",
)
left_chart.plotly_chart(performance_figure, width="stretch")

workload_figure = px.line(
    monthly, x="ay", y=["dagitici_is_yuku", "personel_verimliligi"],
    markers=True, title="İş Yükü ve Personel Verimliliği",
    labels={"ay": "Ay", "value": "Günlük ortalama", "variable": "Gösterge"},
    color_discrete_sequence=["#d6a900", "#2878b5"],
)
workload_figure.update_layout(
    height=410, paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)", hovermode="x unified",
)
right_chart.plotly_chart(workload_figure, width="stretch")

quality_chart, volume_chart = st.columns(2)
quality_figure = px.line(
    monthly, x="ay", y="ortalama_teslim_suresi", markers=True,
    title="Ortalama Teslim Süresi", labels={"ay": "Ay", "ortalama_teslim_suresi": "Gün"},
    color_discrete_sequence=["#c84b45"],
)
quality_figure.update_layout(
    height=350, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)"
)
quality_chart.plotly_chart(quality_figure, width="stretch")

volume_figure = px.bar(
    monthly, x="ay", y="kabul_edilen", title="Aylık Gönderi Hacmi",
    labels={"ay": "Ay", "kabul_edilen": "Kabul edilen gönderi"},
    color_discrete_sequence=["#14213d"],
)
volume_figure.update_layout(
    height=350, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)"
)
volume_chart.plotly_chart(volume_figure, width="stretch")

st.subheader("Günlük KPI Kayıtları")
detail_table = branch_data[
    [
        "tarih", "kabul_edilen", "teslim_edilen", "teslim_basarisi_pct",
        "gecikme_orani_pct", "ortalama_teslim_suresi", "personel_verimliligi",
        "dagitici_is_yuku", "sikayet_sayisi",
    ]
].sort_values("tarih", ascending=False).rename(columns={
    "tarih": "Tarih", "kabul_edilen": "Kabul Edilen",
    "teslim_edilen": "Teslim Edilen", "teslim_basarisi_pct": "Teslim Başarısı (%)",
    "gecikme_orani_pct": "Gecikme Oranı (%)",
    "ortalama_teslim_suresi": "Teslim Süresi (gün)",
    "personel_verimliligi": "Personel Verimliliği",
    "dagitici_is_yuku": "Dağıtıcı İş Yükü", "sikayet_sayisi": "Şikâyet",
})
st.dataframe(detail_table, hide_index=True, width="stretch")
