from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from backend.database.models import Usuario

from backend.database.connection import get_db
from backend.schemas.auth import (
    CadastroRequest,
    LoginRequest,
    AuthResponse,
    UsuarioResponse,
)
from backend.services.auth_service import (
    cadastrar_usuario,
    verificar_senha,
    criar_token_acesso,
    validar_token_acesso,
)


router = APIRouter(
    prefix="/api/auth",
    tags=["Autenticação"],
)

security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    token = credentials.credentials

    usuario = validar_token_acesso(
        token=token,
        db=db,
    )

    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return usuario

@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
)
def registrar_usuario(
    dados: CadastroRequest,
    db: Session = Depends(get_db),
):
    try:
        usuario = cadastrar_usuario(
            db=db,
            nome=dados.nome,
            email=str(dados.email).lower(),
            senha=dados.senha,
            data_nascimento=dados.data_nascimento,
        )

        token = criar_token_acesso(usuario)

        db.commit()

        return AuthResponse(
            access_token=token,
            usuario=UsuarioResponse(
                id=str(usuario.id),
                nome=usuario.nome,
                email=usuario.email,
            ),
        )

    except ValueError as erro:
        db.rollback()  # Reverte a transação em caso de erro

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(erro),
        )

    except Exception:
        db.rollback()  # Reverte a transação em caso de erro

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Não foi possível concluir o cadastro.",
        ) 

@router.post(
    "/login",
    response_model=AuthResponse,
)
def login_usuario(
    dados: LoginRequest,
    db: Session = Depends(get_db),
):
    from sqlalchemy import select
    from backend.database.models import Usuario

    email = str(dados.email).strip().lower()

    usuario = db.scalar(
        select(Usuario).where(Usuario.email == email)
    )

    if not usuario or not verificar_senha(
        dados.senha,
        usuario.senha_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = criar_token_acesso(usuario)

    return AuthResponse(
        access_token=token,
        usuario=UsuarioResponse(
            id=str(usuario.id),
            nome=usuario.nome,
            email=usuario.email,
        ),
    )

@router.get(
    "/me",
    response_model=UsuarioResponse,
)
def obter_usuario_autenticado(
    usuario: Usuario = Depends(get_current_user),
):
    return UsuarioResponse(
        id=str(usuario.id),
        nome=usuario.nome,
        email=usuario.email,
    )