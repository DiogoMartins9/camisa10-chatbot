from pydantic import BaseModel, ConfigDict, Field, EmailStr, field_validator
import re

class CadastroRequest(BaseModel):
    nome: str = Field(min_length=2, max_length=150)
    email: EmailStr
    senha: str = Field(min_length=8)

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