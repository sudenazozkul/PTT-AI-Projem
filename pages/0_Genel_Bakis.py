"""PTT AI Şube Performans Danışmanı Streamlit uygulaması."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]
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
        .branch-highlight {
            min-height: 112px;
            padding: 1rem 1.2rem;
            border-radius: 14px;
            background: white;
            box-shadow: 0 4px 15px rgba(20, 33, 61, 0.08);
        }
        .branch-highlight.success { border-left: 6px solid #237a57; }
        .branch-highlight.risk { border-left: 6px solid #c84b45; }
        .branch-highlight .name { color: #14213d; font-size: 1.2rem; font-weight: 800; }
        .branch-highlight .detail { color: #607086; margin-top: .35rem; }
        section[data-testid="stSidebar"] {
            background: #14213d;
            border-right: 4px solid #ffcc00;
        }
        section[data-testid="stSidebar"] * { color: #f7f9fc; }
        section[data-testid="stSidebar"] [data-baseweb="select"] * { color: #14213d; }
        section[data-testid="stSidebar"] input { color: #14213d; }
        @media (max-width: 900px) {
            .metric-grid { grid-template-columns: repeat(2, 1fr); }
            .ptt-header h1 { font-size: 1.45rem; }

        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    f"""
    <div class="ptt-header">
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

# Kullanıcı seçimlerine göre günlük veriyi filtreler.
st.sidebar.markdown("## Rapor Filtreleri")
st.sidebar.caption("Kartlar, grafikler ve tablo seçimlerinize göre güncellenir.")

minimum_date = daily_kpis["tarih"].min().date()
maximum_date = daily_kpis["tarih"].max().date()
date_range = st.sidebar.date_input(
    "Tarih aralığı",
    value=(minimum_date, maximum_date),
    min_value=minimum_date,
    max_value=maximum_date,
    format="DD.MM.YYYY",
)
if not isinstance(date_range, (tuple, list)) or len(date_range) != 2:
    st.warning("Analiz için başlangıç ve bitiş tarihini birlikte seçin.")
    st.stop()

selected_city = st.sidebar.selectbox(
    "İl", ["Tüm İller", *sorted(daily_kpis["il"].unique())]
)
selected_types = st.sidebar.multiselect(
    "Şube tipi",
    sorted(daily_kpis["sube_tipi"].unique()),
    placeholder="Tüm şube tipleri",
)
available_branches = daily_kpis.copy()
if selected_city != "Tüm İller":
    available_branches = available_branches[available_branches["il"] == selected_city]
if selected_types:
    available_branches = available_branches[
        available_branches["sube_tipi"].isin(selected_types)
    ]
selected_branches = st.sidebar.multiselect(
    "Şube",
    sorted(available_branches["sube_adi"].unique()),
    placeholder="Tüm uygun şubeler",
)

start_date, end_date = date_range
filter_mask = daily_kpis["tarih"].dt.date.between(start_date, end_date)
if selected_city != "Tüm İller":
    filter_mask &= daily_kpis["il"].eq(selected_city)
if selected_types:
    filter_mask &= daily_kpis["sube_tipi"].isin(selected_types)
if selected_branches:
    filter_mask &= daily_kpis["sube_adi"].isin(selected_branches)

daily_kpis = daily_kpis.loc[filter_mask].copy()
if daily_kpis.empty:
    st.warning("Seçilen filtrelere uygun performans kaydı bulunamadı.")
    st.stop()
branch_summary = calculate_branch_summary(daily_kpis)
st.sidebar.markdown("---")
st.sidebar.write(f"**Kayıt:** {format_number(len(daily_kpis))}")
st.sidebar.write(f"**Şube:** {daily_kpis['sube_kodu'].nunique()}")

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

