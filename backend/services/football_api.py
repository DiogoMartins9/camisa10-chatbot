import os
import requests
import unicodedata
import time
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime, timezone

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

API_KEY = os.getenv("API_FOOTBALL_KEY")
FOOTBALL_DATA_TOKEN = os.getenv("FOOTBALL_DATA_TOKEN")

BASE_URL = "https://v3.football.api-sports.io"

_CACHE_COMPETICOES = {
    "dados": None,
    "atualizado_em": 0
}

_CACHE_TIMES_COMPETICAO = {}
TEMPO_CACHE_SEGUNDOS = 3600
TEMPO_CACHE_TIMES_SEGUNDOS = 86400


def normalizar_nome_time(nome):
    if not nome:
        return ""

    nome = (
        unicodedata
        .normalize("NFD", nome)
        .encode("ascii", "ignore")
        .decode("utf-8")
        .lower()
        .strip()
    )

    nome = nome.replace("-", " ")
    nome = " ".join(nome.split())

    aliases = {
    # São Paulo
    "sao paulo fc": "sao paulo",
    "sao paulo": "sao paulo",
    "spfc": "sao paulo",

    # Palmeiras
    "se palmeiras": "palmeiras",
    "palmeiras": "palmeiras",

    # Flamengo
    "cr flamengo": "flamengo",
    "flamengo": "flamengo",
    "clube de regatas do flamengo": "flamengo",

    # Fluminense
    "fluminense fc": "fluminense",
    "fluminense": "fluminense",

    # Corinthians
    "sc corinthians paulista": "corinthians",
    "corinthians": "corinthians",

    # Santos
    "santos fc": "santos",
    "santos": "santos",

    # Outros aliases já utilizados
    "real madrid cf": "real madrid",
    "fc real madrid": "real madrid",
    "fc barcelona": "barcelona",
    "barcelona fc": "barcelona",
    "atletico madrid": "atletico de madrid",
    "club atletico de madrid": "atletico de madrid",
    "atletico mineiro": "atletico mg",
    "clube atletico mineiro": "atletico mg",
    "ca mineiro": "atletico mg",
}

    return aliases.get(nome, nome)

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

def buscar_time(nome_time, pais=None):
    """
    Localiza um time na API-Football pelo nome e, opcionalmente,
    valida o país para evitar correspondências incorretas.
    """

    if not API_KEY:
        return {
            "erro": "A chave API_FOOTBALL_KEY não foi configurada."
        }

    if not nome_time:
        return {
            "erro": "O nome do time não foi informado."
        }

    url = f"{BASE_URL}/teams"

    params = {
        "search": (
            unicodedata
            .normalize("NFD", nome_time)
            .encode("ascii", "ignore")
            .decode("utf-8")
        )
    }

    headers = {
        "x-apisports-key": API_KEY
    }

    try:
        resposta = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=20
        )

        resposta.raise_for_status()
        dados = resposta.json()

    except requests.RequestException:
        return {
            "erro": "Não foi possível consultar a API-Football."
        }

    except ValueError:
        return {
            "erro": "A API-Football retornou uma resposta inválida."
        }

    if dados.get("errors"):
        return {
            "erro": dados["errors"]
        }

    nome_buscado = normalizar_nome_time(nome_time)

    for item in dados.get("response", []):
        time = item.get("team", {})

        nome_api = normalizar_nome_time(time.get("name"))

        if nome_api != nome_buscado:
            continue

        pais_api = normalizar_nome_time(time.get("country"))
        pais_buscado = normalizar_nome_time(pais) if pais else None

        if pais_buscado and pais_api != pais_buscado:
            continue

        return {
            "id": time.get("id"),
            "nome": time.get("name"),
            "pais": time.get("country")
        }

    return {
        "erro": f"Time '{nome_time}' não encontrado na API-Football."
    }

_CACHE_TIMES_PRINCIPAIS = {
    "dados": None,
    "atualizado_em": 0
}

COMPETICOES_PRINCIPAIS = {
    71: "Brasileirão Série A",
    39: "Premier League",
    140: "La Liga",
    78: "Bundesliga",
    135: "Serie A",
    61: "Ligue 1",
    2: "Champions League",
    13: "Libertadores",
    11: "Copa Sul-Americana"
}


