
from fastapi.testclient import TestClient
from unittest.mock import patch

from backend.main import app

client = TestClient(app)




def criar_dados_partida(codigo="CLI", nome="Copa Libertadores", pais="South America"):
    return {
        "partida": {
            "mandante": {
                "id": 1,
                "nome": "Time A",
                "logo": None,
            },
            "visitante": {
                "id": 2,
                "nome": "Time B",
                "logo": None,
            },
            "competicao": {
                "nome": nome,
                "pais": pais,
                "temporada": 2026,
                "logo": None,
                "rodada": "Final",
            },
            "gols": {
                "mandante": 2,
                "visitante": 1,
            },
            "data": "2026-06-01T20:00:00-03:00",
            "status": "FT",
            "status_descricao": "Match Finished",
            "estadio": "Estádio Teste",
            "cidade": "São Paulo",
            "arbitro": "Árbitro Teste",
        },
        "estatisticas": [],
        "escalacoes": [],
        "eventos": [],
        "avisos": {},
    }



def criar_partidas_libertadores():
    return {
        "matches": [
            {
                "stage": "GROUP_STAGE",
                "group": "GROUP_A",
                "homeTeam": {"id": 1, "name": "Time A"},
                "awayTeam": {"id": 2, "name": "Time B"},
                "score": {"fullTime": {"home": 2, "away": 0}},
                "status": "FINISHED",
            },
            {
                "stage": "ROUND_1",
                "id": 100,
                "utcDate": "2026-02-01T20:00:00Z",
                "homeTeam": {"id": 3, "name": "Time C"},
                "awayTeam": {"id": 4, "name": "Time D"},
                "score": {
                    "fullTime": {"home": 2, "away": 1},
                    "regularTime": {"home": 2, "away": 1},
                    "penalties": {"home": None, "away": None},
                },
                "status": "FINISHED",
            },
        ]
    }


def test_endpoint_libertadores():
    partida = criar_dados_partida()

    classificacao = [
        {
            "posicao": 1,
            "time": "Time A",
            "pontos": 10,
            "jogos": 4,
            "vitorias": 3,
            "empates": 1,
            "derrotas": 0,
            "saldo_gols": 5,
        }
    ]

    with (
        patch("backend.main.buscar_detalhes_completos_partida", return_value=partida),
        patch(
            "backend.main.buscar_competicoes_football_data",
            return_value=[
                {
                    "nome": "Copa Libertadores",
                    "pais": "South America",
                    "codigo": "CLI",
                    "tipo": "CUP",
                }
            ],
        ),
        patch(
            "backend.main.buscar_classificacao_competicao",
            return_value=classificacao,
        ),
        patch(
            "backend.main.buscar_detalhes_temporada_football_data",
            return_value=criar_partidas_libertadores(),
        ),
    ):
        resposta = client.get("/api/jogos/999999/tela")

    assert resposta.status_code == 200

    dados = resposta.json()

    assert dados["codigo_competicao"] == "CLI"
    assert dados["fase_de_grupos"]["status"] == "disponivel"
    assert len(dados["fase_de_grupos"]["grupos"]) > 0
    assert len(dados["mata_mata"]["fases_preliminares"]) > 0


def test_endpoint_champions():
    partida = criar_dados_partida(
        codigo="CL",
        nome="UEFA Champions League",
        pais="Europe",
    )

    classificacao = [
        {
            "posicao": 1,
            "time": "Time A",
            "pontos": 12,
            "jogos": 4,
            "vitorias": 4,
            "empates": 0,
            "derrotas": 0,
            "saldo_gols": 10,
        }
    ]

    with (
        patch("backend.main.buscar_detalhes_completos_partida", return_value=partida),
        patch(
            "backend.main.buscar_competicoes_football_data",
            return_value=[
                {
                    "nome": "UEFA Champions League",
                    "pais": "Europe",
                    "codigo": "CL",
                    "tipo": "CUP",
                }
            ],
        ),
        patch(
            "backend.main.buscar_classificacao_competicao",
            return_value=classificacao,
        ),
        patch(
            "backend.main.buscar_detalhes_temporada_football_data",
            return_value={"matches": []},
        ),
    ):
        resposta = client.get("/api/jogos/999999/tela")

    assert resposta.status_code == 200

    dados = resposta.json()

    assert dados["codigo_competicao"] == "CL"
    assert dados["fase_de_liga"]["status"] == "disponivel"
    assert len(dados["fase_de_liga"]["classificacao"]) == 1
    assert dados["mata_mata"]["status"] == "aguardando_inicio"


