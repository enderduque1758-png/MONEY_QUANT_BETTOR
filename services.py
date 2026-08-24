import json
import os
import re
import statistics
import math
from typing import Any, Dict, List, Optional
import requests

try:
    import streamlit as st
except Exception:
    st = None

TIMEOUT = 20

def _get(url, params=None, headers=None):
    r=requests.get(url,params=params,headers=headers,timeout=TIMEOUT); r.raise_for_status(); return r.json()

def _secret(name, default=""):
    value=os.getenv(name,"").strip()
    if value:
        return value
    try:
        if st is not None and name in st.secrets:
            return str(st.secrets[name]).strip()
    except Exception:
        pass
    return default

def odds_api_key(): return _secret("ODDS_API_KEY")
def football_api_key(): return _secret("API_FOOTBALL_KEY")
def sports_api_key(): return _secret("SPORTS_API_KEY")
def openai_api_key(): return _secret("OPENAI_API_KEY")
def openai_model(): return _secret("OPENAI_MODEL", "gpt-5.6-luna")

def get_sports():
    k=odds_api_key(); return _get("https://api.the-odds-api.com/v4/sports/",{"apiKey":k}) if k else []
def get_odds(sport_key,regions="us,eu"):
    k=odds_api_key()
    if not k or not sport_key:return []
    return _get(f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds/",{"apiKey":k,"regions":regions,"markets":"h2h,spreads,totals","oddsFormat":"decimal","dateFormat":"iso"})

def _bookmaker_rows(events,only=None):
    rows=[]; wanted=[re.sub(r"[^a-z0-9]","",x.lower()) for x in only] if only else None
    for e in events:
        for b in e.get("bookmakers",[]):
            name=b.get("title",""); norm=re.sub(r"[^a-z0-9]","",name.lower())
            if wanted and not any(w in norm for w in wanted):continue
            for m in b.get("markets",[]):
                for o in m.get("outcomes",[]): rows.append({"event_id":e.get("id"),"sport":e.get("sport_title"),"start":e.get("commence_time"),"home":e.get("home_team"),"away":e.get("away_team"),"bookmaker":name,"market":m.get("key"),"selection":o.get("name"),"point":o.get("point"),"odds":o.get("price")})
    return rows

def extract_bookmaker_odds(events,names=("Betano","RushBet")): return _bookmaker_rows(events,names)
def all_bookmaker_odds(events): return _bookmaker_rows(events)

def football_get(endpoint,params):
    k=football_api_key()
    return _get(f"https://v3.football.api-sports.io/{endpoint}",params,{"x-apisports-key":k}) if k else {"response":[]}
def football_team_search(name): return football_get("teams",{"search":name}).get("response",[])
def football_find_team(name):
    c=football_team_search(name); target=re.sub(r"[^a-z0-9]","",name.lower()); best=None; score=-1
    for x in c:
        n=x.get("team",{}).get("name",""); z=re.sub(r"[^a-z0-9]","",n.lower()); s=100 if z==target else (80 if target in z or z in target else 0)
        if s>score:best,score=x,s
    return best
def football_h2h(a,b,last=10): return football_get("fixtures/headtohead",{"h2h":f"{a}-{b}","last":last}).get("response",[])
def football_team_last(t,last=10): return football_get("fixtures",{"team":t,"last":last,"status":"FT"}).get("response",[])
def football_fixture_players(fid): return football_get("fixtures/players",{"fixture":fid}).get("response",[])
def football_fixture_enrichment(home,away):
    h,a=football_find_team(home),football_find_team(away)
    if not h or not a:return {"ok":False,"error":"Equipos no encontrados en API-Football"}
    hi,ai=h["team"]["id"],a["team"]["id"]
    return {"ok":True,"teams":{"home":h["team"],"away":a["team"]},"h2h":football_h2h(hi,ai),"home_last":football_team_last(hi),"away_last":football_team_last(ai)}

def projection_from_samples(samples):
    x=[float(v) for v in samples if v is not None and float(v)>=0]
    if not x:return {"mean":0.,"median":0.,"stdev":0.,"count":0}
    return {"mean":statistics.mean(x),"median":statistics.median(x),"stdev":statistics.stdev(x) if len(x)>1 else 0.,"count":len(x)}
def poisson_over_probability(expected,line):
    if expected<=0:return 0.
    c=sum(math.exp(-expected)*expected**k/math.factorial(k) for k in range(math.floor(line)+1))
    return max(0.,min(1.,1-c))
def calculate_market_value(odds,probability):
    o,p=float(odds),max(0.,min(1.,float(probability))); imp=1/o if o>1 else 0.; fair=1/p if p else 0.
    return {"implied_probability":imp,"fair_odds":fair,"edge_points":p-imp,"expected_value":p*o-1}

def baseball_projection(home_runs,away_runs,home_allowed=None,away_allowed=None):
    hf=projection_from_samples(home_runs); af=projection_from_samples(away_runs); hp=projection_from_samples(home_allowed or []); ap=projection_from_samples(away_allowed or [])
    h=.65*hf["mean"]+.35*(ap["mean"] if ap["count"] else hf["mean"]); a=.65*af["mean"]+.35*(hp["mean"] if hp["count"] else af["mean"])
    return {"home_expected":h,"away_expected":a,"total_expected":h+a,"home_samples":hf,"away_samples":af,"home_allowed":hp,"away_allowed":ap}
def baseball_market_probs(projection,line):
    over=poisson_over_probability(projection["total_expected"],line); return {"over":over,"under":1-over}
def basketball_projection(team_points,opp_points=None,pace_factor=1.0):
    a=projection_from_samples(team_points); b=projection_from_samples(opp_points or []); base=a["mean"] if a["count"] else 0; opp=b["mean"] if b["count"] else base
    return {"team_expected":base*pace_factor,"opponent_expected":opp*pace_factor,"total_expected":(base+opp)*pace_factor,"team_stats":a,"opponent_stats":b}
def basketball_market_probs(projection,line):
    sd=max(5.,projection["team_stats"].get("stdev",0.)*1.5); z=(projection["total_expected"]-line)/sd; over=.5*(1+math.erf(z/math.sqrt(2)))
    return {"over":max(0.,min(1.,over)),"under":max(0.,min(1.,1-over))}
def tennis_projection(player_a,player_b):
    a=projection_from_samples(player_a); b=projection_from_samples(player_b); sa=a["mean"] if a["count"] else 0.; sb=b["mean"] if b["count"] else 0.; total=sa+sb; pa=sa/total if total>0 else .5
    return {"player_a_score":sa,"player_b_score":sb,"p_a":pa,"p_b":1-pa,"samples_a":a,"samples_b":b}
def tennis_market_probs(projection): return {"player_a":projection["p_a"],"player_b":projection["p_b"]}

SPORT_BASES={"baseball":"https://v1.baseball.api-sports.io","basketball":"https://v1.basketball.api-sports.io","nba":"https://v1.basketball.api-sports.io","tennis":"https://v1.tennis.api-sports.io"}
def sports_get(sport,endpoint,params=None):
    k=sports_api_key(); base=SPORT_BASES.get(sport,sport if str(sport).startswith("http") else None)
    if not k or not base:return {"response":[],"errors":{"config":"SPORTS_API_KEY no configurada"}}
    try:return _get(f"{base}/{endpoint}",params,{"x-apisports-key":k})
    except Exception as e:return {"response":[],"errors":{"request":str(e)}}

def _norm_name(s): return re.sub(r"[^a-z0-9]","",str(s).lower())
def sports_find_team(sport,name):
    data=sports_get(sport,"teams",{"search":name}).get("response",[]); target=_norm_name(name); best=None; score=-1
    for item in data:
        team=item.get("team",item); n=team.get("name",""); z=_norm_name(n); sc=100 if z==target else (80 if target in z or z in target else 0)
        if sc>score:best,score=team,sc
    return best

def _game_score(g):
    scores=g.get("scores",{})
    def val(side):
        x=scores.get(side,{})
        if isinstance(x,dict):
            for key in ("total","points","runs","score"):
                if x.get(key) is not None:
                    try:return float(x[key])
                    except:pass
        if isinstance(x,(int,float)):return float(x)
        return None
    return val("home"),val("away")

def sports_team_history(sport,name,last=10):
    team=sports_find_team(sport,name)
    if not team:return {"ok":False,"error":f"No se encontró {name} en API-Sports {sport}"}
    tid=team.get("id")
    data=sports_get(sport,"games",{"team":tid,"last":last}).get("response",[])
    rows=[]
    for g in data:
        h,a=_game_score(g)
        if h is None or a is None:continue
        teams=g.get("teams",{}); hn=teams.get("home",{}).get("name"); an=teams.get("away",{}).get("name")
        rows.append({"id":g.get("id"),"date":g.get("date") or g.get("timestamp"),"home":hn,"away":an,"home_score":h,"away_score":a,"total":h+a})
    return {"ok":True,"team":team,"games":rows,"count":len(rows)}

def multisport_enrichment(sport,home,away,last=10):
    s="nba" if sport.startswith("basketball") else ("baseball" if sport.startswith("baseball") else "tennis")
    if s=="tennis": return {"ok":False,"error":"API-Sports Tennis requiere validar la cobertura del proveedor para el circuito/torneo seleccionado."}
    h=sports_team_history(s,home,last); a=sports_team_history(s,away,last)
    if not h.get("ok") or not a.get("ok"):return {"ok":False,"error":h.get("error") or a.get("error")}
    return {"ok":True,"sport":s,"home":h,"away":a}

def normalized_history_samples(enrichment):
    out={"home_scored":[],"home_allowed":[],"away_scored":[],"away_allowed":[],"h2h_total":[]}
    for key,prefix in (("home","home"),("away","away")):
        for g in enrichment.get(key,{}).get("games",[]):
            team_name=enrichment[key]["team"].get("name","").lower()
            if (g.get("home") or "").lower()==team_name: scored,allowed=g["home_score"],g["away_score"]
            else: scored,allowed=g["away_score"],g["home_score"]
            out[f"{prefix}_scored"].append(scored); out[f"{prefix}_allowed"].append(allowed)
    return out

def auto_projection_for_event(sport,home,away):
    e=multisport_enrichment(sport,home,away,10)
    if not e.get("ok"):return e
    x=normalized_history_samples(e)
    if e["sport"]=="baseball": p=baseball_projection(x["home_scored"],x["away_scored"],x["home_allowed"],x["away_allowed"])
    else: p=basketball_projection(x["home_scored"],x["away_scored"])
    e["samples"]=x; e["projection"]=p; return e

def ai_validate(payload):
    k=openai_api_key(); model=openai_model()
    if not k:return {"ok":False,"error":"OPENAI_API_KEY no configurada en Streamlit Secrets o variables de entorno"}
    prompt="""Eres un validador cuantitativo deportivo. Usa SOLO los datos recibidos. No inventes estadísticas, lesiones, pitchers, jugadores, H2H ni cuotas. Compara la proyección con las cuotas y devuelve JSON: recomendacion_principal, opciones_opcionales (máximo 5), probabilidad_modelo, probabilidad_ia, confianza, cuota_justa, mejor_cuota, edge, expected_value, razonamiento, riesgos, calidad_datos. Si faltan datos críticos o EV <= 0 para todas las opciones, usa SIN APUESTA. La IA puede validar pero no sustituye los cálculos matemáticos."""
    r=requests.post("https://api.openai.com/v1/responses",headers={"Authorization":f"Bearer {k}","Content-Type":"application/json"},json={"model":model,"input":prompt+"\nDATOS:\n"+json.dumps(payload,ensure_ascii=False)},timeout=45); r.raise_for_status(); d=r.json(); return {"ok":True,"text":d.get("output_text","")}
