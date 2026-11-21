
import random

CURIOSIDADES_FUTEBOL = [
    "A primeira Copa do Mundo masculina aconteceu em 1930, no Uruguai, e terminou com o título dos anfitriões.",
    "O Brasil é a única seleção que participou de todas as edições da Copa do Mundo masculina até 2022.",
    "Pelé é o único jogador que conquistou três Copas do Mundo como atleta: 1958, 1962 e 1970.",
    "A primeira Copa do Mundo feminina foi realizada em 1991, na China.",
    "Os cartões amarelo e vermelho estrearam em Copas do Mundo na edição de 1970.",
    "A Copa do Mundo de 2010 foi a primeira realizada no continente africano.",
    "O Brasil conquistou sua primeira Copa do Mundo em 1958, na Suécia.",
    "A Copa do Mundo de 2002 foi realizada conjuntamente por Coreia do Sul e Japão.",
    "A FIFA foi fundada em 1904, em Paris, na França.",
    "A Inglaterra conquistou sua primeira Copa do Mundo masculina em 1966.",
    "A Argentina conquistou sua primeira Copa do Mundo masculina em 1978, como país-sede.",
    "A Alemanha venceu a Copa do Mundo de 2014, disputada no Brasil.",
    "A Copa do Mundo de 1998 foi a primeira com 32 seleções participantes.",
    "A Copa do Mundo de 2026 foi a primeira edição com 48 seleções.",
    "A Itália conquistou a Copa do Mundo de 1934 jogando em casa.",
    "A Copa do Mundo de 1950 ficou marcada pelo Maracanazo, quando o Uruguai venceu o Brasil por 2 a 1.",
    "O primeiro torneio olímpico de futebol masculino aconteceu em 1900, em Paris.",
    "A Copa do Mundo de 1930 contou com 13 seleções participantes.",
    "A Copa do Mundo de 2018 foi a primeira realizada na Rússia.",
    "A seleção brasileira conquistou cinco títulos da Copa do Mundo masculina: 1958, 1962, 1970, 1994 e 2002."
]


def obter_curiosidade_aleatoria() -> str:
    curiosidade = random.choice(CURIOSIDADES_FUTEBOL)
    return f"Você sabia? ⚽\n\n{curiosidade}"
