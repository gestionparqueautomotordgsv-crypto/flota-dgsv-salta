import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="DGSV - Flota", layout="wide", page_icon="🚔")

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
conteo = df['ESTADO'].value_counts()

total = len(df)
normal = conteo.get("NORMAL",0)
precario = conteo.get("PRECARIO",0)
fuera = conteo.get("FUERA DE SERVICIO",0)

st.title(f"🚔 DGSV Salta - {col_hoy}")
st.caption(f"Actualizado: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

# --- 4 CAJAS CON COLORES ---
col1, col2, col3, col4 = st.columns(4)
col1.markdown(f"<div style='background-color:#2C3E50;padding:20px;border-radius:10px;text-align:center'><h2 style='color:white;margin:0'>Total</h2><h1 style='color:white;margin:0'>{total}</h1></div>", unsafe_allow_html=True)
col2.markdown(f"<div style='background-color:#2ECC71;padding:20px;border-radius:10px;text-align:center'><h2 style='color:black;margin:0'>NORMAL</h2><h1 style='color:black;margin:0'>{normal}</h1></div>", unsafe_allow_html=True)
col3.markdown(f"<div style='background-color:#F1C40F;padding:20px;border-radius:10px;text-align:center'><h2 style='color:black;margin:0'>PRECARIO</h2><h1 style='color:black;margin:0'>{precario}</h1></div>", unsafe_allow_html=True)
col4.markdown(f"<div style='background-color:#E74C3C;padding:20px;border-radius:10px;text-align:center'><h2 style='color:white;margin:0'>FUERA</h2><h1 style='color:white;margin:0'>{fuera}</h1></div>", unsafe_allow_html=True)

st.write("---")
st.subheader("Estado de Flota")
st.bar_chart(conteo)

st.subheader("Detalle de Móviles")
st.dataframe(df, use_container_width=True, height=600)

if st.button("🔄 Actualizar"):
    st.cache_data.clear()
    st.rerun()
