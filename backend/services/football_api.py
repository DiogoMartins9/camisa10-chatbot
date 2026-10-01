import os
import requests
import unicodedata
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_FOOTBALL_KEY")
FOOTBALL_DATA_TOKEN = os.getenv("FOOTBALL_DATA_TOKEN")

BASE_URL = "https://v3.football.api-sports.io"

def normalizar_nome_time(nome):
    nome = (
        unicodedata
        .normalize("NFD", nome)
        .encode("ascii", "ignore")
        .decode("utf-8")
        .lower()
        .strip()
    )

    nome = nome.replace("-", " ")

    # Padroniza diferentes nomes do Atlético-MG
    if nome in [
        "atletico mg",
        "atletico mineiro",
        "clube atletico mineiro",
        "ca mineiro"
    ]:
        return "atletico mg"

    return nome

def nome_time_portugues(nome):
    traducoes = {
        "Slovenia": "Eslovênia",
        "Slovakia": "Eslováquia",
        "Spain": "Espanha",
        "France": "França",
        "Germany": "Alemanha",
        "Italy": "Itália",
        "England": "Inglaterra",
        "Belgium": "Bélgica",
        "Netherlands": "Holanda",
        "Switzerland": "Suíça",
        "Turkey": "Turquia",
        "Czechia": "República Tcheca",
        "Portugal": "Portugal",
        "Brazil": "Brasil",
        "Argentina": "Argentina",
    }

    return traducoes.get(nome, nome)

def buscar_time(nome_time):
    url = f"{BASE_URL}/teams"

    params = {
        "search": nome_time.replace("-", " ")
    }

    headers = {
        "x-apisports-key": API_KEY
    }

    resposta = requests.get(url, headers=headers, params=params)

    dados = resposta.json()

    if dados["errors"]:
        return {
            "erro": dados["errors"]
        }

    for item in dados["response"]:
        time = item["team"]

        nome_api = time["name"].lower()
        nome_buscado = nome_time.lower()

        nome_api = nome_api.replace("-", " ")
        nome_buscado = nome_buscado.replace("-", " ")

        if nome_api == nome_buscado:
            return {
                "id": time["id"],
                "nome": time["name"],
                "pais": time["country"]
            }

    return {
        "erro": f"Time '{nome_time}' não encontrado."
    }

# def buscar_partidas_data(data):
#    url = f"{BASE_URL}/fixtures"
#
 #   params = {
 #       "date": data
 #   }
#
 #   headers = {
 #       "x-apisports-key": API_KEY
 #   }
#
 #   resposta = requests.get(url, headers=headers, params=params)
#
  #  dados = resposta.json()
#
  #  if dados["errors"]:
  #      return {
  #          "erro": dados["errors"]
  #      }
#
  #  resultado = []
#
   # for partida in dados["response"]:
   #     resultado.append({
   #         "id": partida["fixture"]["id"],
   #         "data": partida["fixture"]["date"],
   #         "status": partida["fixture"]["status"]["short"],
   #         "mandante": partida["teams"]["home"]["name"],
  #          "visitante": partida["teams"]["away"]["name"],
  #          "gols_mandante": partida["goals"]["home"],
  #          "gols_visitante": partida["goals"]["away"],
   #         "competicao": partida["league"]["name"]
   #     })
#
    #return resultado


#partidas = buscar_partidas_data("2026-09-20")

#for partida in partidas:
#    if "São Paulo" in partida["mandante"] or "São Paulo" in partida["visitante"]:
#        print(partida)

#print(buscar_time("Sao Paulo"))

def buscar_jogos_time(team_id, status):
    url = f"https://api.football-data.org/v4/teams/{team_id}/matches"

    headers = {
        "X-Auth-Token": FOOTBALL_DATA_TOKEN,
        "X-Unfold-Goals": "true"
    }

    params = {
        "status": status
    }

    resposta = requests.get(
        url,
        headers=headers,
        params=params
    )

    dados = resposta.json()

    if resposta.status_code != 200:
        return {
            "erro": dados
        }

    resultado = []

    for partida in dados.get("matches", []):

        score = partida["score"]

        if "regularTime" in score:
            gols_mandante = score["regularTime"]["home"]
            gols_visitante = score["regularTime"]["away"]
        else:
            gols_mandante = score["fullTime"]["home"]
            gols_visitante = score["fullTime"]["away"]

        penaltis_mandante = None
        penaltis_visitante = None

        if "penalties" in score:
            penaltis_mandante = score["penalties"]["home"]
            penaltis_visitante = score["penalties"]["away"]

        resultado.append({
            "id": partida["id"],
            "data": partida["utcDate"],
            "status": partida["status"],
            "competicao": partida["competition"]["name"],
            "codigo_competicao": partida["competition"]["code"],
            "mandante": partida["homeTeam"]["name"],
            "visitante": partida["awayTeam"]["name"],
            "gols_mandante": gols_mandante,
            "gols_visitante": gols_visitante,
            "penaltis_mandante": penaltis_mandante,
            "penaltis_visitante": penaltis_visitante

        })

    return resultado

