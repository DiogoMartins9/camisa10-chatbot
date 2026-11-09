import os
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

GNEWS_API_KEY = os.getenv("GNEWS_API_KEY")
GNEWS_URL = "https://gnews.io/api/v4/search"

def buscar_noticias(termo: str, quantidade: int = 10):
    """
    Busca notícias na GNews e retorna os dados
    organizados para o frontend do Camisa10.
    """

    if not GNEWS_API_KEY:
        raise RuntimeError("A variável GNEWS_API_KEY não foi configurada")

    parametros = {
        "q": termo,
        "lang": "pt",
        "country": "br",
        "max": min(max(quantidade, 1), 10),
        "sortby": "publishedAt",
    }

    resposta = requests.get(
        GNEWS_URL,
        params=parametros,
        headers={"X-Api-Key": GNEWS_API_KEY},
        timeout=15,
    )

    resposta.raise_for_status()

    dados = resposta.json()

    noticias = []

    for artigo in dados.get("articles", []):
        fonte = artigo.get("source") or {}

        noticias.append({
            "titulo": artigo.get("title"),
            "descricao": artigo.get("description"),
            "imagem": artigo.get("image"),
            "url": artigo.get("url"),
            "publicado_em": artigo.get("publishedAt"),
            "fonte": fonte.get("name"),
        })

    return noticias
