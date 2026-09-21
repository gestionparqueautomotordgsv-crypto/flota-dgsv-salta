import streamlit as st
import pandas as pd
import altair as alt
import re

st.set_page_config(page_title="Flota DGSV", layout="wide", page_icon="🚔")
URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRO9kumGN6YMvBI_hGc-D9Lb8y29RqNubvkIN1gpgN6I8QKjZ2QBNQ3ItyVkLZeuw/pub?gid=1702506345&single=true&output=csv"

@st.cache_data(ttl=10)
def cargar():
    df=pd.read_csv(URL, dtype=str).fillna("")
    df.columns=[c.strip().upper() for c in df.columns]
    return df

def buscar_col(df, palabras):
    for c in df.columns:
        for p in palabras:
            if p in c:
                return c
    return None

def num(s):
    try:
        s=str(s).replace(".","").replace(",","")
        s=re.sub(r'[^0-9]', '', s)
        return int(s) if s else 0
    except:
        return 0

st.title("🚔 Flota DGSV - En prueba")
if st.button("🔄 Actualizar"):
    st.cache_data.clear()
    st.rerun()

df_all=cargar()
col_tipo=buscar_col(df_all,["RUEDAS"])
col_movil=buscar_col(df_all,["MOVIL"])
col_km_act=buscar_col(df_all,["KM ACTUAL","KILOMETRAJE"])
col_prox=buscar_col(df_all,["PROXIMO"])
col_dep=buscar_col(df_all,["DEPENDENCIA","DESTINO","UNIDAD"])
cols_fecha=[c for c in df_all.columns if "/" in c]

df_2r=df_all[df_all[col_tipo].str.contains("2",na=False)] if col_tipo else df_all
df_4r=df_all[df_all[col_tipo].str.contains("4",na=False)] if col_tipo else df_all

def calcular_estado(row):
    v_diario="NORMAL"
    for c in reversed(cols_fecha):
        v=str(row[c]).strip()
        if v!="" and v.upper()!="NAN":
            v_diario=v.upper()
            break
    if "QRT" in v_diario: return "QRT"
    if "SERVI" in v_diario: return "SERVI"
    if "PRECAR" in v_diario: return "PRECARIO"

    if col_km_act and col_prox:
        km=num(row[col_km_act])
        prox=num(row[col_prox])
        if prox>0 and km>0 and km>=prox-1000:
            return "ALERTA"
    return "NORMAL"

# AVISO GLOBAL DE 1000KM
df_all["ESTADO_TEMP"]=df_all.apply(calcular_estado, axis=1)
alertas_globales=df_all[df_all["ESTADO_TEMP"]=="ALERTA"]
if len(alertas_globales)>0:
    st.toast(f"🟡 {len(alertas_globales)} móviles a 1000km del servi", icon="⚠️")
    lista = ", ".join([f"{r[col_movil]} ({num(r[col_km_act])}/{num(r[col_prox])}km)" for _, r in alertas_globales.iterrows() if col_movil])
    st.markdown(f"<div style='background:#dc3545;color:white;padding:12px;border-radius:8px;text-align:center;font-size:18px'>🚨 <b>ATENCIÓN: {len(alertas_globales)} MÓVILES A 1000KM DEL SERVI -> {lista}</b></div>", unsafe_allow_html=True)

