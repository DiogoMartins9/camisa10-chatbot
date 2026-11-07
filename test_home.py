from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta, timezone

from backend.main import app
from backend.routes.auth import get_current_user
from backend.database.connection import get_db

import pytest

@pytest.fixture(autouse=True)
def limpar_overrides():
    yield
    app.dependency_overrides.clear()

def test_placar_sem_time_favorito():
    db_mock = MagicMock()
    db_mock.scalar.return_value = None

    usuario_mock = MagicMock()

    app.dependency_overrides[get_current_user] = lambda: usuario_mock
    app.dependency_overrides[get_db] = lambda: db_mock

    with TestClient(app) as client:
        resposta = client.get("/api/home/placar")

    assert resposta.status_code == 200

    dados = resposta.json()

    assert dados["mensagem"] == "Nenhum time do coração cadastrado."
    assert dados["time"] is None
    assert dados["jogo"] is None

def test_placar_sem_jogos_disponiveis():
    time_mock = {
        "id": 1776,
        "nome": "São Paulo FC",
        "pais": "Brazil",
        "logo": "https://crests.football-data.org/1776.png",
        "competicoes": ["Campeonato Brasileiro Série A"]
    }

    db_mock = MagicMock()
    usuario_mock = MagicMock()

    app.dependency_overrides[get_current_user] = lambda: usuario_mock
    app.dependency_overrides[get_db] = lambda: db_mock

    perfil_mock = MagicMock()
    perfil_mock.time_coracao_id = "1776"

    db_mock.scalar.return_value = perfil_mock

    with patch(
        "backend.routes.home.buscar_times_todas_competicoes",
        return_value={"times": [time_mock], "avisos": []}
    ), patch(
        "backend.routes.home.buscar_jogos_time",
        return_value=[]
    ):
        with TestClient(app) as client:
            resposta = client.get("/api/home/placar")
    assert resposta.status_code == 200

    dados = resposta.json()

    assert dados["time"]["nome"] == "São Paulo FC"
    assert dados["jogo"] is None

def test_placar_com_jogo_proximo():
    time_mock = {
        "id": 1776,
        "nome": "São Paulo FC",
        "pais": "Brazil",
        "logo": "https://crests.football-data.org/1776.png",
        "competicoes": ["Campeonato Brasileiro Série A"]
    }

    jogo_mock = {
        "id": 123456,
        "data": (
            datetime.now(timezone.utc) + timedelta(days=1)
        ).isoformat().replace("+00:00", "Z"),
        "status": "SCHEDULED",
        "competicao": "Campeonato Brasileiro Série A",
        "codigo_competicao": "BSA",
        "mandante": "São Paulo FC",
        "visitante": "Palmeiras",
        "gols_mandante": None,
        "gols_visitante": None,
        "penaltis_mandante": None,
        "penaltis_visitante": None
    }

    db_mock = MagicMock()
    usuario_mock = MagicMock()

    perfil_mock = MagicMock()
    perfil_mock.time_coracao_id = "1776"

    db_mock.scalar.return_value = perfil_mock

    app.dependency_overrides[get_current_user] = lambda: usuario_mock
    app.dependency_overrides[get_db] = lambda: db_mock

    with patch(
        "backend.routes.home.buscar_times_todas_competicoes",
        return_value={"times": [time_mock], "avisos": []}
    ), patch(
        "backend.routes.home.buscar_jogos_time",
        side_effect=[[jogo_mock], []]
    ):
        with TestClient(app) as client:
            resposta = client.get("/api/home/placar")

    assert resposta.status_code == 200

    dados = resposta.json()

    assert dados["time"]["nome"] == "São Paulo FC"
    assert dados["jogo"]["tipo"] == "proximo"
    assert dados["jogo"]["jogo"]["id"] == 123456
    assert dados["jogo"]["jogo"]["status"] == "SCHEDULED"

def test_placar_com_ultimo_jogo_finalizado():
    time_mock = {
        "id": 1776,
        "nome": "São Paulo FC",
        "pais": "Brazil",
        "logo": "https://crests.football-data.org/1776.png",
        "competicoes": ["Campeonato Brasileiro Série A"]
    }

    jogo_mock = {
        "id": 654321,
        "data": (
            datetime.now(timezone.utc) - timedelta(days=1)
        ).isoformat().replace("+00:00", "Z"),
        "status": "FINISHED",
        "competicao": "Campeonato Brasileiro Série A",
        "codigo_competicao": "BSA",
        "mandante": "São Paulo FC",
        "visitante": "SC Corinthians Paulista",
        "gols_mandante": 2,
        "gols_visitante": 1,
        "penaltis_mandante": None,
        "penaltis_visitante": None
    }

    db_mock = MagicMock()
    usuario_mock = MagicMock()

    perfil_mock = MagicMock()
    perfil_mock.time_coracao_id = "1776"

    db_mock.scalar.return_value = perfil_mock

    app.dependency_overrides[get_current_user] = lambda: usuario_mock
    app.dependency_overrides[get_db] = lambda: db_mock

    with patch(
        "backend.routes.home.buscar_times_todas_competicoes",
        return_value={"times": [time_mock], "avisos": []}
    ), patch(
        "backend.routes.home.buscar_jogos_time",
        side_effect=[[], [jogo_mock]]
    ):
        with TestClient(app) as client:
            resposta = client.get("/api/home/placar")

    assert resposta.status_code == 200

    dados = resposta.json()

    assert dados["time"]["nome"] == "São Paulo FC"
    assert dados["jogo"]["tipo"] == "resultado"
    assert dados["jogo"]["jogo"]["id"] == 654321
    assert dados["jogo"]["jogo"]["status"] == "FINISHED"
    assert dados["jogo"]["jogo"]["gols_mandante"] == 2
    assert dados["jogo"]["jogo"]["gols_visitante"] == 1

