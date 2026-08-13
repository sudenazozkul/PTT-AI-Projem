"""İki veya daha fazla PTT şubesini karşılaştıran dashboard sayfası."""

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
COLORS = ["#14213d", "#d6a900", "#2878b5", "#c84b45", "#237a57", "#7d57a5"]


@st.cache_data(show_spinner="Karşılaştırma verileri hazırlanıyor...")
def load_kpi_data(csv_path: str, modified_at: float) -> pd.DataFrame:
    """CSV'yi doğrulayıp günlük KPI tablosunu hazırlar."""
    _ = modified_at
    raw_data = load_branch_data(csv_path)
    validation = validate_branch_data(raw_data)
    if not validation.is_valid or validation.cleaned_data is None:
        raise ValueError("\n".join(validation.errors))
    return calculate_daily_kpis(validation.cleaned_data)


st.markdown(
    """
    <style>
        .stApp { background-color: #f4f6f8; }
        .block-container { max-width: 1400px; padding-top: 1.5rem; }
        .compare-header {
            padding: 1.2rem 1.5rem;
            border-radius: 16px;
            color: white;
            background: linear-gradient(110deg, #14213d, #21345c);
            border-bottom: 6px solid #ffcc00;
        }
        .compare-header h1 { color: white; margin: 0; }
        .compare-header p { color: #dce5f3; margin: .35rem 0 0; }
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
    <div class="compare-header">
        <h1>Şube Performans Karşılaştırması</h1>
        <p>Şubeleri aynı dönem ve ortak KPI'lar üzerinden yan yana inceleyin</p>
    </div>
    """,
    unsafe_allow_html=True,
)

try:
    daily_data = load_kpi_data(str(DATA_PATH), DATA_PATH.stat().st_mtime)
except (OSError, DataLoadError, ValueError) as error:
    st.error(f"Karşılaştırma verisi hazırlanamadı: {error}")
    st.stop()

