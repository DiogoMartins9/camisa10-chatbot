from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta, timezone

from backend.main import app
from backend.routes.auth import get_current_user
from backend.database.connection import get_db

def test_placar_sem_time_favorito():
    db_mock = MagicMock()
    db_mock.scalar.return_value = None

    usuario_mock = MagicMock()

    app.dependency_overrides[get_current_user] = lambda: usuario_mock
    app.dependency_overrides[get_db] = lambda: db_mock

    try:
        with TestClient(app) as client:
            resposta = client.get("/api/home/placar")

        assert resposta.status_code == 200

        dados = resposta.json()

        assert dados["mensagem"] == "Nenhum time do coração cadastrado."
        assert dados["time"] is None
        assert dados["jogo"] is None

    finally:
        app.dependency_overrides.clear()

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

    try:
        assert resposta.status_code == 200

        dados = resposta.json()

        assert dados["time"]["nome"] == "São Paulo FC"
        assert dados["jogo"] is None

    finally:
        app.dependency_overrides.clear()

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