def buscar_times_principais_competicoes(season=2026):
    """
    Busca os clubes das principais competições na API-Football.
    Reúne clubes repetidos pelo ID e informa suas competições.
    """

    agora = time.time()

    # Verifica se existe uma lista em cache para essa temporada.
    cache = _CACHE_TIMES_PRINCIPAIS

    if (
        cache["dados"] is not None
        and cache.get("season") == season
        and agora - cache["atualizado_em"] < TEMPO_CACHE_SEGUNDOS
    ):
        return cache["dados"]

    if not API_KEY:
        return {
            "erro": "A chave API_FOOTBALL_KEY não foi configurada."
        }

    times_por_id = {}
    avisos = []

    url = f"{BASE_URL}/teams"

    headers = {
        "x-apisports-key": API_KEY
    }

    for league_id, nome_competicao in COMPETICOES_PRINCIPAIS.items():

        params = {
            "league": league_id,
            "season": season
        }

        try:
            resposta = requests.get(
                url,
                headers=headers,
                params=params,
                timeout=20
            )

            resposta.raise_for_status()
            dados = resposta.json()

        except requests.RequestException as erro:
            avisos.append({
                "competicao": nome_competicao,
                "erro": str(erro)
            })
            continue

        except ValueError:
            avisos.append({
                "competicao": nome_competicao,
                "erro": "A API retornou uma resposta inválida."
            })
            continue

        if dados.get("errors"):
            avisos.append({
                "competicao": nome_competicao,
                "erro": dados["errors"]
            })
            continue

        for item in dados.get("response", []):

            time_api = item.get("team", {})
            time_id = time_api.get("id")

            if not time_id:
                continue

            if time_id not in times_por_id:
                times_por_id[time_id] = {
                    "id": time_id,
                    "nome": time_api.get("name"),
                    "logo": time_api.get("logo"),
                    "pais": time_api.get("country"),
                    "competicoes": []
                }

            if nome_competicao not in times_por_id[time_id]["competicoes"]:
                times_por_id[time_id]["competicoes"].append(
                    nome_competicao
                )

    resultado = list(times_por_id.values())

    if not resultado:
        return {
            "erro": "Não foi possível encontrar clubes nas competições.",
            "avisos": avisos
        }

    resultado.sort(key=lambda clube: clube["nome"] or "")

    # Salva o resultado no cache.
    _CACHE_TIMES_PRINCIPAIS["dados"] = resultado
    _CACHE_TIMES_PRINCIPAIS["atualizado_em"] = time.time()
    _CACHE_TIMES_PRINCIPAIS["season"] = season

    if avisos:
        return {
            "times": resultado,
            "avisos": avisos
        }

    return resultado

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
    chave_cache = ("time", team_id, status)
    agora_cache = time.time()

    if chave_cache in _CACHE_JOGOS:
        horario, resultado_cache = _CACHE_JOGOS[chave_cache]

        if agora_cache - horario < _TEMPO_CACHE:
            return resultado_cache
        
    url = f"https://api.football-data.org/v4/teams/{team_id}/matches"

    headers = {
        "X-Auth-Token": FOOTBALL_DATA_TOKEN,
        "X-Unfold-Goals": "true"
    }

    params = {
        "status": status
    }

    try:
        resposta = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=15
        )

        try: 
            dados = resposta.json()
        except ValueError:
            dados = {
                "mensagem": "A API retornou uma resposta inválida."
            }

    except requests.RequestException as erro:
        return {
            "erro": str(erro)
        }

    if resposta.status_code != 200:
        return {
            "erro": dados,
            "codigo": resposta.status_code
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

    _CACHE_JOGOS[chave_cache] = (time.time(), resultado)

    return resultado

_CACHE_JOGOS = {}
_TEMPO_CACHE = 60 * 5  # 5 minutos

def buscar_jogos_competicao(codigo_competicao, status="FINISHED"):
    chave_cache = (codigo_competicao, status)
    agora_cache = time.time()

    if chave_cache in _CACHE_JOGOS:
        horario, resultado_cache = _CACHE_JOGOS[chave_cache]
        
        if agora_cache - horario < _TEMPO_CACHE:
            return resultado_cache

    url = f"https://api.football-data.org/v4/competitions/{codigo_competicao}/matches"

    headers = {
        "X-Auth-Token": FOOTBALL_DATA_TOKEN
    }

    params = {}
    if status:
        params["status"] = status

    try:
        resposta = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=15
        )
        dados = resposta.json()

    except requests.RequestException as erro:
        return {"erro": str(erro)}
    except ValueError:
        return {"erro": "A API retornou uma resposta inválida."}

    if resposta.status_code != 200:
        return {"erro": dados}

    resultado = []

    for partida in dados.get("matches", []):

        score = partida.get("score") or {}
        regular_time = score.get("regularTime") or {} 
        full_time = score.get("fullTime") or {}
        penalties = score.get("penalties") or {}

        if score.get("duration") == "PENALTY_SHOOTOUT":
            gols_mandante = regular_time.get("home")
            gols_visitante = regular_time.get("away")
        else:
            gols_mandante = full_time.get("home")
            gols_visitante = full_time.get("away")

        resultado.append({
            "id": partida["id"],
            "data": partida["utcDate"],
            "status": partida["status"],
            "competicao": partida["competition"]["name"],
            "codigo_competicao": partida["competition"]["code"],
            "temporada": partida.get("season", {}).get("startDate"),
            "mandante": partida["homeTeam"]["name"],
            "visitante": partida["awayTeam"]["name"],
            "gols_mandante": gols_mandante,
            "gols_visitante": gols_visitante,
            "penaltis_mandante": penalties.get("home"),
            "penaltis_visitante": penalties.get("away")
        })

    _CACHE_JOGOS[chave_cache] = (time.time(), resultado)

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


