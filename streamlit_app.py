import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title="Flota DGSV", layout="wide", page_icon="🚔")
URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRO9kumGN6YMvBI_hGc-D9Lb8y29RqNubvkIN1gpgN6I8QKjZ2QBNQ3ItyVkLZeuw/pub?gid=1702506345&single=true&output=csv"

@st.cache_data(ttl=10)
def cargar():
    df=pd.read_csv(URL, dtype=str).fillna("")
    df.columns=[c.strip().upper() for c in df.columns]
    return df

def buscar_col(df, txt):
    for c in df.columns:
        if txt in c:
            return c
    return None

st.title("🚔 Flota DGSV - En prueba")
if st.button("🔄 Actualizar"):
    st.cache_data.clear()
    st.rerun()

df_all=cargar()
col_tipo=buscar_col(df_all,"RUEDAS")
col_movil=buscar_col(df_all,"MOVIL")
col_km_act=buscar_col(df_all,"KM ACTUAL")
col_prox=buscar_col(df_all,"PROXIMO")
cols_fecha=[c for c in df_all.columns if "/" in c]

df_2r=df_all[df_all[col_tipo].str.contains("2",na=False)] if col_tipo else df_all
df_4r=df_all[df_all[col_tipo].str.contains("4",na=False)] if col_tipo else df_all

def panel(df, tipo_rueda):
    df_f=df.copy()

    def get_estado_diario(row):
        for c in reversed(cols_fecha):
            v=str(row[c]).strip()
            if v!="" and v.upper()!="NAN":
                return v
        return "NORMAL"

    def estado_final(row):
        v=get_estado_diario(row).upper()
        if "QRT" in v: return "QRT"
        if "SERVI" in v: return "SERVI"
        if "PRECAR" in v: return "PRECARIO"
        if col_km_act and col_prox:
            try:
                km=int(float(str(row[col_km_act]).replace(".","").replace(",","").strip() or 0))
                prox=int(float(str(row[col_prox]).replace(".","").replace(",","").strip() or 0))
                if prox>0 and km>0 and km>=prox-1000:
                    return "ALERTA"
            except:
                pass
        return "NORMAL"

    df_f["ESTADO"]=df_f.apply(estado_final, axis=1)
    qrt=len(df_f[df_f["ESTADO"]=="QRT"])
    servi=len(df_f[df_f["ESTADO"]=="SERVI"])
    precario=len(df_f[df_f["ESTADO"]=="PRECARIO"])
    alerta_df=df_f[df_f["ESTADO"]=="ALERTA"]
    alerta=len(alerta_df)
    normal=len(df_f[df_f["ESTADO"]=="NORMAL"]) + alerta

    st.markdown(f"**Filtro activo: {tipo_rueda}**")

    ca,cb,cc,cd,ce=st.columns(5)
    ca.markdown(f"<div style='background:#ff6b6b;padding:15px;border-radius:12px;text-align:center'><b>🔴 QRT</b><br><span style='font-size:30px'>{qrt}</span></div>",unsafe_allow_html=True)
    cb.markdown(f"<div style='background:#4dabf7;padding:15px;border-radius:12px;text-align:center'><b>🔵 SERVI</b><br><span style='font-size:30px'>{servi}</span></div>",unsafe_allow_html=True)
    cc.markdown(f"<div style='background:#51cf66;padding:15px;border-radius:12px;text-align:center'><b>🟢 NORMAL</b><br><span style='font-size:30px'>{normal}</span></div>",unsafe_allow_html=True)
    cd.markdown(f"<div style='background:#fcc419;padding:15px;border-radius:12px;text-align:center'><b>🟡 PRECARIO</b><br><span style='font-size:30px'>{precario}</span></div>",unsafe_allow_html=True)
    ce.markdown(f"<div style='background:#1e293b;color:white;padding:15px;border-radius:12px;text-align:center'><b>Total {tipo_rueda}</b><br><span style='font-size:30px'>{len(df_f)}</span></div>",unsafe_allow_html=True)

    if alerta>0:
        st.markdown(f"<div style='background:#fff3cd;border:1px solid #ffe69c;padding:12px;border-radius:8px;margin-top:15px;color:#664d03;font-size:16px'>🟡 <b>ALERTA KM {tipo_rueda}: {alerta} próximos al servi - DENTRO DE NORMAL</b></div>", unsafe_allow_html=True)
        for _, r in alerta_df.iterrows():
            movil=str(r[col_movil]) if col_movil else ""
            km=str(r[col_km_act]) if col_km_act else ""
            prox=str(r[col_prox]) if col_prox else ""
            st.markdown(f"<div style='margin-top:10px;font-size:16px'>⚠️ <b>{movil} - {km}km / Toca {prox}km - {tipo_rueda}</b></div>", unsafe_allow_html=True)
        st.markdown(f"<div style='margin-top:10px;padding:8px;background:#e2e3e5;border-radius:6px'>🔵 <b>ALERTA PARA SERVI {tipo_rueda}: {alerta} móviles</b></div>", unsafe_allow_html=True)

    st.divider()
    graf=df_f["ESTADO"].replace({"ALERTA":"NORMAL"}).value_counts().reset_index()
    graf.columns=["Estado","Cantidad"]
    chart=alt.Chart(graf).mark_bar(cornerRadiusTopLeft=8, cornerRadiusTopRight=8).encode(
        x=alt.X('Estado:N', sort=["NORMAL","QRT","PRECARIO","SERVI"]),
        y='Cantidad:Q',
        color=alt.Color('Estado:N', scale=alt.Scale(domain=["NORMAL","QRT","PRECARIO","SERVI"], range=["#22c55e","#ef4444","#eab308","#3b82f6"]), legend=None)
    ).properties(height=300)
    st.altair_chart(chart, use_container_width=True)
    st.dataframe(df_f, use_container_width=True)

t1,t2=st.tabs([f"🏍️ DOS RUEDAS ({len(df_2r)}) - FILTRO 2 RUEDAS", f"🚔 CUATRO RUEDAS ({len(df_4r)}) - FILTRO 4 RUEDAS"])
with t1:
    panel(df_2r, "2 RUEDAS")
with t2:
    panel(df_4r, "4 RUEDAS")
