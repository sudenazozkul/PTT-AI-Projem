"""PTT AI Şube Performans Danışmanı sayfa yöneticisi."""

import base64
from pathlib import Path

import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parent
LOGO_PATH = PROJECT_ROOT / "PTT_bayragi.png"
LOGO_BASE64 = base64.b64encode(LOGO_PATH.read_bytes()).decode("utf-8")

st.set_page_config(
    page_title="PTT AI Şube Performans Danışmanı",
    page_icon=str(LOGO_PATH),
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    f"""
    <style>
        section[data-testid="stSidebar"] [data-testid="stSidebarHeader"] {{
            min-height: 116px;
            height: 116px;
            padding: 0;
            overflow: hidden;
            background-color: #14213d;
            background-image:
                url("data:image/png;base64,{LOGO_BASE64}"),
                linear-gradient(
                    to bottom,
                    #14213d 0,
                    #14213d 10px,
                    #ffca28 10px,
                    #ffca28 111px,
                    #14213d 111px
                );
            background-size: auto 88px, 100% 100%;
            background-position: center 17px, center;
            background-repeat: no-repeat, no-repeat;
            border-bottom: 5px solid #ffcc00;
        }}
        section[data-testid="stSidebar"] [data-testid="stLogo"] {{
            display: none;
        }}
    </style>
    """,
    unsafe_allow_html=True,
)

navigation = st.navigation(
    [
        st.Page(
            "pages/0_Genel_Bakis.py",
            title="Genel Bakış",
            url_path="genel-bakis",
            default=True,
        ),
        st.Page(
            "pages/1_Sube_Detayi.py",
            title="Şube Detayı",
            url_path="sube-detayi",
        ),
        st.Page(
            "pages/2_Sube_Karsilastirma.py",
            title="Şube Karşılaştırma",
            url_path="sube-karsilastirma",
        ),
        st.Page(
            "pages/3_Analiz_ve_Oneriler.py",
            title="Analiz ve Öneriler",
            url_path="analiz-ve-oneriler",
        ),
    ],
    position="sidebar",
    expanded=True,
)

navigation.run()
