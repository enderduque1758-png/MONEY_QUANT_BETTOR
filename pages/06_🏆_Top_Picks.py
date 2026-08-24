import json
import streamlit as st
import pandas as pd
from services import *

st.set_page_config(page_title='Top Picks | MONEY QUANT BETTOR', page_icon='🏆', layout='wide')
st.title('🏆 TOP PICKS + IA')
st.caption('Datos → modelo → cuota justa → Edge → EV → IA → recomendación principal y opcionales')

sports=get_sports() if odds_api_key() else []
keys={s.get('title',s.get('key')):s.get('key') for s in sports} or {'⚽ Fútbol':'soccer_epl','⚾ MLB':'baseball_mlb','⚾ KBO':'baseball_kbo','⚾ NPB':'baseball_npb','🏀 NBA':'basketball_nba','🎾 ATP':'tennis_atp','🎾 WTA':'tennis_wta'}
selected=st.multiselect('Deportes',list(keys),list(keys)[:1])
min_ev=st.slider('EV mínimo (%)',-10.0,30.0,2.0,0.5)
ai_enabled=bool(os.getenv('OPENAI_API_KEY','').strip())
rows=[]

for label in selected:
    key=keys[label]; events=get_odds(key,'us,eu') if odds_api_key() else []
    for e in events:
        home,away=e.get('home_team',''),e.get('away_team',''); odds_rows=all_bookmaker_odds([e]); model_rows=[]; model_context={}
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
                        s=projection_from_samples(vals); expected=.7*s['mean']+.3*s['median']; model_context={'fuente':'API-Football','muestras':len(vals),'promedio':s['mean'],'mediana':s['median'],'proyeccion':expected,'h2h':len(info.get('h2h',[])),'local_ultimos':len(info.get('home_last',[])),'visitante_ultimos':len(info.get('away_last',[]))}
                        for line in (1.5,2.5,3.5): model_rows.append(('totals',line,poisson_over_probability(expected,line),len(vals),expected))
            elif key.startswith('baseball_') or key.startswith('basketball_'):
                info=auto_projection_for_event(key,home,away)
                if info.get('ok'):
                    p=info['projection']; n=len(info['samples']['home_scored'])+len(info['samples']['away_scored']); model_context={'fuente':'API-Sports','muestras':n,'proyeccion':p}
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
                rows.append({'Deporte':label,'Partido':f'{home} vs {away}','Bookmaker':r.get('bookmaker'),'Selección':r.get('selection'),'Línea':point,'Cuota':odds,'Prob. modelo %':prob*100,'Cuota justa':v['fair_odds'],'Edge %':v['edge_points']*100,'EV %':v['expected_value']*100,'Muestras':n,'Proyección':expected,'Estado':'🟢 VALUE' if v['expected_value']>0 else '🔴 NO BET','_context':model_context,'_event':e})

