from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from backend.database.connection import get_db
from backend.database.models import Usuario, Perfil
from backend.routes.auth import get_current_user
from backend.services.news_api import buscar_noticias
from backend.services.football_api import buscar_times_todas_competicoes

router = APIRouter(
    prefix="/api/news",
    tags=["Notícias"]
)

CATEGORIAS = {
    "todas": "futebol brasileiro",
    "mercado da bola": '"mercado da bola" OR (transferências futebol) OR (negociações futebol)',
    "jogos": "jogos futebol brasileiro",
}

@router.get("/")
def obter_noticias(
    categoria: str = "todas",
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    categoria = categoria.strip().lower()

    if categoria == "seu time":
        perfil = db.scalar(
            select(Perfil).where(Perfil.usuario_id == usuario.id)
        )

        if not perfil or not perfil.time_coracao_id:
            return {
                "categoria": categoria,
                "time": None,
                "noticias": []
            }

        resultado = buscar_times_todas_competicoes()

        if not isinstance(resultado, dict) or resultado.get("erro"):
            raise HTTPException(
                status_code=502,
                detail="Não foi possível consultar o time favorito."
            )

        time_favorito = next(
            (
                time for time in resultado.get("times", [])
                if str(time.get("id")) == str(perfil.time_coracao_id)
            ),
            None
        )

        if not time_favorito:
            return {
                "categoria": categoria,
                "time": None,
                "noticias": []
            }

        nome_time = time_favorito.get("nome")

        nome_busca = nome_time

        for sufixo in [" FC", " F.C.", " Football Club"]:
            nome_busca = nome_busca.replace(sufixo, "")

        nome_busca = nome_busca.strip()

        noticias = buscar_noticias(
            f'{nome_busca} futebol',
            10
        )

        return {
            "categoria": categoria,
            "time": nome_time,
            "noticias": noticias
        }

    termo = CATEGORIAS.get(categoria)

    if not termo:
        raise HTTPException(
            status_code=400,
            detail="Categoria inválida."
        )

    noticias = buscar_noticias(termo, 10)

    return {
        "categoria": categoria,
        "time": None,
        "noticias": noticias
    }