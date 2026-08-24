import streamlit as st
import pandas as pd
from services import *

st.set_page_config(page_title='Top Picks | MONEY QUANT BETTOR', page_icon='🏆', layout='wide')
st.title('🏆 TOP PICKS')
st.caption('Ranking automático: proyección → probabilidad → cuota justa → Edge → EV')

sports = get_sports() if odds_api_key() else []
keys = {s.get('title', s.get('key')): s.get('key') for s in sports} or {
    '⚽ Fútbol': 'soccer_epl', '⚾ MLB': 'baseball_mlb', '⚾ KBO': 'baseball_kbo',
    '⚾ NPB': 'baseball_npb', '🏀 NBA': 'basketball_nba', '🎾 ATP': 'tennis_atp', '🎾 WTA': 'tennis_wta'
}
selected = st.multiselect('Deportes', list(keys), list(keys)[:1])
min_ev = st.slider('EV mínimo (%)', -10.0, 30.0, 2.0, 0.5)
rows = []

for label in selected:
    key = keys[label]
    events = get_odds(key, 'us,eu') if odds_api_key() else []
    for e in events:
        odds_rows = all_bookmaker_odds([e])
        modeled = False
        probabilities = {}
        if key.startswith('soccer_') and football_api_key():
            info = football_fixture_enrichment(e.get('home_team',''), e.get('away_team',''))
            if info.get('ok'):
                def totals(fs):
                    vals=[]
                    for f in fs:
                        h=f.get('goals',{}).get('home'); a=f.get('goals',{}).get('away')
                        if isinstance(h,int) and isinstance(a,int): vals.append(h+a)
                    return vals
                vals = totals(info.get('h2h',[]))[-10:] + totals(info.get('home_last',[]))[-5:] + totals(info.get('away_last',[]))[-5:]
                if vals:
                    p = projection_from_samples(vals)
                    expected = .7*p['mean'] + .3*p['median']
                    for line in (1.5, 2.5, 3.5):
                        probabilities[('totals',f'Over {line}')] = poisson_over_probability(expected,line)
                    modeled = True
        for r in odds_rows:
            try:
                odds = float(r.get('odds',0))
                if odds <= 1: continue
                prob = None
                if r.get('market') == 'totals' and modeled:
                    try:
                        point = float(r.get('point'))
                        selection = str(r.get('selection','')).lower()
                        if 'over' in selection: prob = probabilities.get(('totals',f'Over {point}'))
                        elif 'under' in selection:
                            op = probabilities.get(('totals',f'Over {point}'))
                            prob = 1-op if op is not None else None
                    except: pass
                if prob is None: continue
                v = calculate_market_value(odds, prob)
                rows.append({
                    'Deporte': label, 'Partido': f"{e.get('home_team')} vs {e.get('away_team')}",
                    'Bookmaker': r.get('bookmaker'), 'Mercado': r.get('market'), 'Selección': r.get('selection'),
                    'Línea': r.get('point'), 'Cuota': odds, 'Prob. modelo %': prob*100,
                    'Cuota justa': v['fair_odds'], 'Edge %': v['edge_points']*100, 'EV %': v['expected_value']*100,
                    'Estado': '🟢 VALUE' if v['expected_value'] > 0 else '🔴 NO BET'
                })

if rows:
    df = pd.DataFrame(rows).sort_values(['EV %','Edge %'], ascending=False)
    value = df[df['EV %'] >= min_ev]
    if not value.empty:
        st.success(f'🥇 {len(value)} oportunidades superan el EV mínimo de {min_ev:.1f}%')
        st.dataframe(value.head(50), use_container_width=True, hide_index=True)
        best = value.iloc[0]
        st.subheader('🥇 RECOMENDACIÓN PRINCIPAL')
        c=st.columns(5)
        c[0].metric('Partido',best['Partido']); c[1].metric('Selección',best['Selección']); c[2].metric('Probabilidad',f"{best['Prob. modelo %']:.1f}%"); c[3].metric('Cuota',f"{best['Cuota']:.2f}"); c[4].metric('EV',f"{best['EV %']:.1f}%")
        st.caption('La recomendación principal solo aparece cuando existe una probabilidad modelada y EV suficiente. Los demás mercados se mantienen como opcionales si el modelo los puede calcular.')
    else:
        st.warning('No hay VALUE BET con el EV mínimo seleccionado. 🔴 SIN APUESTA.')
else:
    st.warning('No hay oportunidades modeladas. Configura ODDS_API_KEY y, para fútbol, API_FOOTBALL_KEY.')

st.divider()
st.info('MLB/KBO/NPB, NBA y ATP/WTA aparecen en el selector, pero no se marcarán como VALUE hasta disponer de estadísticas históricas específicas suficientes. Esto evita inventar probabilidades.')
