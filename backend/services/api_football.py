
import os
from datetime import date, timedelta
from functools import lru_cache

import requests
from dotenv import load_dotenv

load_dotenv()

API_FOOTBALL_URL = "https://v3.football.api-sports.io"
API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY")


@lru_cache(maxsize=64)
def _buscar_elenco_time_cacheado(team_id: int) -> dict:
    """
    Consulta e armazena em cache o elenco de uma equipe.
    """
    resposta = requests.get(
        f"{API_FOOTBALL_URL}/players/squads",
        headers={
            "x-apisports-key": API_FOOTBALL_KEY
        },
        params={
            "team": team_id
        },
        timeout=20
    )

    resposta.raise_for_status()
    dados = resposta.json()

    if dados.get("errors"):
        raise ValueError("A API-Football retornou um erro.")

    equipes = dados.get("response", [])

    if not equipes:
        raise ValueError("Elenco não encontrado.")

    equipe = equipes[0]

    jogadores = []

    for jogador in equipe.get("players", []):
        jogadores.append({
            "id": jogador.get("id"),
            "nome": jogador.get("name"),
            "idade": jogador.get("age"),
            "numero": jogador.get("number"),
            "posicao": jogador.get("position"),
            "foto": jogador.get("photo")
        })

    return {
        "time": {
            "id": equipe.get("team", {}).get("id"),
            "nome": equipe.get("team", {}).get("name"),
            "logo": equipe.get("team", {}).get("logo")
        },
        "jogadores": jogadores
    }


def buscar_elenco_time(team_id: int) -> dict:
    """
    Busca o elenco de um time pelo ID da API-Football.
    Resultados bem-sucedidos ficam armazenados em cache.
    """

    if team_id <= 0:
        return {"erro": "ID do time inválido."}

    if not API_FOOTBALL_KEY:
        return {
            "erro": "A variável API_FOOTBALL_KEY não está configurada."
        }

    try:
        return _buscar_elenco_time_cacheado(team_id)

    except requests.RequestException:
        return {
            "erro": "Não foi possível consultar o elenco na API-Football."
        }

    except (ValueError, KeyError, IndexError):
        return {
            "erro": "Não foi possível obter os dados do elenco."
        }



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
            "id_competicao": league.get("id"),
            "pais": league.get("country"),
            "logo_competicao": league.get("logo"),
            "mandante": mandante.get("name"),
            "id_mandante": mandante.get("id"),
            "logo_mandante": mandante.get("logo"),
            "visitante": visitante.get("name"),
            "id_visitante": visitante.get("id"),
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

def buscar_jogos_por_time(time_id: int, tipo: str) -> dict:
    """
    Busca partidas de um time específico.

    tipo pode ser:
    - live: partidas em andamento
    - next: próxima partida
    -last: última partida
    """

    if not API_FOOTBALL_KEY:
        return {
            "erro": "A variável API_FOOTBALL_KEY não está configurada."
        }

    hoje = date.today()

    filtros = {
        "live": {"live": "all"},
        "next": {
            "from": hoje.isoformat(),
            "to": (hoje + timedelta(days=3)).isoformat()
        },
        "last": {"last": 1}
    }
    
    if tipo not in filtros:
        return {
            "erro": "Tipo de consulta inválido."
        }

    parametros = {
        "team": time_id,
        "season": hoje.year,
        "timezone": "America/Sao_Paulo",
        **filtros[tipo]
    }

    try:
        resposta = requests.get(
            f"{API_FOOTBALL_URL}/fixtures",
            headers={
                "x-apisports-key": API_FOOTBALL_KEY
            },
            params=parametros,
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
        "tipo": tipo,
        "quantidade": len(jogos),
        "jogos": jogos
    }
    
