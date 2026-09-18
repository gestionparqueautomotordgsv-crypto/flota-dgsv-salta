    qrt=len(df_f[df_f["ESTADO"]=="QRT"])
    servi=len(df_f[df_f["ESTADO"]=="SERVI"])
    precario=len(df_f[df_f["ESTADO"]=="PRECARIO"])
    alerta_df=df_f[df_f["ESTADO"]=="ALERTA"]
    
    # NORMAL = NORMAL + ALERTA AMARILLA (por eso cierra 19 y 85)
    normal_base=len(df_f[df_f["ESTADO"]=="NORMAL"])
    normal = normal_base + len(alerta_df)

    # CUADROS COMO EN TU FOTO - 4 cuadros + total
    c1,c2,c3,c4 = st.columns(4)
    c1.markdown(f"<div style='background:#ff6b6b;padding:15px;border-radius:12px;text-align:center'><b>🔴 QRT</b><br><span style='font-size:32px'>{qrt}</span></div>", unsafe_allow_html=True)
    c2.markdown(f"<div style='background:#4dabf7;padding:15px;border-radius:12px;text-align:center'><b>🔵 SERVI</b><br><span style='font-size:32px'>{servi}</span></div>", unsafe_allow_html=True)
    c3.markdown(f"<div style='background:#51cf66;padding:15px;border-radius:12px;text-align:center'><b>🟢 NORMAL</b><br><span style='font-size:32px'>{normal}</span></div>", unsafe_allow_html=True)
    c4.markdown(f"<div style='background:#1e293b;padding:15px;border-radius:12px;text-align:center;color:white'><b>Total</b><br><span style='font-size:32px'>{len(df_f)}</span></div>", unsafe_allow_html=True)

    # Si hay precarios, mostramos el 5to cuadro aparte para que no se pierda
    if precario > 0:
        st.markdown(f"<div style='background:#fcc419;padding:10px;border-radius:10px;text-align:center;margin-top:10px'><b>🟡 PRECARIO: {precario}</b></div>", unsafe_allow_html=True)

    if len(alerta_df)>0:
        st.warning(f"🟡 ALERTA AMARILLA: {len(alerta_df)} próximos al servi (1000km antes)")
        for _, r in alerta_df.iterrows():
            st.write(f"⚠️ {r[col_movil]} - {r[col_km_act]}km / Toca {r[col_prox]}km - {r[col_dom]}")