best_branch = branch_summary.iloc[0]
risk_branch = branch_summary.sort_values("gecikme_orani_pct", ascending=False).iloc[0]
best_column, risk_column = st.columns(2)
with best_column:
    st.markdown(
        f"""
        <div class="branch-highlight success">
            <div class="metric-label">En Başarılı Şube</div>
            <div class="name">{best_branch['sube_adi']}</div>
            <div class="detail">Teslim başarısı: %{best_branch['teslim_basarisi_pct']:.2f}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with risk_column:
    st.markdown(
        f"""
        <div class="branch-highlight risk">
            <div class="metric-label">En Riskli Şube</div>
            <div class="name">{risk_branch['sube_adi']}</div>
            <div class="detail">Gecikme oranı: %{risk_branch['gecikme_orani_pct']:.2f}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown('<div class="section-title">Performans Grafikleri</div>', unsafe_allow_html=True)
comparison_column, trend_column = st.columns(2)

comparison_data = branch_summary.sort_values("teslim_basarisi_pct")
comparison_figure = px.bar(
    comparison_data,
    x="teslim_basarisi_pct",
    y="sube_adi",
    orientation="h",
    color="teslim_basarisi_pct",
    color_continuous_scale=["#c84b45", "#ffcc00", "#237a57"],
    text="teslim_basarisi_pct",
    labels={"teslim_basarisi_pct": "Teslim başarısı (%)", "sube_adi": "Şube"},
    title="Şube Teslim Başarısı Karşılaştırması",
)
comparison_figure.update_traces(
    texttemplate="%{text:.2f}%", textposition="outside",
    hovertemplate="<b>%{y}</b><br>Teslim başarısı: %{x:.2f}%<extra></extra>",
)
comparison_figure.update_layout(
    coloraxis_showscale=False, height=430,
    margin=dict(l=10, r=25, t=55, b=10),
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#14213d"),
    xaxis=dict(range=[0, 105], showgrid=True, gridcolor="#e3e8ef"),
    yaxis_title=None,
)
comparison_column.plotly_chart(comparison_figure, width="stretch")

monthly = daily_kpis.assign(
    ay=daily_kpis["tarih"].dt.to_period("M").dt.to_timestamp()
)
monthly = monthly.groupby("ay", as_index=False).agg(
    toplam_kabul=("kabul_edilen", "sum"),
    toplam_teslim=("teslim_edilen", "sum"),
    toplam_geciken=("geciken", "sum"),
    toplam_sikayet=("sikayet_sayisi", "sum"),
)
monthly["teslim_basarisi_pct"] = monthly["toplam_teslim"] / monthly["toplam_kabul"] * 100
monthly["gecikme_orani_pct"] = monthly["toplam_geciken"] / monthly["toplam_kabul"] * 100
monthly["sikayet_orani_binde"] = monthly["toplam_sikayet"] / monthly["toplam_teslim"] * 1000

trend_figure = px.line(
    monthly, x="ay", y="teslim_basarisi_pct", markers=True,
    labels={"ay": "Ay", "teslim_basarisi_pct": "Teslim başarısı (%)"},
    title="Aylık Teslim Başarısı Trendi",
)
trend_figure.update_traces(line_color="#14213d", marker_color="#ffcc00")
trend_figure.update_layout(
    height=430, margin=dict(l=10, r=10, t=55, b=10),
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#14213d"),
    yaxis=dict(showgrid=True, gridcolor="#e3e8ef", ticksuffix="%"),
    xaxis=dict(showgrid=False, tickformat="%b %Y"),
)
trend_column.plotly_chart(trend_figure, width="stretch")

st.markdown('<div class="section-title">Risk ve Kalite Eğilimleri</div>', unsafe_allow_html=True)
delay_column, complaint_column = st.columns(2)
delay_figure = px.area(
    monthly, x="ay", y="gecikme_orani_pct", markers=True,
    labels={"ay": "Ay", "gecikme_orani_pct": "Gecikme oranı (%)"},
    title="Aylık Gecikme Oranı",
)
delay_figure.update_traces(line_color="#c84b45", fillcolor="rgba(200,75,69,.18)")
complaint_figure = px.bar(
    monthly, x="ay", y="sikayet_orani_binde",
    labels={"ay": "Ay", "sikayet_orani_binde": "Şikâyet oranı (‰)"},
    title="Her 1.000 Teslimattaki Şikâyet",
    color_discrete_sequence=["#d6a900"],
)
for figure in (delay_figure, complaint_figure):
    figure.update_layout(
        height=360, margin=dict(l=10, r=10, t=55, b=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#14213d"),
        xaxis=dict(showgrid=False, tickformat="%b %Y"),
        yaxis=dict(showgrid=True, gridcolor="#e3e8ef"),
    )
delay_column.plotly_chart(delay_figure, width="stretch")
complaint_column.plotly_chart(complaint_figure, width="stretch")

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
