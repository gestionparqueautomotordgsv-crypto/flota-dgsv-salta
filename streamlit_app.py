import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title="DGSV - Flota", layout="wide", page_icon="🚔")

URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRO9kumGN6YMvBI_hGc-D9Lb8y29RqNubvkIN1gpgN6I8QKjZ2QBNQ3ItyVkLZeuw/pub?gid=1702506345&single=true&output=csv"

@st.cache_data(ttl=60)
def cargar():
    df = pd.read_csv(URL, dtype=str).fillna("")
    df.columns = [c.strip().upper() for c in df.columns]
    return df

def buscar_col(df, txt):
    for c in df.columns:
        if txt in c:
            return c
    return None

df_all = cargar()
col_tipo = buscar_col(df_all, "RUEDAS")
col_movil = buscar_col(df_all, "MOVIL")
col_dep = buscar_col(df_all, "DEPENDEN")
col_km = buscar_col(df_all, "KM ACTUAL")
col_prox = buscar_col(df_all, "PROXIMO")
cols_fecha = [c for c in df_all.columns if "/" in c]
col_estado = cols_fecha[-1] if cols_fecha else None

df_autos = df_all[df_all[col_tipo].str.contains("4", na=False)] if col_tipo else df_all.head(19)
df_motos = df_all[df_all[col_tipo].str.contains("2", na=False)] if col_tipo else df_all.tail(85)

def panel(df, nombre):
    if df.empty:
        st.warning(f"No hay {nombre}")
        return
    if col_km and col_prox:
        df[col_km] = pd.to_numeric(df[col_km].astype(str).str.replace(".","",regex=False).str.replace(",","",regex=False), errors='coerce').fillna(0)
        df[col_prox] = pd.to_numeric(df[col_prox].astype(str).str.replace(".","",regex=False).str.replace(",","",regex=False), errors='coerce').fillna(0)
        df["FALTAN KM"] = df[col_prox] - df[col_km]
        df["ALERTA"] = df.apply(lambda r: "🔴 SERVICE YA" if r[col_prox]!=0 and r[col_km]>=r[col_prox] else "🟡 CERCA" if r[col_prox]!=0 and r[col_km]>=r[col_prox]-1000 else "🟢 OK", axis=1)

    df_f = df.copy()
    if col_dep and col_dep in df.columns:
        deps = ["TODOS"] + sorted([x for x in df[col_dep].unique() if x!=""])
        sel = st.selectbox(f"Filtro Dependencia {nombre}", deps, key=nombre)
        if sel!="TODOS":
            df_f = df[df[col_dep]==sel]

    if col_estado and col_estado in df_f.columns:
        def sem(v):
            v=str(v).upper()
            if "QRT" in v or "SERVI" in v: return "🔴 QRT"
            if "PRECAR" in v: return "🟡 PRECARIO"
            return "🟢 NORMAL"
        df_f["ESTADO HOY"] = df_f[col_estado].apply(sem)
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Total", len(df_f))
        c2.metric("🟢 NORMAL", len(df_f[df_f["ESTADO HOY"].str.contains("NORMAL")]))
        c3.metric("🟡 PRECARIO", len(df_f[df_f["ESTADO HOY"].str.contains("PRECARIO")]))
        c4.metric("🔴 QRT", len(df_f[df_f["ESTADO HOY"].str.contains("QRT")]))
        graf = df_f["ESTADO HOY"].value_counts().reset_index()
        graf.columns=["Estado","Cantidad"]
        chart = alt.Chart(graf).mark_bar().encode(
            x=alt.X('Estado:N', sort=['🟢 NORMAL','🟡 PRECARIO','🔴 QRT']),
            y='Cantidad:Q',
            color=alt.Color('Estado:N', scale=alt.Scale(domain=['🟢 NORMAL','🟡 PRECARIO','🔴 QRT'], range=['#22c55e','#eab308','#ef4444']), legend=None)
        )
        st.altair_chart(chart, use_container_width=True)

    if "ALERTA" in df_f.columns:
        df_a = df_f[df_f["ALERTA"].str.contains("CERCA|YA")]
        if len(df_a)>0:
            st.error(f"⚠️ {len(df_a)} {nombre} PARA SERVICE: {', '.join(df_a[col_movil].astype(str).tolist())}")
            st.dataframe(df_a[[col_movil, col_dep, col_km, col_prox, "FALTAN KM", "ALERTA"]].sort_values("FALTAN KM"), use_container_width=True, hide_index=True)

    st.divider()
    st.caption(f"Todas las fechas visibles - {nombre} - Último: {col_estado}")
    st.dataframe(df_f, use_container_width=True, height=650)

st.title("🚔 DGSV - Flota")
t1, t2 = st.tabs([f"🚔 MOVILES 4 RUEDAS ({len(df_autos)})", f"🏍️ MOTOS 2 RUEDAS ({len(df_motos)})"])
with t1:
    panel(df_autos, "MOVILES 19")
with t2:
    panel(df_motos, "MOTOS 85")

if st.button("🔄 Actualizar"):
    st.cache_data.clear()
    st.rerun()
