import json
import math
import pandas as pd
import streamlit as st

from services import (
    ai_validate,
    all_bookmaker_odds,
    calculate_market_value,
    football_fixture_enrichment,
    get_odds,
    get_sports,
    odds_api_key,
    projection_from_samples,
    summarize_football_results,
)

st.set_page_config(page_title="MONEY QUANT BETTOR", page_icon="🏆", layout="wide")
st.title("🏆 MONEY QUANT BETTOR")
st.caption("Cuotas + H2H + forma automática + proyección + Value + IA")

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
    st.markdown("**Secrets**")
    st.code("ODDS_API_KEY\nAPI_FOOTBALL_KEY\nOPENAI_API_KEY\nOPENAI_MODEL", language="text")
    st.caption("Nunca pongas claves reales dentro del código o GitHub.")

@st.cache_data(ttl=60)
def load_events(key, reg):
    return get_odds(key, ",".join(reg))

@st.cache_data(ttl=300)
def load_football_enrichment(home, away):
    return football_fixture_enrichment(home, away)

def implied(odds):
    try:
        o = float(odds)
        return 1 / o if o > 1 else None
    except Exception:
        return None

def poisson_cdf(k, lam):
    return sum(math.exp(-lam) * lam ** i / math.factorial(i) for i in range(k + 1))

def poisson_over(lam, line):
    return max(0.0, min(1.0, 1 - poisson_cdf(math.floor(line), lam)))

def build_projection(samples, line):
    s = projection_from_samples(samples)
    center = 0.7 * s["mean"] + 0.3 * s["median"]
    p_over = poisson_over(center, line) if center > 0 else 0.0
    return {**s, "projection": center, "p_over": p_over, "p_under": 1 - p_over}

def result_rows(fixtures):
    rows = []
    totals = []
    for f in fixtures:
        t, g = f.get("teams", {}), f.get("goals", {})
        gh, ga = g.get("home"), g.get("away")
        if isinstance(gh, int) and isinstance(ga, int):
            totals.append(gh + ga)
            rows.append({
                "Fecha": f.get("fixture", {}).get("date"),
                "Local": t.get("home", {}).get("name"),
                "Visitante": t.get("away", {}).get("name"),
                "Marcador": f"{gh}-{ga}",
                "Total goles": gh + ga,
            })
    return rows, totals

events = load_events(sport_key, regions) if odds_api_key() else []
all_rows = all_bookmaker_odds(events)

st.subheader(f"📅 Partidos — {sport_label}")
if events:
    st.dataframe(pd.DataFrame([{
        "Inicio": e.get("commence_time"), "Local": e.get("home_team"),
        "Visitante": e.get("away_team"), "ID": e.get("id")
    } for e in events[:limit]]), use_container_width=True, hide_index=True)
else:
    st.warning("No hay eventos. Configura ODDS_API_KEY y comprueba la cobertura del deporte.")

st.subheader("💰 Comparador de bookmakers")
if all_rows:
    odds_df = pd.DataFrame(all_rows)
    pivot = odds_df.pivot_table(
        index=["event_id", "home", "away", "market", "selection", "point"],
        columns="bookmaker", values="odds", aggfunc="max"
    ).reset_index()
    book_cols = [c for c in pivot.columns if c not in {"event_id", "home", "away", "market", "selection", "point"}]
    if book_cols:
        pivot["Mejor cuota"] = pivot[book_cols].max(axis=1, skipna=True)
        pivot["Prob. implícita"] = pivot["Mejor cuota"].apply(implied)
        st.dataframe(pivot.sort_values("Mejor cuota", ascending=False), use_container_width=True, hide_index=True)
else:
    st.info("No se recibieron cuotas del proveedor.")

st.divider()
st.subheader("🔎 Partido y análisis")
selected_event = {}
selected_rows = []
enrichment = {}
if events:
    labels = {f"{e.get('home_team')} vs {e.get('away_team')} — {e.get('commence_time')}": e for e in events[:limit]}
    selected_event = labels[st.selectbox("Selecciona partido", list(labels))]

