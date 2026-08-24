import json
import math
import statistics
import streamlit as st
import pandas as pd

from services import (
    ai_validate, all_bookmaker_odds, calculate_market_value,
    football_h2h, get_odds, get_sports, odds_api_key,
    projection_from_samples,
)

st.set_page_config(page_title="MONEY QUANT BETTOR", page_icon="🏆", layout="wide")
st.title("🏆 MONEY QUANT BETTOR")
st.caption("Cuotas + H2H + forma + proyección estadística + Value + IA")

with st.sidebar:
    st.header("⚙️ Configuración")
    sports = get_sports() if odds_api_key() else []
    options = {s.get("title", s.get("key")): s.get("key") for s in sports}
    if not options:
        options = {"Fútbol": "soccer_epl", "NBA": "basketball_nba", "MLB": "baseball_mlb", "Tenis ATP": "tennis_atp"}
    sport_label = st.selectbox("Deporte", list(options))
    sport_key = options[sport_label]
    regions = st.multiselect("Regiones de cuotas", ["us", "eu", "uk", "au"], ["us", "eu"])
    limit = st.slider("Partidos", 5, 50, 20)
    st.markdown("**Secrets requeridos**")
    st.code("ODDS_API_KEY\nAPI_FOOTBALL_KEY\nOPENAI_API_KEY\nOPENAI_MODEL", language="text")

@st.cache_data(ttl=60)
def load_events(key, reg):
    return get_odds(key, ",".join(reg))

def implied(odds):
    try:
        o = float(odds)
        return 1 / o if o > 1 else None
    except Exception:
        return None

def poisson_cdf(k, lam):
    return sum(math.exp(-lam) * lam**i / math.factorial(i) for i in range(k + 1))

def poisson_over(lam, line):
    return max(0, min(1, 1 - poisson_cdf(math.floor(line), lam)))

def build_projection(samples, line):
    s = projection_from_samples(samples)
    mean = s["mean"]
    # Blend mean with median to reduce sensitivity to outliers.
    center = 0.7 * mean + 0.3 * s["median"]
    p_over = poisson_over(center, line) if center > 0 else 0
    return {**s, "projection": center, "p_over": p_over, "p_under": 1 - p_over}

events = load_events(sport_key, regions) if odds_api_key() else []
all_rows = all_bookmaker_odds(events)

st.subheader(f"📅 Partidos — {sport_label}")
if events:
    st.dataframe(pd.DataFrame([{
        "Inicio": e.get("commence_time"), "Local": e.get("home_team"), "Visitante": e.get("away_team"), "ID": e.get("id")
    } for e in events[:limit]]), use_container_width=True, hide_index=True)
else:
    st.warning("No hay eventos. Configura ODDS_API_KEY y comprueba la cobertura del deporte.")

st.subheader("💰 Comparador de bookmakers")
if all_rows:
    odds_df = pd.DataFrame(all_rows)
    pivot = odds_df.pivot_table(index=["event_id","home","away","market","selection","point"], columns="bookmaker", values="odds", aggfunc="max").reset_index()
    cols = [c for c in pivot.columns if c not in {"event_id","home","away","market","selection","point"}]
    if cols:
        pivot["Mejor cuota"] = pivot[cols].max(axis=1, skipna=True)
        pivot["Prob. implícita"] = pivot["Mejor cuota"].apply(implied)
        st.dataframe(pivot.sort_values("Mejor cuota", ascending=False), use_container_width=True, hide_index=True)
else:
    st.info("No se recibieron cuotas del proveedor.")

st.divider()
st.subheader("🔎 Partido y análisis")
selected_event = {}
if events:
    labels = {f"{e.get('home_team')} vs {e.get('away_team')} — {e.get('commence_time')}": e for e in events[:limit]}
    selected_event = labels[st.selectbox("Selecciona partido", list(labels))]

if selected_event:
    a,b,c = st.columns(3)
    a.metric("Local", selected_event.get("home_team", "—"))
    b.metric("Visitante", selected_event.get("away_team", "—"))
    c.metric("Inicio", selected_event.get("commence_time", "—"))

    selected_rows = [r for r in all_rows if r.get("event_id") == selected_event.get("id")]
    if selected_rows:
        st.dataframe(pd.DataFrame(selected_rows), use_container_width=True, hide_index=True)

