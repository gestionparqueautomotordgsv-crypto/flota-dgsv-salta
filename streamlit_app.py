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
    d=str(dep).upper()
    claves=["DGSV","EDUCACION","OPERACIONES","EJIDO","NORBERTO","TRANSP"]
    return any(k in d for k in claves)

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

def estado_real(row):
    # Solo lo que dice la planilla, sin alerta
    v="NORMAL"
    for c in reversed(cols_fecha):
        vv=str(row[c]).strip()
        if vv!="" and vv.upper()!="NAN":
            v=vv.upper(); break
    if "QRT" in v: return "QRT"
    if "SERVI" in v: return "SERVI"
    if "PRECAR" in v: return "PRECARIO"
    return "NORMAL"

def es_alerta(row):
    movil=str(row[col_movil]) if col_movil else ""
    if "2378" in movil: return True
    if col_km_act and col_prox:
        km=num(row[col_km_act]); prox=num(row[col_prox])
        if prox>0 and km>0 and km>=prox-1000: return True
    return False

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
    df_base_calc["ESTADO"]=df_base_calc.apply(estado_real, axis=1)
    df_base_calc["ALERTA"]=df_base_calc.apply(es_alerta, axis=1)

    alerta_df = df_base_calc[df_base_calc["ALERTA"]==True]

    # BOTONERA SOLO CON ESTADO REAL - ALERTA NO TOCA NADA
    qrt_c=len(df_base_calc[df_base_calc["ESTADO"]=="QRT"])
    servi_c=len(df_base_calc[df_base_calc["ESTADO"]=="SERVI"])
    precario_c=len(df_base_calc[df_base_calc["ESTADO"]=="PRECARIO"])
    normal_c=len(df_base_calc[df_base_calc["ESTADO"]=="NORMAL"])
    total = len(df_base_calc)

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
        if st.button(f"⬛ TOTAL\n{total}", key=f"total_{tipo_rueda}", use_container_width=True): st.session_state[key]="TODOS"

    if len(alerta_df)>0:
        st.markdown(f"<div style='background:#fff3cd;border:2px solid #ffc107;padding:12px;border-radius:8px;margin-top:10px;color:#664d03'>🟡 <b>ALERTA KM {tipo_rueda}: {len(alerta_df)} próximos al servi - SOLO INFORMATIVO</b></div>", unsafe_allow_html=True)
        for _, r in alerta_df.iterrows():
            st.markdown(f"⚠️ **{r[col_movil]} - {r[col_km_act]}km / Toca {r[col_prox]}km - {r[col_dep]} - Es {r['ESTADO']}**")

    filtro=st.session_state[key]
    df_f=df_base_calc.copy()
    if filtro!="TODOS":
        df_f=df_f[df_f["ESTADO"]==filtro]

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
                "SIGA N° EXPTE": siga, "UBICACION": ubi,
                "ALERTA": "⚠️ SI" if r["ALERTA"] else ""
            })
        st.dataframe(pd.DataFrame(lista), use_container_width=True)
    else:
        st.dataframe(df_f, use_container_width=True)

    # TORTA CON % DENTRO - SOLO ESTADO REAL
    graf=df_f["ESTADO"].value_counts().reset_index()
    graf.columns=["Estado","Cantidad"]
    if len(graf)>0:
        graf["Porcentaje"] = graf["Cantidad"] / graf["Cantidad"].sum() * 100
        graf["Label"] = graf["Estado"] + " " + graf["Porcentaje"].round(1).astype(str) + "%"

        base = alt.Chart(graf).encode(theta=alt.Theta("Cantidad:Q"))

        pie = base.mark_arc(innerRadius=50, outerRadius=120).encode(
            color=alt.Color('Estado:N', scale=alt.Scale(domain=["NORMAL","QRT","PRECARIO","SERVI"], range=["#22c55e","#ef4444","#eab308","#3b82f6"]), legend=None),
            tooltip=['Estado','Cantidad', alt.Tooltip('Porcentaje:Q', format='.1f')]
        )

        text = base.mark_text(radius=155, size=13, fontWeight="bold").encode(
            text=alt.Text('Label:N'),
            color=alt.Color('Estado:N', scale=alt.Scale(domain=["NORMAL","QRT","PRECARIO","SERVI"], range=["#22c55e","#ef4444","#eab308","#3b82f6"]), legend=None),
            theta=alt.Theta('Cantidad:Q')
        )

        st.altair_chart(pie + text, use_container_width=True)

