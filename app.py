import json
import math
from datetime import datetime

import pandas as pd
import streamlit as st

from services import (
    ai_validate,
    extract_bookmaker_odds,
    football_fixture,
    football_fixture_players,
    football_h2h,
    get_odds,
    get_sports,
    odds_api_key,
)

st.set_page_config(page_title="MONEY QUANT BETTOR", page_icon="🏆", layout="wide")

st.title("🏆 MONEY QUANT BETTOR")
st.caption("Motor cuantitativo: cuotas + H2H + estadísticas + enfrentamientos + validación IA")

with st.sidebar:
    st.header("⚙️ Configuración")
    sports = get_sports() if odds_api_key() else []
    sport_options = {s.get("title", s.get("key")): s.get("key") for s in sports}
    if not sport_options:
        sport_options = {
            "Fútbol": "soccer_epl",
            "NBA": "basketball_nba",
            "MLB": "baseball_mlb",
            "Tenis ATP/WTA": "tennis_atp",
        }
    sport_label = st.selectbox("Deporte", list(sport_options.keys()))
    sport_key = sport_options[sport_label]
    regions = st.multiselect("Regiones de cuotas", ["us", "eu", "uk", "au"], ["us", "eu"])
    limit = st.slider("Partidos a mostrar", 5, 50, 15)
    st.info("Configura ODDS_API_KEY, API_FOOTBALL_KEY y OPENAI_API_KEY como Secrets/variables de entorno. Nunca publiques las claves en GitHub.")


def implied_probability(odds):
    try:
        return 1 / float(odds) if float(odds) > 1 else None
    except (TypeError, ValueError, ZeroDivisionError):
        return None


def fair_odds(prob):
    return 1 / prob if prob and prob > 0 else None


def h2h_summary(h2h):
    rows = []
    for item in h2h:
        teams = item.get("teams", {})
        goals = item.get("goals", {})
        rows.append({
            "Fecha": item.get("fixture", {}).get("date"),
            "Local": teams.get("home", {}).get("name"),
            "Visitante": teams.get("away", {}).get("name"),
            "Marcador": f"{goals.get('home', '-')}-{goals.get('away', '-')}",
        })
    return pd.DataFrame(rows)


def calculate_score(odds, model_prob=None):
    imp = implied_probability(odds)
    if imp is None:
        return None
    if model_prob is None:
        return {"prob": imp, "fair": fair_odds(imp), "edge": 0}
    edge = model_prob - imp
    return {"prob": model_prob, "fair": fair_odds(model_prob), "edge": edge}

# --------------------
# Partidos y cuotas
# --------------------
if st.button("🔄 Actualizar partidos y cuotas", type="primary"):
    st.cache_data.clear()

@st.cache_data(ttl=60)
def load_odds(key, reg):
    return get_odds(key, ",".join(reg))

events = load_odds(sport_key, regions) if odds_api_key() else []
rows = extract_bookmaker_odds(events)

if not rows:
    st.warning("No hay cuotas de Betano/RushBet disponibles con la configuración actual. El panel queda listo para mostrar los datos cuando la API/proveedor los entregue.")
else:
    odds_df = pd.DataFrame(rows)
    event_keys = odds_df[["event_id", "home", "away", "start"]].drop_duplicates().head(limit)
    st.subheader(f"📅 Partidos — {sport_label}")
    st.dataframe(event_keys, use_container_width=True, hide_index=True)

    st.subheader("💰 Comparador Betano vs RushBet")
    pivot = odds_df.pivot_table(index=["event_id", "home", "away", "market", "selection", "point"], columns="bookmaker", values="odds", aggfunc="max").reset_index()
    if "Betano" not in pivot.columns and "RushBet" not in pivot.columns:
        st.info("El proveedor no devolvió todavía nombres de bookmaker compatibles. Revisa la cobertura de tu proveedor de cuotas.")
    else:
        for col in ["Betano", "RushBet"]:
            if col not in pivot.columns:
                pivot[col] = float("nan")
        pivot["Mejor cuota"] = pivot[["Betano", "RushBet"]].max(axis=1, skipna=True)
        pivot["Prob. implícita"] = pivot["Mejor cuota"].apply(implied_probability)
        st.dataframe(pivot.sort_values("Mejor cuota", ascending=False), use_container_width=True, hide_index=True)

# --------------------
# Explorador de partido
# --------------------
st.divider()
st.header("🔎 Análisis profundo de un partido")

if rows:
    event_df = pd.DataFrame(rows)[["event_id", "home", "away", "start"]].drop_duplicates()
    labels = {f"{r.home} vs {r.away} — {r.start}": r.event_id for r in event_df.itertuples()}
    selected_label = st.selectbox("Selecciona el partido", list(labels))
    event_id = labels[selected_label]
    selected_event = next((e for e in events if e.get("id") == event_id), {})
else:
    st.info("Carga cuotas para seleccionar un partido real.")
    selected_event = {}

c1, c2, c3 = st.columns(3)
with c1:
    st.metric("Local", selected_event.get("home_team", "—"))
with c2:
    st.metric("Visitante", selected_event.get("away_team", "—"))
with c3:
    st.metric("Inicio", selected_event.get("commence_time", "—"))

# H2H solo cuando tenemos IDs de API-Football configurados y el deporte es fútbol.
if sport_key.startswith("soccer_") and selected_event and st.button("📊 Cargar H2H / enfrentamientos"):
    st.warning("Para H2H de fútbol se necesita API-Football y los IDs de sus equipos. El proveedor de cuotas no siempre comparte esos IDs.")
    st.caption("Puedes introducir los IDs de API-Football para enlazar el partido con su histórico H2H.")
    a, b = st.columns(2)
    team_a = a.number_input("ID equipo local API-Football", min_value=0, step=1)
    team_b = b.number_input("ID equipo visitante API-Football", min_value=0, step=1)
    if team_a and team_b:
        h2h = football_h2h(int(team_a), int(team_b), 10)
        df_h2h = h2h_summary(h2h)
        if not df_h2h.empty:
            st.dataframe(df_h2h, use_container_width=True, hide_index=True)
            scores = []
            for x in h2h:
                g = x.get("goals", {})
                if isinstance(g.get("home"), int) and isinstance(g.get("away"), int):
                    scores.append(g["home"] + g["away"])
            if scores:
                st.metric("Promedio exacto de goles H2H", f"{sum(scores) / len(scores):.2f}")
        else:
            st.info("No se encontraron H2H.")

# --------------------
# IA
# --------------------
st.divider()
st.header("🤖 Validación IA")

ai_payload = {
    "sport": sport_label,
    "event": {
        "home": selected_event.get("home_team"),
        "away": selected_event.get("away_team"),
        "start": selected_event.get("commence_time"),
    },
    "odds": extract_bookmaker_odds([selected_event]) if selected_event else [],
    "method": "Validar solamente datos suministrados; no inventar estadísticas.",
}

if st.button("🧠 Validar proyección más probable con IA", type="primary"):
    with st.spinner("Analizando cuotas, mercado y datos disponibles..."):
        try:
            result = ai_validate(ai_payload)
            if result.get("ok"):
                st.success("Validación IA completada")
                st.code(result.get("text", ""), language="json")
            else:
                st.error(result.get("error", "Error de IA"))
        except Exception as exc:
            st.error(f"No fue posible validar con IA: {exc}")

st.divider()
st.caption("⚠️ Las probabilidades son estimaciones estadísticas, no garantías. Verifica reglas, disponibilidad de mercados y cobertura de cada proveedor antes de apostar.")