def buscar_jogos_competicao(codigo_competicao, status="FINISHED"):
    url = f"https://api.football-data.org/v4/competitions/{codigo_competicao}/matches"

    headers = {
        "X-Auth-Token": FOOTBALL_DATA_TOKEN
    }

    params = {
        "status": status
    }

    resposta = requests.get(
        url,
        headers=headers,
        params=params
    )
        
    dados = resposta.json()

    if resposta.status_code != 200:
        return {"erro": dados}

    resultado = []

    for partida in dados.get("matches", []):

        score = partida["score"]

        if score.get("duration") == "PENALTY_SHOOTOUT":
            gols_mandante = score["regularTime"]["home"]
            gols_visitante = score["regularTime"]["away"]
        else:
            gols_mandante = score["fullTime"]["home"]
            gols_visitante = score["fullTime"]["away"]

        penaltis_mandante = None
        penaltis_visitante = None

        if "penalties" in score:
            penaltis_mandante = score["penalties"]["home"]
            penaltis_visitante = score["penalties"]["away"]

        resultado.append({
            "id": partida["id"],
            "data": partida["utcDate"],
            "status": partida["status"],
            "competicao": partida["competition"]["name"],
            "codigo_competicao": partida["competition"]["code"],
            "mandante": partida["homeTeam"]["name"],
            "visitante": partida["awayTeam"]["name"],
            "gols_mandante": gols_mandante,
            "gols_visitante": gols_visitante,
            "penaltis_mandante": penaltis_mandante,
            "penaltis_visitante": penaltis_visitante
        })

    return resultado

def buscar_classificacao_competicao(codigo_competicao):
    url = f"https://api.football-data.org/v4/competitions/{codigo_competicao}/standings"

    headers = {
        "X-Auth-Token": FOOTBALL_DATA_TOKEN
    }

    resposta = requests.get(
        url,
        headers=headers
    )

    dados = resposta.json()

    if resposta.status_code != 200:
        return {"erro": dados}

    try:
        classificacao = dados["standings"][0]["table"]
    except (KeyError, IndexError):
        return {"erro": "Classificação não encontrada."}

    resultado = []

    for time in classificacao:
        resultado.append({
            "posicao": time["position"],
            "time": time["team"]["name"],
            "pontos": time["points"],
            "jogos": time["playedGames"],
            "vitorias": time["won"],
            "empates": time["draw"],
            "derrotas": time["lost"]
        })

    return resultado

def buscar_ultimo_jogo(team_id):
    jogos = buscar_jogos_time(team_id, "FINISHED")

    if isinstance(jogos, dict) and "erro" in jogos:
        return jogos

    if not jogos:
        return {
            "erro": "Nenhum jogo finalizado encontrado."
        }

    return jogos[-1]

def buscar_proximo_jogo(team_id):
    jogos = buscar_jogos_time(team_id, "SCHEDULED")

    if isinstance(jogos, dict) and "erro" in jogos:
        return jogos

    if not jogos:
        return {
            "erro": "Nenhum próximo jogo encontrado."
        }

    return jogos[0]

def buscar_jogo_contra_adversario(time1, time2):
    competicoes = [
        "BSA", # Brasileirão
        "PD", # La Liga
        "PL", # Premier League
        "SA", # Serie A
        "BL1", # Bundesliga
        "FL1", # Ligue 1
        "CL", # Champions League
        "EC" # Eurocopa
    ]

    if not time1 or not time2:
        return None

    time1_normalizado = normalizar_nome_time(time1)
    time2_normalizado = normalizar_nome_time(time2)

    jogos_encontrados = []

    for codigo_competicao in competicoes:

        jogos = buscar_jogos_competicao(codigo_competicao)

        if isinstance(jogos, dict) and "erro" in jogos:
            continue

        for jogo in jogos:

            mandante_normalizado = normalizar_nome_time(jogo["mandante"])

            visitante_normalizado = normalizar_nome_time(jogo["visitante"])

            confronto_encontrado = (
                (
                    time1_normalizado in mandante_normalizado
                    and time2_normalizado in visitante_normalizado
                )
                or
                (
                    time2_normalizado in mandante_normalizado
                    and time1_normalizado in visitante_normalizado
                )
            )

            if confronto_encontrado:
                jogos_encontrados.append(jogo)

    if not jogos_encontrados:
        return {
            "erro": "Nenhum jogo encontrado contra esse adversário."
        }

    jogos_encontrados.sort(
        key=lambda jogo: jogo["data"]
    )

    return jogos_encontrados[-1]
