from pydantic import BaseModel, ConfigDict, Field, EmailStr, field_validator
import re
from datetime import date

class CadastroRequest(BaseModel):
    nome: str = Field(min_length=2, max_length=150)
    email: EmailStr
    senha: str = Field(min_length=8)
    data_nascimento: date

    @field_validator("nome")
    @classmethod
    def validar_nome(cls, valor: str) -> str:
        valor = valor.strip()

        if len(valor) < 2:
            raise ValueError("O nome deve ter pelo menos 2 caracteres.")

        if not re.fullmatch(r"[A-Za-zÀ-ÖØ-öø-ÿ\s'-]+", valor):
            raise ValueError(
                "O nome deve conter apenas letras, espaços, hífens ou apóstrofos."
            )

        return valor

    @field_validator("data_nascimento")
    @classmethod
    def validar_data_nascimento(cls, valor: date) -> date:
        if valor < date(1900, 1, 1):
            raise ValueError("O ano de nascimento deve ser 1900 ou posterior.")

        if valor > date.today():
            raise ValueError("A data de nascimento não pode ser futura.")

        return valor

class LoginRequest(BaseModel):
    email: EmailStr
    senha: str = Field(min_length=1)

class TimeCoracaoResponse(BaseModel):
    id: int
    nome: str
    logo: str | None = None
    pais: str | None = None
    competicoes: list[str] = []

class UsuarioResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    nome: str
    email: EmailStr
    data_nascimento: date | None = None
    apelido: str | None = None
    avatar_url: str | None = None
    time_coracao_id: str | None = None
    time_coracao: TimeCoracaoResponse | None = None

class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioResponse

class AtualizarPerfilRequest(BaseModel):
    nome: str | None = Field(default=None, min_length=2, max_length=150)
    email: EmailStr | None = None
    data_nascimento: date | None = None
    apelido: str | None = Field(default=None, max_length=50)
    time_coracao_id: str | None = Field(default=None, max_length=100)

    @field_validator("nome")
    @classmethod
    def validar_nome(cls, valor: str | None) -> str | None:
        if valor is None:
            return None

        valor = valor.strip()

        if len(valor) < 2:
            raise ValueError("O nome deve ter pelo menos 2 caracteres.")

        if not re.fullmatch(r"[A-Za-zÀ-ÖØ-öø-ÿ\s'-]+", valor):
            raise ValueError(
                "O nome deve conter apenas letras, espaços, hífens ou apóstrofos."
            )

        return valor

    @field_validator("data_nascimento")
    @classmethod
    def validar_data_nascimento(cls, valor: date | None) -> date | None:
        if valor is None:
            return None

        if valor < date(1900, 1, 1):
            raise ValueError("O ano de nascimento deve ser 1900 ou posterior.")

        if valor > date.today():
            raise ValueError("A data de nascimento não pode ser futura.")

        return valor

    @field_validator("apelido")
    @classmethod
    def validar_apelido(cls, valor: str | None) -> str | None:
        if valor is None:
            return None

        valor = valor.strip()

        if not valor:
            raise ValueError("O nome de usuário não pode ficar vazio.")

        return valor