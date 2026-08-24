import json
import os
import re
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
    wanted = [n.lower().replace(" ", "") for n in names]
    for event in events:
        for bookmaker in event.get("bookmakers", []):
            bname = bookmaker.get("title", "")
            normalized = re.sub(r"[^a-z0-9]", "", bname.lower())
            if not any(w in normalized for w in wanted):
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


def all_bookmaker_odds(events: List[dict]) -> List[dict]:
    rows = []
    for event in events:
        for bookmaker in event.get("bookmakers", []):
            for market in bookmaker.get("markets", []):
                for outcome in market.get("outcomes", []):
                    rows.append({
                        "event_id": event.get("id"), "sport": event.get("sport_title"),
                        "start": event.get("commence_time"), "home": event.get("home_team"),
                        "away": event.get("away_team"), "bookmaker": bookmaker.get("title"),
                        "market": market.get("key"), "selection": outcome.get("name"),
                        "point": outcome.get("point"), "odds": outcome.get("price"),
                    })
    return rows


def football_get(endpoint: str, params: dict) -> dict:
    key = football_api_key()
    if not key:
        return {"response": [], "errors": {"config": "API_FOOTBALL_KEY no configurada"}}
    return _get(
        f"https://v3.football.api-sports.io/{endpoint}",
        params,
        {"x-apisports-key": key},
    )


def football_h2h(team_a: int, team_b: int, last: int = 10) -> List[dict]:
    return football_get("fixtures/headtohead", {"h2h": f"{team_a}-{team_b}", "last": last}).get("response", [])


def football_fixture(fixture_id: int) -> Optional[dict]:
    items = football_get("fixtures", {"id": fixture_id}).get("response", [])
    return items[0] if items else None


def football_fixture_players(fixture_id: int) -> List[dict]:
    return football_get("fixtures/players", {"fixture": fixture_id}).get("response", [])


def football_team_last(team_id: int, last: int = 10) -> List[dict]:
    return football_get("fixtures", {"team": team_id, "last": last, "status": "FT"}).get("response", [])


def poisson_over_probability(expected: float, line: float) -> float:
    if expected <= 0:
        return 0.0
    cutoff = int(line) + 1
    cumulative = sum((expected ** k) * __import__('math').exp(-expected) / __import__('math').factorial(k) for k in range(cutoff))
    return max(0.0, min(1.0, 1.0 - cumulative))


def projection_from_samples(samples: List[float]) -> Dict[str, float]:
    clean = [float(x) for x in samples if x is not None and float(x) >= 0]
    if not clean:
        return {"mean": 0.0, "median": 0.0, "stdev": 0.0, "count": 0}
    import statistics
    return {
        "mean": statistics.mean(clean),
        "median": statistics.median(clean),
        "stdev": statistics.stdev(clean) if len(clean) > 1 else 0.0,
        "count": len(clean),
    }


def calculate_market_value(odds: float, probability: float) -> Dict[str, float]:
    odds = float(odds)
    probability = max(0.0, min(1.0, float(probability)))
    implied = 1.0 / odds if odds > 1 else 0.0
    fair = 1.0 / probability if probability > 0 else 0.0
    return {
        "implied_probability": implied,
        "fair_odds": fair,
        "edge_points": probability - implied,
        "expected_value": probability * odds - 1.0,
    }


def ai_validate(payload: dict) -> Dict[str, Any]:
    key = os.getenv("OPENAI_API_KEY", "").strip()
    model = os.getenv("OPENAI_MODEL", "gpt-5.6-luna").strip()
    if not key:
        return {"ok": False, "error": "OPENAI_API_KEY no configurada"}

    prompt = """Eres un validador cuantitativo deportivo. Usa exclusivamente los datos recibidos; no inventes estadísticas, H2H, lesiones, cuotas ni resultados. Compara la probabilidad estadística con la probabilidad implícita de la mejor cuota. Si la evidencia es insuficiente, recomienda SIN APUESTA. Devuelve únicamente JSON válido con las claves: mercado_recomendado, probabilidad_modelo, probabilidad_ia, confianza, cuota_justa, mejor_cuota, edge, expected_value, razonamiento, riesgos. Las probabilidades deben ser porcentajes 0-100 y confianza 0-10. No garantices resultados."""
    body = {"model": model, "input": prompt + "\nDATOS:\n" + json.dumps(payload, ensure_ascii=False)}
    r = requests.post(
        "https://api.openai.com/v1/responses",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json=body,
        timeout=45,
    )
    r.raise_for_status()
    data = r.json()
    text = data.get("output_text", "")
    return {"ok": True, "text": text, "raw": data}