def buscar_detalhes_partida(fixture_id: int) -> dict:
    """
    Busca os dados gerais de uma partida pelo ID da API-Football.
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
                "id": fixture_id,
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
        
    except ValueError:
        return {
            "erro": "A API-Football retornou uma resposta inválida."
        }
    
    if dados.get("errors"):
        return {
            "erro": "A API-Football retornou um erro.",
            "detalhes": dados["errors"]
        }
        
    partidas = dados.get("response", [])
    
    if not partidas:
        return {
            "erro": "Partida não encontrada."
        }
        
    item = partidas[0]
    
    fixture = item.get("fixture", {})
    league = item.get("league", {})
    teams = item.get("teams", {})
    goals = item.get("goals", {})
    score = item.get("score", {})
    
    mandante = teams.get("home", {})
    visitante = teams.get("away", {})
    status = fixture.get("status", {})
    
    return {
        "id": fixture.get("id"),
        "data": fixture.get("date"),
        "status": status.get("short"),
        "status_descricao": status.get("long"),
        "minuto": status.get("elapsed"),
        "estadio": fixture.get("venue", {}).get("name"),
        "cidade": fixture.get("venue", {}).get("city"),
        "arbitro": fixture.get("referee"),

        "competicao": {
            "id": league.get("id"),
            "nome": league.get("name"),
            "pais": league.get("country"),
            "logo": league.get("logo"),
            "temporada": league.get("season"),
            "rodada": league.get("round")
        },

        "mandante": {
            "id": mandante.get("id"),
            "nome": mandante.get("name"),
            "logo": mandante.get("logo"),
            "vencedor": mandante.get("winner")
        },

        "visitante": {
            "id": visitante.get("id"),
            "nome": visitante.get("name"),
            "logo": visitante.get("logo"),
            "vencedor": visitante.get("winner")
        },

        "gols": {
            "mandante": goals.get("home"),
            "visitante": goals.get("away")
        },

        "placar": {
            "intervalo": score.get("halftime"),
            "final": score.get("fulltime"),
            "prorrogacao": score.get("extratime"),
            "penaltis": score.get("penalty")
        }
    }

def buscar_detalhes_completos_partida(fixture_id: int) -> dict:
    """
    Retorna informações gerais, estatísticas, escalações
    e eventos de uma partida.
    """
    
    partida = buscar_detalhes_partida(fixture_id)
    
    if "erro" in partida:
        return partida
    
    headers = {
        "x-apisports-key": API_FOOTBALL_KEY
    }
    
    endpoints = {
        "estatisticas": "fixtures/statistics",
        "escalacoes": "fixtures/lineups",
        "eventos": "fixtures/events"
    }
    
    resultado = {
        "partida": partida,
        "estatisticas": [],
        "escalacoes": [],
        "eventos": [],
        "avisos": {}
    }
    
    for chave, endpoint in endpoints.items():
        try:
            resposta = requests.get(
                f"{API_FOOTBALL_URL}/{endpoint}",
                headers=headers,
                params={"fixture": fixture_id},
                timeout=20
            )
            
            resposta.raise_for_status()
            dados = resposta.json()
            
            if dados.get("errors"):
                resultado["avisos"][chave] = dados["errors"]
                continue
            
            resultado[chave] = dados.get("response", [])
            
        except requests.RequestException:
            resultado["avisos"][chave] = (
                "Não foi possível consultar este recurso."
            )
            
        except ValueError:
            resultado["avisos"][chave] = (
                "A API retornou uma resposta inválida."
            )
            
    return resultado


@lru_cache(maxsize=32)
def buscar_competicoes_api_football(
    pais: str = None,
    temporada: int = None,
    atuais: bool = True
) -> list:
    """
    Lista competições disponíveis na API-Football.

    Permite filtrar por país, temporada e competições atuais.
    """

    if not API_FOOTBALL_KEY:
        return []

    parametros = {}

    if pais:
        parametros["country"] = pais

    if atuais:
        parametros["current"] = "true"

    if temporada:
        parametros["season"] = temporada

    try:
        resposta = requests.get(
            f"{API_FOOTBALL_URL}/leagues",
            headers={
                "x-apisports-key": API_FOOTBALL_KEY
            },
            params=parametros,
            timeout=20
        )

        resposta.raise_for_status()
        dados = resposta.json()

        if dados.get("errors"):
            print(
                "Erro ao buscar competições:",
                dados["errors"]
            )
            return []

        competicoes = []

        for item in dados.get("response", []):
            liga = item.get("league", {})
            pais_info = item.get("country", {})

            temporadas = item.get("seasons", [])

            competicoes.append({
                "id": liga.get("id"),
                "nome": liga.get("name"),
                "tipo": liga.get("type"),
                "logo": liga.get("logo"),
                "pais": pais_info.get("name"),
                "bandeira": pais_info.get("flag"),
                "temporadas": [
                    {
                        "ano": temporada_info.get("year"),
                        "atual": temporada_info.get("current"),
                        "classificacao": temporada_info.get(
                            "coverage", {}
                        ).get("standings", False),
                        "jogos": temporada_info.get(
                            "coverage", {}
                        ).get("fixtures", {})
                    }
                    for temporada_info in temporadas
                ]
            })

        return competicoes

    except requests.RequestException as erro:
        print(
            "Erro na comunicação com API-Football:",
            erro
        )
        return []

    except ValueError as erro:
        print(
            "Erro ao interpretar resposta da API-Football:",
            erro
        )
        return []
    

def formatar_detalhes_partida(dados: dict, classificacao=None, tipo_competicao=None, codigo_competicao=None) -> dict:
    """
    Organiza os dados da API-Football no formato esperado
    pela tela DetalhesJogos do aplicativo.
    """

    if "erro" in dados:
        return dados

    partida = dados.get("partida", {})
    mandante = partida.get("mandante", {})
    visitante = partida.get("visitante", {})
    competicao = partida.get("competicao", {})

    # Converte valores de estatísticas para números.
    def obter_estatistica(lista, nome):
        for estatistica in lista:
            if estatistica.get("type") == nome:
                valor = estatistica.get("value")

                if valor is None:
                    return None

                if isinstance(valor, str):
                    valor = valor.replace("%", "").strip()

                try:
                    return float(valor) if "." in str(valor) else int(valor)
                except (ValueError, TypeError):
                    return None

        return None

    estatisticas_api = dados.get("estatisticas", [])

    stats_mandante = []
    stats_visitante = []

    for item in estatisticas_api:
        if item.get("team", {}).get("id") == mandante.get("id"):
            stats_mandante = item.get("statistics", [])

        elif item.get("team", {}).get("id") == visitante.get("id"):
            stats_visitante = item.get("statistics", [])

    def valores_estatistica(nome):
        return [
            obter_estatistica(stats_mandante, nome),
            obter_estatistica(stats_visitante, nome)
        ]

    estatisticas = {
        "posse": valores_estatistica("Ball Possession"),
        "finalizacoes": valores_estatistica("Total Shots"),
        "chutesGol": valores_estatistica("Shots on Goal"),
        "escanteios": valores_estatistica("Corner Kicks"),
        "faltas": valores_estatistica("Fouls"),
        "amarelos": valores_estatistica("Yellow Cards")
    }

    # Traduz as posições dos jogadores.
    def traduzir_posicao(posicao):
        posicoes = {
            "G": "GOL",
            "D": "DEF",
            "M": "MEI",
            "F": "ATA"
        }

        return posicoes.get(posicao, posicao)

    # Organiza os jogadores de cada equipe.
    def organizar_escalacao(escalacao):
        if not escalacao:
            return {
                "formacao": None,
                "titulares": [],
                "reservas": []
            }

        titulares = []

        for item in escalacao.get("startXI", []):
            jogador = item.get("player", {})
            grid = jogador.get("grid")

            x = None
            y = None

            if grid:
                try:
                    linha, coluna = map(int, grid.split(":"))

                    # Distribui os jogadores horizontalmente.
                    jogadores_linha = [
                        p for p in escalacao.get("startXI", [])
                        if p.get("player", {}).get("grid")
                        and p["player"]["grid"].split(":")[0] == str(linha)
                    ]

                    posicao_linha = next(
                        i for i, p in enumerate(jogadores_linha)
                        if p.get("player", {}).get("id") == jogador.get("id")
                    )

                    quantidade = len(jogadores_linha)
                    x = round((posicao_linha + 1) * 100 / (quantidade + 1))

                    maior_linha = max(
                        int(p["player"]["grid"].split(":")[0])
                        for p in escalacao.get("startXI", [])
                        if p.get("player", {}).get("grid")
                    )

                    y_base = 100 - ((linha - 0.5) * 80 / maior_linha)

                    # Inverte o campo para o time visitante.
                    if escalacao.get("team", {}).get("id") == visitante.get("id"):
                        y_base = 100 - y_base

                    y = round(y_base)

                except (ValueError, StopIteration, IndexError):
                    pass

            titulares.append({
                "id": jogador.get("id"),
                "n": jogador.get("number"),
                "nome": jogador.get("name"),
                "pos": traduzir_posicao(jogador.get("pos")),
                "x": x,
                "y": y
            })

        reservas = []

        for item in escalacao.get("substitutes", []):
            jogador = item.get("player", {})

            reservas.append({
                "n": jogador.get("number"),
                "nome": jogador.get("name"),
                "pos": traduzir_posicao(jogador.get("pos"))
            })

        return {
            "formacao": escalacao.get("formation"),
            "titulares": titulares,
            "reservas": reservas
        }

    escalacoes_api = dados.get("escalacoes", [])

    escalacao_mandante = next(
        (
            e for e in escalacoes_api
            if e.get("team", {}).get("id") == mandante.get("id")
        ),
        None
    )

    escalacao_visitante = next(
        (
            e for e in escalacoes_api
            if e.get("team", {}).get("id") == visitante.get("id")
        ),
        None
    )

    escalacoes = {
        "mandante": organizar_escalacao(escalacao_mandante),
        "visitante": organizar_escalacao(escalacao_visitante)
    }

    # Organiza os eventos da partida.
    eventos = []

    for evento in dados.get("eventos", []):
        tipo_api = evento.get("type")
        detalhe = evento.get("detail", "")
        jogador = evento.get("player", {})
        assistencia = evento.get("assist", {})
        tempo = evento.get("time", {})

        minuto = tempo.get("elapsed")

        if tempo.get("extra") is not None:
            minuto = f"{minuto}+{tempo['extra']}"

        equipe = evento.get("team", {}).get("name")

        if tipo_api == "Goal":
            eventos.append({
                "minuto": minuto,
                "tipo": "gol",
                "equipe": equipe,
                "jogador": jogador.get("name"),
                "assistencia": assistencia.get("name")
            })

        elif tipo_api == "Card":
            eventos.append({
                "minuto": minuto,
                "tipo": "cartao",
                "cartao": (
                    "vermelho" if "Red" in detalhe else "amarelo"
                ),
                "equipe": equipe,
                "jogador": jogador.get("name"),
                "descricao": evento.get("comments")
            })

        elif tipo_api == "subst":
            eventos.append({
                "minuto": minuto,
                "tipo": "substituicao",
                "equipe": equipe,
                "entrou": assistencia.get("name"),
                "saiu": jogador.get("name")
            })
            
    classificacao_tela = []
    
    if isinstance(classificacao, list):
        for time in classificacao:
            classificacao_tela.append({
                "pos": time.get("posicao"),
                "equipe": time.get("time"),
                "pts": time.get("pontos"),
                "j": time.get("jogos"),
                "v": time.get("vitorias"),
                "e": time.get("empates"),
                "d": time.get("derrotas"),
                "sg": time.get("saldo_gols")
            })
    
    def traduzir_status(codigo, descricao):
        status = {
            "TBD": "A definir",
            "NS": "Não iniciada",
            "1H": "Primeiro tempo",
            "HT": "Intervalo",
            "2H": "Segundo tempo",
            "ET": "Prorrogação",
            "BT": "Intervalo da prorrogação",
            "P": "Disputa de pênaltis",
            "SUSP": "Partida suspensa",
            "INT": "Partida interrompida",
            "FT": "Encerrada",
            "AET": "Encerrada após prorrogação",
            "PEN": "Encerrada nos pênaltis",
            "PST": "Adiada",
            "CANC": "Cancelada",
            "ABD": "Abandonada",
            "AWD": "Vitória por W.O.",
            "WO": "Vitória por W.O.",
            "LIVE": "Em andamento"
        }
        
        return status.get(codigo, descricao)
    
    def traduzir_fase(fase):
        if not fase:
            return fase
        
        traducoes = {
            "league stage": "Fase de Liga",
            "group stage": "Fase de Grupos",
            "regular season": "Temporada Regular",
            "preliminary round": "Fase Preliminar",
            "qualifying round": "Fase Classificatória",
            "play-offs": "Play-offs",
            "playoff": "Play-off",
            "final": "Final",
            "semi-finals": "Semifinais",
            "semi-final": "Semifinal",
            "quarter-finals": "Quartas de Final",
            "quarter-final": "Quartas de Final",
            "round of 16": "Oitavas de Final",
            "round of 32": "16-avos de Final",
            "round of 64": "32-avos de Final",
            "8th finals": "Oitavas de Final",
            "16th finals": "16-avos de Final",
            "32nd finals": "32-avos de Final",
            "relegation round": "Fase de Rebaixamento",
            "championship round": "Fase do Campeonato"
        }
        
        fase_normalizada = fase.strip()
        fase_minuscula = fase_normalizada.lower()
        
        for original, traducao in traducoes.items():
            if fase_minuscula == original:
                return traducao
            
            if fase_minuscula.startswith(original + " - "):
                complemento = fase_normalizada[len(original):]
                return traducao + complemento
        
        return fase

    # Monta o objeto final.
    return {
        "mandante": mandante.get("nome"),
        "visitante": visitante.get("nome"),
        "gols_mandante": partida.get("gols", {}).get("mandante"),
        "gols_visitante": partida.get("gols", {}).get("visitante"),

        "logo_mandante": mandante.get("logo"),
        "logo_visitante": visitante.get("logo"),
        "logo_competicao": competicao.get("logo"),

        "competicao": competicao.get("nome"),
        "pais": competicao.get("pais"),
        "fase": traduzir_fase(competicao.get("rodada")),
        "tipo_competicao": tipo_competicao,
        "codigo_competicao": codigo_competicao,

        "data": partida.get("data"),
        "status": partida.get("status"),
        "status_descricao": traduzir_status(
            partida.get("status"),
            partida.get("status_descricao")    
        ),

        "estadio": partida.get("estadio"),
        "cidade": partida.get("cidade"),
        "arbitro": partida.get("arbitro"),
        "publico": None,

        "estatisticas": estatisticas,
        "escalacoes": escalacoes,
        "eventos": eventos,
        "classificacao": classificacao_tela
    }


def buscar_times_por_pais(pais: str) -> list | None:
    """
    Busca os times disponíveis na API-Football
    utilizando o nome do país.
    """

    if not API_FOOTBALL_KEY or not pais:
        return None

    try:
        resposta = requests.get(
            f"{API_FOOTBALL_URL}/teams",
            headers={
                "x-apisports-key": API_FOOTBALL_KEY
            },
            params={
                "country": pais
            },
            timeout=20
        )

        resposta.raise_for_status()
        dados = resposta.json()

        if dados.get("errors"):
            print(
                f"Erro ao buscar times de {pais}:",
                dados["errors"]
            )
            return None

        times = []

        for item in dados.get("response", []):
            time = item.get("team", {})

            if not time.get("id") or not time.get("name"):
                continue

            times.append({
                "id": time.get("id"),
                "nome": time.get("name"),
                "logo": time.get("logo"),
                "pais": time.get("country"),
                "nacional": bool(time.get("national", False)),
            })

        return times

    except requests.RequestException as erro:
        print(f"Erro na consulta de times de {pais}: {erro}")
        return None
    
def buscar_paises_api_football() -> list:
    if not API_FOOTBALL_KEY:
        return []
    
    try:
        resposta = requests.get(
            f"{API_FOOTBALL_URL}/teams/countries",
            headers={"x-apisports-key": API_FOOTBALL_KEY},
            timeout=20,
        )
        
        resposta.raise_for_status()
        dados = resposta.json()
        
        if dados.get("errors"):
            print("Erro ao buscar países:", dados["errors"])
            return []
        
        return [
            item["name"]
            for item in dados.get("response", [])
            if item.get("name")
        ]
    
    except requests.RequestException as erro:
        print("Erro ao consultar países:", erro)
        return []


def consultar_cota_api_football() -> dict:
    if not API_FOOTBALL_KEY:
        return {
            "disponivel": False,
            "erro": "API_FOOTBALL_KEY não configurada",
        }

    try:
        resposta = requests.get(
            f"{API_FOOTBALL_URL}/status",
            headers={"x-apisports-key": API_FOOTBALL_KEY},
            timeout=20,
        )

        resposta.raise_for_status()
        dados = resposta.json()

        if dados.get("errors"):
            return {
                "disponivel": False,
                "erro": dados["errors"],
            }

        requisicoes = dados["response"]["requests"]
        limite = int(requisicoes["limit_day"])
        utilizadas = int(requisicoes["current"])

        return {
            "disponivel": True,
            "utilizadas": utilizadas,
            "limite": limite,
            "restantes": max(0, limite - utilizadas),
        }

    except (requests.RequestException, KeyError, TypeError, ValueError) as erro:
        return {
            "disponivel": False,
            "erro": str(erro),
        }


