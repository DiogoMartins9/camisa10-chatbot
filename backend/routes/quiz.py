from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.database.connection import get_db
from backend.database.models import (
    Quiz,
    PerguntaQuiz,
    TentativaQuiz,
    RespostaQuiz,
)
from backend.schemas.quiz import (
    QuizResponse,
    PerguntaResponse,
    EnviarRespostasRequest,
    ResultadoQuizResponse,
    ResultadoPerguntaResponse,
    EstatisticasGamificacaoResponse,
)
from backend.routes.auth import get_current_user

router = APIRouter(
    prefix="/api/quiz",
    tags=["Quizzes"],
)

def calcular_nivel(xp_total: int) -> dict:
    xp_total = max(0, int(xp_total))

    def calcular_xp_nivel(nivel: int) -> int:
        if nivel <= 1:
            return 0

        quantidade_niveis = nivel - 1

        return (
            quantidade_niveis * 10000
            + (
                (quantidade_niveis - 1)
                * quantidade_niveis
                * 1000
            ) / 2
        )

    nivel_atual = 1

    while xp_total >= calcular_xp_nivel(nivel_atual + 1):
        nivel_atual += 1

    xp_inicio_nivel = int(calcular_xp_nivel(nivel_atual))
    xp_proximo_nivel = int(calcular_xp_nivel(nivel_atual + 1))

    xp_atual_nivel = xp_total - xp_inicio_nivel
    xp_necessario_nivel = xp_proximo_nivel - xp_inicio_nivel

    progresso_nivel = min(
        100,
        max(
            0,
            (xp_atual_nivel / xp_necessario_nivel) * 100,
        ),
    )

    return {
        "nivel": nivel_atual,
        "xp_inicio_nivel": xp_inicio_nivel,
        "xp_proximo_nivel": xp_proximo_nivel,
        "xp_atual_nivel": xp_atual_nivel,
        "xp_necessario_nivel": xp_necessario_nivel,
        "progresso_nivel": round(progresso_nivel, 2),
    }

@router.get("/", response_model=list[QuizResponse])
def listar_quizzes(
    usuario=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    quizzes = (
        db.query(Quiz)
        .order_by(Quiz.titulo.asc())
        .all()
    )

    return quizzes

@router.get(
    "/estatisticas",
    response_model=EstatisticasGamificacaoResponse,
)
def obter_estatisticas(
    usuario=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Busca as estatísticas das tentativas finalizadas do usuário.
    resumo = (
        db.query(
            func.count(TentativaQuiz.id).label("quizzes_concluidos"),
            func.count(
                func.distinct(TentativaQuiz.quiz_id)
            ).label("quizzes_diferentes"),
            func.coalesce(
                func.sum(TentativaQuiz.acertos), 0
            ).label("acertos"),
            func.coalesce(
                func.sum(TentativaQuiz.xp_total), 0
            ).label("xp_total"),
        )
        .filter(
            TentativaQuiz.usuario_id == usuario.id,
            TentativaQuiz.finalizada.is_(True),
        )
        .one()
    )

    # Conta as perguntas respondidas nas tentativas finalizadas.
    perguntas_respondidas = (
        db.query(func.count(RespostaQuiz.id))
        .join(
            TentativaQuiz,
            TentativaQuiz.id == RespostaQuiz.tentativa_id,
        )
        .filter(
            TentativaQuiz.usuario_id == usuario.id,
            TentativaQuiz.finalizada.is_(True),
        )
        .scalar()
    ) or 0

    acertos = int(resumo.acertos)
    total = int(perguntas_respondidas)

    # Calcula a taxa de acerto.
    taxa_acerto = (
        (acertos / total) * 100
        if total > 0
        else 0.0
    )

    xp_total = int(resumo.xp_total)

    dados_nivel = calcular_nivel(xp_total)

    return EstatisticasGamificacaoResponse(
        xp_total=xp_total,
        **dados_nivel,
        quizzes_concluidos=int(resumo.quizzes_concluidos),
        quizzes_diferentes=int(resumo.quizzes_diferentes),
        perguntas_respondidas=total,
        acertos=acertos,
        taxa_acerto=round(taxa_acerto, 2),
    )

@router.get("/{codigo}/perguntas", response_model=list[PerguntaResponse])
def listar_perguntas(
    codigo: str,
    usuario=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    quiz = (
        db.query(Quiz)
        .filter(Quiz.codigo == codigo)
        .first()
    )

    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz não encontrado.",
        )

    perguntas = (
        db.query(PerguntaQuiz)
        .filter(PerguntaQuiz.quiz_id == quiz.id)
        .order_by(PerguntaQuiz.ordem.asc())
        .all()
    )

    return perguntas

@router.post(
    "/responder",
    response_model=ResultadoQuizResponse,
)
def responder_quiz(
    dados: EnviarRespostasRequest,
    usuario=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    quiz = (
        db.query(Quiz)
        .filter(Quiz.codigo == dados.codigo_quiz)
        .first()
    )

    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz não encontrado.",
        )

    # Verifica se existem perguntas duplicadas no envio.
    ids_perguntas = [
        resposta.pergunta_id for resposta in dados.respostas
    ]

    if len(ids_perguntas) != len(set(ids_perguntas)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não envie a mesma pergunta mais de uma vez.",
        )

    perguntas = (
        db.query(PerguntaQuiz)
        .filter(
            PerguntaQuiz.quiz_id == quiz.id,
            PerguntaQuiz.id.in_(ids_perguntas),
        )
        .all()
    )

    if len(perguntas) != len(dados.respostas):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uma ou mais perguntas não pertencem a este quiz.",
        )

    perguntas_por_id = {
        pergunta.id: pergunta for pergunta in perguntas
    }

    # Confere se todas as perguntas do quiz foram respondidas.
    if len(dados.respostas) != quiz.total_perguntas:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Responda todas as perguntas do quiz.",
        )

    # Cria uma tentativa.
    tentativa = TentativaQuiz(
        usuario_id=usuario.id,
        quiz_id=quiz.id,
        finalizada=False,
    )

    db.add(tentativa)
    db.flush()

    resultados = []
    acertos = 0
    xp_total = 0

    for resposta in dados.respostas:
        pergunta = perguntas_por_id[resposta.pergunta_id]

        if resposta.resposta_selecionada >= len(pergunta.alternativas):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Índice de alternativa inválido.",
            )

        correta = (
            resposta.resposta_selecionada == pergunta.resposta_correta
        )

        xp_ganho = 1000 if correta else 0

        if correta:
            acertos += 1
            xp_total += xp_ganho

        registro = RespostaQuiz(
            tentativa_id=tentativa.id,
            pergunta_id=pergunta.id,
            resposta_selecionada=resposta.resposta_selecionada,
            correta=correta,
            xp_ganho=xp_ganho,
        )

        db.add(registro)

        resultados.append(
            ResultadoPerguntaResponse(
                pergunta_id=pergunta.id,
                resposta_selecionada=resposta.resposta_selecionada,
                resposta_correta=pergunta.resposta_correta,
                correta=correta,
                explicacao=pergunta.explicacao,
                xp_ganho=xp_ganho,
            )
        )

    tentativa.acertos = acertos
    tentativa.pontuacao = acertos
    tentativa.xp_total = xp_total
    tentativa.finalizada = True
    tentativa.finalizada_em = datetime.now()

    db.commit()
    db.refresh(tentativa)

    return ResultadoQuizResponse(
        tentativa_id=tentativa.id,
        acertos=acertos,
        total_perguntas=len(dados.respostas),
        pontuacao=acertos,
        xp_total=xp_total,
        resultados=resultados,
    )