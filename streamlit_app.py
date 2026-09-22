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
col_ubi=buscar_col(df_all,["UBICACION","UBICACIÓN"]) # <-- NUEVA
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
    df_base_calc=df_base.copy()
    df_base_calc["ESTADO"]=df_base_calc.apply(calcular_estado, axis=1)
    qrt_c=len(df_base_calc[df_base_calc["ESTADO"]=="QRT"])
    servi_c=len(df_base_calc[df_base_calc["ESTADO"]=="SERVI"])
    precario_c=len(df_base_calc[df_base_calc["ESTADO"]=="PRECARIO"])
    normal_c=len(df_base_calc[df_base_calc["ESTADO"].isin(["NORMAL","ALERTA"])])

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

    filtro=st.session_state[key]
    df_f=df_base.copy()
    df_f["ESTADO"]=df_f.apply(calcular_estado, axis=1)
    if filtro=="QRT": df_f=df_f[df_f["ESTADO"]=="QRT"]
    elif filtro=="SERVI": df_f=df_f[df_f["ESTADO"]=="SERVI"]
    elif filtro=="PRECARIO": df_f=df_f[df_f["ESTADO"]=="PRECARIO"]
    elif filtro=="NORMAL": df_f=df_f[df_f["ESTADO"].isin(["NORMAL","ALERTA"])]
    st.divider()

    if filtro in ["QRT","NORMAL","SERVI","PRECARIO"]:
        st.subheader(f"📋 {filtro} en {tipo_rueda} - con SIGA y UBICACION")
        lista=[]
        for _, r in df_f.iterrows():
            fecha, est = ultima_fecha_estado(r, cols_fecha)
            siga = str(r[col_siga]).strip() if col_siga and col_siga in r else ""
            ubi = str(r[col_ubi]).strip() if col_ubi and col_ubi in r else ""
            if siga=="" or siga.upper()=="NAN": siga="SIN EXPTE"
            if ubi=="" or ubi.upper()=="NAN": ubi="SIN UBICACION"
            lista.append({
                "MOVIL": r[col_movil] if col_movil else "",
                "ULTIMA FECHA": fecha,
                "ESTADO": est,
                "DEPENDENCIA": r[col_dep] if col_dep else "",
                "SIGA N° EXPTE": siga,
                "UBICACION": ubi
            })
        st.dataframe(pd.DataFrame(lista), use_container_width=True)
    else:
        st.dataframe(df_f, use_container_width=True)

t1,t2=st.tabs([f"🏍️ DOS RUEDAS ({len(df_2r)})", f"🚔 CUATRO RUEDAS ({len(df_4r)})"])
with t1: panel(df_2r, "2 RUEDAS")
with t2: panel(df_4r, "4 RUEDAS")