if selected_event:
    a, b, c = st.columns(3)
    a.metric("Local", selected_event.get("home_team", "—"))
    b.metric("Visitante", selected_event.get("away_team", "—"))
    c.metric("Inicio", selected_event.get("commence_time", "—"))
    selected_rows = [r for r in all_rows if r.get("event_id") == selected_event.get("id")]
    if selected_rows:
        st.dataframe(pd.DataFrame(selected_rows), use_container_width=True, hide_index=True)

    # ---------------- AUTOMATIC FOOTBALL DATA ----------------
    if sport_key.startswith("soccer_"):
        st.markdown("### ⚽ Datos automáticos del partido")
        enrichment = load_football_enrichment(selected_event.get("home_team", ""), selected_event.get("away_team", ""))
        if enrichment.get("ok"):
            home = enrichment["teams"]["home"]
            away = enrichment["teams"]["away"]
            x, y = st.columns(2)
            x.metric("ID API-Football local", home.get("id", "—"))
            y.metric("ID API-Football visitante", away.get("id", "—"))

            hrows, htotals = result_rows(enrichment.get("h2h", []))
            hlast_rows, hlast_totals = result_rows(enrichment.get("home_last", []))
            alast_rows, alast_totals = result_rows(enrichment.get("away_last", []))

            tabs = st.tabs(["🤝 H2H", "🏠 Últimos local", "✈️ Últimos visitante", "📊 Resumen"])
            with tabs[0]:
                if hrows:
                    st.dataframe(pd.DataFrame(hrows), use_container_width=True, hide_index=True)
                    hs = projection_from_samples(htotals)
                    m1, m2, m3 = st.columns(3)
                    m1.metric("H2H — promedio goles", f"{hs['mean']:.2f}")
                    m2.metric("H2H — mediana", f"{hs['median']:.2f}")
                    m3.metric("H2H — partidos", hs["count"])
                else:
                    st.info("No hay H2H disponible.")
            with tabs[1]:
                if hlast_rows:
                    st.dataframe(pd.DataFrame(hlast_rows), use_container_width=True, hide_index=True)
                    s = projection_from_samples(hlast_totals)
                    st.metric("Promedio de goles últimos partidos local", f"{s['mean']:.2f}")
                else:
                    st.info("No hay partidos recientes disponibles.")
            with tabs[2]:
                if alast_rows:
                    st.dataframe(pd.DataFrame(alast_rows), use_container_width=True, hide_index=True)
                    s = projection_from_samples(alast_totals)
                    st.metric("Promedio de goles últimos partidos visitante", f"{s['mean']:.2f}")
                else:
                    st.info("No hay partidos recientes disponibles.")
            with tabs[3]:
                hsum = summarize_football_results(enrichment.get("h2h", []))
                home_sum = summarize_football_results(enrichment.get("home_last", []))
                away_sum = summarize_football_results(enrichment.get("away_last", []))
                st.dataframe(pd.DataFrame([
                    {"Fuente": "H2H", "Partidos": hsum["matches"], "Promedio total goles": round(hsum["avg_total_goals"], 2)},
                    {"Fuente": "Últimos local", "Partidos": home_sum["matches"], "Promedio total goles": round(home_sum["avg_total_goals"], 2)},
                    {"Fuente": "Últimos visitante", "Partidos": away_sum["matches"], "Promedio total goles": round(away_sum["avg_total_goals"], 2)},
                ]), use_container_width=True, hide_index=True)
        else:
            st.warning(enrichment.get("error", "No se pudo cargar API-Football."))

# ---------------- PROJECTION ----------------
st.divider()
st.subheader("📐 Proyección automática")
projection = {}
line = st.number_input("Línea a evaluar", min_value=0.0, value=2.5 if sport_key.startswith("soccer_") else 8.5, step=0.5)

