import json
import math
import pandas as pd
import streamlit as st
from services import *

st.set_page_config(page_title="MONEY QUANT BETTOR", page_icon="🏆", layout="wide", initial_sidebar_state="expanded")

st.title("🏆 MONEY QUANT BETTOR")
st.caption("Centro único de análisis: partidos • cuotas • H2H • estadísticas • proyección • Value • IA")

with st.sidebar:
    st.header("⚙️ Fuentes y filtros")
    sports = get_sports() if odds_api_key() else []
    sport_options = {s.get("title", s.get("key")): s.get("key") for s in sports} or {
        "⚽ Fútbol": "soccer_epl", "⚾ MLB": "baseball_mlb", "⚾ KBO": "baseball_kbo",
        "⚾ NPB": "baseball_npb", "🏀 NBA": "basketball_nba", "🎾 ATP": "tennis_atp", "🎾 WTA": "tennis_wta"
    }
    sport_label = st.selectbox("Deporte", list(sport_options))
    sport_key = sport_options[sport_label]
    regions = st.multiselect("Regiones de cuotas", ["us", "eu", "uk", "au"], ["us", "eu"])
    limit = st.slider("Partidos a analizar", 5, 50, 20)
    min_ev = st.slider("EV mínimo para recomendar", -0.20, 0.30, 0.02, 0.01)
    st.divider()
    st.markdown("**Secrets requeridos**")
    st.code("ODDS_API_KEY\nAPI_FOOTBALL_KEY\nSPORTS_API_KEY\nOPENAI_API_KEY\nOPENAI_MODEL", language="text")
    st.caption("No coloques claves directamente en app.py.")

@st.cache_data(ttl=60)
def load_events(key, reg):
    return get_odds(key, ",".join(reg))

@st.cache_data(ttl=300)
def load_football(home, away):
    return football_fixture_enrichment(home, away)

def nums(text):
    try:
        return [float(x.strip()) for x in text.split(",") if x.strip()]
    except Exception:
        return []

def safe_float(v, default=None):
    try:
        return float(v)
    except Exception:
        return default

def market_rows(event_rows, market):
    return [r for r in event_rows if r.get("market") == market]

def value_table(rows, probability, label):
    output = []
    for r in rows:
        odds = safe_float(r.get("odds"))
        if odds is None or odds <= 1:
            continue
        v = calculate_market_value(odds, probability)
        output.append({
            "Bookmaker": r.get("bookmaker"), "Selección": r.get("selection"), "Línea": r.get("point"),
            "Cuota": odds, "Mercado": label, "Prob. modelo": round(probability * 100, 2),
            "Cuota justa": round(v["fair_odds"], 3), "Edge": round(v["edge_points"] * 100, 2),
            "EV": round(v["expected_value"] * 100, 2),
        })
    return pd.DataFrame(output).sort_values("EV", ascending=False) if output else pd.DataFrame()

def render_recommendations(candidates, title="🎯 Recomendaciones"):
    st.subheader(title)
    if not candidates:
        st.warning("No hay una recomendación con datos suficientes.")
        return
    df = pd.DataFrame(candidates).sort_values(["EV", "Confianza"], ascending=False)
    primary = df.iloc[0]
    st.markdown("### 🥇 RECOMENDACIÓN PRINCIPAL")
    cols = st.columns(5)
    cols[0].metric("Mercado", str(primary["Mercado"]))
    cols[1].metric("Probabilidad", f"{primary['Probabilidad']:.1f}%")
    cols[2].metric("Cuota", f"{primary['Cuota']:.2f}")
    cols[3].metric("EV", f"{primary['EV']:.1f}%")
    cols[4].metric("Confianza", f"{primary['Confianza']:.1f}/10")
    if primary["EV"] > 0:
        st.success(f"🟢 VALUE BET — {primary['Mercado']} @ {primary['Cuota']:.2f} ({primary['Bookmaker']})")
    else:
        st.error("🔴 NO BET — el valor esperado no es positivo.")
    if len(df) > 1:
        st.markdown("### 🔵 OPCIONES ALTERNATIVAS")
        st.dataframe(df.iloc[1:8], use_container_width=True, hide_index=True)

