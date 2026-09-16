import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="DGSV - Flota", layout="wide", page_icon="🚔")

# --- COLORES ---
COLORS = {
    "NORMAL": "#2ECC71",           # Verde
    "PRECARIO": "#F1C40F",         # Amarillo
    "FUERA DE SERVICIO": "#E74C3C", # Rojo
    "SIN DATO": "#95A5A6"
}

URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRO9kumGN6YMvBI_hGc-D9Lb8y29RqNubvkIN1gpgN6I8QKjZ2QBNQ3ItyVkLZeuw/pub?gid=1702506345&single=true&output=csv"

@st.cache_data(ttl=60)
def cargar():
    df = pd.read_csv(URL, dtype=str).fillna("")
    df.columns = [c.strip() for c in df.columns]
    return df

df = cargar()
col_hoy = df.columns[-1]

def normalizar(v):
    v = str(v).upper().strip()
    if "NORMAL" in v: return "NORMAL"
    if "PRECA" in v: return "PRECARIO"
    if "QRT" in v or "FUERA" in v or "SERVI" in v: return "FUERA DE SERVICIO"
    return v if v else "SIN DATO"

df['ESTADO'] = df[col_hoy].apply(normalizar)

# --- CSS PARA METRICAS CON COLOR ---
st.markdown(f"""
<style>
div[data-testid="stMetric"] {{
    background-color: #1E1E1E;
    border-left: 8px solid {COLORS['NORMAL']};
    padding: 10px;
    border-radius: 10px;
}}
</style>
""", unsafe_allow_html=True)

st.title(f"🚔 DGSV Salta - {col_hoy}")
st.caption(f"Actualizado: {datetime.now().strftime('%d/%m/%Y %H:%M')} | Total: {len(df)} móviles")

conteo = df['ESTADO'].value_counts()

c1,c2,c3,c4 = st.columns(4)
c1.metric("🚔 Total Flota", len(df))
c2.metric("✅ NORMAL", conteo.get("NORMAL",0))
c3.metric("⚠️ PRECARIO", conteo.get("PRECARIO",0))
c4.metric("❌ FUERA SERV.", conteo.get("FUERA DE SERVICIO",0))

# --- GRAFICO DE BARRAS CON COLORES ---
st.markdown("### Estado de Flota")
chart_df = pd.DataFrame({
    "ESTADO": conteo.index,
    "CANTIDAD": conteo.values
})
# Asignar colores
chart_df["COLOR"] = chart_df["ESTADO"].map(COLORS)

st.bar_chart(chart_df.set_index("ESTADO")["CANTIDAD"], color=COLORS.values())

# --- TABLA CON COLORES ---
def color_fila(val):
    color = COLORS.get(val, "#FFFFFF")
    return f'background-color: {color}; color: black; font-weight: bold'

st.markdown("### Detalle de Móviles")
# Aplicar color a la columna ESTADO
styled = df.style.applymap(lambda v: f'background-color: {COLORS.get(v, "#FFF")}; color: black; font-weight: bold', subset=['ESTADO'])
st.dataframe(styled, use_container_width=True, height=600)

if st.button("🔄 Actualizar datos"):
    st.cache_data.clear()
    st.rerun()