# For football, automatically build samples from H2H + recent team games.
auto_samples = []
if enrichment.get("ok") and sport_key.startswith("soccer_"):
    _, h2h_totals = result_rows(enrichment.get("h2h", []))
    _, home_totals = result_rows(enrichment.get("home_last", []))
    _, away_totals = result_rows(enrichment.get("away_last", []))
    # Recency/source weights are applied as repeated observations rather than pretending the sources are independent.
    auto_samples = h2h_totals[-10:] + home_totals[-5:] + away_totals[-5:]

if auto_samples:
    projection = build_projection(auto_samples, line)
    st.success(f"Se cargaron automáticamente {len(auto_samples)} observaciones históricas.")
else:
    raw = st.text_input("Datos históricos manuales (fallback)", placeholder="2, 3, 1, 4, 2, 3")
    if raw:
        try:
            samples = [float(x.strip()) for x in raw.split(",") if x.strip()]
            projection = build_projection(samples, line)
        except ValueError:
            st.error("Usa números separados por comas.")

if projection:
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Promedio exacto", f"{projection['mean']:.2f}")
    c2.metric("Mediana", f"{projection['median']:.2f}")
    c3.metric("Desv. estándar", f"{projection['stdev']:.2f}")
    c4.metric("Proyección", f"{projection['projection']:.2f}")
    c5.metric(f"P(Over {line})", f"{projection['p_over'] * 100:.1f}%")

# ---------------- VALUE SCANNER ----------------
st.divider()
st.subheader("🎯 Value Scanner")
value_rows = []
if selected_event and selected_rows and projection:
    for r in selected_rows:
        try:
            odds = float(r.get("odds"))
        except (TypeError, ValueError):
            continue
        if str(r.get("market")) != "totals":
            continue
        selection = str(r.get("selection", ""))
        p = projection["p_over"] if selection.lower().startswith("over") else projection["p_under"]
        v = calculate_market_value(odds, p)
        value_rows.append({**r, "Prob. modelo": p, "Cuota justa": v["fair_odds"], "Edge": v["edge_points"], "EV": v["expected_value"]})

if value_rows:
    vdf = pd.DataFrame(value_rows).sort_values("EV", ascending=False)
    st.dataframe(vdf, use_container_width=True, hide_index=True)
    best = vdf.iloc[0]
    if float(best["EV"]) > 0:
        st.success(f"🟢 VALUE: {best['selection']} @ {best['odds']:.2f} — EV {best['EV'] * 100:.1f}%")
    else:
        st.warning("🔴 NO BET: no hay EV positivo con los datos actuales.")
else:
    st.info("No hay suficientes datos/proyección/mercado total para ejecutar el Value Scanner.")

# ---------------- AI ----------------
st.divider()
st.subheader("🤖 Validación IA")
ai_payload = {
    "sport": sport_label,
    "event": {"home": selected_event.get("home_team"), "away": selected_event.get("away_team"), "start": selected_event.get("commence_time")},
    "odds": selected_rows,
    "automatic_statistics": enrichment,
    "projection": projection,
}
if st.button("🧠 Validar proyección con IA", type="primary"):
    try:
        result = ai_validate(ai_payload)
        if result.get("ok"):
            try:
                parsed = json.loads(result.get("text", ""))
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Mercado", parsed.get("mercado_recomendado", "SIN APUESTA"))
                c2.metric("Prob. IA", f"{float(parsed.get('probabilidad_ia', 0)):.1f}%")
                c3.metric("Cuota justa", f"{float(parsed.get('cuota_justa', 0)):.2f}")
                c4.metric("Confianza", f"{float(parsed.get('confianza', 0)):.1f}/10")
                st.write("**Edge:**", parsed.get("edge"))
                st.write("**EV:**", parsed.get("expected_value"))
                st.write("**Razonamiento:**", parsed.get("razonamiento"))
                st.write("**Riesgos:**", parsed.get("riesgos"))
            except Exception:
                st.code(result.get("text", ""), language="json")
        else:
            st.error(result.get("error", "Error de IA"))
    except Exception as exc:
        st.error(f"Error conectando con IA: {exc}")

st.caption("⚠️ Las estimaciones no garantizan resultados. El sistema debe marcar SIN APUESTA cuando los datos sean insuficientes o el precio no ofrezca valor.")
