import streamlit as st
import pandas as pd
from services import *

st.set_page_config(page_title="Baloncesto | MONEY QUANT BETTOR", page_icon="🏀", layout="wide")
st.title("🏀 Baloncesto")
st.caption("NBA y otras ligas | puntos + ritmo + total + Value")
sports=get_sports() if odds_api_key() else []
keys=[s.get('key') for s in sports if str(s.get('key','')).startswith('basketball_')] or ['basketball_nba']
key=st.selectbox('Liga',keys); events=get_odds(key,'us,eu') if odds_api_key() else []
if not events: st.warning('Configura ODDS_API_KEY para cargar partidos.'); st.stop()
labels={f"{e['home_team']} vs {e['away_team']} — {e['commence_time']}":e for e in events}; e=labels[st.selectbox('Partido',list(labels))]
st.subheader(f"{e['home_team']} vs {e['away_team']}")
def nums(s):
    try:return [float(x.strip()) for x in s.split(',') if x.strip()]
    except:return []
c1,c2,c3=st.columns(3); team=nums(c1.text_input('Puntos equipo últimos 10')); opp=nums(c2.text_input('Puntos rivales últimos 10')); pace=c3.slider('Factor de ritmo',.8,1.2,1.,.01)
if team:
    p=basketball_projection(team,opp,pace); line=st.number_input('Total puntos',100.,300.,220.,1.); pr=basketball_market_probs(p,line)
    m=st.columns(5); m[0].metric('Equipo',f"{p['team_expected']:.1f}"); m[1].metric('Rival',f"{p['opponent_expected']:.1f}"); m[2].metric('Total',f"{p['total_expected']:.1f}"); m[3].metric('Over',f"{pr['over']*100:.1f}%"); m[4].metric('Under',f"{pr['under']*100:.1f}%")
    rows=[r for r in all_bookmaker_odds([e]) if r['market']=='totals']; table=[]
    for r in rows:
        v=calculate_market_value(r['odds'],pr['over']); table.append({'Bookmaker':r['bookmaker'],'Selección':r['selection'],'Cuota':r['odds'],'Justa':v['fair_odds'],'Edge %':v['edge_points']*100,'EV %':v['expected_value']*100})
    if table: st.dataframe(pd.DataFrame(table).sort_values('EV %',ascending=False),use_container_width=True)
else: st.info('Introduce puntos históricos para activar la proyección.')
st.markdown('### 🎯 Mercados')
st.write('Ganador • Spread • Total • Puntos de equipo • Props de jugadores cuando la fuente estadística esté conectada.')