# ===================== DATOS AUTOMÁTICOS =====================
events = load_events(sport_key, regions) if odds_api_key() else []
all_rows = all_bookmaker_odds(events)

st.subheader(f"📅 Partidos disponibles — {sport_label}")
if events:
    event_df = pd.DataFrame([{
        "Inicio": e.get("commence_time"), "Local": e.get("home_team"),
        "Visitante": e.get("away_team"), "ID": e.get("id")
    } for e in events[:limit]])
    st.dataframe(event_df, use_container_width=True, hide_index=True)
    labels = {f"{e.get('home_team')} vs {e.get('away_team')} — {e.get('commence_time')}": e for e in events[:limit]}
    selected = labels[st.selectbox("🔎 Selecciona un partido", list(labels))]
else:
    selected = {}
    st.warning("No hay eventos. Configura ODDS_API_KEY y verifica la cobertura del deporte.")

selected_rows = [r for r in all_rows if selected and r.get("event_id") == selected.get("id")]

# ===================== CABECERA DEL PARTIDO =====================
if selected:
    st.divider()
    a, b, c, d = st.columns(4)
    a.metric("🏠 Local", selected.get("home_team", "—"))
    b.metric("✈️ Visitante", selected.get("away_team", "—"))
    c.metric("🕐 Inicio", str(selected.get("commence_time", "—"))[:19])
    d.metric("💰 Cuotas", len(selected_rows))

    with st.expander("💰 Todas las cuotas del partido", expanded=True):
        if selected_rows:
            st.dataframe(pd.DataFrame(selected_rows), use_container_width=True, hide_index=True)
        else:
            st.info("No hay cuotas disponibles para este evento.")

# Contexto que se irá entregando a IA
analysis_context = {
    "sport": sport_label,
    "event": {
        "home": selected.get("home_team"), "away": selected.get("away_team"),
        "start": selected.get("commence_time"), "event_id": selected.get("id")
    },
    "bookmaker_odds": selected_rows,
    "statistical_model": {},
    "h2h": {},
    "form": {},
    "player_data": {},
    "risk_flags": []
}
candidates = []

