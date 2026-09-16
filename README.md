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

st.title(f"🚔 DGSV Salta - {col_hoy}")
st.caption(f"Actualizado: {datetime.now().strftime('%d/%m %H:%M')} | Total: {len(df)} móviles")

c1,c2,c3,c4 = st.columns(4)
c1.metric("Total", len(df))
c2.metric("✅ NORMAL", len(df[df['ESTADO']=="NORMAL"]))
c3.metric("⚠️ PRECARIO", len(df[df['ESTADO']=="PRECARIO"]))
c4.metric("❌ FUERA", len(df[df['ESTADO']=="FUERA DE SERVICIO"]))

st.bar_chart(df['ESTADO'].value_counts())

filtro = st.multiselect("Filtrar por estado:", ["NORMAL","PRECARIO","FUERA DE SERVICIO"])
df_show = df[df['ESTADO'].isin(filtro)] if filtro else df
st.dataframe(df_show, use_container_width=True, height=600)

if st.button("🔄 Actualizar"): st.cache_data.clear(); st.rerun()
