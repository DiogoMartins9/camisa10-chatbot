from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

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
)
from backend.routes.auth import get_current_user

router = APIRouter(
    prefix="/api/quiz",
    tags=["Quizzes"],
)

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