# ===================== FÚTBOL =====================
if sport_key.startswith("soccer_") and selected:
    st.divider(); st.header("⚽ Análisis completo de fútbol")
    e = load_football(selected.get("home_team", ""), selected.get("away_team", ""))
    if e.get("ok"):
        def parse_results(fixtures):
            rows, totals = [], []
            for f in fixtures:
                g = f.get("goals", {}); t = f.get("teams", {})
                h, a = g.get("home"), g.get("away")
                if isinstance(h, int) and isinstance(a, int):
                    totals.append(h + a)
                    rows.append({"Fecha": f.get("fixture", {}).get("date"), "Local": t.get("home", {}).get("name"), "Visitante": t.get("away", {}).get("name"), "Marcador": f"{h}-{a}", "Total": h + a})
            return rows, totals
        hrows, htot = parse_results(e.get("h2h", [])); hrows2, htot2 = parse_results(e.get("home_last", [])); arows, atot = parse_results(e.get("away_last", []))
        tabs = st.tabs(["🤝 H2H", "🏠 Local", "✈️ Visitante", "📊 Resumen"])
        with tabs[0]: st.dataframe(pd.DataFrame(hrows), use_container_width=True, hide_index=True) if hrows else st.info("Sin H2H disponible")
        with tabs[1]: st.dataframe(pd.DataFrame(hrows2), use_container_width=True, hide_index=True) if hrows2 else st.info("Sin forma disponible")
        with tabs[2]: st.dataframe(pd.DataFrame(arows), use_container_width=True, hide_index=True) if arows else st.info("Sin forma disponible")
        with tabs[3]:
            summary = [{"Fuente": n, "Muestras": len(v), "Promedio": round(sum(v)/len(v), 2) if v else 0} for n, v in [("H2H", htot), ("Local", htot2), ("Visitante", atot)]]
            st.dataframe(pd.DataFrame(summary), use_container_width=True, hide_index=True)
        combined = htot[-10:] + htot2[-5:] + atot[-5:]
        analysis_context["h2h"] = {"games": hrows, "average_goals": round(sum(htot)/len(htot), 3) if htot else None}
        analysis_context["form"] = {"home_last_average_goals": round(sum(htot2)/len(htot2), 3) if htot2 else None, "away_last_average_goals": round(sum(atot)/len(atot), 3) if atot else None}
        if combined:
            p = projection_from_samples(combined)
            expected = .70 * p["mean"] + .30 * p["median"]
            line = st.number_input("Línea total de goles", 0.5, 8.5, 2.5, 0.5, key="soc_line")
            over = poisson_over_probability(expected, line)
            st.markdown("### 📐 Proyección")
            m = st.columns(5)
            m[0].metric("Promedio exacto", f"{p['mean']:.2f}"); m[1].metric("Mediana", f"{p['median']:.2f}"); m[2].metric("Proyección", f"{expected:.2f}"); m[3].metric(f"Over {line}", f"{over*100:.1f}%"); m[4].metric(f"Under {line}", f"{(1-over)*100:.1f}%")
            analysis_context["statistical_model"] = {"sample_count": p["count"], "mean": p["mean"], "median": p["median"], "projection": expected, "line": line, "over_probability": over, "under_probability": 1-over}
            over_rows = market_rows(selected_rows, "totals")
            dfv = value_table(over_rows, over, f"Over {line}")
            if not dfv.empty:
                st.markdown("### 💰 Value del mercado")
                st.dataframe(dfv, use_container_width=True, hide_index=True)
                for _, r in dfv.head(5).iterrows():
                    candidates.append({"Mercado": r["Mercado"], "Bookmaker": r["Bookmaker"], "Cuota": float(r["Cuota"]), "Probabilidad": float(r["Prob. modelo"]), "EV": float(r["EV"]), "Confianza": min(10, 5 + max(0, float(r["Edge"])) / 5)})
    else:
        analysis_context["risk_flags"].append("API-Football no disponible o equipos no encontrados")
        st.warning(e.get("error", "No se pudo enriquecer el partido."))

# ===================== BÉISBOL =====================
elif sport_key.startswith("baseball_") and selected:
    st.divider(); st.header("⚾ Análisis completo de béisbol")
    st.info("La arquitectura admite pitcher, bullpen, bateadores, H2H, 1ª entrada y primeras 5 entradas. Si una fuente no entrega esos campos, no se inventan.")
    with st.expander("📥 Datos estadísticos de respaldo", expanded=False):
        c1,c2,c3,c4 = st.columns(4)
        h = nums(c1.text_input("Carreras local últimos 10", key="bb_h")); a = nums(c2.text_input("Carreras visitante últimos 10", key="bb_a")); ha = nums(c3.text_input("Permitidas local", key="bb_ha")); aa = nums(c4.text_input("Permitidas visitante", key="bb_aa"))
    if h and a:
        bp = baseball_projection(h, a, ha, aa)
        line = st.number_input("Línea total de carreras", 0.5, 15.5, 8.5, .5, key="bb_line")
        probs = baseball_market_probs(bp, line)
        m=st.columns(5); m[0].metric("Local esperado",f"{bp['home_expected']:.2f}"); m[1].metric("Visitante esperado",f"{bp['away_expected']:.2f}"); m[2].metric("Total esperado",f"{bp['total_expected']:.2f}"); m[3].metric("Over",f"{probs['over']*100:.1f}%"); m[4].metric("Under",f"{probs['under']*100:.1f}%")
        analysis_context["statistical_model"] = {"projection": bp, "line": line, "over_probability": probs["over"], "under_probability": probs["under"]}
        dfv = value_table(market_rows(selected_rows, "totals"), probs["over"], f"Over {line}")
        if not dfv.empty:
            st.dataframe(dfv, use_container_width=True, hide_index=True)
            for _, r in dfv.head(5).iterrows(): candidates.append({"Mercado":r["Mercado"],"Bookmaker":r["Bookmaker"],"Cuota":float(r["Cuota"]),"Probabilidad":float(r["Prob. modelo"]),"EV":float(r["EV"]),"Confianza":min(10,5+max(0,float(r["Edge"])) / 5)})
    else:
        analysis_context["risk_flags"].append("Faltan datos históricos de carreras para el motor cuantitativo")

