from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError

from google.oauth2 import id_token
from google.auth.transport import requests

import secrets

from backend.database.models import (
    Usuario,
    Perfil,
    ConfiguracaoAcessibilidade,
)

import os
from datetime import datetime, timedelta, timezone, date

import jwt

password_hasher = PasswordHasher()

def validar_token_google(token: str) -> dict:
    """
    Valida o ID Token emitido pelo Google e retorna
    os dados básicos do usuário autenticado.
    """
    client_id = os.getenv("GOOGLE_CLIENT_ID")

    if not client_id:
        raise RuntimeError(
            "GOOGLE_CLIENT_ID não configurado."
        )

    try:
        dados_token = id_token.verify_oauth2_token(
            token,
            requests.Request(),
            audience=client_id,
        )

        return {
            "google_id": dados_token["sub"],
            "email": dados_token["email"].strip().lower(),
            "nome": dados_token.get("name", ""),
            "email_verificado": dados_token.get(
                "email_verified", False
            ),
        }

    except ValueError:
        raise ValueError(
            "Token do Google inválido ou expirado."
        )

def cadastrar_usuario(
        db: Session, 
        nome: str, 
        email: str, 
        senha: str,
        data_nascimento: date
) -> Usuario:

    email = email.strip().lower()
    nome = nome.strip()

    usuario_existente = db.scalar(
        select(Usuario).where(Usuario.email == email)
    )

    if usuario_existente:
        raise ValueError("Este e-mail já está cadastrado.")

    senha_hash = password_hasher.hash(senha)

    try:
        usuario = Usuario(
            nome=nome,
            email=email,
            senha_hash=senha_hash,
            data_nascimento=data_nascimento
        )

        db.add(usuario)
        db.flush()  # Gera o ID do usuário antes de criar o perfil

        perfil = Perfil(
            usuario_id=usuario.id
        )

        configuracoes = ConfiguracaoAcessibilidade(
            usuario_id=usuario.id
        )

        db.add_all([perfil, configuracoes])

        return usuario

    except IntegrityError:
        db.rollback()
        raise ValueError("Este e-mail já está cadastrado.")

    except Exception:
        db.rollback()
        raise

def obter_ou_criar_usuario_google(
        db: Session,
        dados_google: dict,
) -> Usuario:

    google_id = dados_google["google_id"]
    email = dados_google["email"]
    nome = dados_google["nome"]

    if not dados_google["email_verificado"]:
        raise ValueError(
            "O e-mail da conta Google não foi verificado."
        )

    usuario = db.scalar(
        select(Usuario).where(
            Usuario.google_id == google_id
        )
    )

    if usuario:
        return usuario

    usuario_existente = db.scalar(
        select(Usuario).where(
            Usuario.email == email
        )
    )

    if usuario_existente:
        raise ValueError(
            "Este e-mail já possui cadastro."
            "Entre com sua senha para acessar essa conta."
        )

    senha_hash = password_hasher.hash(
        secrets.token_urlsafe(32)
    )

    usuario = Usuario(
        nome=nome or email.split("@")[0],
        email=email,
        google_id=google_id,
        senha_hash=senha_hash,
        data_nascimento=None,
    )

    db.add(usuario)
    db.flush()

    perfil = Perfil(
        usuario_id=usuario.id
    )

    configuracoes = ConfiguracaoAcessibilidade(
        usuario_id=usuario.id
    )

    db.add_all([perfil, configuracoes])

    return usuario

def verificar_senha(
        senha: str,
        senha_hash: str,
) -> bool:

    try:
        return password_hasher.verify(senha_hash, senha)

    except (VerifyMismatchError, VerificationError):
        return False

def criar_token_acesso(usuario: Usuario) -> str:
    """
    Gera um token JWT para autenticar o usuário.
    """

    chave_secreta = os.getenv("JWT_SECRET_KEY")
    algoritmo = os.getenv("JWT_ALGORITHM", "HS256")
    validade_minutos = int(
        os.getenv("JWT_EXPIRE_MINUTES", "60")
    )

    if not chave_secreta:
        raise RuntimeError(
            "JWT_SECRET_KEY não configurada."
        )

    agora = datetime.now(timezone.utc)

    payload = {
        "sub": str(usuario.id),
        "iat": agora,
        "exp": agora + timedelta(minutes=validade_minutos),
    }

    return jwt.encode(
        payload,
        chave_secreta,
        algorithm=algoritmo
    )

def validar_token_acesso(
        token: str,
        db: Session,
) -> Usuario | None:
    """
    Valida o JWT e recupera o usuário correspondente.
    """

    chave_secreta = os.getenv("JWT_SECRET_KEY")
    algoritmo = os.getenv("JWT_ALGORITHM", "HS256")

    if not chave_secreta:
        raise RuntimeError(
            "JWT_SECRET_KEY não configurada."
        )

    try:
        payload = jwt.decode(
            token,
            chave_secreta,
            algorithms=[algoritmo]
        )

        usuario_id = payload.get("sub")

        if not usuario_id:
            return None

        usuario = db.scalar(
            select(Usuario).where(
                Usuario.id == usuario_id
            )
        )

        return usuario

    except jwt.InvalidTokenError:
        return None
