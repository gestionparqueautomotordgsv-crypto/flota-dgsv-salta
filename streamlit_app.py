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

def es_capital(dep):
    dep = str(dep).upper()
    claves = ["DGSV","EDUCACION","OPERACIONES","EJIDO","NORBERTO","TRANSP","JEFATURA"]
    return any(k in dep for k in claves)

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
        busca_movil = st.text_input(f"🔍 MOVIL {tipo_rueda}", key=f"mov_{tipo_rueda}")
    with c2:
        deps = ["TODAS"] + sorted([x for x in df_base[col_dep].unique() if str(x).strip()!=""]) if col_dep else ["TODAS"]
        busca_dep = st.selectbox(f"🏢 DEPENDENCIA", deps, key=f"dep_{tipo_rueda}")
    df_base_f = df_base.copy()
    if busca_movil and col_movil:
        df_base_f = df_base_f[df_base_f[col_movil].astype(str).str.contains(busca_movil, na=False)]
    if busca_dep!="TODAS" and col_dep:
        df_base_f = df_base_f[df_base_f[col_dep]==busca_dep]
    df_base_calc=df_base_f.copy()
    df_base_calc["ESTADO"]=df_base_calc.apply(calcular_estado, axis=1)
    qrt_c=len(df_base_calc[df_base_calc["ESTADO"]=="QRT"])
    servi_c=len(df_base_calc[df_base_calc["ESTADO"]=="SERVI"])
    precario_c=len(df_base_calc[df_base_calc["ESTADO"]=="PRECARIO"])
    normal_c=len(df_base_calc[df_base_calc["ESTADO"].isin(["NORMAL","ALERTA"])])
    ca,cb,cc,cd,ce=st.columns(5)
    with ca:
        if st.button(f"🔴 QRT {qrt_c}", key=f"qrt_{tipo_rueda}", use_container_width=True): st.session_state[key]="QRT"
    with cb:
        if st.button(f"🔵 SERVI {servi_c}", key=f"servi_{tipo_rueda}", use_container_width=True): st.session_state[key]="SERVI"
    with cc:
        if st.button(f"🟢 NORMAL {normal_c}", key=f"normal_{tipo_rueda}", use_container_width=True): st.session_state[key]="NORMAL"
    with cd:
        if st.button(f"🟡 PRECARIO {precario_c}", key=f"prec_{tipo_rueda}", use_container_width=True): st.session_state[key]="PRECARIO"
    with ce:
        if st.button(f"⬛ TOTAL {len(df_base_calc)}", key=f"total_{tipo_rueda}", use_container_width=True): st.session_state[key]="TODOS"
    filtro=st.session_state[key]
    df_f=df_base_calc.copy()
    if filtro=="QRT": df_f=df_f[df_f["ESTADO"]=="QRT"]
    elif filtro=="SERVI": df_f=df_f[df_f["ESTADO"]=="SERVI"]
    elif filtro=="PRECARIO": df_f=df_f[df_f["ESTADO"]=="PRECARIO"]
    elif filtro=="NORMAL": df_f=df_f[df_f["ESTADO"].isin(["NORMAL","ALERTA"])]
    st.divider()
    graf=df_f["ESTADO"].replace({"ALERTA":"NORMAL"}).value_counts().reset_index()
    graf.columns=["Estado","Cantidad"]
    if len(graf)>0:
        graf["Porcentaje"] = graf["Cantidad"] / graf["Cantidad"].sum() * 100
        pie = alt.Chart(graf).mark_arc(innerRadius=50).encode(theta="Cantidad:Q", color=alt.Color("Estado:N", scale=alt.Scale(domain=["NORMAL","QRT","PRECARIO","SERVI"], range=["#22c55e","#ef4444","#eab308","#3b82f6"])), tooltip=["Estado","Cantidad",alt.Tooltip("Porcentaje:Q",format=".2f")])
        st.altair_chart(pie, use_container_width=True)
        for _, r in graf.iterrows():
            st.write(f"{r['Estado']}: {r['Cantidad']} = {r['Porcentaje']:.2f}%")
    lista=[]
    for _, r in df_f.iterrows():
        fecha, est = ultima_fecha_estado(r, cols_fecha)
        siga = str(r[col_siga]).strip() if col_siga else ""
        ubi = str(r[col_ubi]).strip() if col_ubi else ""
        lista.append({"MOVIL":r[col_movil],"FECHA":fecha,"ESTADO":est,"DEP":r[col_dep],"SIGA":siga if siga else "SIN EXPTE","UBI":ubi if ubi else "SIN UBICACION"})
    st.dataframe(pd.DataFrame(lista), use_container_width=True)

