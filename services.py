import os
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
    if not key:
        return []
    return _get("https://api.the-odds-api.com/v4/sports/", {"apiKey": key})


def get_odds(sport_key: str, regions: str = "us,eu") -> List[dict]:
    key = odds_api_key()
    if not key or not sport_key:
        return []
    return _get(
        f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds/",
        {
            "apiKey": key,
            "regions": regions,
            "markets": "h2h,spreads,totals",
            "oddsFormat": "decimal",
            "dateFormat": "iso",
        },
    )


def extract_bookmaker_odds(events: List[dict], names=("Betano", "RushBet")) -> List[dict]:
    rows = []
    wanted = [n.lower() for n in names]
    for event in events:
        for bookmaker in event.get("bookmakers", []):
            bname = bookmaker.get("title", "")
            if not any(w in bname.lower() for w in wanted):
                continue
            for market in bookmaker.get("markets", []):
                for outcome in market.get("outcomes", []):
                    rows.append({
                        "event_id": event.get("id"),
                        "sport": event.get("sport_title"),
                        "start": event.get("commence_time"),
                        "home": event.get("home_team"),
                        "away": event.get("away_team"),
                        "bookmaker": bname,
                        "market": market.get("key"),
                        "selection": outcome.get("name"),
                        "point": outcome.get("point"),
                        "odds": outcome.get("price"),
                    })
    return rows


def football_get(endpoint: str, params: dict) -> dict:
    key = football_api_key()
    if not key:
        return {"response": [], "errors": {"config": "API_FOOTBALL_KEY no configurada"}}
    headers = {"x-apisports-key": key}
    return _get(f"https://v3.football.api-sports.io/{endpoint}", params, headers)


def football_h2h(team_a: int, team_b: int, last: int = 10) -> List[dict]:
    data = football_get("fixtures/headtohead", {"h2h": f"{team_a}-{team_b}", "last": last})
    return data.get("response", [])


def football_fixture(fixture_id: int) -> Optional[dict]:
    data = football_get("fixtures", {"id": fixture_id})
    items = data.get("response", [])
    return items[0] if items else None


def football_fixture_players(fixture_id: int) -> List[dict]:
    data = football_get("fixtures/players", {"fixture": fixture_id})
    return data.get("response", [])


def football_player_search(name: str, season: int) -> List[dict]:
    data = football_get("players", {"search": name, "season": season})
    return data.get("response", [])


def ai_validate(payload: dict) -> Dict[str, Any]:
    key = os.getenv("OPENAI_API_KEY", "").strip()
    model = os.getenv("OPENAI_MODEL", "gpt-5.6-luna").strip()
    if not key:
        return {"ok": False, "error": "OPENAI_API_KEY no configurada"}

    prompt = """Actúa como validador cuantitativo deportivo. No inventes datos. Analiza exclusivamente los datos entregados. Devuelve JSON con: mercado_recomendado, probabilidad_modelo_0_100, confianza_0_10, cuota_justa, edge_porcentual, razonamiento, riesgos. Si los datos son insuficientes, indica mercado_recomendado='SIN APUESTA'. No garantices resultados."""
    body = {
        "model": model,
        "input": prompt + "\n\nDATOS:\n" + str(payload),
    }
    r = requests.post(
        "https://api.openai.com/v1/responses",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json=body,
        timeout=45,
    )
    r.raise_for_status()
    data = r.json()
    return {"ok": True, "text": data.get("output_text", "")}
