import json, math
import pandas as pd
import streamlit as st
from services import *

st.set_page_config(page_title="MONEY QUANT BETTOR", page_icon="🏆", layout="wide")
st.title("🏆 MONEY QUANT BETTOR")
st.caption("Multi-deporte: cuotas + estadísticas + H2H + proyección + Value + IA")

with st.sidebar:
    st.header("⚙️ Configuración")
    sports=get_sports() if odds_api_key() else []
    options={s.get("title",s.get("key")):s.get("key") for s in sports} or {
        "⚽ Fútbol":"soccer_epl","⚾ MLB":"baseball_mlb","⚾ KBO":"baseball_kbo","⚾ NPB":"baseball_npb","🏀 NBA":"basketball_nba","🎾 ATP":"tennis_atp","🎾 WTA":"tennis_wta"}
    sport_label=st.selectbox("Deporte",list(options)); sport_key=options[sport_label]
    regions=st.multiselect("Regiones de cuotas",["us","eu","uk","au"],["us","eu"])
    limit=st.slider("Partidos",5,50,20)
    st.markdown("**Secrets**")
    st.code("ODDS_API_KEY\nAPI_FOOTBALL_KEY\nSPORTS_API_KEY\nOPENAI_API_KEY\nOPENAI_MODEL",language="text")
    st.caption("SPORTS_API_KEY es opcional y se usa como adaptador para fuentes deportivas compatibles.")

@st.cache_data(ttl=60)
def load_events(key,reg): return get_odds(key,",".join(reg))
@st.cache_data(ttl=300)
def load_football(home,away): return football_fixture_enrichment(home,away)

def implied(o):
    try: o=float(o); return 1/o if o>1 else None
    except: return None

def normal_over(mean,sd,line):
    sd=max(float(sd),1e-6); z=(mean-line)/sd
    return max(0,min(1,.5*(1+math.erf(z/math.sqrt(2)))))

def show_value(rows,prob,market_label):
    out=[]
    for r in rows:
        try:o=float(r.get("odds"))
        except:continue
        v=calculate_market_value(o,prob)
        out.append({**r,"Mercado":market_label,"Prob. modelo":prob,"Cuota justa":v["fair_odds"],"Edge":v["edge_points"],"EV":v["expected_value"]})
    if not out:return
    df=pd.DataFrame(out).sort_values("EV",ascending=False); st.dataframe(df,use_container_width=True,hide_index=True)
    best=df.iloc[0]
    if float(best["EV"])>0: st.success(f"🟢 VALUE: {best['selection']} @ {best['odds']:.2f} | EV {best['EV']*100:.1f}%")
    else: st.warning("🔴 NO BET: EV no positivo")

events=load_events(sport_key,regions) if odds_api_key() else []
all_rows=all_bookmaker_odds(events)
st.subheader(f"📅 Partidos — {sport_label}")
if events: st.dataframe(pd.DataFrame([{"Inicio":e.get("commence_time"),"Local":e.get("home_team"),"Visitante":e.get("away_team"),"ID":e.get("id")} for e in events[:limit]]),use_container_width=True,hide_index=True)
else: st.warning("No hay eventos. Configura ODDS_API_KEY y verifica la cobertura.")

selected={}; selected_rows=[]
if events:
    labels={f"{e.get('home_team')} vs {e.get('away_team')} — {e.get('commence_time')}":e for e in events[:limit]}
    selected=labels[st.selectbox("🔎 Selecciona partido",list(labels))]
    selected_rows=[r for r in all_rows if r.get("event_id")==selected.get("id")]
    if selected_rows: st.dataframe(pd.DataFrame(selected_rows),use_container_width=True,hide_index=True)

