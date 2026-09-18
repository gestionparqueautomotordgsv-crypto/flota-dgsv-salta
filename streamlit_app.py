import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title="DGSV - Flota", layout="wide", page_icon="🚔")

# ===== USUARIOS =====
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

if "login" not in st.session_state: st.session_state.login = False

if not st.session_state.login:
    st.markdown("""
    <style>.stApp{background:#1e293b;} h1{color:#fb923c;text-align:center;font-family:monospace;}</style>
    <h1>Ingreso al Sistema</h1>
    """, unsafe_allow_html=True)
    user = st.text_input("Usuario")
    pwd = st.text_input("Contraseña", type="password")
    if st.button("Iniciar sesión", type="primary", use_container_width=True):
        if user in USUARIOS and USUARIOS[user]==pwd:
            st.session_state.login=True; st.session_state.usuario_actual=user; st.rerun()
        else: st.error("Usuario o clave incorrecta")
    st.stop()

# ===== APP =====
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
col_km_act = buscar_col(df_all, "KM ACTUAL")
col_prox = buscar_col(df_all, "PROXIMO")
cols_fecha = [c for c in df_all.columns if "/" in c]
col_estado = cols_fecha[-1] if cols_fecha else None

df_autos = df_all[df_all[col_tipo].str.contains("4", na=False)] if col_tipo else df_all.head(19)
df_motos = df_all[df_all[col_tipo].str.contains("2", na=False)] if col_tipo else df_all.tail(85)

def panel(df, nombre):
    busc = st.text_input(f"🔍 Buscar {nombre}", placeholder="Ej: 2553, DGSV, RANGER", key=f"busc_{nombre}").upper()
    df_f = df.copy()
    if busc:
        df_f = df_f[df_f.apply(lambda r: busc in " ".join([str(x).upper() for x in r.values]), axis=1)]
        if len(df_f)==1:
            r=df_f.iloc[0]; st.success(f"✅ {r[col_movil]} {r[col_dep]} - DOM {r[col_dom]} - {r[col_estado] if col_estado else ''}")

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

    if col_estado and col_estado in df_f.columns:
        df_f["ESTADO HOY"] = df_f.apply(estado_final, axis=1)

        qrt = len(df_f[df_f["ESTADO HOY"]=="🔴 QRT"])
        servi = len(df_f[df_f["ESTADO HOY"]=="🔵 SERVI"])
        alerta = len(df_f[df_f["ESTADO HOY"].str.contains("ALERTA")])

        c1,c2,c3,c4 = st.columns(4)
        c1.markdown(f"<div style='background:#fecaca;padding:12px;border-radius:10px;text-align:center'>🔴 QRT<br><b style='font-size:26px'>{qrt}</b></div>", unsafe_allow_html=True)
        c2.markdown(f"<div style='background:#bfdbfe;padding:12px;border-radius:10px;text-align:center'>🔵 SERVI<br><b style='font-size:26px'>{servi}</b></div>", unsafe_allow_html=True)
        c3.markdown(f"<div style='background:#fef08a;padding:12px;border-radius:10px;text-align:center'>🟡 POR VENCER<br><b style='font-size:26px'>{alerta}</b></div>", unsafe_allow_html=True)
        c4.metric("Total", len(df_f))

        if qrt>0 or servi>0:
            st.info(f"Resumen {nombre}: {qrt} QRT - {servi} SERVI - {alerta} por vencer (a 1000km)")

        def pintar(fila):
            if "QRT" in fila["ESTADO HOY"]: return ['background-color: #fecaca']*len(fila)
            if "SERVI" in fila["ESTADO HOY"]: return ['background-color: #bfdbfe']*len(fila)
            if "ALERTA" in fila["ESTADO HOY"]: return ['background-color: #fef9c3']*len(fila)
            return ['']*len(fila)

        st.dataframe(df_f.style.apply(pintar, axis=1), use_container_width=True, height=550)

# Header
c_a,c_b = st.columns([4,1])
c_a.title(f"🚔 DGSV - {st.session_state.usuario_actual}")
if c_b.button("Salir"): st.session_state.login=False; st.rerun()

t1,t2 = st.tabs([f"🚔 4 RUEDAS ({len(df_autos)})", f"🏍️ MOTOS ({len(df_motos)})"])
with t1: panel(df_autos, "AUTOS")
with t2: panel(df_motos, "MOTOS")
