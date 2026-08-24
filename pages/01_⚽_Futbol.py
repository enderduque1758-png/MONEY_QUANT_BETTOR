import streamlit as st
import pandas as pd
from services import *

st.set_page_config(page_title="Fútbol | MONEY QUANT BETTOR", page_icon="⚽", layout="wide")
st.title("⚽ Fútbol")
st.caption("Partidos + H2H + forma + proyección + cuotas + IA")

sports = get_sports() if odds_api_key() else []
keys = [s.get("key") for s in sports if str(s.get("key","")).startswith("soccer_")] or ["soccer_epl"]
key = st.selectbox("Competición", keys)
events = get_odds(key, "us,eu") if odds_api_key() else []
if not events:
    st.warning("Configura ODDS_API_KEY para cargar partidos.")
    st.stop()
labels={f"{e['home_team']} vs {e['away_team']} — {e['commence_time']}":e for e in events}
e=labels[st.selectbox("Partido",list(labels))]
st.write(f"### {e['home_team']} vs {e['away_team']}")

info=football_fixture_enrichment(e['home_team'],e['away_team'])
if not info.get('ok'):
    st.error(info.get('error','No se pudo obtener H2H'))
    st.stop()

def totals(fs):
    out=[]
    for f in fs:
        h=f.get('goals',{}).get('home'); a=f.get('goals',{}).get('away')
        if isinstance(h,int) and isinstance(a,int): out.append(h+a)
    return out
h2h=totals(info['h2h']); home=totals(info['home_last']); away=totals(info['away_last'])
t1,t2,t3=st.tabs(['🤝 H2H','🏠 Local','✈️ Visitante'])
with t1: st.dataframe(pd.DataFrame(info['h2h']),use_container_width=True)
with t2: st.dataframe(pd.DataFrame(info['home_last']),use_container_width=True)
with t3: st.dataframe(pd.DataFrame(info['away_last']),use_container_width=True)
vals=h2h[-10:]+home[-5:]+away[-5:]
if vals:
    p=projection_from_samples(vals); expected=.7*p['mean']+.3*p['median']; line=st.number_input('Línea de goles',.5,8.5,2.5,.5)
    prob=poisson_over_probability(expected,line)
    c=st.columns(4); c[0].metric('Promedio',f"{p['mean']:.2f}"); c[1].metric('Proyección',f"{expected:.2f}"); c[2].metric('Over',f"{prob*100:.1f}%"); c[3].metric('Under',f"{(1-prob)*100:.1f}%")
    rows=all_bookmaker_odds([e]); rows=[r for r in rows if r['market']=='totals']
    table=[]
    for r in rows:
        v=calculate_market_value(r['odds'],prob); table.append({'Bookmaker':r['bookmaker'],'Selección':r['selection'],'Cuota':r['odds'],'Cuota justa':v['fair_odds'],'Edge %':v['edge_points']*100,'EV %':v['expected_value']*100})
    if table: st.dataframe(pd.DataFrame(table).sort_values('EV %',ascending=False),use_container_width=True)
else: st.info('No hay suficientes resultados históricos.')

st.info('La IA del panel principal puede validar esta proyección usando el contexto del partido y las cuotas.')