def buscar_competicoes_football_data():
    agora = time.time()

    if (
        _CACHE_COMPETICOES["dados"] is not None
        and agora - _CACHE_COMPETICOES["atualizado_em"] < TEMPO_CACHE_SEGUNDOS
    ):
        return _CACHE_COMPETICOES["dados"]

    url = "https://api.football-data.org/v4/competitions"
    headers = {
        "X-Auth-Token": FOOTBALL_DATA_TOKEN
    }

    try:
        resposta = requests.get(
            url,
            headers=headers,
            timeout=30
        )
        dados = resposta.json()
    except requests.RequestException as erro:
        return {
            "erro": str(erro)
        }
    except ValueError:
        return {
            "erro": "A API retornou uma resposta inválida."
        }

    if resposta.status_code != 200:
        return {
            "erro": dados,
            "codigo": resposta.status_code
        }

    competicoes = []

    for competicao in dados.get("competitions", []):
        competicoes.append({
            "id": competicao.get("id"),
            "nome": competicao.get("name"),
            "codigo": competicao.get("code"),
            "pais": competicao.get("area", {}).get("name")
        })

    _CACHE_COMPETICOES["dados"] = competicoes
    _CACHE_COMPETICOES["atualizado_em"] = time.time()

    return competicoes

def buscar_times_competicao(codigo_competicao):
    agora = time.time()

    cache = _CACHE_TIMES_COMPETICAO.get(codigo_competicao)

    if cache and agora - cache["atualizado_em"] < TEMPO_CACHE_TIMES_SEGUNDOS:
        return cache["dados"]

    url = (
        "https://api.football-data.org/v4/competitions/"
        f"{codigo_competicao}/teams"
    )

    headers = {
        "X-Auth-Token": FOOTBALL_DATA_TOKEN
    }

    try:
        resposta = requests.get(url, headers=headers, timeout=30)
        dados = resposta.json()
    except requests.RequestException as erro:
        return {
            "erro": str(erro)
        }
    except ValueError:
        return {
            "erro": "A API retornou uma resposta inválida."
        }

    if resposta.status_code != 200:
        return {
            "erro": dados,
            "codigo": resposta.status_code
        }

    times = []

    for time_api in dados.get("teams", []):
        times.append({
            "id": time_api.get("id"),
            "nome": time_api.get("name"),
            "pais": time_api.get("area", {}).get("name"),
            "competicoes": time_api.get("runningCompetitions", []),
            "logo": time_api.get("crest"),
        })

    _CACHE_TIMES_COMPETICAO[codigo_competicao] = {
        "dados": times,
        "atualizado_em": time.time()
    }

    return times