# ================= FÚTBOL =================
if sport_key.startswith("soccer_") and selected:
    st.divider(); st.header("⚽ Fútbol — H2H + forma + jugadores")
    e=load_football(selected.get("home_team",""),selected.get("away_team",""))
    if e.get("ok"):
        def results(fs):
            rr=[]; totals=[]
            for f in fs:
                g=f.get("goals",{}); t=f.get("teams",{}); h,a=g.get("home"),g.get("away")
                if isinstance(h,int) and isinstance(a,int):
                    totals.append(h+a); rr.append({"Fecha":f.get("fixture",{}).get("date"),"Local":t.get("home",{}).get("name"),"Visitante":t.get("away",{}).get("name"),"Marcador":f"{h}-{a}","Total":h+a})
            return rr,totals
        hrows,ht=results(e["h2h"]); hr,htm=results(e["home_last"]); ar,atm=results(e["away_last"])
        tabs=st.tabs(["🤝 H2H","🏠 Local","✈️ Visitante","📊 Resumen"])
        with tabs[0]:
            st.dataframe(pd.DataFrame(hrows),use_container_width=True,hide_index=True) if hrows else st.info("Sin H2H")
        with tabs[1]: st.dataframe(pd.DataFrame(hr),use_container_width=True,hide_index=True) if hr else st.info("Sin forma local")
        with tabs[2]: st.dataframe(pd.DataFrame(ar),use_container_width=True,hide_index=True) if ar else st.info("Sin forma visitante")
        with tabs[3]:
            vals=[("H2H",ht),("Local últimos",htm),("Visitante últimos",atm)]
            st.dataframe(pd.DataFrame([{"Fuente":n,"Muestras":len(v),"Promedio goles":round(sum(v)/len(v),2) if v else 0} for n,v in vals]),use_container_width=True,hide_index=True)
        combined=ht[-10:]+htm[-5:]+atm[-5:]
        if combined:
            p=projection_from_samples(combined); line=st.number_input("Línea de goles",2.5,7.5,2.5,.5); prob=poisson_over_probability(.7*p["mean"]+.3*p["median"],line)
            c1,c2,c3=st.columns(3); c1.metric("Promedio",f"{p['mean']:.2f}"); c2.metric("Proyección",f"{(.7*p['mean']+.3*p['median']):.2f}"); c3.metric(f"P(Over {line})",f"{prob*100:.1f}%")
            totals=[r for r in selected_rows if r.get("market")=="totals"]; show_value(totals,prob,f"Over {line}")
    else: st.warning(e.get("error","API-Football no disponible"))

# ================= BÉISBOL =================
elif sport_key.startswith("baseball_") and selected:
    st.divider(); st.header("⚾ Béisbol — MLB / KBO / NPB")
    st.info("El motor está preparado para pitchers, bateadores, bullpen, carreras, 1ª entrada, 5 entradas y total. Introduce datos normalizados si tu proveedor no los expone todavía.")
    c1,c2,c3,c4=st.columns(4)
    home_runs=c1.text_input("Carreras local últimos 10","",key="brh"); away_runs=c2.text_input("Carreras visitante últimos 10","",key="bra")
    home_allowed=c3.text_input("Carreras permitidas local","",key="bah"); away_allowed=c4.text_input("Carreras permitidas visitante","",key="baa")
    def nums(s):
        try:return [float(x.strip()) for x in s.split(",") if x.strip()]
        except:return []
    h,a,ha,aa=nums(home_runs),nums(away_runs),nums(home_allowed),nums(away_allowed)
    if h and a:
        bp=baseball_projection(h,a,ha,aa); line=st.number_input("Total carreras",0.,12.,8.5,.5,key="bl")
        probs=baseball_market_probs(bp,line); c=st.columns(4); c[0].metric("Local esperado",f"{bp['home_expected']:.2f}"); c[1].metric("Visitante esperado",f"{bp['away_expected']:.2f}"); c[2].metric("Total esperado",f"{bp['total_expected']:.2f}"); c[3].metric(f"P(Over {line})",f"{probs['over']*100:.1f}%")
        totals=[r for r in selected_rows if r.get("market")=="totals"]; show_value(totals,probs["over"],f"Over {line}")
        st.subheader("🎯 Mercados especiales")
        st.write("Primera entrada, primeras 5 entradas, carreras por equipo y Run Line quedan listos para alimentar cuando la fuente entregue esos mercados y estadísticas.")

