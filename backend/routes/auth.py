from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from backend.database.models import Usuario, Perfil
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from backend.services.football_api import buscar_times_todas_competicoes

from backend.database.connection import get_db
from backend.schemas.auth import (
    CadastroRequest,
    LoginRequest,
    AuthResponse,
    UsuarioResponse,
    AtualizarPerfilRequest,
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

def buscar_dados_time_coracao(time_coracao_id: str | None):
    """
    Localiza os dados completos do time favorito
    usando o ID salvo no perfil do usuário.
    """

    if not time_coracao_id:
        return None

    resultado = buscar_times_todas_competicoes()

    if not isinstance(resultado, dict):
        return None

    times = resultado.get("times", [])

    for time in times:
        if str(time.get("id")) == str(time_coracao_id):
            return time

    return None

@router.get(
    "/me",
    response_model=UsuarioResponse,
)
def obter_usuario_autenticado(
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    perfil = db.scalar(
        select(Perfil).where(Perfil.usuario_id == usuario.id)
    )

    return UsuarioResponse(
        id=str(usuario.id),
        nome=usuario.nome,
        email=usuario.email,
        data_nascimento=usuario.data_nascimento,
        apelido=perfil.apelido if perfil else None,
        time_coracao_id=perfil.time_coracao_id if perfil else None,
        time_coracao=buscar_dados_time_coracao(
            perfil.time_coracao_id if perfil else None
        ),
    )

@router.put("/me", response_model=UsuarioResponse)
def atualizar_perfil(
    dados: AtualizarPerfilRequest,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        # Obtém somente os campos enviados pelo frontend.
        atualizacoes = dados.model_dump(exclude_unset=True)

        # Localiza o perfil já criado durante o cadastro.
        perfil = db.scalar(
            select(Perfil).where(Perfil.usuario_id == usuario.id)
        )

        if not perfil:
            raise HTTPException(
                status_code=404,
                detail="Perfil do usuário não encontrado.",
            )

        # Atualiza os dados da tabela usuarios.
        if "nome" in atualizacoes:
            usuario.nome = atualizacoes["nome"]

        if "data_nascimento" in atualizacoes:
            usuario.data_nascimento = atualizacoes["data_nascimento"]

        if "email" in atualizacoes:
            novo_email = str(atualizacoes["email"]).strip().lower()

            # Verifica se outro usuário já utiliza esse e-mail.
            outro_usuario = db.scalar(
                select(Usuario).where(
                    Usuario.email == novo_email,
                    Usuario.id != usuario.id,
                )
            )

            if outro_usuario:
                raise HTTPException(
                    status_code=409,
                    detail="Este e-mail já está sendo utilizado.",
                )

            usuario.email = novo_email

        # Atualiza os dados da tabela perfis.
        if "apelido" in atualizacoes:
            perfil.apelido = atualizacoes["apelido"]

        if "time_coracao_id" in atualizacoes:
            perfil.time_coracao_id = atualizacoes["time_coracao_id"]

        db.commit()
        db.refresh(usuario)

        return UsuarioResponse(
            id=str(usuario.id),
            nome=usuario.nome,
            email=usuario.email,
            data_nascimento=usuario.data_nascimento,
            apelido=perfil.apelido,
            time_coracao_id=perfil.time_coracao_id,
        )

    except HTTPException:
        db.rollback()
        raise

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Não foi possível atualizar os dados. Verifique se o e-mail já está em uso.",
        )

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Não foi possível atualizar o perfil.",
        )