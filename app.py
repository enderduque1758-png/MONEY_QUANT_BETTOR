import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import requests

st.title("🏆 Panel IA + Casas de Apuestas")
st.subheader("Dashboard Multi‑Mercado con Value Bets")

# ---------------------------
# Funciones para APIs (ejemplo)
# ---------------------------
def obtener_cuotas_betfair(market_id):
    url = "https://api.betfair.com/exchange/betting/rest/v1.0/listMarketBook/"
    headers = {"X-Application": "YOUR_APP_KEY", "X-Authentication": "YOUR_SESSION_TOKEN"}
    payload = {"marketIds": [market_id], "priceProjection": {"priceData": ["EX_BEST_OFFERS"]}}
    r = requests.post(url, headers=headers, json=payload)
    return r.json() if r.status_code == 200 else None

def obtener_cuotas_bet365(event_id):
    url = f"https://api.bet365.com/v1/event/{event_id}/odds"
    headers = {"Authorization": "Bearer YOUR_TOKEN"}
    r = requests.get(url, headers=headers)
    return r.json() if r.status_code == 200 else None

def obtener_cuotas_pinnacle(sport_id, league_id):
    url = f"https://api.pinnacle.com/v1/odds?sportId={sport_id}&leagueId={league_id}"
    headers = {"Authorization": "Basic YOUR_API_KEY"}
    r = requests.get(url, headers=headers)
    return r.json() if r.status_code == 200 else None

# ---------------------------
# Datos de ejemplo (simulados)
# ---------------------------
mercados = {
    "OVER 2.5": {"cuota": 1.85, "prob_ia": 0.61},
    "UNDER 2.5": {"cuota": 1.90, "prob_ia": 0.39},
    "BTTS": {"cuota": 1.75, "prob_ia": 0.62},
    "Chelsea Gana": {"cuota": 2.20, "prob_ia": 0.45},
    "Fulham Gana": {"cuota": 3.00, "prob_ia": 0.35},
    "Hándicap Asiático -1.5 Chelsea": {"cuota": 2.50, "prob_ia": 0.42},
    "Corners +10.5": {"cuota": 1.95, "prob_ia": 0.55},
    "Tarjetas +4.5": {"cuota": 2.10, "prob_ia": 0.48}
}

# ---------------------------
# Función para ranking
# ---------------------------
def generar_ranking(mercados, filtro=None):
    ranking = []
    for mercado, datos in mercados.items():
        if filtro and filtro not in mercado:
            continue
        cuota = datos["cuota"]
        prob_ia = datos["prob_ia"]
        prob_imp = 1 / cuota
        diferencia = prob_ia - prob_imp
        ranking.append({"Mercado": mercado, "Prob IA": prob_ia, "Prob Implícita": prob_imp, "Diferencia": diferencia})
    return pd.DataFrame(ranking).sort_values(by="Diferencia", ascending=False).head(5)

# ---------------------------
# Tabs principales
# ---------------------------
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "Populares", "Más/Menos", "BTTS", "Hándicap Asiático", 
    "Corners", "Tarjetas", "Especiales"
])

# Populares
with tab1:
    st.write("📊 Top Value Bets Populares")
    df_pop = generar_ranking(mercados)
    st.dataframe(df_pop)
    fig, ax = plt.subplots()
    sns.barplot(data=df_pop, x="Mercado", y="Diferencia", palette="coolwarm", ax=ax)
    plt.xticks(rotation=45)
    st.pyplot(fig)

# Más/Menos
with tab2:
    st.write("📊 Over/Under")
    df_ou = generar_ranking(mercados, filtro="OVER")
    st.dataframe(df_ou)

# BTTS
with tab3:
    st.write("📊 Ambos Marcan (BTTS)")
    df_btts = generar_ranking(mercados, filtro="BTTS")
    st.dataframe(df_btts)

# Hándicap Asiático
with tab4:
    st.write("📊 Hándicap Asiático")
    df_handicap = generar_ranking(mercados, filtro="Hándicap")
    st.dataframe(df_handicap)

# Corners
with tab5:
    st.write("📊 Tiros de Esquina")
    df_corners = generar_ranking(mercados, filtro="Corners")
    st.dataframe(df_corners)

# Tarjetas
with tab6:
    st.write("📊 Tarjetas")
    df_cards = generar_ranking(mercados, filtro="Tarjetas")
    st.dataframe(df_cards)

# Especiales
with tab7:
    st.write("📊 Especiales")
    df_specials = generar_ranking(mercados, filtro="Especiales")
    st.dataframe(df_specials)

# ---------------------------
# Gráfico comparativo IA vs Casas
# ---------------------------
st.subheader("🏅 Comparación IA vs Casas de Apuestas")
mercado = "OVER 2.5"
prob_ia = 0.61
cuotas = {"Betfair": 1.85, "Bet365": 1.80, "Pinnacle": 1.88}
prob_imp = {casa: 1/cuota for casa, cuota in cuotas.items()}

df_comp = pd.DataFrame({
    "Fuente": ["IA"] + list(prob_imp.keys()),
    "Probabilidad": [prob_ia] + list(prob_imp.values())
})

fig, ax = plt.subplots(figsize=(7,5))
sns.barplot(data=df_comp, x="Fuente", y="Probabilidad", palette="viridis", ax=ax)
ax.set_title(f"Comparación Prob IA vs Casas de Apuestas ({mercado})")
ax.set_ylabel("Probabilidad")
st.pyplot(fig)
