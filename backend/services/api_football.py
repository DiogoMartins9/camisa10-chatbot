
import os
from datetime import date
from functools import lru_cache

import requests
from dotenv import load_dotenv

load_dotenv()

API_FOOTBALL_URL = "https://v3.football.api-sports.io"
API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY")


def buscar_jogos_por_data(data_jogo: str) -> dict:
    """
    Consulta as partidas disponíveis para uma data.
    Recebe a data no formato YYYY-MM-DD.
    """
    if not API_FOOTBALL_KEY:
        return {
            "erro": "A variável API_FOOTBALL_KEY não está configurada."
        }

    try:
        resposta = requests.get(
            f"{API_FOOTBALL_URL}/fixtures",
            headers={
                "x-apisports-key": API_FOOTBALL_KEY
            },
            params={
                "date": data_jogo,
                "timezone": "America/Sao_Paulo"
            },
            timeout=20
        )

        resposta.raise_for_status()
        dados = resposta.json()

    except requests.RequestException:
        return {
            "erro": "Não foi possível consultar a API-Football."
        }

    if dados.get("errors"):
        return {
            "erro": "A API-Football retornou um erro.",
            "detalhes": dados["errors"]
        }

    jogos = []

    for item in dados.get("response", []):
        fixture = item.get("fixture", {})
        league = item.get("league", {})
        teams = item.get("teams", {})
        goals = item.get("goals", {})
        status = fixture.get("status", {})

        mandante = teams.get("home", {})
        visitante = teams.get("away", {})

        jogos.append({
            "id": fixture.get("id"),
            "data": fixture.get("date"),
            "status": status.get("short"),
            "status_descricao": status.get("long"),
            "competicao": league.get("name"),
            "pais": league.get("country"),
            "logo_competicao": league.get("logo"),
            "mandante": mandante.get("name"),
            "logo_mandante": mandante.get("logo"),
            "visitante": visitante.get("name"),
            "logo_visitante": visitante.get("logo"),
            "gols_mandante": goals.get("home"),
            "gols_visitante": goals.get("away"),
            "estadio": fixture.get("venue", {}).get("name")
        })

    return {
        "data": data_jogo,
        "quantidade": len(jogos),
        "jogos": jogos
    }
