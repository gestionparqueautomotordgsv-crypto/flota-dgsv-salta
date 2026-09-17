import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title="DGSV - Flota 19", layout="wide", page_icon="🚔")

URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRO9kumGN6YMvBI_hGc-D9Lb8y29RqNubvkIN1gpgN6I8QKjZ2QBNQ3ItyVkLZeuw/pub?output=csv"

@st.cache_data(ttl=60)
def cargar():
    df = pd.read_csv(URL, dtype=str).fillna("")
    df.columns = [c.strip() for c in df.columns]
    col_m = next((c for c in df.columns if "MOVIL" in c.upper()), df.columns[0])
    df = df[df[col_m].astype(str).str.strip()!= ""]
    return df.head(19)

def buscar_col(df, txt):
    for c in df.columns:
        if txt.upper() in c.upper():
            return c
    return None

df = cargar()

col_movil = buscar_col(df, "MOVIL")
col_dep = buscar_col(df, "DEPENDEN")
col_km = buscar_col(df, "KM ACTUAL")
col_prox = buscar_col(df, "PROXIMO SERVICE")
cols_fecha = [c for c in df.columns if "/" in c and "2026" in c]
col_estado = cols_fecha[-1] if cols_fecha else None

# --- CALCULO KM ---
if col_km and col_prox:
    df[col_km] = pd.to_numeric(df[col_km].astype(str).str.replace(".", "", regex=False).str.replace(",", "", regex=False), errors='coerce').fillna(0)
    df[col_prox] = pd.to_numeric(df[col_prox].astype(str).str.replace(".", "", regex=False).str.replace(",", "", regex=False), errors='coerce').fillna(0)
    df["FALTAN KM"] = df[col_prox] - df[col_km]
    df["ALERTA SERVICE"] = df.apply(lambda r: "⚪" if r[col_prox]==0 else "🔴 SERVICE YA" if r[col_km]>=r[col_prox] else "🟡 CERCA SERVICE" if r[col_km]>=r[col_prox]-1000 else "🟢 OK", axis=1)

# --- UI ---
st.title("🚔 Flota DGSV - 19 Móviles")
df_filtro = df.copy()

if col_dep:
    deps = ["TODOS"] + sorted([x for x in df[col_dep].unique() if x!=""])
    sel = st.selectbox("Filtrar por Dependencia", deps)
    if sel!= "TODOS":
        df_filtro = df[df[col_dep]==sel]

# --- CUADRO Y GRAFICO 1 al 5 ---
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
        x=alt.X('Estado:N', sort=['🟢 NORMAL','🟡 PRECARIO','🔴 QRT']),
        y='Cantidad:Q',
        color=alt.Color('Estado:N', scale=alt.Scale(domain=['🟢 NORMAL','🟡 PRECARIO','🔴 QRT'], range=['#22c55e','#eab308','#ef4444']), legend=None),
        tooltip=['Estado','Cantidad']
    )
    st.altair_chart(chart, use_container_width=True)

# --- ALERTA KM CON NUMERO DE MOVIL ---
if "ALERTA SERVICE" in df_filtro.columns and col_movil:
    df_service = df_filtro[df_filtro["ALERTA SERVICE"].str.contains("CERCA|YA")]

    if len(df_service) > 0:
        st.error(f"⚠️ ATENCIÓN: {len(df_service)} vehículo/s para SERVICE")
        cols_mostrar = [col_movil]
        if col_dep: cols_mostrar.append(col_dep)
        cols_mostrar += [col_km, col_prox, "FALTAN KM", "ALERTA SERVICE"]
        st.dataframe(df_service[cols_mostrar].sort_values("FALTAN KM"), use_container_width=True, hide_index=True)
    else:
        st.success("✅ Todos los móviles OK de KM")

# --- TABLA COMPLETA CON TODAS LAS FECHAS ---
st.divider()
st.subheader(f"Detalle completo - Último parte: {col_estado}" if col_estado else "Detalle completo")
st.dataframe(df_filtro, use_container_width=True, height=650)

if st.button("🔄 Actualizar datos"):
    st.cache_data.clear()
    st.rerun()
