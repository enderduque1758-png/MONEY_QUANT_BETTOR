import json
import os
import re
import statistics
import math
from typing import Any, Dict, List, Optional

import requests

TIMEOUT = 20


def _get(url: str, params: Optional[dict] = None, headers: Optional[dict] = None) -> Any:
    r = requests.get(url, params=params, headers=headers, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()


def odds_api_key() -> str:
    return os.getenv("ODDS_API_KEY", "").strip()


def football_api_key() -> str:
    return os.getenv("API_FOOTBALL_KEY", "").strip()


def get_sports() -> List[dict]:
    key = odds_api_key()
    return _get("https://api.the-odds-api.com/v4/sports/", {"apiKey": key}) if key else []


def get_odds(sport_key: str, regions: str = "us,eu") -> List[dict]:
    key = odds_api_key()
    if not key or not sport_key:
        return []
    return _get(f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds/", {
        "apiKey": key, "regions": regions, "markets": "h2h,spreads,totals",
        "oddsFormat": "decimal", "dateFormat": "iso"
    })


def _bookmaker_rows(events: List[dict], only=None) -> List[dict]:
    rows = []
    wanted = [x.lower().replace(" ", "") for x in only] if only else None
    for event in events:
        for bookmaker in event.get("bookmakers", []):
            bname = bookmaker.get("title", "")
            norm = re.sub(r"[^a-z0-9]", "", bname.lower())
            if wanted and not any(w in norm for w in wanted):
                continue
            for market in bookmaker.get("markets", []):
                for outcome in market.get("outcomes", []):
                    rows.append({
                        "event_id": event.get("id"), "sport": event.get("sport_title"),
                        "start": event.get("commence_time"), "home": event.get("home_team"),
                        "away": event.get("away_team"), "bookmaker": bname,
                        "market": market.get("key"), "selection": outcome.get("name"),
                        "point": outcome.get("point"), "odds": outcome.get("price")
                    })
    return rows


def extract_bookmaker_odds(events: List[dict], names=("Betano", "RushBet")) -> List[dict]:
    return _bookmaker_rows(events, names)


def all_bookmaker_odds(events: List[dict]) -> List[dict]:
    return _bookmaker_rows(events)


def football_get(endpoint: str, params: dict) -> dict:
    key = football_api_key()
    if not key:
        return {"response": [], "errors": {"config": "API_FOOTBALL_KEY no configurada"}}
    return _get(f"https://v3.football.api-sports.io/{endpoint}", params, {"x-apisports-key": key})


def football_team_search(name: str) -> List[dict]:
    if not name:
        return []
    return football_get("teams", {"search": name}).get("response", [])


def football_find_team(name: str) -> Optional[dict]:
    candidates = football_team_search(name)
    if not candidates:
        return None
    target = re.sub(r"[^a-z0-9]", "", name.lower())
    best = None
    best_score = -1
    for item in candidates:
        team = item.get("team", {})
        candidate = re.sub(r"[^a-z0-9]", "", team.get("name", "").lower())
        score = 100 if candidate == target else (80 if target in candidate or candidate in target else 0)
        if score > best_score:
            best, best_score = item, score
    return best


def football_h2h(team_a: int, team_b: int, last: int = 10) -> List[dict]:
    return football_get("fixtures/headtohead", {"h2h": f"{team_a}-{team_b}", "last": last}).get("response", [])


def football_fixture(fixture_id: int) -> Optional[dict]:
    items = football_get("fixtures", {"id": fixture_id}).get("response", [])
    return items[0] if items else None


def football_fixture_players(fixture_id: int) -> List[dict]:
    return football_get("fixtures/players", {"fixture": fixture_id}).get("response", [])


def football_team_last(team_id: int, last: int = 10) -> List[dict]:
    return football_get("fixtures", {"team": team_id, "last": last, "status": "FT"}).get("response", [])


def football_team_stats(team_id: int, league_id: int, season: int) -> dict:
    return football_get("teams/statistics", {"team": team_id, "league": league_id, "season": season}).get("response", {})


def football_injuries(team_id: int, season: int) -> List[dict]:
    return football_get("injuries", {"team": team_id, "season": season}).get("response", [])