def panel_zonas(df_all):
    st.header("🏙️ CAPITAL vs 🌄 INTERIOR")
    df_all["ZONA"] = df_all[col_dep].apply(lambda x: "CAPITAL" if es_capital(x) else "INTERIOR")
    df_all["ESTADO"] = df_all.apply(calcular_estado, axis=1)
    df_all["ESTADO_GRAF"] = df_all["ESTADO"].replace({"ALERTA":"NORMAL"})

    # RESUMEN RAPIDO
    c1,c2 = st.columns(2)
    for zona, col in [("CAPITAL", c1), ("INTERIOR", c2)]:
        with col:
            df_z = df_all[df_all["ZONA"]==zona]
            total=len(df_z)
            qrt=len(df_z[df_z["ESTADO"]=="QRT"])
            servi=len(df_z[df_z["ESTADO"]=="SERVI"])
            prec=len(df_z[df_z["ESTADO"]=="PRECARIO"])
            norm=len(df_z[df_z["ESTADO"].isin(["NORMAL","ALERTA"])])
            st.subheader(f"{zona} ({total})")
            st.metric("NORMAL", norm)
            st.metric("QRT", qrt)
            st.metric("SERVI", servi)
            st.metric("PRECARIO", prec)
            graf=df_z["ESTADO_GRAF"].value_counts().reset_index()
            graf.columns=["Estado","Cantidad"]
            if len(graf)>0:
                graf["Porcentaje"]=graf["Cantidad"]/graf["Cantidad"].sum()*100
                pie=alt.Chart(graf).mark_arc().encode(theta="Cantidad:Q", color=alt.Color("Estado:N", scale=alt.Scale(domain=["NORMAL","QRT","PRECARIO","SERVI"], range=["#22c55e","#ef4444","#eab308","#3b82f6"])), tooltip=["Estado","Cantidad",alt.Tooltip("Porcentaje:Q",format=".2f")])
                st.altair_chart(pie, use_container_width=True)

    st.divider()
    st.subheader("📋 Detalle por ZONA")
    filtro_z = st.selectbox("Filtrar ZONA", ["TODAS","CAPITAL","INTERIOR"])
    filtro_e = st.selectbox("Filtrar ESTADO", ["TODOS","QRT","NORMAL","SERVI","PRECARIO"])
    df_show = df_all.copy()
    if filtro_z!="TODAS": df_show=df_show[df_show["ZONA"]==filtro_z]
    if filtro_e!="TODOS":
        if filtro_e=="NORMAL": df_show=df_show[df_show["ESTADO"].isin(["NORMAL","ALERTA"])]
        else: df_show=df_show[df_show["ESTADO"]==filtro_e]
    st.dataframe(df_show[[col_movil,col_dep,"ZONA","ESTADO",col_km_act,col_prox]], use_container_width=True)

t1,t2,t3=st.tabs([f"🏍️ DOS RUEDAS ({len(df_2r)})", f"🚔 CUATRO RUEDAS ({len(df_4r)})", f"🏙️ CAPITAL / INTERIOR"])
with t1: panel(df_2r, "2 RUEDAS")
with t2: panel(df_4r, "4 RUEDAS")
with t3: panel_zonas(df_all.copy())
