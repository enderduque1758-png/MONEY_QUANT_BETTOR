import streamlit as st
import pandas as pd
from services import *

st.set_page_config(page_title='Top Picks | MONEY QUANT BETTOR', page_icon='🏆', layout='wide')
st.title('🏆 TOP PICKS')
st.caption('Datos históricos → proyección → probabilidad → cuota justa → Edge → EV')

sports=get_sports() if odds_api_key() else []
keys={s.get('title',s.get('key')):s.get('key') for s in sports} or {'⚽ Fútbol':'soccer_epl','⚾ MLB':'baseball_mlb','⚾ KBO':'baseball_kbo','⚾ NPB':'baseball_npb','🏀 NBA':'basketball_nba','🎾 ATP':'tennis_atp','🎾 WTA':'tennis_wta'}
selected=st.multiselect('Deportes',list(keys),list(keys)[:1])
min_ev=st.slider('EV mínimo (%)',-10.0,30.0,2.0,0.5)
rows=[]

for label in selected:
    key=keys[label]; events=get_odds(key,'us,eu') if odds_api_key() else []
    for e in events:
        home,away=e.get('home_team',''),e.get('away_team',''); odds_rows=all_bookmaker_odds([e])
        model_rows=[]
        try:
            if key.startswith('soccer_') and football_api_key():
                info=football_fixture_enrichment(home,away)
                if info.get('ok'):
                    vals=[]
                    for fs in (info.get('h2h',[])[-10:],info.get('home_last',[])[-5:],info.get('away_last',[])[-5:]):
                        for f in fs:
                            h=f.get('goals',{}).get('home'); a=f.get('goals',{}).get('away')
                            if isinstance(h,int) and isinstance(a,int): vals.append(h+a)
                    if len(vals)>=5:
                        s=projection_from_samples(vals); expected=.7*s['mean']+.3*s['median']
                        for line in (1.5,2.5,3.5): model_rows.append(('totals',line,poisson_over_probability(expected,line),len(vals),expected))
            elif key.startswith('baseball_') or key.startswith('basketball_'):
                info=auto_projection_for_event(key,home,away)
                if info.get('ok'):
                    p=info['projection']; n=len(info['samples']['home_scored'])+len(info['samples']['away_scored'])
                    if key.startswith('baseball_'):
                        for line in (7.5,8.5,9.5): model_rows.append(('totals',line,poisson_over_probability(p['total_expected'],line),n,p['total_expected']))
                    else:
                        for line in (210.5,220.5,230.5): model_rows.append(('totals',line,basketball_market_probs(p,line)['over'],n,p['total_expected']))
        except Exception: continue
        for r in odds_rows:
            if r.get('market')!='totals' or r.get('point') is None: continue
            try: point=float(r['point']); odds=float(r['odds'])
            except: continue
            for _,line,over,n,expected in model_rows:
                if abs(point-line)>0.01: continue
                selection=str(r.get('selection','')).lower(); prob=over if 'over' in selection else (1-over if 'under' in selection else None)
                if prob is None: continue
                v=calculate_market_value(odds,prob)
                rows.append({'Deporte':label,'Partido':f'{home} vs {away}','Bookmaker':r.get('bookmaker'),'Selección':r.get('selection'),'Línea':point,'Cuota':odds,'Prob. modelo %':prob*100,'Cuota justa':v['fair_odds'],'Edge %':v['edge_points']*100,'EV %':v['expected_value']*100,'Muestras':n,'Proyección':expected,'Estado':'🟢 VALUE' if v['expected_value']>0 else '🔴 NO BET'})

if rows:
    df=pd.DataFrame(rows).sort_values(['EV %','Edge %','Prob. modelo %'],ascending=False)
    value=df[df['EV %']>=min_ev]
    if value.empty: st.warning('🔴 SIN APUESTA: ninguna oportunidad supera el EV mínimo.')
    else:
        best=value.iloc[0]; st.success(f"🥇 PRINCIPAL: {best['Partido']} — {best['Selección']} @ {best['Cuota']:.2f} | Prob. {best['Prob. modelo %']:.1f}% | Edge {best['Edge %']:.1f}% | EV {best['EV %']:.1f}%")
        st.subheader('🥇 Recomendación principal')
        st.dataframe(pd.DataFrame([best]),use_container_width=True,hide_index=True)
        st.subheader('🔵 Opciones opcionales')
        st.dataframe(value.iloc[1:6],use_container_width=True,hide_index=True)
        st.subheader('📊 Ranking completo')
        st.dataframe(df.head(100),use_container_width=True,hide_index=True)
else:
    st.warning('No hay oportunidades modeladas. Configura las APIs y verifica la cobertura histórica.')

st.divider(); st.caption('La aplicación no inventa estadísticas: si el proveedor no devuelve datos suficientes, la oportunidad queda fuera del ranking. Las probabilidades son estimaciones y no garantizan resultados.')
