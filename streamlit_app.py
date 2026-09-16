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

# Contar
conteo = df['ESTADO'].value_counts()
total = len(df)
normal = conteo.get("NORMAL",0)
precario = conteo.get("PRECARIO",0)
fuera = conteo.get("FUERA DE SERVICIO",0)

st.title(f"🚔 DGSV Salta - {col_hoy}")
st.caption(f"Actualizado: {datetime.now().strftime('%d/%m/%Y %H:%M')} | Total: {total} móviles")

# --- METRICAS CON COLORES ---
c1,c2,c3,c4 = st.columns(4)
with c1:
    st.markdown(f"<div style='background:#2E4053;padding:15px;border-radius:10px;text-align:center;color:white'><h3>Total</h3><h1>{total}</h1></div>", unsafe_allow_html=True)
with c2:
    st.markdown(f"<div style='background:#2ECC71;padding:15px;border-radius:10px;text-align:center;color:black'><h3>NORMAL</h3><h1>{normal}</h1></div>", unsafe_allow_html=True)
with c3:
    st.markdown(f"<div style='background:#F1C40F;padding:15px;border-radius:10px;text-align:center;color:black'><h3>PRECARIO</h3><h1>{precario}</h1></div>", unsafe_allow_html=True)
with c4:
    st.markdown(f"<div style='background:#E74C3C;padding:15px;border-radius:10px;text-align:center;color:white'><h3>FUERA</h3><h1>{fuera}</h1></div>", unsafe_allow_html=True)

st.markdown("---")

# --- GRAFICO SIMPLE (sin error) ---
st.markdown("### Estado de Flota")
st.bar_chart(conteo)

# --- TABLA CON COLORES ---
def color_estado(val):
    if val == "NORMAL": return 'background-color: #2ECC71; color: black; font-weight: bold'
    if val == "PRECARIO": return 'background-color: #F1C40F; color: black; font-weight: bold'
    if val == "FUERA DE SERVICIO": return 'background-color: #E74C3C; color: white; font-weight: bold'
    return ''

st.markdown("### Detalle de Móviles")
styled = df.style.applymap(color_estado, subset=['ESTADO'])
st.dataframe(styled, use_container_width=True, height=600)

if st.button("🔄 Actualizar"):
    st.cache_data.clear()
    st.rerun()
