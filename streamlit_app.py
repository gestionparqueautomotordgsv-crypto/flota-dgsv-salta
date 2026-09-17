import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title="DGSV - Flota", layout="wide", page_icon="🚔")

URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRO9kumGN6YMvBI_hGc-D9Lb8y29RqNubvkIN1gpgN6I8QKjZ2QBNQ3ItyVkLZeuw/pub?output=csv"

@st.cache_data(ttl=60)
def cargar():
    df = pd.read_csv(URL, dtype=str).fillna("")
    df.columns = [c.strip() for c in df.columns]
    # deja solo los 19 con MOVIL cargado
    col_m = next((c for c in df.columns if "MOVIL" in c.upper()), df.columns[0])
    df = df[df[col_m].astype(str).str.strip()!= ""]
    return df.head(19)

def buscar_col(df, txt):
    for c in df.columns:
        if txt.upper() in str(c).upper():
            return c
    return None

df = cargar()

col_dep = buscar_col(df, "DEPENDEN")
col_km = buscar_col(df, "KM ACTUAL")
col_prox = buscar_col(df, "PROXIMO SERVICE")
# todas las columnas que son fecha 9/1/2026 etc
cols_fecha = [c for c in df.columns if "/" in c and "2026" in c]
col_estado = cols_fecha[-1] if cols_fecha else None

# CALCULO KM
if col_km and col_prox:
    df[col_km] = pd.to_numeric(df[col_km].astype(str).str.replace(".", "", regex=False).str.replace(",", "", regex=False), errors='coerce').fillna(0)
    df[col_prox] = pd.to_numeric(df[col_prox].astype(str).str.replace(".", "", regex=False).str.replace(",", "", regex=False), errors='coerce').fillna(0)
    df["FALTAN KM"] = df[col_prox] - df[col_km]
    df["ALERTA SERVICE"] = df.apply(lambda r: "⚪" if r[col_prox]==0 else "🔴 SERVICE YA" if r[col_km]>=r[col_prox] else "🟡 CERCA" if r[col_km]>=r[col_prox]-1000 else "🟢 OK", axis=1)

# FILTRO DEPENDENCIA
st.title("🚔 Flota DGSV - 19 Móviles")
df_filtro = df.copy()
if col_dep:
    deps = ["TODOS"] + sorted([x for x in df[col_dep].unique() if x!=""])
    sel = st.selectbox("Filtrar por Dependencia", deps)
    if sel!="TODOS":
        df_filtro = df[df[col_dep]==sel]

# CUADRO Y GRAFICO VERDE AMARILLO ROJO (usa la ultima fecha)
if col_estado:
    def semaforo(v):
        v=str(v).upper()
        if "QRT" in v or "SERVI" in v: return "🔴 QRT"
        if "PRECAR" in v: return "🟡 PRECARIO"
        return "🟢 NORMAL"
    df_filtro["ESTADO HOY"] = df_filtro[col_estado].apply(semaforo)

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Total", len(df_filtro))
    c2.metric("🟢 NORMAL", df_filtro[df_filtro["ESTADO HOY"].str.contains("NORMAL")].shape[0])
    c3.metric("🟡 PRECARIO", df_filtro[df_filtro["ESTADO HOY"].str.contains("PRECARIO")].shape[0])
    c4.metric("🔴 QRT", df_filtro[df_filtro["ESTADO HOY"].str.contains("QRT")].shape[0])

    graf = df_filtro["ESTADO HOY"].value_counts().reset_index()
    graf.columns = ["Estado","Cantidad"]
    chart = alt.Chart(graf).mark_bar().encode(
        x='Estado:N', y='Cantidad:Q',
        color=alt.Color('Estado:N', scale=alt.Scale(domain=['🟢 NORMAL','🟡 PRECARIO','🔴 QRT'], range=['#22c55e','#eab308','#ef4444'])),
        tooltip=['Estado','Cantidad']
    )
    st.altair_chart(chart, use_container_width=True)

if "ALERTA SERVICE" in df_filtro.columns:
    cerca = df_filtro[df_filtro["ALERTA SERVICE"].str.contains("CERCA|YA")].shape[0]
    if cerca>0:
        st.warning(f"⚠️ {cerca} vehículos para service")

# ESTA ES LA TABLA COMO EN TU FOTO, CON TODAS LAS FECHAS
st.dataframe(df_filtro, use_container_width=True, height=650)