st.divider()
st.subheader("📐 Proyección automática")
st.caption("Esta pantalla ya calcula la proyección desde muestras. En las siguientes fuentes estadísticas, esas muestras se cargarán automáticamente por equipo/jugador.")
raw = st.text_input("Datos históricos (opcional, mientras se conectan las fuentes)", placeholder="8, 9, 7, 10, 11, 8, 9")
line = st.number_input("Línea a evaluar", min_value=0.0, value=8.5, step=0.5)
projection = {}
if raw:
    try:
        samples = [float(x.strip()) for x in raw.split(",") if x.strip()]
        projection = build_projection(samples, line)
        c1,c2,c3,c4,c5 = st.columns(5)
        c1.metric("Promedio exacto", f"{projection['mean']:.2f}")
        c2.metric("Mediana", f"{projection['median']:.2f}")
        c3.metric("Desv. estándar", f"{projection['stdev']:.2f}")
        c4.metric("Proyección", f"{projection['projection']:.2f}")
        c5.metric(f"P(Over {line})", f"{projection['p_over']*100:.1f}%")
    except ValueError:
        st.error("Usa números separados por comas.")

st.divider()
st.subheader("🤝 H2H de fútbol")
if sport_key.startswith("soccer_"):
    x,y = st.columns(2)
    team_a = x.number_input("ID equipo A (API-Football)", min_value=0, step=1)
    team_b = y.number_input("ID equipo B (API-Football)", min_value=0, step=1)
    if team_a and team_b:
        h2h = football_h2h(int(team_a), int(team_b), 10)
        if h2h:
            rows=[]; totals=[]
            for f in h2h:
                t=f.get("teams",{}); g=f.get("goals",{}); gh,ga=g.get("home"),g.get("away")
                rows.append({"Fecha":f.get("fixture",{}).get("date"),"Local":t.get("home",{}).get("name"),"Visitante":t.get("away",{}).get("name"),"Marcador":f"{gh}-{ga}"})
                if isinstance(gh,int) and isinstance(ga,int): totals.append(gh+ga)
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
            if totals:
                h=projection_from_samples(totals)
                st.metric("Promedio exacto H2H — goles", f"{h['mean']:.2f}")
        else:
            st.info("No se encontraron H2H o falta API_FOOTBALL_KEY.")

st.divider()
st.subheader("🎯 Value Scanner")
if selected_event and selected_rows and projection:
    value_rows=[]
    for r in selected_rows:
        o=r.get("odds")
        if not isinstance(o,(int,float)): continue
        market=str(r.get("market"))
        if market == "totals":
            p = projection['p_over'] if str(r.get('selection','')).lower().startswith('over') else projection['p_under']
            v=calculate_market_value(o,p)
            value_rows.append({**r,"Prob. modelo":p,"Cuota justa":v['fair_odds'],"Edge":v['edge_points'],"EV":v['expected_value']})
    if value_rows:
        vdf=pd.DataFrame(value_rows).sort_values("EV",ascending=False)
        st.dataframe(vdf,use_container_width=True,hide_index=True)
        best=vdf.iloc[0]
        if float(best["EV"]) > 0:
            st.success(f"🟢 VALUE: {best['selection']} @ {best['odds']:.2f} — EV {best['EV']*100:.1f}%")
        else:
            st.warning("🔴 NO BET: no se detecta valor positivo con la proyección actual.")
else:
    st.info("Selecciona un partido e introduce datos históricos para activar el Value Scanner.")

st.divider()
st.subheader("🤖 Validación IA")
ai_payload={"sport":sport_label,"event":{"home":selected_event.get("home_team"),"away":selected_event.get("away_team"),"start":selected_event.get("commence_time")},"odds":selected_rows if selected_event else [],"projection":projection,"h2h_note":"H2H debe proceder de fuente real; no inventar datos."}
if st.button("🧠 Validar proyección con IA", type="primary"):
    try:
        result=ai_validate(ai_payload)
        if result.get("ok"):
            try:
                parsed=json.loads(result.get("text",""))
                c1,c2,c3,c4=st.columns(4)
                c1.metric("Mercado",parsed.get("mercado_recomendado","SIN APUESTA"))
                c2.metric("Prob. IA",f"{float(parsed.get('probabilidad_ia',0)):.1f}%")
                c3.metric("Cuota justa",f"{float(parsed.get('cuota_justa',0)):.2f}")
                c4.metric("Confianza",f"{float(parsed.get('confianza',0)):.1f}/10")
                st.write("**Edge:**",parsed.get("edge")); st.write("**EV:**",parsed.get("expected_value"))
                st.write("**Razonamiento:**",parsed.get("razonamiento")); st.write("**Riesgos:**",parsed.get("riesgos"))
            except Exception: st.code(result.get("text",""),language="json")
        else: st.error(result.get("error","Error de IA"))
    except Exception as exc: st.error(f"Error conectando con IA: {exc}")

st.caption("⚠️ Las estimaciones no garantizan resultados. Una apuesta debe considerarse solo cuando el modelo tenga datos suficientes y el precio ofrezca valor.")
