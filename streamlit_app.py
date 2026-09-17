import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title="DGSV - Flota", layout="wide", page_icon="🚔")

URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRO9kumGN6YMvBI_hGc-D9Lb8y29RqNubvkIN1gpgN6I8QKjZ2QBNQ3ItyVkLZeuw/pub?output=csv"

@st.cache_data(ttl=60)
def cargar():
    try:
        df = pd.read_csv(URL, dtype=str).fillna("")
        df.columns = [c.strip() for c in df.columns]
        return df
    except Exception as e:
        st.error("⚠️ Error leyendo el Sheets")
        st.code(str(e))
        st.stop()

def buscar_col(df, texto):
    for c in df.columns:
        if texto.upper() in str(c).upper():
            return c
    return None

df_orig = cargar()
col_km = buscar_col(df_orig, "KM ACTUAL")
col_prox = buscar_col(df_orig, "PROXIMO SERVICE")
col_movil = buscar_col(df_orig, "MOVIL")
col_dep = buscar_col(df_orig, "DEPENDEN")

if col_km and col_prox:
    df_orig[col_km] = pd.to_numeric(df_orig[col_km].astype(str).str.replace(".", "", regex=False).str.replace(",", "", regex=False), errors='coerce').fillna(0)
    df_orig[col_prox] = pd.to_numeric(df_orig[col_prox].astype(str).str.replace(".", "", regex=False).str.replace(",", "", regex=False), errors='coerce').fillna(0)
    df_orig["FALTAN KM"] = df_orig[col_prox] - df_orig[col_km]
    df_orig["ALERTA SERVICE"] = df_orig.apply(lambda r: "⚪ Sin dato" if r[col_prox]==0 else "🔴 SERVICE YA" if r[col_km]>=r[col_prox] else "🟡 CERCA SERVICE" if r[col_km]>=r[col_prox]-1000 else "🟢 OK", axis=1)

st.title("🚔 Flota DGSV Salta")
df = df_orig.copy()
if col_dep:
    deps = ["TODOS"] + sorted([x for x in df_orig[col_dep].unique() if x!=""])
    sel = st.selectbox("Filtrar por Dependencia", deps)
    if sel!="TODOS":
        df = df_orig[df_orig[col_dep]==sel]

if "ALERTA SERVICE" in df.columns:
    cerca = df[df["ALERTA SERVICE"].str.contains("CERCA|YA", na=False)].shape[0]
    if cerca>0:
        st.error(f"⚠️ {cerca} vehículos cerca de service")
    else:
        st.success("✅ Flota OK en KM")

    st.subheader("📊 Estado por KM")
    graf = df["ALERTA SERVICE"].value_counts().reset_index()
    graf.columns = ["Estado", "Cantidad"]
    chart = alt.Chart(graf).mark_bar().encode(x='Estado:N', y='Cantidad:Q', color='Estado:N', tooltip=['Estado','Cantidad'])
    st.altair_chart(chart, use_container_width=True)

    if "FALTAN KM" in df.columns and col_movil:
        st.subheader("🚨 Top 5 más cerca del service")
        top = df[pd.to_numeric(df["FALTAN KM"], errors='coerce')>0].sort_values("FALTAN KM").head(5)
        if not top.empty:
            chart2 = alt.Chart(top).mark_bar().encode(x='FALTAN KM:Q', y=alt.Y(f'{col_movil}:N', sort='-x'), color='ALERTA SERVICE:N', tooltip=[col_movil, 'FALTAN KM'])
            st.altair_chart(chart2, use_container_width=True)

st.dataframe(df, use_container_width=True, height=600)
