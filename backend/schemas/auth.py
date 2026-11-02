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

class UsuarioResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    nome: str
    email: EmailStr

class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioResponse