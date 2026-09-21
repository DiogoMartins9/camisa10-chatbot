from backend.services.football_api import (
    buscar_ultimo_jogo,
    buscar_proximo_jogo
)

print("ÚLTIMO JOGO:")
print(buscar_ultimo_jogo(1776))

print("\nPRÓXIMO JOGO:")
print(buscar_proximo_jogo(1776))