# ===================== BALONCESTO =====================
elif sport_key.startswith("basketball_") and selected:
    st.divider(); st.header("🏀 Análisis completo de baloncesto")
    with st.expander("📥 Datos estadísticos de respaldo", expanded=False):
        c1,c2=st.columns(2); team=nums(c1.text_input("Puntos equipo últimos 10",key="bk_team")); opp=nums(c2.text_input("Puntos rivales últimos 10",key="bk_opp"))
        pace=st.slider("Factor de ritmo", .80, 1.20, 1.00, .01)
    if team:
        bp=basketball_projection(team,opp,pace); line=st.number_input("Línea total de puntos",100.,300.,220.,1.,key="bk_line"); probs=basketball_market_probs(bp,line)
        m=st.columns(5); m[0].metric("Equipo",f"{bp['team_expected']:.1f}"); m[1].metric("Rival",f"{bp['opponent_expected']:.1f}"); m[2].metric("Total",f"{bp['total_expected']:.1f}"); m[3].metric("Over",f"{probs['over']*100:.1f}%"); m[4].metric("Under",f"{probs['under']*100:.1f}%")
        analysis_context["statistical_model"]={"projection":bp,"line":line,"over_probability":probs["over"],"under_probability":probs["under"],"pace_factor":pace}
        dfv=value_table(market_rows(selected_rows,"totals"),probs["over"],f"Over {line}")
        if not dfv.empty:
            st.dataframe(dfv,use_container_width=True,hide_index=True)
            for _,r in dfv.head(5).iterrows(): candidates.append({"Mercado":r["Mercado"],"Bookmaker":r["Bookmaker"],"Cuota":float(r["Cuota"]),"Probabilidad":float(r["Prob. modelo"]),"EV":float(r["EV"]),"Confianza":min(10,5+max(0,float(r["Edge"])) / 5)})
    else: analysis_context["risk_flags"].append("Faltan datos históricos de puntos")

# ===================== TENIS =====================
elif sport_key.startswith("tennis_") and selected:
    st.divider(); st.header("🎾 Análisis completo de tenis")
    with st.expander("📥 Datos estadísticos de respaldo", expanded=False):
        c1,c2=st.columns(2); pa=nums(c1.text_input("Rendimiento jugador A últimos partidos",key="ten_a")); pb=nums(c2.text_input("Rendimiento jugador B últimos partidos",key="ten_b"))
    if pa and pb:
        tp=tennis_projection(pa,pb); probs=tennis_market_probs(tp)
        m=st.columns(4); m[0].metric("Fuerza A",f"{tp['player_a_score']:.2f}"); m[1].metric("Fuerza B",f"{tp['player_b_score']:.2f}"); m[2].metric("P(A)",f"{tp['p_a']*100:.1f}%"); m[3].metric("P(B)",f"{tp['p_b']*100:.1f}%")
        analysis_context["statistical_model"]={"projection":tp,"player_a_probability":tp["p_a"],"player_b_probability":tp["p_b"]}
        rows=market_rows(selected_rows,"h2h")
        dfv=value_table(rows,tp["p_a"],"Ganador A")
        if not dfv.empty:
            st.dataframe(dfv,use_container_width=True,hide_index=True)
            for _,r in dfv.head(5).iterrows(): candidates.append({"Mercado":r["Mercado"],"Bookmaker":r["Bookmaker"],"Cuota":float(r["Cuota"]),"Probabilidad":float(r["Prob. modelo"]),"EV":float(r["EV"]),"Confianza":min(10,5+max(0,float(r["Edge"])) / 5)})
    else: analysis_context["risk_flags"].append("Faltan datos de rendimiento de los jugadores")