# ================= BALONCESTO =================
elif sport_key.startswith("basketball_") and selected:
    st.divider(); st.header("🏀 Baloncesto — puntos + ritmo + total")
    c1,c2=st.columns(2); team=c1.text_input("Puntos equipo últimos 10","",key="bkp"); opp=c2.text_input("Puntos rivales últimos 10","",key="bko")
    def nums2(s):
        try:return [float(x.strip()) for x in s.split(",") if x.strip()]
        except:return []
    t,o=nums2(team),nums2(opp)
    if t:
        pace=st.slider("Factor de ritmo",.8,1.2,1.,.01); bp=basketball_projection(t,o,pace); line=st.number_input("Total puntos",100.,300.,220.,1.,key="bkl")
        probs=basketball_market_probs(bp,line); c=st.columns(4); c[0].metric("Equipo esperado",f"{bp['team_expected']:.1f}"); c[1].metric("Rival esperado",f"{bp['opponent_expected']:.1f}"); c[2].metric("Total esperado",f"{bp['total_expected']:.1f}"); c[3].metric(f"P(Over {line})",f"{probs['over']*100:.1f}%")
        totals=[r for r in selected_rows if r.get("market")=="totals"]; show_value(totals,probs["over"],f"Over {line}")
        st.subheader("👤 Jugadores")
        st.write("El esquema admite puntos, rebotes, asistencias, triples y PRA cuando la fuente de estadísticas individuales esté conectada.")

# ================= TENIS =================
elif sport_key.startswith("tennis_") and selected:
    st.divider(); st.header("🎾 Tenis — H2H + forma + juegos")
    c1,c2=st.columns(2); pa=c1.text_input("Rendimiento jugador A últimos partidos","",key="tpa"); pb=c2.text_input("Rendimiento jugador B últimos partidos","",key="tpb")
    def nums3(s):
        try:return [float(x.strip()) for x in s.split(",") if x.strip()]
        except:return []
    a,b=nums3(pa),nums3(pb)
    if a and b:
        tp=tennis_projection(a,b); line=st.number_input("Línea de juegos/mercado",0.,60.,22.5,.5,key="tl")
        c=st.columns(4); c[0].metric("Fuerza A",f"{tp['player_a_score']:.2f}"); c[1].metric("Fuerza B",f"{tp['player_b_score']:.2f}"); c[2].metric("P(A)",f"{tp['p_a']*100:.1f}%"); c[3].metric("P(B)",f"{tp['p_b']*100:.1f}%")
        h2h_note=st.text_area("H2H reciente (opcional)","",key="th2h",placeholder="Resultados o métricas normalizadas")
        ml=[r for r in selected_rows if r.get("market")=="h2h"]
        show_value(ml,tp["p_a"],"Ganador jugador A")

# ================= IA =================
st.divider(); st.header("🤖 IA — validación final")
payload={"sport":sport_label,"event":{"home":selected.get("home_team"),"away":selected.get("away_team"),"start":selected.get("commence_time")},"odds":selected_rows,"note":"Usar solo datos disponibles; no inventar H2H, lesiones, pitchers, jugadores o resultados."}
if st.button("🧠 Validar proyección con IA",type="primary"):
    try:
        r=ai_validate(payload)
        if r.get("ok"):
            try:
                p=json.loads(r.get("text","")); c=st.columns(4); c[0].metric("Mercado",p.get("mercado_recomendado","SIN APUESTA")); c[1].metric("Prob. IA",f"{float(p.get('probabilidad_ia',0)):.1f}%"); c[2].metric("Cuota justa",f"{float(p.get('cuota_justa',0)):.2f}"); c[3].metric("Confianza",f"{float(p.get('confianza',0)):.1f}/10"); st.write("**Edge:**",p.get("edge")); st.write("**EV:**",p.get("expected_value")); st.write("**Razonamiento:**",p.get("razonamiento")); st.write("**Riesgos:**",p.get("riesgos"))
            except Exception: st.code(r.get("text",""),language="json")
        else: st.error(r.get("error","IA no configurada"))
    except Exception as ex: st.error(f"Error IA: {ex}")

st.caption("⚠️ El modelo estima probabilidades; no garantiza resultados. Si faltan datos críticos o no hay valor positivo, debe marcar SIN APUESTA.")
