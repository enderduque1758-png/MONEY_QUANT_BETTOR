import streamlit as st
import pandas as pd
from services import *

st.set_page_config(page_title="Béisbol | MONEY QUANT BETTOR", page_icon="⚾", layout="wide")
st.title("⚾ Béisbol")
st.caption("MLB • KBO • NPB | carreras + proyección + mercados")

sports=get_sports() if odds_api_key() else []
keys=[s.get('key') for s in sports if str(s.get('key','')).startswith('baseball_')] or ['baseball_mlb','baseball_kbo','baseball_npb']
key=st.selectbox('Liga',keys)
events=get_odds(key,'us,eu') if odds_api_key() else []
if not events: st.warning('Configura ODDS_API_KEY para cargar partidos.'); st.stop()
labels={f"{e['home_team']} vs {e['away_team']} — {e['commence_time']}":e for e in events}; e=labels[st.selectbox('Partido',list(labels))]
st.subheader(f"{e['home_team']} vs {e['away_team']}")
c1,c2,c3,c4=st.columns(4)
def nums(s):
    try:return [float(x.strip()) for x in s.split(',') if x.strip()]
    except:return []
h=c1.text_input('Carreras local últimos 10'); a=c2.text_input('Carreras visitante últimos 10'); ha=c3.text_input('Permitidas local'); aa=c4.text_input('Permitidas visitante')
h,a,ha,aa=nums(h),nums(a),nums(ha),nums(aa)
if h and a:
    p=baseball_projection(h,a,ha,aa); line=st.number_input('Total carreras',.5,15.5,8.5,.5); pr=baseball_market_probs(p,line)
    m=st.columns(5); m[0].metric('Local esperado',f"{p['home_expected']:.2f}"); m[1].metric('Visitante esperado',f"{p['away_expected']:.2f}"); m[2].metric('Total',f"{p['total_expected']:.2f}"); m[3].metric('Over',f"{pr['over']*100:.1f}%"); m[4].metric('Under',f"{pr['under']*100:.1f}%")
    rows=[r for r in all_bookmaker_odds([e]) if r['market']=='totals']; table=[]
    for r in rows:
        v=calculate_market_value(r['odds'],pr['over']); table.append({'Bookmaker':r['bookmaker'],'Selección':r['selection'],'Cuota':r['odds'],'Justa':v['fair_odds'],'Edge %':v['edge_points']*100,'EV %':v['expected_value']*100})
    if table: st.dataframe(pd.DataFrame(table).sort_values('EV %',ascending=False),use_container_width=True)
else: st.info('Introduce datos históricos para completar el motor cuantitativo.')
st.markdown('### 🎯 Mercados preparados')
st.write('Ganador • Run Line • Total • 1ª entrada • Primeras 5 entradas • Carreras por equipo.')
