def panel(df, nombre):
    busc = st.text_input(f"🔍 Buscar {nombre}", placeholder="Ej: 2553, DGSV", key=f"busc_{nombre}").upper()
    df_f = df.copy()
    if busc:
        df_f = df_f[df_f.apply(lambda r: busc in " ".join([str(x).upper() for x in r.values]), axis=1)]

    def estado_final(row):
        v = str(row[col_estado]).upper() if col_estado else ""
        if "QRT" in v: return "🔴 QRT"
        if "SERVI" in v: return "🔵 SERVI"
        if col_km_act and col_prox:
            try:
                km_act = int(float(str(row[col_km_act]).replace(".","").replace(",","").strip() or 0))
                prox = int(float(str(row[col_prox]).replace(".","").replace(",","").strip() or 0))
                if prox>0 and km_act>0:
                    if km_act >= prox: return "🔵 SERVI"
                    if km_act >= prox-1000: return f"🟡 ALERTA SERVI {prox}"
            except: pass
        if "PRECAR" in v: return "🟡 PRECARIO"
        return "🟢 NORMAL"

    if col_estado and col_estado in df_f.columns:
        df_f["ESTADO HOY"] = df_f.apply(estado_final, axis=1)

        qrt = len(df_f[df_f["ESTADO HOY"]=="🔴 QRT"])
        servi = len(df_f[df_f["ESTADO HOY"]=="🔵 SERVI"])
        alerta_df = df_f[df_f["ESTADO HOY"].str.contains("ALERTA")]
        alerta = len(alerta_df)

        # ===== RESUMEN SEPARADO COMO PEDISTE =====
        st.markdown(f"### {nombre}")
        c1,c2,c3 = st.columns(3)
        c1.markdown(f"<div style='background:#ef4444;color:white;padding:15px;border-radius:12px;text-align:center'><b>🔴 QRT</b><br><span style='font-size:32px'>{qrt}</span></div>", unsafe_allow_html=True)
        c2.markdown(f"<div style='background:#3b82f6;color:white;padding:15px;border-radius:12px;text-align:center'><b>🔵 SERVI</b><br><span style='font-size:32px'>{servi}</span></div>", unsafe_allow_html=True)
        c3.metric("Total Flota", len(df_f))

        st.write("") # otra linea
        if alerta > 0:
            st.markdown(f"<div style='background:#fef08a;border:2px solid #eab308;padding:12px;border-radius:12px'>🟡 <b>ALERTA AMARILLA - PRÓXIMOS AL SERVI (a 1000km): {alerta}</b></div>", unsafe_allow_html=True)
            for _, r in alerta_df.iterrows():
                st.warning(f"⚠️ Movil {r[col_movil]} - {r[col_dep]} - {r[col_km_act]} km / Le toca a los {r[col_prox]} km - Dominio {r[col_dom]}")
        else:
            st.success("🟢 Sin alertas por kilometraje")

        st.divider()

        # ===== GRAFICO =====
        graf = df_f["ESTADO HOY"].value_counts().reset_index()
        graf.columns=["Estado","Cantidad"]
        chart = alt.Chart(graf).mark_bar(cornerRadiusTopLeft=8, cornerRadiusTopRight=8).encode(
            x=alt.X('Estado:N', sort=['🟢 NORMAL','🟡 PRECARIO','🟡 ALERTA SERVI 10000','🔴 QRT','🔵 SERVI']),
            y='Cantidad:Q',
            color=alt.Color('Estado:N', scale=alt.Scale(domain=['🟢 NORMAL','🟡 PRECARIO','🔴 QRT','🔵 SERVI'], range=['#22c55e','#eab308','#ef4444','#3b82f6']), legend=None),
            tooltip=['Estado','Cantidad']
        )
        st.altair_chart(chart, use_container_width=True)

        # TABLA CON COLORES
        def pintar(fila):
            if "QRT" in fila["ESTADO HOY"]: return ['background-color: #fecaca']*len(fila)
            if "SERVI" in fila["ESTADO HOY"] and "ALERTA" not in fila["ESTADO HOY"]: return ['background-color: #bfdbfe']*len(fila)
            if "ALERTA" in fila["ESTADO HOY"]: return ['background-color: #fef9c3']*len(fila)
            return ['']*len(fila)

        st.dataframe(df_f.style.apply(pintar, axis=1), use_container_width=True, height=550)
