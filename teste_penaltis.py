import requests
from dotenv import load_dotenv
import os

load_dotenv()

TOKEN = os.getenv("FOOTBALL_DATA_TOKEN")

url = "https://api.football-data.org/v4/competitions/PD/matches"

headers = {
    "X-Auth-Token": TOKEN
}

params = {
    "status": "FINISHED"
}

resposta = requests.get(
    url,
    headers=headers,
    params=params
)

dados = resposta.json()

if resposta.status_code != 200:
    print("Erro:", dados)

else:
    encontrado = False

    for partida in dados.get("matches", []):

        mandante = partida["homeTeam"]["name"]
        visitante = partida["awayTeam"]["name"]

        if (
            "Real Betis" in mandante
            and "Getafe" in visitante
        ) or (
            "Getafe" in mandante
            and "Real Betis" in visitante
        ):

            print("\nJOGO ENCONTRADO!")
            print("ID:", partida["id"])
            print("Competição:", partida["competition"]["name"])
            print("Mandante:", mandante)
            print("Visitante:", visitante)

            score = partida["score"]

            print(
                "Placar:",
                score["fullTime"]["home"],
                "x",
                score["fullTime"]["away"]
            )

            encontrado = True
            break

    if not encontrado:
        print("Real Betis x Getafe não encontrado.")