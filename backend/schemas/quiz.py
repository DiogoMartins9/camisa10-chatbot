from pydantic import BaseModel, Field
from uuid import UUID

class QuizResponse(BaseModel):
    id: UUID
    codigo: str
    titulo: str
    categoria: str | None
    total_perguntas: int

class PerguntaResponse(BaseModel):
    id: UUID
    enunciado: str
    alternativas: list[str]
    ordem: int

class RespostaEnvio(BaseModel):
    pergunta_id: UUID
    resposta_selecionada: int = Field(ge=0, le=3)

class EnviarRespostasRequest(BaseModel):
    codigo_quiz: str
    respostas: list[RespostaEnvio] = Field(min_length=1)

class ResultadoPerguntaResponse(BaseModel):
    pergunta_id: UUID
    resposta_selecionada: int
    resposta_correta: int
    correta: bool
    explicacao: str
    xp_ganho: int

class ResultadoQuizResponse(BaseModel):
    tentativa_id: UUID
    acertos: int
    total_perguntas: int
    pontuacao: int
    xp_total: int
    resultados: list[ResultadoPerguntaResponse]

class EstatisticasGamificacaoResponse(BaseModel):
    xp_total: int
    nivel: int
    xp_inicio_nivel: int
    xp_proximo_nivel: int
    xp_atual_nivel: int
    xp_necessario_nivel: int
    progresso_nivel: float
    quizzes_concluidos: int
    quizzes_diferentes: int
    perguntas_respondidas: int
    acertos: int
    taxa_acerto: float
