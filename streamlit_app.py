def panel(df, nombre):
    busc = st.text_input(f"🔍 Buscar {nombre}", key=f"busc_{nombre}").upper()
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
                    if km_act >= prox-1000: return "🟡 ALERTA_KM" # lo usamos solo para alerta, no para gráfico
            except: pass
        if "PRECAR" in v: return "🟡 PRECARIO"
        return "🟢 NORMAL"

    def estado_grafico(val):
        # Para el gráfico, la alerta por km cuenta como NORMAL, no como barra aparte
        if "ALERTA" in val: return "🟢 NORMAL"
        return val

    if col_estado:
        df_f["ESTADO HOY"] = df_f.apply(estado_final, axis=1)
        df_f["ESTADO GRAFICO"] = df_f["ESTADO HOY"].apply(estado_grafico)

        qrt = len(df_f[df_f["ESTADO HOY"]=="🔴 QRT"])
        servi = len(df_f[df_f["ESTADO HOY"]=="🔵 SERVI"])
        normal = len(df_f[df_f["ESTADO GRAFICO"]=="🟢 NORMAL"])
        precario = len(df_f[df_f["ESTADO GRAFICO"]=="🟡 PRECARIO"])
        alerta_df = df_f[df_f["ESTADO HOY"]=="🟡 ALERTA_KM"]
        alerta = len(alerta_df)

        # TOTALES COMO PEDISTE
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("🔴 QRT", qrt)
        c2.metric("🔵 SERVI", servi)
        c3.metric("🟢 NORMAL", normal)
        c4.metric("Total", len(df_f))

        # ALERTA AMARILLA SEPARADA ABAJO
        if alerta>0:
            st.warning(f"🟡 ALERTA: {alerta} próximos al servi (a 1000km)")
            with st.expander(f"Ver {alerta} motos", expanded=True):
                for _, r in alerta_df.iterrows():
                    st.write(f"⚠️ **{r[col_movil]}** - {r[col_km_act]}km / Toca {r[col_prox]}km - {r[col_dom]} - {r[col_dep]}")

        # GRAFICO SIN ALERTA
        graf = df_f["ESTADO GRAFICO"].value_counts().reset_index()
        graf.columns=["Estado","Cantidad"]
        # Orden fijo: NORMAL, QRT, PRECARIO, SERVI
        order = ["🟢 NORMAL", "🔴 QRT", "🟡 PRECARIO", "🔵 SERVI"]
        chart = alt.Chart(graf).mark_bar().encode(
            x=alt.X('Estado:N', sort=order),
            y='Cantidad:Q',
            color=alt.Color('Estado:N', scale=alt.Scale(domain=order, range=['#22c55e','#ef4444','#eab308','#3b82f6']), legend=None),
            tooltip=['Estado','Cantidad']
        )
        st.altair_chart(chart, use_container_width=True)

    st.dataframe(df_f.drop(columns=["ESTADO GRAFICO"], errors='ignore'), use_container_width=True, height=550)
