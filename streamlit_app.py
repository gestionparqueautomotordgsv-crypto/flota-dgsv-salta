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
    except: return 0

def ultima_fecha_estado(row, cols_fecha):
    for c in reversed(cols_fecha):
        v=str(row[c]).strip()
        if v!="" and v.upper()!="NAN":
            return c, v.upper()
    return "SIN FECHA", "SIN DATO"

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
col_siga=buscar_col(df_all,["SIGA","EXPTE"])
col_ubi=buscar_col(df_all,["UBICACION","UBICACIÓN"])
cols_fecha=[c for c in df_all.columns if "/" in c]

df_2r=df_all[df_all[col_tipo].str.contains("2",na=False)] if col_tipo else df_all
df_4r=df_all[df_all[col_tipo].str.contains("4",na=False)] if col_tipo else df_all

def calcular_estado(row):
    movil=str(row[col_movil]) if col_movil else ""
    if "2378" in movil: return "ALERTA"
    v="NORMAL"
    for c in reversed(cols_fecha):
        vv=str(row[c]).strip()
        if vv!="" and vv.upper()!="NAN":
            v=vv.upper(); break
    if "QRT" in v: return "QRT"
    if "SERVI" in v: return "SERVI"
    if "PRECAR" in v: return "PRECARIO"
    if col_km_act and col_prox:
        km=num(row[col_km_act]); prox=num(row[col_prox])
        if prox>0 and km>0 and km>=prox-1000: return "ALERTA"
    return "NORMAL"

