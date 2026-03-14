import streamlit as st
import pandas as pd
import requests
import json
import base64

# Crédito al final de la app (cámbialo por tu nombre o enlace a LinkedIn)
HECHO_POR = "Hecho por [tu nombre o enlace a LinkedIn]"

# Detectar si hay Secrets (producción): entonces ocultar sidebar por completo
try:
    st.secrets["API_LOGIN"]
    _usar_secrets = True
except Exception:
    _usar_secrets = False

st.set_page_config(
    page_title="Tourism Demand Index",
    layout="wide",
    initial_sidebar_state="collapsed" if _usar_secrets else "auto"
)
st.title("Tourism Demand Index")

# En producción: ocultar sidebar, menú, cabecera y que nadie vea tu correo
if _usar_secrets:
    st.markdown("""
        <style>
            [data-testid="stSidebar"] { display: none !important; width: 0 !important; }
            section[data-testid="stSidebar"] { display: none !important; }
            [data-testid="collapsedControl"] { display: none !important; }
            .stApp [data-testid="stSidebar"] { display: none !important; }
            header[data-testid="stHeader"] { display: none !important; }
            [data-testid="stHeader"] { display: none !important; }
            [data-testid="stToolbar"] { display: none !important; }
            #MainMenu { visibility: hidden !important; }
            footer { visibility: hidden !important; }
            header { visibility: hidden !important; }
            /* Capa que tapa la barra superior donde Streamlit Cloud muestra el correo */
            .stApp::before {
                content: "";
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                height: 56px;
                background: #ffffff;
                z-index: 999999;
                pointer-events: none;
            }
            [data-testid="stAppViewContainer"] { padding-top: 0 !important; }
        </style>
    """, unsafe_allow_html=True)

# ── Credenciales (solo desarrollo; en producción no se muestra nada en sidebar)
def get_credentials():
    try:
        return st.secrets["API_LOGIN"], st.secrets["API_PASSWORD"]
    except Exception:
        with st.sidebar:
            st.subheader("🔑 Conexión (solo desarrollo)")
            login = st.text_input("Email", placeholder="tu_email@ejemplo.com", key="api_login")
            password = st.text_input("Clave", type="password", placeholder="tu_clave", key="api_pass")
        return login, password

API_LOGIN, API_PASSWORD = get_credentials()

if API_LOGIN and API_PASSWORD:
    credentials = base64.b64encode(f"{API_LOGIN}:{API_PASSWORD}".encode()).decode()
    headers = {
        "Authorization": f"Basic {credentials}",
        "Content-Type": "application/json"
    }
    try:
        st.secrets["API_LOGIN"]
    except Exception:
        st.sidebar.success("✅ Conectado")
else:
    headers = None
    try:
        st.secrets["API_LOGIN"]
    except Exception:
        st.sidebar.warning("Introduce credenciales para datos en vivo.")

# ── Keywords y países ────────────────────────────────────
KEYWORDS_TURISMO = [
    "viajes a Dubai", "vuelos a Abu Dhabi", "turismo España", "viajes Grecia",
    "turismo Tailandia", "vuelos Japón", "viajes Marruecos", "turismo Canarias",
    "viajes Croacia", "turismo Malta"
]
LOCATION_CODES = {
    "España": 2724, "Alemania": 2276, "Reino Unido": 2826,
    "Francia": 2250, "Italia": 2380
}


def get_demo_data():
    """Datos de ejemplo para que los visitantes vean el dashboard sin consumir API."""
    return pd.DataFrame([
        {"País": "España", "Keyword": "turismo España", "Volumen Mensual": 201000, "Competencia": 0.85, "CPC (€)": 0.42},
        {"País": "España", "Keyword": "viajes a Dubai", "Volumen Mensual": 165000, "Competencia": 0.72, "CPC (€)": 0.89},
        {"País": "Alemania", "Keyword": "turismo España", "Volumen Mensual": 135000, "Competencia": 0.78, "CPC (€)": 0.38},
        {"País": "Reino Unido", "Keyword": "viajes Grecia", "Volumen Mensual": 110000, "Competencia": 0.81, "CPC (€)": 0.55},
        {"País": "Francia", "Keyword": "turismo Tailandia", "Volumen Mensual": 99000, "Competencia": 0.69, "CPC (€)": 0.62},
        {"País": "Italia", "Keyword": "viajes Marruecos", "Volumen Mensual": 74000, "Competencia": 0.65, "CPC (€)": 0.48},
        {"País": "España", "Keyword": "turismo Canarias", "Volumen Mensual": 90500, "Competencia": 0.71, "CPC (€)": 0.31},
        {"País": "Alemania", "Keyword": "vuelos Japón", "Volumen Mensual": 82300, "Competencia": 0.88, "CPC (€)": 1.12},
        {"País": "Reino Unido", "Keyword": "turismo Malta", "Volumen Mensual": 60100, "Competencia": 0.58, "CPC (€)": 0.44},
        {"País": "Francia", "Keyword": "viajes Croacia", "Volumen Mensual": 55200, "Competencia": 0.64, "CPC (€)": 0.52},
        {"País": "España", "Keyword": "vuelos a Abu Dhabi", "Volumen Mensual": 49500, "Competencia": 0.76, "CPC (€)": 0.95},
        {"País": "Italia", "Keyword": "viajes a Dubai", "Volumen Mensual": 67800, "Competencia": 0.74, "CPC (€)": 0.87},
        {"País": "Reino Unido", "Keyword": "turismo España", "Volumen Mensual": 142000, "Competencia": 0.82, "CPC (€)": 0.41},
        {"País": "Alemania", "Keyword": "viajes Grecia", "Volumen Mensual": 88700, "Competencia": 0.77, "CPC (€)": 0.58},
        {"País": "Francia", "Keyword": "turismo Canarias", "Volumen Mensual": 32100, "Competencia": 0.62, "CPC (€)": 0.35},
    ])


