import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime

st.set_page_config(page_title="DGSV - Flota", layout="wide", page_icon="🚔")

URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRO9kumGN6YMvBI_hGc-D9Lb8y29RqNubvkIN1gpgN6I8QKjZ2QBNQ3ItyVkLZeuw/pub?output=csv"

@st.cache_data(ttl=60)
def cargar():
    df = pd.read_csv(URL, dtype=str).fillna("")
    df.columns = [c.strip() for c in df.columns]
    return df

def buscar_col(df, texto):
    texto = texto.upper()
    for col in df.columns:
        if texto in str(col).upper():
            return col
    return None

df_orig = cargar()

# Columnas fijas nuevas (no importa donde esten)
col_km = buscar_col(df_orig, "KM ACTUAL")
col_prox = buscar_col(df_orig, "PROXIMO SERVICE")
col_movil = buscar_col(df_orig, "MOVIL")
col_dep = buscar_col(df_orig, "DEPENDEN")
col_tipo = buscar_col(df_orig, "4 RUEDAS")

# Calcular alerta KM
if col_km and col_prox:
    df_orig[col_km] = pd.to_numeric(df_orig[col_km].str.replace(".","").str.replace(",",""), errors='coerce').fillna(0)
    df_orig[col_prox] = pd.to_numeric(df_orig[col_prox].str.replace(".","").str.replace(",",""), errors='coerce').fillna(0)

    def alerta_km(row):
        km = row[col_km]
        prox = row[col_prox]
        if prox == 0:
            return "⚪ Sin dato"
        if km >= prox:
            return "🔴 SERVICE YA"
        if km >= prox - 1000:
            return "🟡 CERCA SERVICE"
        return "🟢 OK"

    df_orig["ALERTA SERVICE"] = df_orig.apply(alerta_km, axis=1)
    df_orig["FALTAN KM"] = df_orig[col_prox] - df_orig[col_km]

st.title("🚔 Flota DGSV Salta")

# Filtros
if col_dep:
    deps = ["TODOS"] + sorted(df_orig[col_dep].unique().tolist())
    sel = st.selectbox("Dependencia", deps)
    if sel!= "TODOS":
        df = df_orig[df_orig[col_dep]==sel]
    else:
        df = df_orig
else:
    df = df_orig

# Metricas de KM
if col_km and col_prox:
    cerca = df[df["ALERTA SERVICE"].str.contains("CERCA|SERVICE YA")].shape[0]
    if cerca>0:
        st.error(f"⚠️ {cerca} vehículos cerca de service")
    else:
        st.success("✅ Flota OK en KM")

# Mostrar tabla con las columnas que te importan
cols_mostrar = []
for c in [col_dep, col_tipo, col_km, col_prox, "FALTAN KM", "ALERTA SERVICE", col_movil]:
    if c and c in df.columns:
        cols_mostrar.append(c)

# agregar ultimas columnas de estado (fechas)
cols_mostrar = cols_mostrar + [c for c in df.columns if "/" in c][-3:]

st.dataframe(df[cols_mostrar], use_container_width=True, height=600)