def test_endpoint_premier_league():
    partida = criar_dados_partida(
        nome="Premier League",
        pais="England",
    )

    classificacao = [
        {
            "posicao": 1,
            "time": "Arsenal FC",
            "pontos": 85,
            "jogos": 38,
            "vitorias": 26,
            "empates": 7,
            "derrotas": 5,
            "saldo_gols": 44,
        }
    ]

    with (
        patch("backend.main.buscar_detalhes_completos_partida", return_value=partida),
        patch(
            "backend.main.buscar_competicoes_football_data",
            return_value=[
                {
                    "nome": "Premier League",
                    "pais": "England",
                    "codigo": "PL",
                    "tipo": "LEAGUE",
                }
            ],
        ),
        patch(
            "backend.main.buscar_classificacao_competicao",
            return_value=classificacao,
        ),
    ):
        resposta = client.get("/api/jogos/999999/tela")

    assert resposta.status_code == 200

    dados = resposta.json()

    assert dados["codigo_competicao"] == "PL"
    assert dados["tipo_competicao"] == "LEAGUE"
    assert len(dados["classificacao"]) == 1
    assert dados["fase_de_grupos"]["status"] == "nao_aplicavel"
    assert dados["fase_de_liga"]["status"] == "nao_aplicavel"
    assert dados["mata_mata"]["status"] == "nao_aplicavel"


def test_endpoint_falha_consulta_competicao():
    partida = criar_dados_partida(
        nome="Premier League",
        pais="England",
    )

    with (
        patch("backend.main.buscar_detalhes_completos_partida", return_value=partida),
        patch(
            "backend.main.buscar_competicoes_football_data",
            return_value={"erro": "Serviço indisponível"},
        ),
    ):
        resposta = client.get("/api/jogos/999999/tela")

    assert resposta.status_code == 200

    dados = resposta.json()

    assert dados["mandante"] == "Time A"
    assert dados["visitante"] == "Time B"
    assert dados["codigo_competicao"] is None
    assert dados["classificacao"] == []


def test_endpoint_classificacao_indisponivel():
    partida = criar_dados_partida(nome="Premier League", pais="England")

    with (
        patch("backend.main.buscar_detalhes_completos_partida", return_value=partida),
        patch("backend.main.buscar_competicoes_football_data", return_value=[
            {
                "nome": "Premier League",
                "pais": "England",
                "codigo": "PL",
                "tipo": "LEAGUE",
            }
        ]),
        patch("backend.main.buscar_classificacao_competicao", return_value={"erro": "Indisponível"}),
    ):
        resposta = client.get("/api/jogos/999999/tela")

    assert resposta.status_code == 200
    dados = resposta.json()
    assert dados["mandante"] == "Time A"
    assert dados["visitante"] == "Time B"
    assert dados["codigo_competicao"] == "PL"
    assert dados["classificacao"] == []


def test_endpoint_temporada_sem_partidas():
    partida = criar_dados_partida()

    with (
        patch("backend.main.buscar_detalhes_completos_partida", return_value=partida),
        patch("backend.main.buscar_competicoes_football_data", return_value=[
            {
                "nome": "Copa Libertadores",
                "pais": "South America",
                "codigo": "CLI",
                "tipo": "CUP",
            }
        ]),
        patch("backend.main.buscar_classificacao_competicao", return_value=[]),
        patch("backend.main.buscar_detalhes_temporada_football_data", return_value={"matches": []}),
    ):
        resposta = client.get("/api/jogos/999999/tela")

    assert resposta.status_code == 200
    dados = resposta.json()
    assert dados["mandante"] == "Time A"
    assert dados["visitante"] == "Time B"
    assert dados["fase_de_grupos"]["status"] == "indisponivel"
    assert dados["mata_mata"]["status"] == "aguardando_inicio"


