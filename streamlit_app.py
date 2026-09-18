def panel(df, nombre):
    st.markdown(f"#### 🔍 Filtros {nombre}")
    c_b1, c_b2 = st.columns(2)
    with c_b1:
        f_movil = st.text_input(f"MOVIL", placeholder="Ej: 2363, 2553", key=f"mov_{nombre}").upper()
    with c_b2:
        f_dep = st.text_input(f"DEPENDENCIA", placeholder="Ej: VIAL, DGSV", key=f"dep_{nombre}").upper()

    df_f = df.copy()
    
    if f_movil:
        df_f = df_f[df_f[col_movil].astype(str).str.upper().str.contains(f_movil, na=False)]
    if f_dep:
        df_f = df_f[df_f[col_dep].astype(str).str.upper().str.contains(f_dep, na=False)]

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

    df_f["ESTADO HOY"]=df_f.apply(estado_final, axis=1)

    qrt=len(df_f[df_f["ESTADO HOY"]=="QRT"])
    servi=len(df_f[df_f["ESTADO HOY"]=="SERVI"])
    normal=len(df_f[df_f["ESTADO HOY"]=="NORMAL"])
    alerta_df=df_f[df_f["ESTADO HOY"]=="ALERTA"]

    # RESUMEN QUE SI SE VE
    c1,c2,c3,c4=st.columns(4)
    c1.markdown(f"<div style='background:#ef4444;padding:12px;border-radius:10px;text-align:center'><span style='color:white;font-weight:bold'>🔴 QRT</span><br><span style='color:white;font-size:34px;font-weight:bold'>{qrt}</span></div>", unsafe_allow_html=True)
    c2.markdown(f"<div style='background:#3b82f6;padding:12px;border-radius:10px;text-align:center'><span style='color:white;font-weight:bold'>🔵 SERVI</span><br><span style='color:white;font-size:34px;font-weight:bold'>{servi}</span></div>", unsafe_allow_html=True)
    c3.markdown(f"<div style='background:#22c55e;padding:12px;border-radius:10px;text-align:center'><span style='color:white;font-weight:bold'>🟢 NORMAL</span><br><span style='color:white;font-size:34px;font-weight:bold'>{normal}</span></div>", unsafe_allow_html=True)
    c4.markdown(f"<div style='background:#f1f5f9;padding:12px;border-radius:10px;text-align:center'><span style='color:#334155;font-weight:bold'>Total filtrado</span><br><span style='color:#334155;font-size:34px;font-weight:bold'>{len(df_f)}</span></div>", unsafe_allow_html=True)

    # CUENTA POR DEPENDENCIA
    if len(df_f)>0:
        st.caption(f"Mostrando {len(df_f)} motos de {nombre}")
        conteo_dep = df_f[col_dep].value_counts().reset_index()
        conteo_dep.columns=["Dependencia","Cantidad"]
        if len(conteo_dep)>1:
            st.dataframe(conteo_dep, use_container_width=True, height=150)

    st.write("")
    if len(alerta_df)>0:
        st.markdown(f"<div style='background:#fef08a;border-left:6px solid #eab308;padding:10px;border-radius:8px'><b>🟡 ALERTA: {len(alerta_df)} próximos al servi</b></div>", unsafe_allow_html=True)
        for _, r in alerta_df.iterrows():
            st.info(f"⚠️ {r[col_movil]} - {r[col_km_act]}km / Toca {r[col_prox]}km - {r[col_dom]} - {r[col_dep]}")

    # GRAFICO
    df_graf=df_f.copy()
    df_graf["GRAFICO"]=df_graf["ESTADO HOY"].replace({"ALERTA":"NORMAL"})
    graf=df_graf["GRAFICO"].value_counts().reset_index()
    graf.columns=["Estado","Cantidad"]
    chart=alt.Chart(graf).mark_bar().encode(
        x=alt.X('Estado:N', sort=["NORMAL","QRT","PRECARIO","SERVI"]),
        y='Cantidad:Q',
        color=alt.Color('Estado:N', scale=alt.Scale(domain=["NORMAL","QRT","PRECARIO","SERVI"], range=["#22c55e","#ef4444","#eab308","#3b82f6"]), legend=None)
    )
    st.altair_chart(chart, use_container_width=True)

    st.dataframe(df_f, use_container_width=True, height=600)