def panel_capital_interior(df_all):
    st.header("🏙️ CAPITAL vs 🌄 INTERIOR")
    df = df_all.copy()
    df["ESTADO"] = df.apply(estado_real, axis=1)
    df["ALERTA"] = df.apply(es_alerta, axis=1)
    df["ZONA"] = df[col_dep].apply(lambda x: "CAPITAL" if es_capital(x) else "INTERIOR")

    c1,c2 = st.columns(2)
    with c1:
        f_zona = st.selectbox("Filtrar ZONA", ["TODAS","CAPITAL","INTERIOR"], key="f_zona")
    with c2:
        f_estado = st.selectbox("Filtrar ESTADO", ["TODOS","NORMAL","QRT","SERVI","PRECARIO"], key="f_estado")

    df_filt = df.copy()
    if f_zona!="TODAS":
        df_filt = df_filt[df_filt["ZONA"]==f_zona]
    if f_estado!="TODOS":
        df_filt = df_filt[df_filt["ESTADO"]==f_estado]

    col_cap, col_int = st.columns(2)
    for zona, col in [("CAPITAL", col_cap), ("INTERIOR", col_int)]:
        with col:
            if f_zona!="TODAS":
                dz = df_filt
            else:
                dz = df[ df["ZONA"]==zona ]
                if f_estado!="TODOS":
                    dz = dz[dz["ESTADO"]==f_estado]

            total=len(dz)
            qrt=len(dz[dz["ESTADO"]=="QRT"])
            serv=len(dz[dz["ESTADO"]=="SERVI"])
            prec=len(dz[dz["ESTADO"]=="PRECARIO"])
            norm=len(dz[dz["ESTADO"]=="NORMAL"])

            st.subheader(f"{zona} - {total} móviles")
            m1,m2,m3,m4=st.columns(4)
            m1.metric("NORMAL", norm)
            m2.metric("QRT", qrt)
            m3.metric("SERVI", serv)
            m4.metric("PRECARIO", prec)

            graf=dz["ESTADO"].value_counts().reset_index()
            graf.columns=["Estado","Cantidad"]
            if len(graf)>0:
                graf["Porcentaje"]=graf["Cantidad"]/graf["Cantidad"].sum()*100
                chart=alt.Chart(graf).mark_bar().encode(
                    x=alt.X('Estado:N', sort=["NORMAL","QRT","PRECARIO","SERVI"]),
                    y='Cantidad:Q',
                    color=alt.Color('Estado:N', scale=alt.Scale(domain=["NORMAL","QRT","PRECARIO","SERVI"], range=["#22c55e","#ef4444","#eab308","#3b82f6"]), legend=None),
                    tooltip=['Estado','Cantidad', alt.Tooltip('Porcentaje:Q', format='.1f')]
                ).properties(height=250)
                st.altair_chart(chart, use_container_width=True)

    st.divider()
    st.subheader(f"📋 Listado {f_zona} - {f_estado}")
    lista=[]
    for _, r in df_filt.iterrows():
        fecha, est = ultima_fecha_estado(r, cols_fecha)
        lista.append({
            "MOVIL": r[col_movil],
            "ZONA": r["ZONA"],
            "ESTADO": est,
            "ALERTA": "⚠️" if r["ALERTA"] else "",
            "DEPENDENCIA": r[col_dep],
            "SIGA": r[col_siga] if str(r[col_siga]).strip()!="" else "SIN EXPTE",
            "UBICACION": r[col_ubi] if str(r[col_ubi]).strip()!="" else "SIN UBICACION"
        })
    st.dataframe(pd.DataFrame(lista), use_container_width=True)

t1,t2,t3=st.tabs([f"🏍️ DOS RUEDAS ({len(df_2r)})", f"🚔 CUATRO RUEDAS ({len(df_4r)})", "🏙️ CAPITAL / INTERIOR"])
with t1: panel(df_2r, "2 RUEDAS")
with t2: panel(df_4r, "4 RUEDAS")
with t3: panel_capital_interior(df_all)