if rows:
    df=pd.DataFrame(rows).sort_values(['EV %','Edge %','Prob. modelo %'],ascending=False)
    value=df[df['EV %']>=min_ev].copy()
    if value.empty: st.warning('🔴 SIN APUESTA: ninguna oportunidad supera el EV mínimo.')
    else:
        # Automatic AI validation for the best candidate plus up to 5 alternatives.
        candidates=value.head(6).copy(); ai_results=[]
        if ai_enabled:
            with st.spinner('🤖 Validando automáticamente las mejores oportunidades con IA...'):
                for idx,row in candidates.iterrows():
                    payload={'deporte':row['Deporte'],'partido':row['Partido'],'mercado':row['Selección'],'linea':row['Línea'],'cuota':row['Cuota'],'probabilidad_modelo':row['Prob. modelo %'],'cuota_justa':row['Cuota justa'],'edge':row['Edge %'],'ev':row['EV %'],'muestras':row['Muestras'],'proyeccion':row['Proyección'],'contexto_historico':row['_context'],'cuotas_disponibles':all_bookmaker_odds([row['_event']]),'regla':'No inventar datos. Si faltan datos críticos, responder SIN APUESTA. Validar, no reemplazar, los cálculos del modelo.'}
                    try:
                        result=ai_validate(payload); parsed={}
                        if result.get('ok'):
                            text=result.get('text','').strip()
                            try: parsed=json.loads(text)
                            except: parsed={'razonamiento':text}
                        ai_results.append((idx,parsed))
                    except Exception as ex: ai_results.append((idx,{'error':str(ex)}))
            for idx,p in ai_results:
                candidates.loc[idx,'IA confianza']=p.get('confianza','-'); candidates.loc[idx,'IA probabilidad']=p.get('probabilidad_ia','-'); candidates.loc[idx,'IA decisión']=p.get('mercado_recomendado','SIN APUESTA'); candidates.loc[idx,'IA riesgos']=p.get('riesgos','-'); candidates.loc[idx,'IA razonamiento']=p.get('razonamiento','-')
            # IA can reject a candidate, but cannot invent a positive EV: mathematical EV remains mandatory.
            accepted=[]
            for idx,row in candidates.iterrows():
                p=next((x[1] for x in ai_results if x[0]==idx),{})
                decision=str(p.get('mercado_recomendado','')).upper()
                try: conf=float(p.get('confianza',0))
                except: conf=0
                accepted.append(idx if decision not in ('SIN APUESTA','NO BET','NO_APUESTA') and conf>=5 else None)
            accepted=[x for x in accepted if x is not None]
            if accepted: best=candidates.loc[accepted].sort_values(['EV %','Edge %'],ascending=False).iloc[0]
            else: best=candidates.iloc[0]
        else: best=candidates.iloc[0]

        st.success(f"🥇 PRINCIPAL: {best['Partido']} — {best['Selección']} @ {best['Cuota']:.2f} | Prob. {best['Prob. modelo %']:.1f}% | Edge {best['Edge %']:.1f}% | EV {best['EV %']:.1f}%")
        c=st.columns(6); c[0].metric('Prob. modelo',f"{best['Prob. modelo %']:.1f}%"); c[1].metric('Cuota justa',f"{best['Cuota justa']:.2f}"); c[2].metric('Mejor cuota',f"{best['Cuota']:.2f}"); c[3].metric('Edge',f"{best['Edge %']:.1f}%"); c[4].metric('EV',f"{best['EV %']:.1f}%"); c[5].metric('Muestras',int(best['Muestras']))
        if ai_enabled and 'IA decisión' in best.index:
            st.subheader('🤖 Validación IA')
            a,b,c,d=st.columns(4); a.metric('Decisión IA',str(best.get('IA decisión','SIN APUESTA'))); b.metric('Prob. IA',str(best.get('IA probabilidad','-'))); c.metric('Confianza',f"{best.get('IA confianza','-')}/10"); d.metric('Estado','🟢 VALIDADA' if str(best.get('IA decisión','')).upper() not in ('SIN APUESTA','NO BET') else '🔴 NO BET')
            st.write('**Razonamiento:**',best.get('IA razonamiento','-')); st.write('**Riesgos:**',best.get('IA riesgos','-'))
        elif not ai_enabled: st.warning('OPENAI_API_KEY no configurada: se muestra solo el modelo matemático.')

        st.subheader('🔵 Opciones opcionales')
        optional=candidates[candidates.index!=best.name].head(5).copy()
        display_cols=[x for x in ['Deporte','Partido','Bookmaker','Selección','Línea','Cuota','Prob. modelo %','Cuota justa','Edge %','EV %','IA decisión','IA probabilidad','IA confianza'] if x in optional.columns]
        st.dataframe(optional[display_cols],use_container_width=True,hide_index=True)
        st.subheader('📊 Ranking completo')
        display_df=df.drop(columns=['_context','_event'],errors='ignore'); st.dataframe(display_df.head(100),use_container_width=True,hide_index=True)
else:
    st.warning('No hay oportunidades modeladas. Configura las APIs y verifica la cobertura histórica.')

st.divider(); st.caption('La IA valida los datos disponibles y puede rechazar una selección. Nunca sustituye el cálculo matemático ni inventa estadísticas. Las probabilidades son estimaciones y no garantizan resultados.')