# ===================== RECOMENDACIONES AUTOMÁTICAS =====================
if candidates:
    st.divider()
    filtered=[x for x in candidates if x["EV"] >= min_ev*100]
    render_recommendations(filtered or candidates, "🎯 Recomendaciones matemáticas")

# ===================== IA ÚNICA =====================
st.divider()
st.header("🤖 IA — Proyección y recomendaciones finales")
st.caption("La IA recibe automáticamente el partido, cuotas, H2H, forma y resultados del modelo calculados arriba. No debe inventar datos.")

if st.button("🧠 ANALIZAR TODO CON IA", type="primary", use_container_width=True):
    with st.spinner("La IA está cruzando cuotas + estadísticas + H2H + proyección + Value..."):
        try:
            # Añadimos las candidatas ya calculadas para que la IA compare mercados reales.
            analysis_context["candidate_markets"] = candidates
            result = ai_validate({**analysis_context, "instruction": "Selecciona una recomendación PRINCIPAL y hasta 5 OPCIONALES. Usa solo datos presentes. Si faltan datos críticos, marca SIN APUESTA."})
            if not result.get("ok"):
                st.error(result.get("error", "IA no configurada"))
            else:
                raw = result.get("text", "")
                try:
                    ai = json.loads(raw)
                    st.session_state["ai_result"] = ai
                except Exception:
                    st.session_state["ai_result"] = {"raw": raw}
        except Exception as ex:
            st.error(f"Error conectando con IA: {ex}")

if "ai_result" in st.session_state:
    ai = st.session_state["ai_result"]
    if "raw" in ai:
        st.code(ai["raw"], language="json")
    else:
        st.markdown("### 🥇 RECOMENDACIÓN PRINCIPAL")
        c=st.columns(5)
        c[0].metric("Mercado",str(ai.get("mercado_recomendado","SIN APUESTA")))
        c[1].metric("Prob. IA",f"{safe_float(ai.get('probabilidad_ia'),0):.1f}%")
        c[2].metric("Cuota justa",f"{safe_float(ai.get('cuota_justa'),0):.2f}")
        c[3].metric("Confianza",f"{safe_float(ai.get('confianza'),0):.1f}/10")
        c[4].metric("EV",str(ai.get("expected_value","—")))
        principal = str(ai.get("mercado_recomendado","SIN APUESTA"))
        if principal.upper() == "SIN APUESTA": st.error("🔴 IA: SIN APUESTA — datos insuficientes o sin valor.")
        else: st.success(f"🟢 IA recomienda: {principal}")
        st.markdown("### 🔵 OPCIONES OPCIONALES")
        optional = ai.get("opciones_opcionales", ai.get("alternativas", []))
        if isinstance(optional, list) and optional:
            st.dataframe(pd.DataFrame(optional), use_container_width=True, hide_index=True)
        elif optional:
            st.write(optional)
        else:
            st.info("La IA no encontró alternativas suficientemente sólidas.")
        st.markdown("### 📊 Justificación")
        st.write(ai.get("razonamiento", "Sin razonamiento devuelto."))
        st.markdown("### ⚠️ Riesgos")
        st.write(ai.get("riesgos", "Sin riesgos devueltos."))
        st.markdown("### 🔍 Datos usados")
        st.json({"modelo": analysis_context.get("statistical_model", {}), "H2H": analysis_context.get("h2h", {}), "forma": analysis_context.get("form", {}), "candidatas": candidates})

st.divider()
st.caption("⚠️ MONEY QUANT BETTOR estima probabilidades y valor esperado; no garantiza resultados. Una recomendación solo debe considerarse cuando los datos sean suficientes y exista valor positivo.")
