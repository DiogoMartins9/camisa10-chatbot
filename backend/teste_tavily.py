import os
import httpx
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("TAVILY_API_KEY")

if not api_key:
    raise RuntimeError(
        "Chave TAVILY_API_KEY não encontrada no arquivo .env"
    )

url = "https://api.tavily.com/search"

payload = {
    "api_key": api_key,
    "query": "site:fifa.com Pelé three FIFA World Cup titles",
    "topic": "general",
    "search_depth": "basic",
    "max_results": 3,
}

try:
    response = httpx.post(
        url,
        json=payload,
        timeout=20.0,
    )

    response.raise_for_status()
    dados = response.json()

    print("Pesquisa realizada com sucesso!\n")

    for i, resultado in enumerate(dados.get("results", []), start=1):
        print(f"Resultado {i}: {resultado.get('title', 'Sem título')}")
        print(f"URL: {resultado.get('url', 'Sem URL')}")
        print(f"Trecho: {resultado.get('content', 'Sem trecho')}")
        print("-" * 60)

    if not dados.get("results"):
        print("A pesquisa não retornou resultados.")

except httpx.HTTPStatusError as erro:
    print(f"Erro HTTP: {erro.response.status_code}")
    print("Verifique a chave, os créditos disponíveis e os dados enviados.")

except httpx.RequestError as erro:
    print(f"Erro de conexão com o Tavily: {erro}")