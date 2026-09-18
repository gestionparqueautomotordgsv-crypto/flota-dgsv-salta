import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title="Flota DGSV", layout="wide", page_icon="🚔")
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

# --- PARCHE: ARREGLA BLANCOS Y CELDAS COMBINADAS - PEGADO ACÁ ---
col_dep_temp = buscar_col(df_all,"DEPENDEN")
col_tipo_temp = buscar_col(df_all,"RUEDAS")
if col_dep_temp:
    df_all[col_dep_temp]=df_all[col_dep_temp].astype(str).str.strip()
    # Si quedó "2 RUEDAS" en dependencia, lo sacamos
    df_all[col_dep_temp]=df_all[col_dep_temp].str.upper().str.replace("2 RUEDAS","").str.replace("4 RUEDAS","").str.strip()
    df_all[col_dep_temp]=df_all[col_dep_temp].replace(["","NAN","NONE","N/A"],"DGSV")
    df_all[col_dep_temp]=df_all[col_dep_temp].replace(r'^\s*$','DGSV',regex=True)
if col_tipo_temp:
    df_all[col_tipo_temp]=df_all[col_tipo_temp].astype(str).str.upper().str.strip()
    df_all.loc[df_all[col_tipo_temp].str.contains("2",na=False), col_tipo_temp]="2 RUEDAS"
    df_all.loc[df_all[col_tipo_temp].str.contains("4",na=False), col_tipo_temp]="4 RUEDAS"
# --- FIN PARCHE ---

col_tipo=buscar_col(df_all,"RUEDAS")
col_movil=buscar_col(df_all,"MOVIL")
col_dep=buscar_col(df_all,"DEPENDEN")
col_dom=buscar_col(df_all,"DOMINIO")
col_km_act=buscar_col(df_all,"KM ACTUAL")
col_prox=buscar_col(df_all,"PROXIMO")
cols_fecha=[c for c in df_all.columns if "/" in c]
col_estado=cols_fecha[-1] if cols_fecha else None

df_2r=df_all[df_all[col_tipo].str.contains("2",na=False)] if col_tipo else df_all
df_4r=df_all[df_all[col_tipo].str.contains("4",na=False)] if col_tipo else df_all

def panel(df, nombre):
    c1,c2=st.columns(2)
    with c1: f_movil=st.text_input("MOVIL", key=f"m_{nombre}").upper()
    with c2: f_dep=st.text_input("DEPENDENCIA", key=f"d_{nombre}").upper()
    df_f=df.copy()
    if f_movil and col_movil:
        df_f=df_f[df_f[col_movil].astype(str).str.upper().str.contains(f_movil,na=False)]
    if f_dep and col_dep:
        df_f=df_f[df_f[col_dep].astype(str).str.upper().str.contains(f_dep,na=False)]
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
    precario=len(df_f[df_f["ESTADO"]=="PRECARIO"])
    alerta_df=df_f[df_f["ESTADO"]=="ALERTA"]
    normal=len(df_f[df_f["ESTADO"]=="NORMAL"])+len(alerta_df)
    ca,cb,cc,cd,ce=st.columns(5)
    ca.markdown(f"<div style='background:#ff6b6b;padding:15px;border-radius:12px;text-align:center;height:95px'><b>🔴 QRT</b><br><span style='font-size:32px;font-weight:bold'>{qrt}</span></div>",unsafe_allow_html=True)
    cb.markdown(f"<div style='background:#4dabf7;padding:15px;border-radius:12px;text-align:center;height:95px'><b>🔵 SERVI</b><br><span style='font-size:32px;font-weight:bold'>{servi}</span></div>",unsafe_allow_html=True)
    cc.markdown(f"<div style='background:#51cf66;padding:15px;border-radius:12px;text-align:center;height:95px'><b>🟢 NORMAL</b><br><span style='font-size:32px;font-weight:bold'>{normal}</span></div>",unsafe_allow_html=True)
    cd.markdown(f"<div style='background:#fcc419;padding:15px;border-radius:12px;text-align:center;height:95px'><b>🟡 PRECARIO</b><br><span style='font-size:32px;font-weight:bold'>{precario}</span></div>",unsafe_allow_html=True)
    ce.markdown(f"<div style='background:#1e293b;padding:15px;border-radius:12px;text-align:center;color:white;height:95px'><b>Total</b><br><span style='font-size:32px;font-weight:bold'>{len(df_f)}</span></div>",unsafe_allow_html=True)
    if len(alerta_df)>0:
        st.warning(f"🟡 ALERTA: {len(alerta_df)} próximos al servi - YA SUMADO EN NORMAL")
        for _, r in alerta_df.iterrows():
            st.write(f"⚠️ {r[col_movil]} - {r[col_km_act]}km / Toca {r[col_prox]}km")
    st.dataframe(df_f, use_container_width=True, height=600)

st.title("🚔 Flota DGSV - En prueba")
t1,t2=st.tabs([f"🏍️ DOS RUEDAS ({len(df_2r)})", f"🚔 CUATRO RUEDAS ({len(df_4r)})"])
with t1: panel(df_2r, "2R")
with t2: panel(df_4r, "4R")