def buscar_times_todas_competicoes():
    """
    Reúne os clubes de todas as competições disponíveis
    na conta da football-data.org.
    Remove clubes duplicados pelo ID.
    """

    competicoes = buscar_competicoes_football_data()

    if isinstance(competicoes, dict) and competicoes.get("erro"):
        return competicoes

    codigos_permitidos = {
        "BSA",  # Brasileirão Série A
        "PL",   # Premier League
        "PD",   # La Liga
        "BL1",  # Bundesliga
        "SA",   # Serie A italiana
        "FL1",  # Ligue 1
        "CL",   # Champions League
        "CLI",  # Libertadores
    }

    competicoes = [
        competicao
        for competicao in competicoes
        if competicao.get("codigo") in codigos_permitidos
    ]

    times_por_id = {}
    avisos = []

    for competicao in competicoes:
        codigo = competicao.get("codigo")
        nome_competicao = competicao.get("nome")

        if not codigo:
            continue

        resultado = buscar_times_competicao(codigo)

        if isinstance(resultado, dict) and resultado.get("erro"):
            avisos.append(
                f"{nome_competicao}: {resultado['erro']}"
            )
            continue

        for time in resultado:
            time_id = time.get("id")

            if time_id is None:
                continue

            if time_id not in times_por_id:
                times_por_id[time_id] = {
                    "id": time_id,
                    "nome": time.get("nome"),
                    "pais": time.get("pais"),
                    "logo": time.get("logo"),
                    "competicoes": []
                }

            if nome_competicao not in times_por_id[time_id]["competicoes"]:
                times_por_id[time_id]["competicoes"].append(
                    nome_competicao
                )

    times = sorted(
        times_por_id.values(),
        key=lambda time: (time.get("nome") or "").casefold()
    )

    return {
        "times": times,
        "avisos": avisos
    }


def buscar_competicoes_do_time(nome_time):
    competicoes = buscar_competicoes_football_data()

    if isinstance(competicoes, dict) and "erro" in competicoes:
        print("Erro ao buscar competições:", competicoes)
        return competicoes

    nome_busca = normalizar_nome_time(nome_time)
    encontradas = []

    for competicao in competicoes:
        codigo = competicao.get("codigo")

        if not codigo:
            continue

        classificacao = buscar_classificacao_competicao(codigo)

        if isinstance(classificacao, dict) and "erro" in classificacao:
            print(
                f"Erro ao consultar {competicao.get('nome')}:", classificacao
            )
            continue

        for time in classificacao:
            nome_api = normalizar_nome_time(time["time"])

            if nome_busca == nome_api:
                encontradas.append({
                    "competicao": competicao["nome"],
                    "codigo": codigo,
                    "time": time["time"],
                    "posicao": time["posicao"],
                    "pontos": time["pontos"],
                    "jogos": time["jogos"],
                    "vitorias": time["vitorias"],
                    "empates": time["empates"],
                    "derrotas": time["derrotas"]
                })
                break

    return encontradas


def buscar_time_football_data(nome_time):
    nome_buscado = normalizar_nome_time(nome_time)

    competicoes = buscar_competicoes_football_data()

    if isinstance(competicoes, dict) and "erro" in competicoes:
        return competicoes

    for competicao in competicoes:
        codigo = competicao.get("codigo")

        if not codigo:
            continue

        times = buscar_times_competicao(codigo)

        if isinstance(times, dict) and "erro" in times:
            continue

        for time_api in times:
            nome_api = normalizar_nome_time(time_api.get("nome", ""))
            nome_buscado_sem_sufixo = nome_buscado.removesuffix(" fc")
            nome_api_sem_sufixo = nome_api.removesuffix(" fc")

            if (
                nome_buscado == nome_api
                or nome_buscado_sem_sufixo == nome_api_sem_sufixo
                
            ):
                return time_api

    return {
        "erro": f"Time '{nome_time}' não encontrado nas competições disponíveis."
    }

def buscar_ultimo_jogo(team_id):
    jogos = buscar_jogos_time(team_id, "FINISHED")

    if isinstance(jogos, dict) and "erro" in jogos:
        return jogos

    if not jogos:
        return {
            "erro": "Nenhum jogo finalizado encontrado."
        }

    return jogos[-1]

def buscar_ultimos_jogos(team_id, limite=5):
    jogos = buscar_jogos_time(team_id, "FINISHED")

    if isinstance(jogos, dict) and "erro" in jogos:
        return jogos

    if not jogos:
        return []

    jogos.sort(
        key=lambda jogo: datetime.fromisoformat(
            jogo["data"].replace("Z", "+00:00")
        ),
        reverse=True
    )

    return jogos[:limite]

def buscar_proximo_jogo(team_id):
    jogos = buscar_jogos_time(team_id, "SCHEDULED")

    if isinstance(jogos, dict) and "erro" in jogos:
        return jogos

    if not jogos:
        return {
            "erro": "Nenhum próximo jogo encontrado."
        }

    return jogos[0]

