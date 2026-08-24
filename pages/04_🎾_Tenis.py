import streamlit as st
import pandas as pd
from services import *

st.set_page_config(page_title="Tenis | MONEY QUANT BETTOR", page_icon="🎾", layout="wide")
st.title("🎾 Tenis")
st.caption("ATP / WTA | forma + H2H + ganador + Value")
sports=get_sports() if odds_api_key() else []
keys=[s.get('key') for s in sports if str(s.get('key','')).startswith('tennis_')] or ['tennis_atp','tennis_wta']
key=st.selectbox('Circuito',keys); events=get_odds(key,'us,eu') if odds_api_key() else []
if not events: st.warning('Configura ODDS_API_KEY para cargar partidos.'); st.stop()
labels={f"{e['home_team']} vs {e['away_team']} — {e['commence_time']}":e for e in events}; e=labels[st.selectbox('Partido',list(labels))]
st.subheader(f"{e['home_team']} vs {e['away_team']}")
def nums(s):
    try:return [float(x.strip()) for x in s.split(',') if x.strip()]
    except:return []
c1,c2=st.columns(2); a=nums(c1.text_input('Rendimiento jugador A últimos partidos')); b=nums(c2.text_input('Rendimiento jugador B últimos partidos'))
if a and b:
    p=tennis_projection(a,b); m=st.columns(4); m[0].metric('Fuerza A',f"{p['player_a_score']:.2f}"); m[1].metric('Fuerza B',f"{p['player_b_score']:.2f}"); m[2].metric('P(A)',f"{p['p_a']*100:.1f}%"); m[3].metric('P(B)',f"{p['p_b']*100:.1f}%")
    rows=[r for r in all_bookmaker_odds([e]) if r['market']=='h2h']; table=[]
    for r in rows:
        prob=p['p_a'] if r['selection']==e['home_team'] else p['p_b']; v=calculate_market_value(r['odds'],prob); table.append({'Bookmaker':r['bookmaker'],'Selección':r['selection'],'Cuota':r['odds'],'Prob.':prob*100,'Justa':v['fair_odds'],'Edge %':v['edge_points']*100,'EV %':v['expected_value']*100})
    if table: st.dataframe(pd.DataFrame(table).sort_values('EV %',ascending=False),use_container_width=True)
else: st.info('Introduce métricas históricas normalizadas para activar el modelo.')
st.markdown('### 🎯 Mercados')
st.write('Ganador • Sets • Juegos • Hándicap • Totales, según los mercados entregados por la API.')
