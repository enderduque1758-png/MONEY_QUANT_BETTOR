import json
import os
import re
import statistics
import math
from typing import Any, Dict, List, Optional
import requests

TIMEOUT = 20

def _get(url, params=None, headers=None):
    r=requests.get(url,params=params,headers=headers,timeout=TIMEOUT); r.raise_for_status(); return r.json()

def _api_get(base,key,endpoint,params=None,headers=None):
    if not key: return {"response":[],"errors":{"config":f"{base} API key no configurada"}}
    return _get(f"{base}/{endpoint}",params,headers)

def odds_api_key(): return os.getenv("ODDS_API_KEY","").strip()
def football_api_key(): return os.getenv("API_FOOTBALL_KEY","").strip()
def sports_api_key(): return os.getenv("SPORTS_API_KEY","").strip()

def get_sports():
    k=odds_api_key(); return _get("https://api.the-odds-api.com/v4/sports/",{"apiKey":k}) if k else []
def get_odds(sport_key,regions="us,eu"):
    k=odds_api_key()
    if not k or not sport_key:return []
    return _get(f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds/",{"apiKey":k,"regions":regions,"markets":"h2h,spreads,totals","oddsFormat":"decimal","dateFormat":"iso"})

def _bookmaker_rows(events,only=None):
    rows=[]; wanted=[x.lower().replace(" ","") for x in only] if only else None
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

# Generic statistical engines. They accept normalized API data so any provider can feed them.
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
    """Projection for MLB/KBO/NPB team totals. Feed last-5/10 runs and runs allowed."""
    hf=projection_from_samples(home_runs); af=projection_from_samples(away_runs)
    hp=projection_from_samples(home_allowed or []); ap=projection_from_samples(away_allowed or [])
    h=0.65*hf["mean"]+0.35*(ap["mean"] if ap["count"] else hf["mean"])
    a=0.65*af["mean"]+0.35*(hp["mean"] if hp["count"] else af["mean"])
    return {"home_expected":h,"away_expected":a,"total_expected":h+a,"home_samples":hf,"away_samples":af,"home_allowed":hp,"away_allowed":ap}

def baseball_market_probs(projection,line):
    total=projection["total_expected"]; over=poisson_over_probability(total,line)
    return {"over":over,"under":1-over}

def basketball_projection(team_points,opp_points=None,pace_factor=1.0):
    a=projection_from_samples(team_points); b=projection_from_samples(opp_points or [])
    base=a["mean"] if a["count"] else 0
    opp=b["mean"] if b["count"] else base
    return {"team_expected":base*pace_factor,"opponent_expected":opp*pace_factor,"total_expected":(base+opp)*pace_factor,"team_stats":a,"opponent_stats":b}

def basketball_market_probs(projection,line):
    sd=max(5.,projection["team_stats"].get("stdev",0.)*1.5)
    z=(projection["total_expected"]-line)/sd
    over=.5*(1+math.erf(z/math.sqrt(2)))
    return {"over":max(0.,min(1.,over)),"under":max(0.,min(1.,1-over))}

def tennis_projection(player_a,player_b):
    a=projection_from_samples(player_a); b=projection_from_samples(player_b)
    # Inputs can be games won, service points won, or a normalized performance score.
    score_a=a["mean"] if a["count"] else 0.; score_b=b["mean"] if b["count"] else 0.
    total=score_a+score_b
    p_a=score_a/(total) if total>0 else .5
    return {"player_a_score":score_a,"player_b_score":score_b,"p_a":p_a,"p_b":1-p_a,"samples_a":a,"samples_b":b}

def tennis_market_probs(projection): return {"player_a":projection["p_a"],"player_b":projection["p_b"]}

# Optional provider adapter: API-Sports unified key for baseball/basketball/tennis.
def sports_get(endpoint,params=None):
    k=sports_api_key()
    if not k:return {"response":[],"errors":{"config":"SPORTS_API_KEY no configurada"}}
    return _get(f"https://v1.{endpoint}",params,{"x-apisports-key":k})

def ai_validate(payload):
    k=os.getenv("OPENAI_API_KEY","").strip(); model=os.getenv("OPENAI_MODEL","gpt-5.6-luna").strip()
    if not k:return {"ok":False,"error":"OPENAI_API_KEY no configurada"}
    prompt="""Valida cuantitativamente una predicción deportiva usando SOLO los datos entregados. No inventes datos. Si faltan datos críticos responde SIN APUESTA. Devuelve JSON con mercado_recomendado, probabilidad_modelo, probabilidad_ia, confianza, cuota_justa, mejor_cuota, edge, expected_value, razonamiento y riesgos. Probabilidades 0-100; confianza 0-10."""
    r=requests.post("https://api.openai.com/v1/responses",headers={"Authorization":f"Bearer {k}","Content-Type":"application/json"},json={"model":model,"input":prompt+"\nDATOS:\n"+json.dumps(payload,ensure_ascii=False)},timeout=45); r.raise_for_status(); d=r.json(); return {"ok":True,"text":d.get("output_text","")}