def buscar_proximos_jogos(team_id, quantidade=5):
    jogos = buscar_jogos_time(team_id, "SCHEDULED")

    if isinstance(jogos, dict) and "erro" in jogos:
        return jogos

    if not jogos:
        return {
            "erro": "Nenhum próximo jogo encontrado."
        }

    return jogos[:quantidade]

def buscar_historico_confrontos(id_partida, limite=10):
    url = (
        f"https://api.football-data.org/v4/"
        f"matches/{id_partida}/head2head"
    )

    headers = {
        "X-Auth-Token": FOOTBALL_DATA_TOKEN
    }

    params = {
        "limit": limite
    }

    try:
        resposta = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=15
        )
        dados = resposta.json()

    except requests.RequestException as erro:
        return {"erro": str(erro)}

    except ValueError:
        return {"erro": "A API retornou uma resposta inválida."}

    if resposta.status_code != 200:
        return {"erro": dados}

    resultado = []

    for partida in dados.get("matches", []):
        score = partida.get("score") or {}
        full_time = score.get("fullTime") or {}
        penalties = score.get("penalties") or {}

        resultado.append({
            "id": partida["id"],
            "data": partida["utcDate"],
            "status": partida["status"],
            "competicao": partida["competition"]["name"],
            "codigo_competicao": partida["competition"]["code"],
            "temporada": partida.get("season", {}).get("startDate"),
            "mandante": partida["homeTeam"]["name"],
            "visitante": partida["awayTeam"]["name"],
            "gols_mandante": full_time.get("home"),
            "gols_visitante": full_time.get("away"),
            "penaltis_mandante": penalties.get("home"),
            "penaltis_visitante": penalties.get("away")
        })

    return resultado

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
    ids_partidas = []

    for codigo_competicao in competicoes:

        jogos = buscar_jogos_competicao(codigo_competicao, status=None)

        if isinstance(jogos, dict) and "erro" in jogos:
            print(
                f"Erro ao buscar jogos da competição {codigo_competicao}: {jogos['erro']}"
            )
            continue

        for jogo in jogos:

            mandante_normalizado = normalizar_nome_time(jogo["mandante"])

            visitante_normalizado = normalizar_nome_time(jogo["visitante"])

            confronto_encontrado = (
                (
                    time1_normalizado == mandante_normalizado
                    and time2_normalizado == visitante_normalizado
                )
                or
                (
                    time2_normalizado == mandante_normalizado
                    and time1_normalizado == visitante_normalizado
                )
            )

            if confronto_encontrado:
                jogos_encontrados.append(jogo)
                ids_partidas.append(jogo["id"])

    historico = []

    if ids_partidas:

        historico = buscar_historico_confrontos(
            ids_partidas[0],
            limite=10
        )


        if isinstance(historico, dict) and "erro" in historico:
            print(
                "Erro ao buscar histórico:",
                historico["erro"]
            )
            historico = []
    else:
        print(
            "Nenhum ID de confronto foi encontrado para:",
            time1,
            "e",
            time2
        )
        historico = []

    if not isinstance(historico, list):
        historico = []

    jogos_por_id = {
        jogo["id"]: 
        jogo for jogo in jogos_encontrados
        }

    for jogo in historico:
        jogos_por_id[jogo["id"]] = jogo

    jogos_encontrados = list(jogos_por_id.values())

    agora = datetime.now(timezone.utc)

    jogos_finalizados = []
    jogos_futuros = []

    for jogo in jogos_encontrados:
        data_jogo = datetime.fromisoformat(
            jogo["data"].replace("Z", "+00:00")
        )

        if jogo["status"] == "FINISHED":
            jogos_finalizados.append((data_jogo, jogo))

        elif jogo["status"] in ("SCHEDULED", "TIMED"):
            if data_jogo >= agora:
                jogos_futuros.append((data_jogo, jogo))

    jogos_finalizados.sort(key=lambda item: item[0], reverse=True)
    
    jogos_futuros.sort(key=lambda item: item[0])

    return {
        "ultimo_jogo": (jogos_finalizados[0][1] 
                        if jogos_finalizados 
                        else None),
        "proximo_jogo": (jogos_futuros[0][1] 
                         if jogos_futuros 
                         else None)
    }

    