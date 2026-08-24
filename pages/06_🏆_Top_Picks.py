import streamlit as st
import pandas as pd
from services import *

st.set_page_config(page_title='Top Picks | MONEY QUANT BETTOR', page_icon='🏆', layout='wide')
st.title('🏆 TOP PICKS')
st.caption('Ranking de oportunidades disponibles por EV y probabilidad')

sports = get_sports() if odds_api_key() else []
keys = {s.get('title',s.get('key')):s.get('key') for s in sports} or {'⚽ Fútbol':'soccer_epl','⚾ MLB':'baseball_mlb','🏀 NBA':'basketball_nba','🎾 ATP':'tennis_atp'}
selected = st.multiselect('Deportes', list(keys), list(keys)[:1])
rows=[]
for label in selected:
    events=get_odds(keys[label],'us,eu') if odds_api_key() else []
    for e in events:
        for r in all_bookmaker_odds([e]):
            try:
                odds=float(r['odds'])
                if odds>1: rows.append({'Deporte':label,'Partido':f"{e['home_team']} vs {e['away_team']}",'Bookmaker':r['bookmaker'],'Mercado':r['market'],'Selección':r['selection'],'Cuota':odds,'Prob. implícita':1/odds*100})
            except: pass
if rows:
    df=pd.DataFrame(rows).sort_values('Prob. implícita',ascending=False)
    st.dataframe(df.head(50),use_container_width=True,hide_index=True)
    st.info('El ranking de valor requiere proyección estadística por partido; no se presenta una cuota como apuesta recomendada sin probabilidad modelada.')
else:
    st.warning('Configura ODDS_API_KEY para cargar oportunidades.')