@st.cache_data(ttl=86400)  # Máximo 1 consulta real cada 24 h para no agotar saldo
def fetch_search_volume(headers):
    """Consulta volumen de búsqueda y devuelve DataFrame."""
    resultados = []
    for pais, location_code in LOCATION_CODES.items():
        payload = [{
            "location_code": location_code,
            "language_code": "es",
            "keywords": KEYWORDS_TURISMO
        }]
        response = requests.post(
            "https://api.dataforseo.com/v3/keywords_data/google_ads/search_volume/live",
            headers=headers,
            json=payload,
            timeout=60
        )
        data = response.json()
        if data.get("status_code") == 20000:
            for task in data.get("tasks", []):
                for item in task.get("result", []):
                    resultados.append({
                        "País": pais,
                        "Keyword": item.get("keyword"),
                        "Volumen Mensual": item.get("search_volume"),
                        "Competencia": item.get("competition"),
                        "CPC (€)": item.get("cpc")
                    })
        else:
            st.error(f"❌ {pais}: {data.get('status_message', 'Error desconocido')}")
    return pd.DataFrame(resultados)


# ── Tabs: Demand Index + Volumen búsqueda ──────────────────
tab_demand, tab_seo = st.tabs(["📈 Demand Index", "🔍 Volumen de búsqueda por destino"])

with tab_demand:
    df = pd.DataFrame({
        "value": [100, 105, 98, 112, 118, 125, 130, 128, 115, 108, 102, 110],
        "month": ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
    })
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Índice actual", f"{df['value'].iloc[-1]}", f"{df['value'].iloc[-1] - df['value'].iloc[0]:+.0f} vs Ene")
    with col2:
        st.metric("Máximo (año)", df["value"].max(), "pico")
    with col3:
        st.metric("Mínimo (año)", df["value"].min(), "mínimo")
    st.line_chart(df.set_index("month")["value"])

with tab_seo:
    # Por defecto mostramos datos de ejemplo; así la gente prueba sin gastar saldo
    if "df_seo" not in st.session_state:
        st.session_state["df_seo"] = get_demo_data()
        st.session_state["df_seo_live"] = False  # indica que son datos de ejemplo

    if headers:
        if st.button("📡 Actualizar con datos en vivo", type="primary"):
            with st.spinner("Consultando..."):
                df_seo = fetch_search_volume(headers)
            if df_seo.empty:
                st.warning("No se pudieron cargar datos. Prueba más tarde.")
            else:
                st.session_state["df_seo"] = df_seo
                st.session_state["df_seo_live"] = True
                st.success(f"✅ Datos actualizados: {len(df_seo)} filas")
        st.caption("La actualización en vivo se limita a una vez al día para mantener la calidad del servicio.")

    df_seo = st.session_state["df_seo"].copy()
    es_demo = not st.session_state.get("df_seo_live", False)
    if es_demo:
        st.info("📋 Estás viendo **datos de ejemplo**. Usa el botón de arriba para actualizar con datos en vivo (máx. 1 vez al día).")

    st.subheader("Resumen")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total filas", len(df_seo), "")
    with c2:
        st.metric("Volumen total (aprox.)", f"{df_seo['Volumen Mensual'].sum():,.0f}", "búsquedas/mes")
    with c3:
        top_kw = df_seo.loc[df_seo["Volumen Mensual"].idxmax(), "Keyword"]
        st.metric("Keyword más buscada", top_kw[:25] + ("…" if len(top_kw) > 25 else ""), "")
    with c4:
        st.metric("Países", df_seo["País"].nunique(), "")

    with st.expander("🔽 Filtrar por país y keyword"):
        paises_sel = st.multiselect("País", options=sorted(df_seo["País"].unique()), default=sorted(df_seo["País"].unique()), key="filtro_pais")
        keywords_sel = st.multiselect("Keyword", options=sorted(df_seo["Keyword"].unique()), default=sorted(df_seo["Keyword"].unique()), key="filtro_kw")
        df_seo = df_seo[df_seo["País"].isin(paises_sel) & df_seo["Keyword"].isin(keywords_sel)]

    top_n = st.slider("Top N en tabla", 10, 50, 20, key="top_n")
    st.subheader(f"Tabla por volumen (top {top_n})")
    top = df_seo.sort_values("Volumen Mensual", ascending=False).head(top_n)
    st.dataframe(top, use_container_width=True)

    st.subheader("Top keywords por volumen")
    chart_data = df_seo.groupby("Keyword")["Volumen Mensual"].sum().sort_values(ascending=False).head(15)
    st.bar_chart(chart_data)

    col_dl, col_space = st.columns([1, 3])
    with col_dl:
        csv = df_seo.to_csv(index=False).encode("utf-8-sig")
        st.download_button("📥 Descargar CSV", csv, "keywords_turismo_volumen.csv", "text/csv", key="dl_csv")

    with st.expander("Ver todos los datos"):
        st.dataframe(df_seo, use_container_width=True)

# Pie de página en toda la app
st.divider()
st.markdown(
    f'<p style="text-align: center; color: #666; font-size: 0.85rem;">{HECHO_POR}</p>',
    unsafe_allow_html=True
)
