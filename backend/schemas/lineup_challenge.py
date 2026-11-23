
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator
from uuid import UUID
from datetime import datetime


class EscalacaoRequest(BaseModel):
    formacao: str = Field(
        min_length=3,
        max_length=15,
        pattern=r"^\d+(?:-\d+){2,3}$"
    )

    jogadores: list[int] = Field(
        min_length=11,
        max_length=11
    )

    @field_validator("jogadores")
    @classmethod
    def validar_jogadores(cls, jogadores):
        if any(jogador <= 0 for jogador in jogadores):
            raise ValueError("Os IDs dos jogadores devem ser positivos.")

        if len(set(jogadores)) != 11:
            raise ValueError("Não pode haver jogadores repetidos.")

        return jogadores

    @field_validator("formacao")
    @classmethod
    def validar_formacao(cls, formacao):
        numeros = [int(n) for n in formacao.split("-")]

        if sum(numeros) != 10:
            raise ValueError(
                "A formação deve representar os 10 jogadores de linha."
            )

        if any(n <= 0 for n in numeros):
            raise ValueError("A formação possui valores inválidos.")

        return formacao


class EnviarPrevisaoRequest(BaseModel):
    mandante: EscalacaoRequest | None = None
    visitante: EscalacaoRequest | None = None

    @model_validator(mode="after")
    def validar_previsao(self):
        if self.mandante is None and self.visitante is None:
            raise ValueError(
                "É necessário informar ao menos uma equipe."
            )

        return self


class PrevisaoEscalacaoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    usuario_id: UUID
    fixture_id: int

    mandante_nome: str | None = None
    mandante_escudo: str | None = None
    visitante_nome: str | None = None
    visitante_escudo: str | None = None
    competicao: str | None = None
    data_partida: datetime | None = None

    mandante: dict | None
    visitante: dict | None

    pontuacao_mandante: int
    pontuacao_visitante: int
    pontuacao_total: int

    status: str
    criado_em: datetime
    atualizado_em: datetime
