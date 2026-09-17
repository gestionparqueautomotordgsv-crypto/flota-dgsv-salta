import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title="DGSV - Flota", layout="wide", page_icon="🚔")

URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRO9kumGN6YMvBI_hGc-D9Lb8y29RqNubvkIN1gpgN6I8QKjZ2QBNQ3ItyVkLZeuw/pub?output=csv"

@st.cache_data(ttl=60)
def cargar():
    df = pd.read_csv(URL, dtype=str).fillna("")
    df.columns = [c.strip() for c in df.columns]
    # SOLO LOS 19 DEL DRIVE - saca filas vacías
    if "MOVIL" in df.columns or any("MOVIL" in c.upper() for c in df.columns):
        col = next((c for c in df.columns if "MOVIL" in c.upper()), df.columns[0])
        df = df[df[col].astype(str).str.strip()!= ""]
    return df.head(19)

def buscar_col(df, txt):
    for c in df.columns:
        if txt.upper() in str(c).upper():
            return c
    return None

df_orig = cargar()

col_movil = buscar_col(df_orig, "MOVIL")
col_dep = buscar_col(df_orig, "DEPENDEN")
col_km = buscar_col(df_orig, "KM ACTUAL")
col_prox = buscar_col(df_orig, "PROXIMO SERVICE")
cols_fecha = [c for c in df_orig.columns if "/" in c]
col_estado = cols_fecha[-1] if cols_fecha else None

# SEMAFORO NORMAL/PRECARIO/QRT
if col_estado:
    def semaforo(v):
        v=str(v).upper()
        if "QRT" in v: return "🔴 QRT"
        if "PRECAR" in v: return "🟡 PRECARIO"
        return "🟢 NORMAL"
    df_orig["ESTADO"] = df_orig[col_estado].apply(semaforo)

# ALERTA KM
if col_km and col_prox:
    df_orig[col_km] = pd.to_numeric(df_orig[col_km].astype(str).str.replace(".", "", regex=False).str.replace(",", "", regex=False), errors='coerce').fillna(0)
    df_orig[col_prox] = pd.to_numeric(df_orig[col_prox].astype(str).str.replace(".", "", regex=False).str.replace(",", "", regex=False), errors='coerce').fillna(0)
    df_orig["FALTAN KM"] = df_orig[col_prox] - df_orig[col_km]
    df_orig["ALERTA SERVICE"] = df_orig.apply(lambda r: "⚪ Sin dato" if r[col_prox]==0 else "🔴 SERVICE YA" if r[col_km]>=r[col_prox] else "🟡 CERCA SERVICE" if r[col_km]>=r[col_prox]-1000 else "🟢 OK", axis=1)

st.title("🚔 Flota DGSV - 19 Móviles")

df = df_orig.copy()
if col_dep:
    deps = ["TODOS"] + sorted([x for x in df_orig[col_dep].unique() if x!=""])
    sel = st.selectbox("Filtrar por Dependencia", deps)
    if sel!="TODOS":
        df = df[df[col_dep]==sel]

# CUADRO DE COLORES
if "ESTADO" in df.columns:
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Total", len(df))
    c2.metric("🟢 NORMAL", df[df["ESTADO"].str.contains("NORMAL")].shape[0])
    c3.metric("🟡 PRECARIO", df[df["ESTADO"].str.contains("PRECARIO")].shape[0])
    c4.metric("🔴 QRT", df[df["ESTADO"].str.contains("QRT")].shape[0])

    graf = df["ESTADO"].value_counts().reset_index()
    graf.columns = ["Estado","Cantidad"]
    chart = alt.Chart(graf).mark_bar().encode(
        x='Estado:N', y='Cantidad:Q',
        color=alt.Color('Estado:N', scale=alt.Scale(domain=['🟢 NORMAL','🟡 PRECARIO','🔴 QRT'], range=['#22c55e','#eab308','#ef4444'])),
        tooltip=['Estado','Cantidad']
    )
    st.altair_chart(chart, use_container_width=True)

# ALERTA SERVICE
if "ALERTA SERVICE" in df.columns:
    cerca = df[df["ALERTA SERVICE"].str.contains("CERCA|YA")].shape[0]
    if cerca>0:
        st.error(f"⚠️ {cerca} vehículos cerca de service (Faltan menos de 1000 KM)")
    st.dataframe(df[[col_movil, col_dep, col_km, col_prox, "FALTAN KM", "ALERTA SERVICE", "ESTADO"] if col_movil else df.columns], use_container_width=True)
else:
    st.dataframe(df, use_container_width=True)
