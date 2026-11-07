from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from backend.database.connection import get_db
from backend.database.models import Usuario, Perfil
from backend.routes.auth import get_current_user
from backend.services.football_api import (
    buscar_times_todas_competicoes,
    buscar_jogos_time
)

from datetime import datetime, timedelta, timezone

router = APIRouter(
    prefix="/api/home",
    tags=["Home"]
)

def buscar_time_favorito_usuario(usuario: Usuario, db: Session):
    """
    Recupera os dados do time favorito do usuário
    usamos o ID armazenado no perfil.
    """

    perfil = db.scalar(
        select(Perfil).where(Perfil.usuario_id == usuario.id)
    )

    if not perfil or not perfil.time_coracao_id:
        return None

    resultado = buscar_times_todas_competicoes()

    if not isinstance(resultado, dict) or resultado.get("erro"):
        return {"erro": resultado.get("erro", "Resposta inválida da Football-Data.")}

    times = resultado.get("times", [])

    for time in times:
        if str(time.get("id")) == str(perfil.time_coracao_id):
            return time

    return None

def ordenar_jogos_por_data(jogos, mais_recente=False):
    """
    Ordena os jogos pela data.
    Por padrão, do mais próximo ao mais distante.
    """

    return sorted(
        jogos,
        key=lambda jogo: datetime.fromisoformat(
            jogo["data"].replace("Z", "+00:00")
        ),
        reverse=mais_recente
    )

def selecionar_jogo_destaque(team_id: int):
    """
    Prioridade:
    1. Próximo jogo dentro de 3 dias.
    2. Último jogo finalizado.
    """

    agora = datetime.now(timezone.utc)
    limite = agora + timedelta(days=3)

    proximos = buscar_jogos_time(team_id, "SCHEDULED")

    if isinstance(proximos, dict) and "erro" in proximos:
        return proximos

    if isinstance(proximos, list) and proximos:
        proximos = [
            jogo for jogo in proximos
            if jogo.get("status") not in ("POSTPONED", "CANCELLED")
        ]

        proximos = ordenar_jogos_por_data(proximos)

        for jogo in proximos:
            data_jogo = datetime.fromisoformat(
                jogo["data"].replace("Z", "+00:00")
            )

            if agora <= data_jogo <= limite:
                return {
                    "tipo": "proximo",
                    "jogo": jogo
                }

    finalizados = buscar_jogos_time(team_id, "FINISHED")

    if isinstance(finalizados, dict) and "erro" in finalizados:
        return finalizados

    if isinstance(finalizados, list) and finalizados:
        finalizados = ordenar_jogos_por_data(
            finalizados,
            mais_recente=True
        )

        return {
            "tipo": "resultado",
            "jogo": finalizados[0]
        }

    return None

@router.get("/placar")
def obter_placar_home(
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    time_favorito = buscar_time_favorito_usuario(usuario, db)

    if isinstance(time_favorito, dict) and "erro" in time_favorito:
        raise HTTPException(
            status_code=502,
            detail="Não foi possível consultar os times na Football-Data."
        )

    if not time_favorito:
        return {
            "mensagem": "Nenhum time do coração cadastrado.",
            "time": None,
            "jogo": None
        }

    jogo_destaque = selecionar_jogo_destaque(
        int(time_favorito["id"])
    )

    if isinstance(jogo_destaque, dict) and "erro" in jogo_destaque:
        raise HTTPException(
            status_code=502,
            detail= "Não foi possível consultar os jogos na Football-Data"
        )

    return {
        "time": time_favorito,
        "jogo": jogo_destaque
    }