def test_placar_com_erro_na_api_de_times():
    db_mock = MagicMock()
    usuario_mock = MagicMock()

    perfil_mock = MagicMock()
    perfil_mock.time_coracao_id = "1776"

    db_mock.scalar.return_value = perfil_mock

    app.dependency_overrides[get_current_user] = lambda: usuario_mock
    app.dependency_overrides[get_db] = lambda: db_mock

    with patch(
        "backend.routes.home.buscar_times_todas_competicoes",
        return_value={"erro": "Falha na comunicação com a Football-Data."}
    ):
        with TestClient(app) as client:
            resposta = client.get("/api/home/placar")

    assert resposta.status_code == 502
    assert resposta.json()["detail"] == (
        "Não foi possível consultar os times na Football-Data."
    )

def test_placar_com_erro_na_api_de_jogos():
    time_mock = {
        "id": 1776,
        "nome": "São Paulo FC",
        "pais": "Brazil",
        "logo": "https://crests.football-data.org/1776.png",
        "competicoes": ["Campeonato Brasileiro Série A"]
    }

    db_mock = MagicMock()
    usuario_mock = MagicMock()

    perfil_mock = MagicMock()
    perfil_mock.time_coracao_id = "1776"

    db_mock.scalar.return_value = perfil_mock

    app.dependency_overrides[get_current_user] = lambda: usuario_mock
    app.dependency_overrides[get_db] = lambda: db_mock

    with patch(
        "backend.routes.home.buscar_times_todas_competicoes",
        return_value={"times": [time_mock], "avisos": []}
    ), patch(
        "backend.routes.home.buscar_jogos_time",
        return_value={"erro": "Falha na consulta de partidas."}
    ):
        with TestClient(app) as client:
            resposta = client.get("/api/home/placar")

    assert resposta.status_code == 502
    assert resposta.json()["detail"] == (
        "Não foi possível consultar os jogos na Football-Data"
    )

def test_placar_ignora_jogos_adiados_e_cancelados():
    time_mock = {
        "id": 1776,
        "nome": "São Paulo FC",
        "pais": "Brazil",
        "logo": "https://crests.football-data.org/1776.png",
        "competicoes": ["Campeonato Brasileiro Série A"]
    }

    jogo_adiado = {
        "id": 111111,
        "data": (
            datetime.now(timezone.utc) + timedelta(days=1)
        ).isoformat().replace("+00:00", "Z"),
        "status": "POSTPONED",
        "competicao": "Campeonato Brasileiro Série A",
        "codigo_competicao": "BSA",
        "mandante": "São Paulo FC",
        "visitante": "Palmeiras",
        "gols_mandante": None,
        "gols_visitante": None,
        "penaltis_mandante": None,
        "penaltis_visitante": None
    }

    jogo_cancelado = {
        "id": 222222,
        "data": (
            datetime.now(timezone.utc) + timedelta(days=2)
        ).isoformat().replace("+00:00", "Z"),
        "status": "CANCELLED",
        "competicao": "Campeonato Brasileiro Série A",
        "codigo_competicao": "BSA",
        "mandante": "São Paulo FC",
        "visitante": "Palmeiras",
        "gols_mandante": None,
        "gols_visitante": None,
        "penaltis_mandante": None,
        "penaltis_visitante": None
    }

    jogo_finalizado = {
        "id": 333333,
        "data": (
            datetime.now(timezone.utc) - timedelta(days=1)
        ).isoformat().replace("+00:00", "Z"),
        "status": "FINISHED",
        "competicao": "Campeonato Brasileiro Série A",
        "codigo_competicao": "BSA",
        "mandante": "São Paulo FC",
        "visitante": "SC Corinthians Paulista",
        "gols_mandante": 1,
        "gols_visitante": 0,
        "penaltis_mandante": None,
        "penaltis_visitante": None
    }

    db_mock = MagicMock()
    usuario_mock = MagicMock()

    perfil_mock = MagicMock()
    perfil_mock.time_coracao_id = "1776"

    db_mock.scalar.return_value = perfil_mock

    app.dependency_overrides[get_current_user] = lambda: usuario_mock
    app.dependency_overrides[get_db] = lambda: db_mock

    with patch(
        "backend.routes.home.buscar_times_todas_competicoes",
        return_value={"times": [time_mock], "avisos": []}
    ), patch(
        "backend.routes.home.buscar_jogos_time",
        side_effect=[
            [jogo_adiado, jogo_cancelado],
            [jogo_finalizado]
        ]
    ):
        with TestClient(app) as client:
            resposta = client.get("/api/home/placar")

    assert resposta.status_code == 200

    dados = resposta.json()

    assert dados["time"]["nome"] == "São Paulo FC"
    assert dados["jogo"]["tipo"] == "resultado"
    assert dados["jogo"]["jogo"]["id"] == 333333
    assert dados["jogo"]["jogo"]["status"] == "FINISHED"
