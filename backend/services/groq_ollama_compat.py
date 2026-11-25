
import os
from pathlib import Path

import httpx
from dotenv import load_dotenv


# Carrega o .env localizado na raiz do projeto.
ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


def chat(model=None, messages=None, options=None):
    """
    Mantém o formato de chamada e resposta do Ollama,
    utilizando a API da Groq por baixo dos panos.
    """

    if not GROQ_API_KEY:
        raise RuntimeError(
            "A variável GROQ_API_KEY não foi configurada."
        )

    opcoes = options or {}

    payload = {
        "model": GROQ_MODEL,
        "messages": messages or [],
        "temperature": opcoes.get("temperature", 0.2),
    }

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    resposta = httpx.post(
        GROQ_URL,
        headers=headers,
        json=payload,
        timeout=90.0,
    )

    resposta.raise_for_status()

    dados = resposta.json()
    conteudo = dados["choices"][0]["message"]["content"]

    # Compatibilidade com o formato esperado pelo projeto.
    return {
        "message": {
            "content": (conteudo or "").strip()
        }
    }
