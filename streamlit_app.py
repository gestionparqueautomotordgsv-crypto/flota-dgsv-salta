import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title="DGSV - Flota", layout="wide", page_icon="🚔")

USUARIOS = {
    "admin": "dgsv2026",
    "jefe": "1234",
    "logistica": "log2026",
    "usuario1": "1111",
    "usuario2": "2222",
    "usuario3": "3333",
    "usuario4": "4444",
    "usuario5": "5555",
    "usuario6": "6666",
    "usuario7": "7777",
}

if "login" not in st.session_state:
    st.session_state.login = False

if not st.session_state.login:
    col1,col2,col3 = st.columns([1,2,1])
    with col2:
        st.title("🚔 Ingreso al Sistema")
        st.caption("Flota Policial - Acceso seguro")
        user = st.text_input("Usuario")
        pwd = st.text_input("Contraseña", type="password")
        if st.button("Iniciar sesión", type="primary", use_container_width=True):
            if user in USUARIOS and USUARIOS[user]==pwd:
                st.session_state.login=True
                st.session_state.usuario_actual=user
                st.rerun()
            else:
                st.error("Usuario o clave incorrecta")
    st.stop()

# --- APP ---
URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRO9kumGN6YMvBI_hGc-D9Lb8y29RqNubvkIN1gpgN6I8QKjZ2QBNQ3ItyVkLZeuw/pub?gid=1702506345&single=true&output=csv"

@st.cache_data(ttl=60)
def cargar():
    df = pd.read_csv(URL, dtype=str).fillna("")
    df.columns = [c.strip().upper() for c in df.columns]
    return df

def buscar_col(df, txt):
    for c in df.columns:
        if txt in c:
            return c
    return None

df_all = cargar()
col_tipo = buscar_col(df_all, "RUEDAS")
col_movil = buscar_col(df_all, "MOVIL")
col_dep = buscar_col(df_all, "DEPENDEN")
col_dom = buscar_col(df_all, "DOMINIO")
col_km_act = buscar_col(df_all, "KM ACTUAL")
col_prox = buscar_col(df_all, "PROXIMO")
cols_fecha = [c for c in df_all.columns if "/" in c]
col_estado = cols_fecha[-1] if cols_fecha else None

df_autos = df_all[df_all[col_tipo].str.contains("4", na=False)] if col_tipo else df_all
df_motos = df_all[df_all[col_tipo].str.contains("2", na=False)] if col_tipo else df_all

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
                    if km_act >= prox-1000: return f"🟡 ALERTA {prox}"
            except: pass
        if "PRECAR" in v: return "🟡 PRECARIO"
        return "🟢 NORMAL"

    if col_estado:
        df_f["ESTADO HOY"] = df_f.apply(estado_final, axis=1)
        qrt = len(df_f[df_f["ESTADO HOY"]=="🔴 QRT"])
        servi = len(df_f[df_f["ESTADO HOY"]=="🔵 SERVI"])
        alerta_df = df_f[df_f["ESTADO HOY"].str.contains("ALERTA")]
        alerta = len(alerta_df)

        # RESUMEN SEPARADO
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("🔴 QRT", qrt)
        c2.metric("🔵 SERVI", servi)
        c3.metric("🟡 POR VENCER", alerta)
        c4.metric("Total", len(df_f))

        if alerta>0:
            with st.expander(f"🟡 Ver {alerta} próximos al servi (a 1000km)", expanded=True):
                for _, r in alerta_df.iterrows():
                    st.write(f"⚠️ **{r[col_movil]}** - {r[col_dep]} - {r[col_km_act]}km / Toca {r[col_prox]}km - {r[col_dom]}")

        # GRAFICO
        graf = df_f["ESTADO HOY"].value_counts().reset_index()
        graf.columns=["Estado","Cantidad"]
        chart = alt.Chart(graf).mark_bar().encode(x='Estado:N', y='Cantidad:Q', color=alt.Color('Estado:N', legend=None))
        st.altair_chart(chart, use_container_width=True)

    st.dataframe(df_f, use_container_width=True, height=600)

# Header
ca,cb = st.columns([5,1])
ca.title(f"🚔 DGSV - {st.session_state.usuario_actual}")
if cb.button("Salir"):
    st.session_state.login=False
    st.rerun()

t1,t2 = st.tabs([f"🚔 4 RUEDAS ({len(df_autos)})", f"🏍️ MOTOS ({len(df_motos)})"])
with t1: panel(df_autos, "4 RUEDAS")
with t2: panel(df_motos, "MOTOS")