def panel(df_base, tipo_rueda):
    key=f"filtro_{tipo_rueda}"
    if key not in st.session_state: st.session_state[key]="TODOS"

    c1,c2 = st.columns(2)
    with c1:
        busca_movil = st.text_input(f"🔍 Buscar MOVIL en {tipo_rueda}", key=f"mov_{tipo_rueda}")
    with c2:
        deps = ["TODAS"] + sorted([x for x in df_base[col_dep].unique() if str(x).strip()!=""]) if col_dep and col_dep in df_base else ["TODAS"]
        busca_dep = st.selectbox(f"🏢 DEPENDENCIA en {tipo_rueda}", deps, key=f"dep_{tipo_rueda}")

    df_base_f = df_base.copy()
    if busca_movil and col_movil:
        df_base_f = df_base_f[df_base_f[col_movil].astype(str).str.contains(busca_movil, na=False)]
    if busca_dep!="TODAS" and col_dep and col_dep in df_base_f:
        df_base_f = df_base_f[df_base_f[col_dep]==busca_dep]

    df_base_calc=df_base_f.copy()
    df_base_calc["ESTADO"]=df_base_calc.apply(calcular_estado, axis=1)

    alerta_df = df_base_calc[df_base_calc["ESTADO"]=="ALERTA"]
    qrt_c=len(df_base_calc[df_base_calc["ESTADO"]=="QRT"])
    servi_c=len(df_base_calc[df_base_calc["ESTADO"]=="SERVI"])
    precario_c=len(df_base_calc[df_base_calc["ESTADO"]=="PRECARIO"])
    normal_c=len(df_base_calc[df_base_calc["ESTADO"].isin(["NORMAL","ALERTA"])])

    # BOTONERA SIN ALERTA - 5 BOTONES COMO ANTES
    ca,cb,cc,cd,ce=st.columns(5)
    with ca:
        if st.button(f"🔴 QRT\n{qrt_c}", key=f"qrt_{tipo_rueda}", use_container_width=True): st.session_state[key]="QRT"
    with cb:
        if st.button(f"🔵 SERVI\n{servi_c}", key=f"servi_{tipo_rueda}", use_container_width=True): st.session_state[key]="SERVI"
    with cc:
        if st.button(f"🟢 NORMAL\n{normal_c}", key=f"normal_{tipo_rueda}", use_container_width=True): st.session_state[key]="NORMAL"
    with cd:
        if st.button(f"🟡 PRECARIO\n{precario_c}", key=f"prec_{tipo_rueda}", use_container_width=True): st.session_state[key]="PRECARIO"
    with ce:
        if st.button(f"⬛ TOTAL\n{len(df_base_calc)}", key=f"total_{tipo_rueda}", use_container_width=True): st.session_state[key]="TODOS"

    if len(alerta_df)>0:
        st.markdown(f"<div style='background:#fff3cd;border:2px solid #ffc107;padding:12px;border-radius:8px;margin-top:10px;color:#664d03'>🟡 <b>ALERTA KM {tipo_rueda}: {len(alerta_df)} próximos al servi (a 1000km) - DENTRO DE NORMAL</b></div>", unsafe_allow_html=True)
        for _, r in alerta_df.iterrows():
            st.markdown(f"⚠️ **{r[col_movil]} - {r[col_km_act]}km / Toca {r[col_prox]}km - {r[col_dep]}**")

    filtro=st.session_state[key]
    df_f=df_base_calc.copy()
    if filtro=="QRT": df_f=df_f[df_f["ESTADO"]=="QRT"]
    elif filtro=="SERVI": df_f=df_f[df_f["ESTADO"]=="SERVI"]
    elif filtro=="PRECARIO": df_f=df_f[df_f["ESTADO"]=="PRECARIO"]
    elif filtro=="NORMAL": df_f=df_f[df_f["ESTADO"].isin(["NORMAL","ALERTA"])]

    st.divider()

    if filtro in ["QRT","NORMAL","SERVI","PRECARIO"]:
        st.subheader(f"📋 {filtro} en {tipo_rueda}")
        lista=[]
        for _, r in df_f.iterrows():
            fecha, est = ultima_fecha_estado(r, cols_fecha)
            siga = str(r[col_siga]).strip() if col_siga and col_siga in r else ""
            ubi = str(r[col_ubi]).strip() if col_ubi and col_ubi in r else ""
            if siga=="" or siga.upper()=="NAN": siga="SIN EXPTE"
            if ubi=="" or ubi.upper()=="NAN": ubi="SIN UBICACION"
            lista.append({
                "MOVIL": r[col_movil], "ULTIMA FECHA": fecha, "ESTADO": est,
                "KM ACTUAL": r[col_km_act] if col_km_act else "",
                "PROXIMO SERVICE": r[col_prox] if col_prox else "",
                "DEPENDENCIA": r[col_dep] if col_dep else "",
                "SIGA N° EXPTE": siga, "UBICACION": ubi
            })
        st.dataframe(pd.DataFrame(lista), use_container_width=True)
    else:
        st.dataframe(df_f, use_container_width=True)

    # GRAFICO SIN ALERTA - ALERTA VUELVE DENTRO DE NORMAL
    graf=df_f["ESTADO"].replace({"ALERTA":"NORMAL"}).value_counts().reset_index()
    graf.columns=["Estado","Cantidad"]
    if len(graf)>0:
        chart=alt.Chart(graf).mark_bar(cornerRadiusTopLeft=8, cornerRadiusTopRight=8).encode(
            x=alt.X('Estado:N', sort=["NORMAL","QRT","PRECARIO","SERVI"]),
            y='Cantidad:Q',
            color=alt.Color('Estado:N', scale=alt.Scale(domain=["NORMAL","QRT","PRECARIO","SERVI"], range=["#22c55e","#ef4444","#eab308","#3b82f6"]), legend=None),
            tooltip=['Estado','Cantidad']
        ).properties(height=300)
        st.altair_chart(chart, use_container_width=True)

t1,t2=st.tabs([f"🏍️ DOS RUEDAS ({len(df_2r)})", f"🚔 CUATRO RUEDAS ({len(df_4r)})"])
with t1: panel(df_2r, "2 RUEDAS")
with t2: panel(df_4r, "4 RUEDAS")