def football_fixture_enrichment(home: str, away: str) -> Dict[str, Any]:
    """Resolve team names automatically and return H2H/form data when API-Football is configured."""
    if not football_api_key():
        return {"ok": False, "error": "API_FOOTBALL_KEY no configurada"}
    home_match = football_find_team(home)
    away_match = football_find_team(away)
    if not home_match or not away_match:
        return {"ok": False, "error": "No se pudieron resolver ambos equipos en API-Football"}
    home_team = home_match.get("team", {})
    away_team = away_match.get("team", {})
    home_id, away_id = home_team.get("id"), away_team.get("id")
    h2h = football_h2h(home_id, away_id, 10)
    home_last = football_team_last(home_id, 10)
    away_last = football_team_last(away_id, 10)
    return {
        "ok": True,
        "teams": {"home": home_team, "away": away_team},
        "h2h": h2h,
        "home_last": home_last,
        "away_last": away_last,
    }


def summarize_football_results(fixtures: List[dict]) -> Dict[str, float]:
    goals_for, goals_against, totals = [], [], []
    wins = draws = losses = 0
    for f in fixtures:
        teams, goals = f.get("teams", {}), f.get("goals", {})
        home, away = goals.get("home"), goals.get("away")
        if not isinstance(home, int) or not isinstance(away, int):
            continue
        is_home = teams.get("home", {}).get("id") == teams.get("home", {}).get("id")
        # API data does not identify caller here; preserve match totals for neutral summary.
        totals.append(home + away)
        goals_for.append(home)
        goals_against.append(away)
        if home > away: wins += 1
        elif home == away: draws += 1
        else: losses += 1
    return {
        "matches": len(totals),
        "avg_total_goals": statistics.mean(totals) if totals else 0.0,
        "avg_home_goals": statistics.mean(goals_for) if goals_for else 0.0,
        "avg_away_goals": statistics.mean(goals_against) if goals_against else 0.0,
        "wins": wins, "draws": draws, "losses": losses
    }


def poisson_over_probability(expected: float, line: float) -> float:
    if expected <= 0:
        return 0.0
    cutoff = int(math.floor(line)) + 1
    cumulative = sum(math.exp(-expected) * expected ** k / math.factorial(k) for k in range(cutoff))
    return max(0.0, min(1.0, 1.0 - cumulative))


def projection_from_samples(samples: List[float]) -> Dict[str, float]:
    clean = [float(x) for x in samples if x is not None and float(x) >= 0]
    if not clean:
        return {"mean": 0.0, "median": 0.0, "stdev": 0.0, "count": 0}
    return {"mean": statistics.mean(clean), "median": statistics.median(clean), "stdev": statistics.stdev(clean) if len(clean) > 1 else 0.0, "count": len(clean)}


def calculate_market_value(odds: float, probability: float) -> Dict[str, float]:
    odds, probability = float(odds), max(0.0, min(1.0, float(probability)))
    implied = 1.0 / odds if odds > 1 else 0.0
    fair = 1.0 / probability if probability > 0 else 0.0
    return {"implied_probability": implied, "fair_odds": fair, "edge_points": probability - implied, "expected_value": probability * odds - 1.0}


def ai_validate(payload: dict) -> Dict[str, Any]:
    key = os.getenv("OPENAI_API_KEY", "").strip()
    model = os.getenv("OPENAI_MODEL", "gpt-5.6-luna").strip()
    if not key:
        return {"ok": False, "error": "OPENAI_API_KEY no configurada"}
    prompt = """Eres un validador cuantitativo deportivo. Usa exclusivamente los datos recibidos; no inventes estadísticas. Si faltan datos relevantes, devuelve SIN APUESTA. Devuelve JSON válido con mercado_recomendado, probabilidad_modelo, probabilidad_ia, confianza, cuota_justa, mejor_cuota, edge, expected_value, razonamiento y riesgos. Probabilidades 0-100; confianza 0-10. Nunca garantices resultados."""
    body = {"model": model, "input": prompt + "\nDATOS:\n" + json.dumps(payload, ensure_ascii=False)}
    r = requests.post("https://api.openai.com/v1/responses", headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}, json=body, timeout=45)
    r.raise_for_status()
    data = r.json()
    return {"ok": True, "text": data.get("output_text", ""), "raw": data}
