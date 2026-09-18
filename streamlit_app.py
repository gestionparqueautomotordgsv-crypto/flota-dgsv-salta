import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title="DGSV - Flota", layout="wide", page_icon="🚔")
URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRO9kumGN6YMvBI_hGc-D9Lb8y29RqNubvkIN1gpgN6I8QKjZ2QBNQ3ItyVkLZeuw/pub?gid=1702506345&single=true&output=csv"

@st.cache_data(ttl=60)
def cargar():
    df = pd.read_csv(URL, dtype=str).fillna("")
    df.columns = [c.strip().upper() for c in df.columns]
    return df

def buscar_col(df, txt):
    for c in df.columns:
        if txt in c: return c
    return None

df_all = cargar()
col_tipo = buscar_col(df_all, "RUEDAS")
col_movil = buscar_col(df_all, "MOVIL")
col_dep = buscar_col(df_all, "DEPENDEN")
col_dom = buscar_col(df_all, "DOMINIO")
col_km = buscar_col(df_all, "KM ACTUAL")
col_prox = buscar_col(df_all, "PROXIMO")
cols_fecha = [c for c in df_all.columns if "/" in c]
col_estado = cols_fecha[-1] if cols_fecha else None

df_autos = df_all[df_all[col_tipo].str.contains("4", na=False)] if col_tipo else df_all.head(19)
df_motos = df_all[df_all[col_tipo].str.contains("2", na=False)] if col_tipo else df_all.tail(85)

def panel(df, nombre):
    if df.empty: return
    
    # 1 - BUSCADOR
    busc = st.text_input(f"🔍 Buscar en {nombre} (Movil, Dominio, Marca)", key=f"busc_{nombre}").upper()
    df_f = df.copy()
    if busc:
        df_f = df_f[df_f.apply(lambda r: busc in str(r[col_movil]).upper() + str(r[col_dom]).upper() + str(r.to_string()).upper(), axis=1)]

    # Filtro dependencia
    if col_dep and col_dep in df.columns:
        deps = ["TODOS"] + sorted([x for x in df[col_dep].unique() if x!=""])
        sel = st.selectbox(f"Filtro Dependencia {nombre}", deps, key=f"dep_{nombre}")
        if sel!="TODOS":
            df_f = df_f[df_f[col_dep]==sel]

    if col_estado and col_estado in df_f.columns:
        def sem(v):
            v=str(v).upper()
            if "SERVI" in v or "TALLER" in v: return "🔵 SERVI"
            if "QRT" in v: return "🔴 QRT"
            if "PRECAR" in v: return "🟡 PRECARIO"
            return "🟢 NORMAL"
        df_f["ESTADO HOY"] = df_f[col_estado].apply(sem)
        
        c1,c2,c3,c4,c5 = st.columns(5)
        c1.metric("Total", len(df_f))
        c2.metric("🟢 NORMAL", len(df_f[df_f["ESTADO HOY"].str.contains("NORMAL")]))
        c3.metric("🟡 PRECARIO", len(df_f[df_f["ESTADO HOY"].str.contains("PRECARIO")]))
        c4.metric("🔴 QRT", len(df_f[df_f["ESTADO HOY"].str.contains("QRT")]))
        c5.metric("🔵 SERVI", len(df_f[df_f["ESTADO HOY"].str.contains("SERVI")]))

        graf = df_f["ESTADO HOY"].value_counts().reset_index()
        graf.columns=["Estado","Cantidad"]
        chart = alt.Chart(graf).mark_bar().encode(
            x=alt.X('Estado:N', sort=['🟢 NORMAL','🟡 PRECARIO','🔴 QRT','🔵 SERVI']),
            y='Cantidad:Q',
            color=alt.Color('Estado:N', scale=alt.Scale(domain=['🟢 NORMAL','🟡 PRECARIO','🔴 QRT','🔵 SERVI'], range=['#22c55e','#eab308','#ef4444','#3b82f6']), legend=None),
            tooltip=['Estado','Cantidad']
        )
        st.altair_chart(chart, use_container_width=True)

        # 2 - BOTON QRT PARA WHATSAPP
        df_qrt = df_f[df_f["ESTADO HOY"].str.contains("QRT|SERVI")]
        if not df_qrt.empty:
            st.error(f"🔴 {len(df_qrt)} en QRT/SERVI")
            txt_wsp = f"*PARTE QRT/SERVI - {nombre} - {col_estado}*\n\n"
            for _, r in df_qrt.iterrows():
                txt_wsp += f"• {r[col_movil]} - {r[col_dep]} - {r[col_estado]} - DOM: {r[col_dom]}\n"
            st.text_area("Texto listo para WhatsApp", txt_wsp, height=150, key=f"wsp_{nombre}")
            st.download_button(f"📥 Descargar lista QRT {nombre}", txt_wsp, file_name=f"QRT_{nombre}.txt", key=f"down_{nombre}")

    st.dataframe(df_f, use_container_width=True, height=600)

st.title("🚔 DGSV - Flota")
t1, t2 = st.tabs([f"🚔 MOVILES ({len(df_autos)})", f"🏍️ MOTOS ({len(df_motos)})"])
with t1: panel(df_autos, "MOVILES 19")
with t2: panel(df_motos, "MOTOS 85")

if st.button("🔄 Actualizar"): 
    st.cache_data.clear()
    st.rerun()