def test_endpoint_mata_mata_nao_iniciado():
    partida = criar_dados_partida(nome="UEFA Champions League", pais="Europe")

    with (
        patch("backend.main.buscar_detalhes_completos_partida", return_value=partida),
        patch("backend.main.buscar_competicoes_football_data", return_value=[
            {
                "nome": "UEFA Champions League",
                "pais": "Europe",
                "codigo": "CL",
                "tipo": "CUP",
            }
        ]),
        patch("backend.main.buscar_classificacao_competicao", return_value=[
            {
                "posicao": 1,
                "time": "Time A",
                "pontos": 12,
                "jogos": 4,
                "vitorias": 4,
                "empates": 0,
                "derrotas": 0,
                "saldo_gols": 10,
            }
        ]),
        patch("backend.main.buscar_detalhes_temporada_football_data", return_value={"matches": []}),
    ):
        resposta = client.get("/api/jogos/999999/tela")

    assert resposta.status_code == 200
    dados = resposta.json()
    assert dados["fase_de_liga"]["status"] == "disponivel"
    assert dados["mata_mata"]["status"] == "aguardando_inicio"
    assert dados["mata_mata"]["fases_preliminares"] == []
    assert dados["mata_mata"]["mata_mata_principal"] == []


def test_endpoint_falha_detalhes_temporada():
    partida = criar_dados_partida()

    with (
        patch("backend.main.buscar_detalhes_completos_partida", return_value=partida),
        patch("backend.main.buscar_competicoes_football_data", return_value=[
            {
                "nome": "Copa Libertadores",
                "pais": "South America",
                "codigo": "CLI",
                "tipo": "CUP",
            }
        ]),
        patch("backend.main.buscar_classificacao_competicao", return_value=[]),
        patch("backend.main.buscar_detalhes_temporada_football_data", return_value={"erro": "Serviço indisponível"}),
    ):
        resposta = client.get("/api/jogos/999999/tela")

    assert resposta.status_code == 200
    dados = resposta.json()
    assert dados["mandante"] == "Time A"
    assert dados["visitante"] == "Time B"
    assert dados["codigo_competicao"] == "CLI"
    assert dados["fase_de_grupos"]["status"] == "indisponivel"
    assert dados["mata_mata"]["status"] == "indisponivel"


def test_endpoint_temporada_matches_none():
    partida = criar_dados_partida()

    with (
        patch("backend.main.buscar_detalhes_completos_partida", return_value=partida),
        patch("backend.main.buscar_competicoes_football_data", return_value=[
            {
                "nome": "Copa Libertadores",
                "pais": "South America",
                "codigo": "CLI",
                "tipo": "CUP",
            }
        ]),
        patch("backend.main.buscar_classificacao_competicao", return_value=[]),
        patch("backend.main.buscar_detalhes_temporada_football_data", return_value={"matches": None}),
    ):
        resposta = client.get("/api/jogos/999999/tela")

    assert resposta.status_code == 200
    dados = resposta.json()
    assert dados["mandante"] == "Time A"
    assert dados["visitante"] == "Time B"


def test_endpoint_classificacao_none():
    partida = criar_dados_partida(
        nome="Premier League",
        pais="England"
    )

    with (
        patch("backend.main.buscar_detalhes_completos_partida", return_value=partida),
        patch("backend.main.buscar_competicoes_football_data", return_value=[
            {
                "nome": "Premier League",
                "pais": "England",
                "codigo": "PL",
                "tipo": "LEAGUE",
            }
        ]),
        patch("backend.main.buscar_classificacao_competicao", return_value=None),
    ):
        resposta = client.get("/api/jogos/999999/tela")

    assert resposta.status_code == 200

    dados = resposta.json()

    assert dados["mandante"] == "Time A"
    assert dados["visitante"] == "Time B"
    assert dados["codigo_competicao"] == "PL"
    assert dados["classificacao"] == []


def test_endpoint_sem_competicao():
    partida = criar_dados_partida()

    partida["partida"]["competicao"] = {}

    with (
        patch("backend.main.buscar_detalhes_completos_partida", return_value=partida),
        patch("backend.main.buscar_competicoes_football_data", return_value=[]),
    ):
        resposta = client.get("/api/jogos/999999/tela")

    assert resposta.status_code == 200

    dados = resposta.json()

    assert dados["mandante"] == "Time A"
    assert dados["visitante"] == "Time B"
    assert dados["codigo_competicao"] is None
    assert dados["classificacao"] == []


def test_endpoint_id_zero():
    resposta = client.get("/api/jogos/0/tela")

    assert resposta.status_code == 200
    assert resposta.json()["erro"] == "ID da partida inválido."


def test_endpoint_id_negativo():
    resposta = client.get("/api/jogos/-10/tela")

    assert resposta.status_code == 200
    assert resposta.json()["erro"] == "ID da partida inválido."
