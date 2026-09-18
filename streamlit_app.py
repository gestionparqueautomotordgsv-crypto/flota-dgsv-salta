import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title="DGSV - Flota", layout="wide", page_icon="🚔")

URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRO9kumGN6YMvBI_hGc-D9Lb8y29RqNubvkIN1gpgN6I8QKjZ2QBNQ3ItyVkLZeuw/pub?gid=1702506345&single=true&output=csv"

@st.cache_data(ttl=60)
def cargar():
    df=pd.read_csv(URL, dtype=str).fillna("")
    df.columns=[c.strip().upper() for c in df.columns]
    return df

def buscar_col(df, txt):
    for c in df.columns:
        if txt in c: return c
    return None

df_all=cargar()
col_tipo=buscar_col(df_all,"RUEDAS")
col_movil=buscar_col(df_all,"MOVIL")
col_dep=buscar_col(df_all,"DEPENDEN")
col_dom=buscar_col(df_all,"DOMINIO")
col_km_act=buscar_col(df_all,"KM ACTUAL")
col_prox=buscar_col(df_all,"PROXIMO")
cols_fecha=[c for c in df_all.columns if "/" in c]
col_estado=cols_fecha[-1] if cols_fecha else None

# FIX PARA 0,1,2 VACIOS - Ahora cuenta bien 19
if col_dep:
    df_all[col_dep] = df_all[col_dep].astype(str).str.strip().replace(["","NAN","NONE","N/A"], "DGSV")
    df_all[col_dep] = df_all[col_dep].replace(r'^\s*$', 'DGSV', regex=True)

df_2r=df_all[df_all[col_tipo].str.contains("2", na=False)] if col_tipo else df_all
df_4r=df_all[df_all[col_tipo].str.contains("4", na=False)] if col_tipo else df_all

def panel(df, nombre):
    c1,c2=st.columns(2)
    with c1:
        f_movil=st.text_input("MOVIL", key=f"m_{nombre}").upper()
    with c2:
        f_dep=st.text_input("DEPENDENCIA", key=f"d_{nombre}").upper()

    df_f=df.copy()
    if f_movil and col_movil:
        df_f=df_f[df_f[col_movil].astype(str).str.upper().str.contains(f_movil, na=False)]
    if f_dep and col_dep:
        df_f=df_f[df_f[col_dep].astype(str).str.upper().str.contains(f_dep, na=False)]

    def estado_final(row):
        v=str(row[col_estado]).upper() if col_estado else ""
        if "QRT" in v: return "QRT"
        if "SERVI" in v: return "SERVI"
        if col_km_act and col_prox:
            try:
                km=int(float(str(row[col_km_act]).replace(".","").replace(",","").strip() or 0))
                prox=int(float(str(row[col_prox]).replace(".","").replace(",","").strip() or 0))
                if prox>0 and km>0:
                    if km>=prox: return "SERVI"
                    if km>=prox-1000: return "ALERTA"
            except: pass
        if "PRECAR" in v: return "PRECARIO"
        return "NORMAL"

    df_f["ESTADO"]=df_f.apply(estado_final, axis=1)

    qrt=len(df_f[df_f["ESTADO"]=="QRT"])
    servi=len(df_f[df_f["ESTADO"]=="SERVI"])
    normal=len(df_f[df_f["ESTADO"]=="NORMAL"])
    precario=len(df_f[df_f["ESTADO"]=="PRECARIO"])
    alerta_df=df_f[df_f["ESTADO"]=="ALERTA"]

    ca,cb,cc,cd,ce=st.columns(5)
    ca.metric("🔴 QRT", qrt)
    cb.metric("🔵 SERVI", servi)
    cc.metric("🟢 NORMAL", normal)
    cd.metric("🟡 PRECARIO", precario)
    ce.metric("Total", len(df_f))

    if len(alerta_df)>0:
        st.warning(f"🟡 ALERTA: {len(alerta_df)} próximos al servi")
        for _, r in alerta_df.iterrows():
            st.write(f"⚠️ {r[col_movil]} - {r[col_km_act]}km / Toca {r[col_prox]}km")

    df_graf=df_f.copy()
    df_graf["GRAF"]=df_graf["ESTADO"].replace({"ALERTA":"NORMAL"})
    graf=df_graf["GRAF"].value_counts().reset_index()
    graf.columns=["Estado","Cantidad"]
    chart=alt.Chart(graf).mark_bar().encode(
        x=alt.X('Estado:N', sort=["NORMAL","QRT","PRECARIO","SERVI"]),
        y='Cantidad:Q',
        color=alt.Color('Estado:N', scale=alt.Scale(domain=["NORMAL","QRT","PRECARIO","SERVI"], range=["#22c55e","#ef4444","#eab308","#3b82f6"]), legend=None)
    )
    st.altair_chart(chart, use_container_width=True)
    st.dataframe(df_f, use_container_width=True, height=600)

st.title("🚔 Flota DGSV - En prueba")
t1,t2=st.tabs([f"🏍️ DOS RUEDAS ({len(df_2r)})", f"🚔 CUATRO RUEDAS ({len(df_4r)})"])
with t1: panel(df_2r, "2R")
with t2: panel(df_4r, "4R")
