from backend.services.football_api import buscar_jogos_competicao, normalizar_nome_time
import requests
from backend.services.football_api import FOOTBALL_DATA_TOKEN

url = "https://api.football-data.org/v4/matches/564723/head2head"

headers = {
    "X-Auth-Token": FOOTBALL_DATA_TOKEN
}

params = {
    "limit": 10
}

resposta = requests.get(
    url,
    headers=headers,
    params=params,
    timeout=15
)

print("Status HTTP:", resposta.status_code)
print("Resposta da API:")
print(resposta.text)