def panel(df_base, tipo_rueda):
    df_base_calc = df_base.copy()
    df_base_calc["ESTADO"] = df_base_calc.apply(calcular_estado, axis=1)
    alerta_total_df = df_base_calc[df_base_calc["ESTADO"]=="ALERTA"]

    c1,c2 = st.columns(2)
    with c1:
        busca_movil = st.text_input(f"🔍 Buscar MOVIL en {tipo_rueda} (ej: 1318 / 2378)", key=f"mov_{tipo_rueda}")
    with c2:
        deps = ["TODAS"] + sorted([x for x in df_base[col_dep].unique() if str(x).strip()!=""]) if col_dep and col_dep in df_base else ["TODAS"]
        busca_dep = st.selectbox(f"🏢 DEPENDENCIA en {tipo_rueda}", deps, key=f"dep_{tipo_rueda}")

    df_f = df_base.copy()
    if busca_movil and col_movil:
        df_f = df_f[df_f[col_movil].astype(str).str.contains(busca_movil, na=False)]
    if busca_dep!="TODAS" and col_dep and col_dep in df_f:
        df_f = df_f[df_f[col_dep]==busca_dep]

    df_f["ESTADO"]=df_f.apply(calcular_estado, axis=1)
    qrt=len(df_f[df_f["ESTADO"]=="QRT"])
    servi=len(df_f[df_f["ESTADO"]=="SERVI"])
    precario=len(df_f[df_f["ESTADO"]=="PRECARIO"])
    normal=len(df_f[df_f["ESTADO"]=="NORMAL"]) + len(df_f[df_f["ESTADO"]=="ALERTA"])

    ca,cb,cc,cd,ce=st.columns(5)
    ca.markdown(f"<div style='background:#ff6b6b;padding:15px;border-radius:12px;text-align:center'><b>🔴 QRT</b><br><span style='font-size:30px'>{qrt}</span></div>",unsafe_allow_html=True)
    cb.markdown(f"<div style='background:#4dabf7;padding:15px;border-radius:12px;text-align:center'><b>🔵 SERVI</b><br><span style='font-size:30px'>{servi}</span></div>",unsafe_allow_html=True)
    cc.markdown(f"<div style='background:#51cf66;padding:15px;border-radius:12px;text-align:center'><b>🟢 NORMAL</b><br><span style='font-size:30px'>{normal}</span></div>",unsafe_allow_html=True)
    cd.markdown(f"<div style='background:#fcc419;padding:15px;border-radius:12px;text-align:center'><b>🟡 PRECARIO</b><br><span style='font-size:30px'>{precario}</span></div>",unsafe_allow_html=True)
    ce.markdown(f"<div style='background:#1e293b;color:white;padding:15px;border-radius:12px;text-align:center'><b>Total {tipo_rueda}</b><br><span style='font-size:30px'>{len(df_f)}</span></div>",unsafe_allow_html=True)

    if len(alerta_total_df)>0:
        st.markdown(f"<div style='background:#fff3cd;border:2px solid #ffc107;padding:12px;border-radius:8px;margin-top:15px;color:#664d03;font-size:17px'>🟡 <b>ALERTA KM {tipo_rueda}: {len(alerta_total_df)} próximos al servi - FALTAN 1000KM O MENOS - DENTRO DE NORMAL</b></div>", unsafe_allow_html=True)
        for _, r in alerta_total_df.iterrows():
            movil=str(r[col_movil]) if col_movil else ""
            km=num(r[col_km_act])
            prox=num(r[col_prox])
            falta=prox-km
            dep=str(r[col_dep]) if col_dep else ""
            st.markdown(f"⚠️ **{movil} - {km}km / Toca {prox}km (FALTAN {falta}km) - {dep} - {tipo_rueda}**")
    else:
        st.success(f"✅ Sin alertas de KM en {tipo_rueda}")

    st.divider()
    graf=df_f["ESTADO"].replace({"ALERTA":"NORMAL"}).value_counts().reset_index()
    graf.columns=["Estado","Cantidad"]
    if len(graf)>0:
        chart=alt.Chart(graf).mark_bar(cornerRadiusTopLeft=8, cornerRadiusTopRight=8).encode(
            x=alt.X('Estado:N', sort=["NORMAL","QRT","PRECARIO","SERVI"]),
            y='Cantidad:Q',
            color=alt.Color('Estado:N', scale=alt.Scale(domain=["NORMAL","QRT","PRECARIO","SERVI"], range=["#22c55e","#ef4444","#eab308","#3b82f6"]), legend=None)
        ).properties(height=300)
        st.altair_chart(chart, use_container_width=True)
    st.dataframe(df_f, use_container_width=True)

t1,t2=st.tabs([f"🏍️ DOS RUEDAS ({len(df_2r)})", f"🚔 CUATRO RUEDAS ({len(df_4r)})"])
with t1:
    panel(df_2r, "2 RUEDAS")
with t2:
    panel(df_4r, "4 RUEDAS")