branch_options = sorted(daily_data["sube_adi"].unique())
st.sidebar.markdown("## Karşılaştırma Seçimleri")
selected_branches = st.sidebar.multiselect(
    "Şubeler",
    branch_options,
    default=branch_options[:2],
    max_selections=6,
    help="En az 2, en fazla 6 şube seçin.",
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

if len(selected_branches) < 2:
    st.info("Karşılaştırma için en az iki şube seçin.")
    st.stop()
if not isinstance(date_range, (tuple, list)) or len(date_range) != 2:
    st.warning("Başlangıç ve bitiş tarihini birlikte seçin.")
    st.stop()

start_date, end_date = date_range
comparison_data = daily_data[
    daily_data["sube_adi"].isin(selected_branches)
    & daily_data["tarih"].dt.date.between(start_date, end_date)
].copy()
if comparison_data.empty:
    st.warning("Seçilen şube ve döneme uygun kayıt bulunamadı.")
    st.stop()

summary = calculate_branch_summary(comparison_data)
st.caption(
    f"{len(selected_branches)} şube · "
    f"{start_date.strftime('%d.%m.%Y')}–{end_date.strftime('%d.%m.%Y')} · "
    f"{len(comparison_data):,.0f} günlük kayıt".replace(",", ".")
)

best = summary.iloc[0]
lowest_delay = summary.sort_values("gecikme_orani_pct").iloc[0]
highest_productivity = summary.sort_values("personel_verimliligi", ascending=False).iloc[0]
highest_revenue = summary.sort_values("gonderi_basi_gelir", ascending=False).iloc[0]
cards = st.columns(4)
cards[0].metric("En Yüksek Teslim Başarısı", best["sube_adi"], f"%{best['teslim_basarisi_pct']:.2f}")
cards[1].metric("En Düşük Gecikme", lowest_delay["sube_adi"], f"%{lowest_delay['gecikme_orani_pct']:.2f}")
cards[2].metric("En Yüksek Verimlilik", highest_productivity["sube_adi"], f"{highest_productivity['personel_verimliligi']:.2f}")
cards[3].metric("En Yüksek Birim Gelir", highest_revenue["sube_adi"], f"{highest_revenue['gonderi_basi_gelir']:.2f} TL")

metric_labels = {
    "teslim_basarisi_pct": "Teslim Başarısı (%)",
    "gecikme_orani_pct": "Gecikme Oranı (%)",
    "iade_orani_pct": "İade Oranı (%)",
    "sikayet_orani_binde": "Şikâyet Oranı (‰)",
    "personel_verimliligi": "Personel Verimliliği",
    "dagitici_is_yuku": "Dağıtıcı İş Yükü",
    "gonderi_basi_gelir": "Gönderi Başına Gelir (TL)",
    "ortalama_teslim_suresi": "Ortalama Teslim Süresi (gün)",
}
selected_metric = st.selectbox(
    "Karşılaştırılacak gösterge",
    list(metric_labels),
    format_func=metric_labels.get,
)

bar_figure = px.bar(
    summary.sort_values(selected_metric, ascending=False),
    x="sube_adi",
    y=selected_metric,
    color="sube_adi",
    text=selected_metric,
    title=metric_labels[selected_metric],
    labels={"sube_adi": "Şube", selected_metric: metric_labels[selected_metric]},
    color_discrete_sequence=COLORS,
)
bar_figure.update_traces(texttemplate="%{text:.2f}", textposition="outside")
bar_figure.update_layout(
    height=430, showlegend=False,
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    yaxis=dict(showgrid=True, gridcolor="#e3e8ef"),
)
st.plotly_chart(bar_figure, width="stretch")

monthly = comparison_data.assign(
    ay=comparison_data["tarih"].dt.to_period("M").dt.to_timestamp()
).groupby(["ay", "sube_adi"], as_index=False).agg(
    toplam_kabul=("kabul_edilen", "sum"),
    toplam_teslim=("teslim_edilen", "sum"),
    toplam_geciken=("geciken", "sum"),
)
monthly["teslim_basarisi_pct"] = monthly["toplam_teslim"] / monthly["toplam_kabul"] * 100
monthly["gecikme_orani_pct"] = monthly["toplam_geciken"] / monthly["toplam_kabul"] * 100

success_column, delay_column = st.columns(2)
success_figure = px.line(
    monthly, x="ay", y="teslim_basarisi_pct", color="sube_adi", markers=True,
    title="Aylık Teslim Başarısı", labels={"ay": "Ay", "teslim_basarisi_pct": "Başarı (%)", "sube_adi": "Şube"},
    color_discrete_sequence=COLORS,
)
delay_figure = px.line(
    monthly, x="ay", y="gecikme_orani_pct", color="sube_adi", markers=True,
    title="Aylık Gecikme Oranı", labels={"ay": "Ay", "gecikme_orani_pct": "Gecikme (%)", "sube_adi": "Şube"},
    color_discrete_sequence=COLORS,
)
for figure in (success_figure, delay_figure):
    figure.update_layout(
        height=390, paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)", hovermode="x unified",
        xaxis=dict(tickformat="%b %Y", showgrid=False),
        yaxis=dict(showgrid=True, gridcolor="#e3e8ef", ticksuffix="%"),
    )
success_column.plotly_chart(success_figure, width="stretch")
delay_column.plotly_chart(delay_figure, width="stretch")

st.subheader("Karşılaştırma Tablosu")
table = summary[
    ["sube_adi", *metric_labels.keys(), "toplam_kabul", "toplam_gelir"]
].rename(columns={
    "sube_adi": "Şube", **metric_labels,
    "toplam_kabul": "Toplam Gönderi", "toplam_gelir": "Toplam Gelir",
})
st.dataframe(
    table,
    hide_index=True,
    width="stretch",
    column_config={
        "Teslim Başarısı (%)": st.column_config.ProgressColumn(
            min_value=0, max_value=100, format="%.2f%%"
        )
    },
)
