from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database.connection import get_db
from backend.database.models import PrevisaoEscalacao
from backend.schemas.lineup_challenge import (
    EnviarPrevisaoRequest,
    PrevisaoEscalacaoResponse,
)
from backend.services.api_football import buscar_detalhes_partida
from backend.services.lineup_challenge import (
    validar_escalacao,
    verificar_prazo_previsao,
    avaliar_previsao,
    escalacao_oficial_valida
)
from backend.routes.auth import get_current_user
from backend.services.api_football import buscar_elenco_time
from backend.services.api_football import (
    buscar_detalhes_completos_partida,
    formatar_detalhes_partida,
)

from datetime import datetime

router = APIRouter(
    prefix="/api/desafio-escalacao",
    tags=["Acerte a Escalação"]
)

@router.get("/elenco/{team_id}")
def consultar_elenco(
    team_id: int,
    usuario=Depends(get_current_user)
):
    """
    Retorna os jogadores disponíveis para montar uma escalação.
    Requer autenticação.
    """
    
    if team_id <= 0:
        raise HTTPException(
            status_code=400,
            detail="ID do time inválido."
        )
        
    resultado = buscar_elenco_time(team_id)
    
    if "erro" in resultado:
        raise HTTPException(
            status_code=502,
            detail=resultado["erro"]
        )
        
    return resultado


@router.post(
    "/{fixture_id}/previsao",
    response_model=PrevisaoEscalacaoResponse,
)
def salvar_previsao(
    fixture_id: int,
    dados: EnviarPrevisaoRequest,
    usuario=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if fixture_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID da partida inválido.",
        )

    # Primeiro verifica se já existe uma previsão no banco.
    previsao = (
        db.query(PrevisaoEscalacao)
        .filter(
            PrevisaoEscalacao.usuario_id == usuario.id,
            PrevisaoEscalacao.fixture_id == fixture_id,
        )
        .with_for_update()
        .first()
    )

    if previsao and previsao.status == "avaliada":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Esta previsão já foi avaliada e não pode ser alterada.",
        )

    # Se já existe previsão, reutiliza os dados armazenados.
    if previsao:
        mandante_id = previsao.mandante_id
        visitante_id = previsao.visitante_id

        data_partida = previsao.data_partida

    else:
        # Primeira previsão: consulta a partida na API.
        partida = buscar_detalhes_partida(fixture_id)

        if "erro" in partida:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=partida["erro"],
            )

        mandante_id = partida.get("mandante", {}).get("id")
        visitante_id = partida.get("visitante", {}).get("id")

        if not mandante_id or not visitante_id:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Não foi possível identificar os times da partida.",
            )

        data_partida = datetime.fromisoformat(
            partida.get("data", "").replace("Z", "+00:00")
        )

        # Cria o registro com os metadados da partida.
        previsao = PrevisaoEscalacao(
            usuario_id=usuario.id,
            fixture_id=fixture_id,
            mandante_id=mandante_id,
            visitante_id=visitante_id,
            mandante_nome=partida.get("mandante", {}).get("nome"),
            mandante_escudo=partida.get("mandante", {}).get("logo"),
            visitante_nome=partida.get("visitante", {}).get("nome"),
            visitante_escudo=partida.get("visitante", {}).get("logo"),
            competicao=partida.get("competicao", {}).get("nome"),
            data_partida=data_partida,
        )

        db.add(previsao)

    # Confere o prazo usando a data armazenada ou recém-consultada.
    prazo = verificar_prazo_previsao(data_partida.isoformat())

    if not prazo["permitido"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=prazo["mensagem"],
        )

    if not mandante_id or not visitante_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Os IDs dos times não estão disponíveis para esta previsão.",
        )

    # Valida os jogadores escolhidos.
    if dados.mandante:
        resultado = validar_escalacao(
            mandante_id,
            dados.mandante.model_dump(),
        )

        if "erro" in resultado:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=resultado["erro"],
            )

    if dados.visitante:
        resultado = validar_escalacao(
            visitante_id,
            dados.visitante.model_dump(),
        )

        if "erro" in resultado:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=resultado["erro"],
            )

    # Atualiza somente as equipes enviadas.
    if dados.mandante is not None:
        previsao.mandante = dados.mandante.model_dump()

    if dados.visitante is not None:
        previsao.visitante = dados.visitante.model_dump()

    previsao.status = "aberta"

    try:
        db.commit()
        db.refresh(previsao)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Não foi possível salvar a previsão.",
        )

    return previsao


@router.get(
    "/historico",
    response_model=list[PrevisaoEscalacaoResponse],
)
def consultar_historico(
    usuario=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    previsoes = (
        db.query(PrevisaoEscalacao)
        .filter(
            PrevisaoEscalacao.usuario_id == usuario.id
        )
        .order_by(PrevisaoEscalacao.criado_em.desc())
        .all()
    )

    return previsoes


@router.get(
    "/{fixture_id}/previsao",
    response_model=PrevisaoEscalacaoResponse,
)
def consultar_previsao(
    fixture_id: int,
    usuario=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if fixture_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID da partida inválido.",
        )

    previsao = (
        db.query(PrevisaoEscalacao)
        .filter(
            PrevisaoEscalacao.usuario_id == usuario.id,
            PrevisaoEscalacao.fixture_id == fixture_id,
        )
        .first()
    )

    if not previsao:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Você ainda não fez uma previsão para esta partida.",
        )

    return previsao


@router.post(
    "/{fixture_id}/avaliar",
    response_model=PrevisaoEscalacaoResponse,
)
def avaliar_resultado_previsao(
    fixture_id: int,
    usuario=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if fixture_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID da partida inválido.",
        )

    previsao = (
        db.query(PrevisaoEscalacao)
        .filter(
            PrevisaoEscalacao.usuario_id == usuario.id,
            PrevisaoEscalacao.fixture_id == fixture_id,
        )
        .with_for_update()
        .first()
    )

    if not previsao:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Previsão não encontrada.",
        )

    if previsao.status == "avaliada":
        return previsao

    dados_partida = buscar_detalhes_completos_partida(fixture_id)

    if "erro" in dados_partida:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=dados_partida["erro"],
        )

    partida = dados_partida.get("partida", {})
    status_partida = partida.get("status")

    if status_partida not in ("FT", "AET", "PEN"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A partida ainda não foi finalizada.",
        )

    dados_formatados = formatar_detalhes_partida(dados_partida)

    escalacoes = dados_formatados.get("escalacoes", {})

    # Verifica se todas as equipes previstas possuem escalação oficial.
    if previsao.mandante:
        oficiais = escalacoes.get("mandante", {})
        
        if not escalacao_oficial_valida(oficiais):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A escalação oficial do mandante ainda não está disponível ou é inválida.",
            )
    
    if previsao.visitante:
        oficiais = escalacoes.get("visitante", {})
        
        if not escalacao_oficial_valida(oficiais):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A escalação oficial do visitante ainda não está disponível ou é inválida.",
            )

    pontuacao = avaliar_previsao(
        {
            "mandante": previsao.mandante,
            "visitante": previsao.visitante,
        },
        escalacoes,
    )

    previsao.pontuacao_mandante = pontuacao["pontuacao_mandante"]
    previsao.pontuacao_visitante = pontuacao["pontuacao_visitante"]
    previsao.pontuacao_total = pontuacao["pontuacao_total"]
    previsao.status = "avaliada"

    try:
        db.commit()
        db.refresh(previsao)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Não foi possível salvar a pontuação.",
        )

    return previsao
