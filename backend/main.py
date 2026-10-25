from time import time
from backend.knowledge.tactical_knowledge import CONHECIMENTO_TATICO
from fastapi import FastAPI
from pydantic import BaseModel
import ollama
from backend.services.football_api import (buscar_competicoes_football_data, buscar_proximos_jogos, buscar_time_football_data, buscar_competicoes_do_time, buscar_time, buscar_proximo_jogo, buscar_ultimo_jogo, buscar_ultimos_jogos, normalizar_nome_time, buscar_jogo_contra_adversario,buscar_jogos_time, FOOTBALL_DATA_TOKEN, API_KEY, nome_time_portugues, buscar_classificacao_competicao, buscar_historico_confrontos, buscar_jogos_competicao)
from backend.knowledge.football_knowledge import CONHECIMENTO_FUTEBOL
import unicodedata
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from backend.knowledge.historic_knowledge import buscar_conhecimento_historico
from backend.knowledge.external_research import (pesquisar_na_web, formatar_resultados_pesquisa, pergunta_sobre_divergencia_estatistica, pergunta_sobre_comparacao_estatistica)
import requests
import re

app = FastAPI()

class Pergunta(BaseModel):
    pergunta: str

@app.get("/")
def inicio():
    return {
        "message": "API do Chatbot Camisa 10 funcionando!"
    }

@app.get("/api/identificar-time")
def identificar_time(pergunta):
    texto = pergunta.lower()

    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(
        caractere
        for caractere in texto
        if unicodedata.category(caractere) != "Mn"
    )

    apelidos = {
        "spfc": "Sao Paulo",
        "tricolor": "Sao Paulo",
        "soberano": "Sao Paulo",
        "verdao": "Palmeiras",
        "timao": "Corinthians",
        "mengao": "Flamengo",
        "peixe": "Santos",
        "santastico": "Santos",
        "fogao": "Botafogo",
        "fluzao": "Fluminense",
        "vascao": "Vasco da Gama",
        "gigante da colina": "Vasco da Gama",
        "imortal": "Gremio",
        "colorado": "Internacional",
        "cabuloso": "Cruzeiro",
        "galo": "Atletico-MG",
        "leao do pici": "Fortaleza",
    }

    selecoes = {
        "brasil": "Brazil",
        "argentina": "Argentina",
        "uruguai": "Uruguay",
        "colombia": "Colombia",
        "chile": "Chile",
        "equador": "Ecuador",
        "peru": "Peru",
        "bolivia": "Bolivia",
        "paraguai": "Paraguay",
        "venezuela": "Venezuela",

        "portugal": "Portugal",
        "espanha": "Spain",
        "franca": "France",
        "alemanha": "Germany",
        "italia": "Italy",
        "inglaterra": "England",
        "belgica": "Belgium",
        "holanda": "Netherlands",
        "paises baixos": "Netherlands",
        "croacia": "Croatia",
        "eslovenia": "Slovenia",
        "eslovaquia": "Slovakia",
        "suecia": "Sweden",
        "suica": "Switzerland",
        "dinamarca": "Denmark",
        "noruega": "Norway",
        "polonia": "Poland",
        "turquia": "Turkey",
        "grecia": "Greece",
        "japao": "Japan",
        "coreia do sul": "South Korea",
        "mexico": "Mexico",
        "estados unidos": "United States",
    }

    nomes = [
        "sao paulo",
        "palmeiras",
        "corinthians",
        "flamengo",
        "santos",
        "botafogo",
        "fluminense",
        "vasco",
        "gremio",
        "internacional",
        "cruzeiro",
        "atletico mineiro",
        "atletico mg",
        "atletico-mg",
        "bahia",
        "fortaleza",
        "sport",
        "barcelona",
        "sevilla",
        "real madrid",
        "manchester city",
        "manchester united",
    ]

    # 1. Tenta reconhecer apelidos conhecidos
    for apelido, nome in apelidos.items():
        if apelido in texto:
            return nome

    # 1.5. Tenta reconhecer seleções
    for nome, nome_api in selecoes.items():
        if texto.strip() == nome:
            return nome_api

    # 2. Tenta reconhecer times já conhecidos
    for nome in nomes:
        if nome in texto:
            return nome.replace(
                "atletico mineiro",
                "Atletico-MG"
            )

    # 3. Se não encontrou, tenta descobrir pela API
    url = "https://api.football-data.org/v4/teams"
    headers = {"X-Auth-Token": FOOTBALL_DATA_TOKEN}
    params = {"limit": 500}

    resposta = requests.get(
        url,
        headers=headers,
        params=params
    )

    if resposta.status_code != 200:
        return None

    dados = resposta.json()

    for time in dados.get("teams", []):
        nome_api = normalizar_nome_time(time["name"])
        nome_curto_api = normalizar_nome_time(
            time.get("shortName") or ""
        )

        if nome_api and nome_api in texto:
            return time["name"]

        if nome_curto_api and nome_curto_api in texto:
            return time["name"]

    return None

IDS_TIMES = {
    "sao paulo": 1776,
    "palmeiras": 1769,
    "corinthians": 1779,
    "flamengo": 1783,
    "santos": 6685,
    "botafogo": 1770,
    "fluminense": 1765,
    "vasco": 1780,
    "gremio": 1767,
    "internacional": 6684,
    "cruzeiro": 1771,
    "atletico mg": 1766,
    "bahia": 1777,
    "fortaleza": 1768,
    "barcelona": 81,
    "sevilla": 559,
    "manchester city": 65,
    "manchester united": 66,
}

def obter_id_time(nome_time):
    if nome_time is None:
        return None

    nome_normalizado = normalizar_nome_time(nome_time)

    # Primeiro tenta encontrar no dicionário local
    if nome_normalizado in IDS_TIMES:
        return IDS_TIMES[nome_normalizado]

    # Se não encontrou, consulta a API
    url = "https://api.football-data.org/v4/teams"
    headers = {"X-Auth-Token": FOOTBALL_DATA_TOKEN}
    params = {"limit": 500}

    resposta = requests.get(
        url,
        headers=headers,
        params=params
    )

    if resposta.status_code != 200:
        return None

    dados = resposta.json()

    for time in dados.get("teams", []):
        nome_api = normalizar_nome_time(time["name"])
        nome_curto_api = normalizar_nome_time(time.get("shortName") or "")

        if (
            nome_api == nome_normalizado
            or nome_curto_api == nome_normalizado
        ):
            return time["id"]

    return None

def nome_exibicao_time(nome_time):
    if not nome_time:
        return "Time não identificado"
    
    nomes = {
        "sao paulo": "São Paulo",
        "palmeiras": "Palmeiras",
        "corinthians": "Corinthians",
        "flamengo": "Flamengo",
        "santos": "Santos",
        "botafogo": "Botafogo",
        "fluminense": "Fluminense",
        "vasco": "Vasco",
        "gremio": "Grêmio",
        "internacional": "Internacional",
        "cruzeiro": "Cruzeiro",
        "atletico mg": "Atlético-MG",
        "bahia": "Bahia",
        "barcelona": "Barcelona",
        "fortaleza": "Fortaleza"
    }

    nome_normalizado = normalizar_nome_time(nome_time)

    return nomes.get(nome_normalizado, nome_time)

def nome_exibicao_api(nome_time):
    nomes = {
        "São Paulo FC": "São Paulo",
        "SE Palmeiras": "Palmeiras",
        "SC Corinthians Paulista": "Corinthians",
        "CR Flamengo": "Flamengo",
        "Santos FC": "Santos",
        "Botafogo FR": "Botafogo",
        "Fluminense FC": "Fluminense",
        "CR Vasco da Gama": "Vasco",
        "Grêmio FBPA": "Grêmio",
        "SC Internacional": "Internacional",
        "Cruzeiro EC": "Cruzeiro",
        "Clube Atlético Mineiro": "Atlético-MG",
        "CA Mineiro": "Atlético-MG",
        "EC Bahia": "Bahia",
        "Fortaleza EC": "Fortaleza"
    }

    return nomes.get(nome_time, nome_time)

def identificar_dado_classificacao(pergunta):

    texto = pergunta.lower()

    if (
        "classificação" in texto
        or "classificacao" in texto
        or "posição" in texto
        or "posicao" in texto
        or "lugar" in texto
        or "colocação" in texto
        or "colocacao" in texto
    ):
        return "posicao"

    if "ponto" in texto or "pontos" in texto:
        return "pontos"

    if "vitoria" in texto or "vitória" in texto or "venceu" in texto or "ganhou" in texto:
        return "vitorias"

    if "empate" in texto or "empatou" in texto:
        return "empates"
    
    if "derrota" in texto or "perdeu" in texto or "foi derrotado" in texto:
        return "derrotas"

    if "jogo" in texto or "partida" in texto:
        return "jogos"

    return None


def comparar_conceitos_futebol(pergunta):
    texto = pergunta.lower()

    palavras_comparacao = [
        "qual a diferença",
        "qual é a diferença",
        "qual a diferenca",
        "qual é a diferenca",
        "diferença entre",
        "diferenca entre",
        "compare",
        "comparar"
    ]

    if not any(expressao in texto for expressao in palavras_comparacao):
        return None

    conceitos = {
        "impedimento": "impedimento",
        "falta": "falta",
        "escanteio": "escanteio",
        "tiro de meta": "tiro_de_meta",
        "gol": "gol",
        "assistência": "assistencia",
        "assistencia": "assistencia",
        "pênalti": "penalti",
        "penalti": "penalti",
        "cartão amarelo": "cartao_amarelo",
        "cartao amarelo": "cartao_amarelo",
        "cartão vermelho": "cartao_vermelho",
        "cartao vermelho": "cartao_vermelho"
    }

    encontrados = []

    for termo, chave in conceitos.items():
        if termo in texto and chave not in encontrados:
            encontrados.append(chave)

    if len(encontrados) < 2:
        return None

    partes = []

    for chave in encontrados:
        if chave in CONHECIMENTO_FUTEBOL:
            partes.append(CONHECIMENTO_FUTEBOL[chave])

    if len(partes) < 2:
        return None

    resposta = "\n\n".join(partes)

    diferencas = {
        ("escanteio", "tiro_de_meta"): (
            "A diferença principal é quem tocou na bola por último antes "
            "de ela sair pela linha de fundo: no escanteio, foi um defensor; "
            "no tiro de meta, foi um atacante."
        ),
        ("impedimento", "falta"): (
            "A diferença principal é que o impedimento está relacionado "
            "à posição e à participação do atacante na jogada, enquanto "
            "a falta envolve uma infração às regras, como uma ação irregular "
            "contra um adversário."
        ),
        ("cartao_amarelo", "cartao_vermelho"): (
            "A diferença principal é a consequência disciplinar: o cartão amarelo "
            "é uma advertência, enquanto o cartão vermelho resulta na expulsão "
            "do jogador. Um jogador que recebe dois cartões amarelos na mesma partida "
            "também é expulso."
        ),
        ("gol", "assistencia"): (
            "A diferença principal é que o gol é marcado pelo jogador que "
            "coloca a bola na meta adversária, enquanto a assistência é o "
            "passe ou a ação que contribui diretamente para a marcação do gol."
        ),
        ("falta", "gol"): (
            "A diferença principal é que a falta é uma infração às regras do futebol, "
            "enquanto o gol é uma forma de pontuar quando a bola ultrapassa completamente "
            "a linha de gol, entre as traves e por baixo do travessão, sem infração "
            "da equipe que marcou."
        ),
        ("impedimento", "escanteio"): (
            "A diferença principal é que o impedimento está relacionado à posição "
            "e à participação de um jogador atacante na jogada, enquanto o escanteio "
            "é uma forma de reiniciar o jogo quando a bola sai pela linha de fundo "
            "após o último toque de um jogador da equipe defensora, sem que seja gol."
        ),
        ("gol", "impedimento"): (
            "A diferença principal é que o gol é uma forma de pontuar quando "
            "a bola ultrapassa completamente a linha de gol, enquanto o impedimento "
            "é uma infração relacionada à posição e à participação de um atacante "
            "na jogada. Um gol pode ser anulado se houver impedimento na jogada."
        ),
        ("falta", "penalti"): (
            "A diferença principal é que a falta é uma infração às regras do futebol "
            "que pode resultar em tiro livre direto ou indireto, enquanto o pênalti "
            "é uma cobrança concedida quando a equipe defensora comete, dentro da "
            "própria área penal, uma infração punível com tiro livre direto."
        ),
        ("cartao_amarelo", "falta"): (
            "A diferença principal é que a falta é uma infração às regras do futebol, "
            "enquanto o cartão amarelo é uma punição disciplinar aplicada pelo árbitro. "
            "Uma falta pode resultar em cartão amarelo, mas nem toda falta recebe essa punição."
        ),
        ("escanteio", "falta"): (
            "A diferença principal é que a falta ocorre quando um jogador comete "
            "uma infração às regras, enquanto o escanteio é uma forma de reiniciar "
            "o jogo quando a bola sai pela linha de fundo após o último toque de "
            "um jogador da equipe defensora, sem que seja gol."
        ),
        ("assistencia", "impedimento"): (
            "A diferença principal é que a assistência é o passe ou a ação que "
            "contribui diretamente para um gol, enquanto o impedimento é uma "
            "infração relacionada à posição e à participação de um atacante na jogada. "
            "Uma assistência pode ocorrer em uma jogada regular, sem impedimento."
        ),
    }

    for (conceito_a, conceito_b), diferenca in diferencas.items():
        if conceito_a in encontrados and conceito_b in encontrados:
            resposta += "\n\n" + diferenca
            break

        if conceito_b in encontrados and conceito_a in encontrados:
            resposta += "\n\n" + diferenca
            break

    return resposta

def buscar_conhecimento(pergunta):

    texto = pergunta.lower()

    if (
        ("pelé" in texto or "pele" in texto or "rei do futebol" in texto)
        and ("gol" in texto or "gols" in texto)
        and any(
            termo in texto
            for termo in ["quantos", "quantas", "oficial", "carreira", "marcou",
                          "total", "números diferentes", "numero diferente", "por que",
                          "porque"]
        )
    ):
        return None

    if (
        ("pênalti" in texto or "penalti" in texto)
        and "goleiro" in texto
        and ("defende a bola" in texto or "defendeu a bola" in texto)
        and ("cobrador" in texto or "jogador" in texto)
        and ("toca novamente" in texto or "tocou novamente" in texto)
        and ("erra o gol" in texto or "erra a cobrança" in texto
             or "bola sai pela linha de fundo" in texto
             or "sai pela linha de fundo" in texto)
    ):
        return (
            "O árbitro deve conceder tiro de meta à equipe defensora, "
            "pois o goleiro tocou na bola ao defender o pênalti, permitindo "
            "o segundo toque do cobrador. Como a bola saiu pela linha de "
            "fundo sem entrar no gol, o jogo recomeça com tiro de meta."
        )

    if (
        ("pênalti" in texto or "penalti" in texto)
        and "goleiro" in texto
        and ("defende a bola" in texto or "defendeu a bola" in texto)
        and "rebote" in texto
        and ("companheiro" in texto or "colega" in texto)
        and ("marca o gol" in texto or "marca o gol no rebote" in texto
             or "marcou o gol" in texto or "marca o gol no rebote" in texto)
    ):
        return (
            "O árbitro deve validar o gol, desde que não haja outra "
            "infração. Como o goleiro tocou na bola ao defender o pênalti, "
            "o companheiro do cobrador pode aproveitar o rebote e marcar."
        )

    if (
        ("pênalti" in texto or "penalti" in texto)
        and "goleiro" in texto
        and ("defende a bola" in texto or "defendeu a bola" in texto
             or "defesa do goleiro" in texto)
        and "rebote" in texto
        and ("cobrador" in texto or "jogador" in texto)
        and ("marca o gol" in texto or "marca o gol" in texto
             or "marca o gol" in texto or "faz o gol" in texto)
        and ("antes que qualquer outro jogador" in texto
             or "antes de qualquer outro jogador" in texto)
    ):
        return (
            "O árbitro deve validar o gol, desde que não haja outra "
            "infração. Como o goleiro tocou na bola ao defender o "
            "pênalti, o cobrador pode tocar nela novamente e marcar "
            "no rebote."
        )

    if (
        ("pênalti" in texto or "penalti" in texto)
        and ("companheiro" in texto or "colega" in texto)
        and ("cobrador" in texto or "jogador" in texto)
        and "trave" in texto
        and ("toca na bola" in texto or "tocou na bola" in texto)
        and ("antes que qualquer defensor" in texto
             or "antes de qualquer defensor" in texto)
    ):
        return (
            "O árbitro deve deixar o jogo continuar, pois o companheiro "
            "do cobrador pode tocar na bola após o rebote na trave. "
            "A infração de dois toques só ocorre se o próprio cobrador "
            "tocar novamente na bola antes que outro jogador a toque."
        )

    if (
        ("pênalti" in texto or "penalti" in texto)
        and "goleiro" in texto
        and ("permanece sobre a linha" in texto
             or "permanece na linha" in texto
             or "ficou sobre a linha" in texto)
        and "trave" in texto
        and ("defensor afasta" in texto
             or "defensor afastou" in texto
             or "afasta a bola" in texto)
    ):
        return (
            "O árbitro deve deixar o jogo continuar. O goleiro permaneceu "
            "sobre a linha durante a cobrança, a bola bateu na trave e "
            "um defensor afastou o rebote antes que um atacante a tocasse. "
            "Como não houve infração, não há motivo para repetir o pênalti."
        )

    if (
        ("pênalti" in texto or "penalti" in texto)
        and "goleiro" in texto
        and ("permanece sobre a linha" in texto
             or "permanece na linha" in texto
             or "ficou sobre a linha" in texto)
        and "trave" in texto
        and ("rebote" in texto or "volta para o campo" in texto)
        and ("atacante" in texto or "jogador" in texto)
        and ("marca no rebote" in texto or "marca no rebote" in texto
             or "marca o gol" in texto or "faz o gol" in texto)
    ):
        return (
            "O árbitro deve validar o gol, desde que não tenha ocorrido "
            "outra infração. O goleiro permaneceu sobre a linha durante "
            "a cobrança, e o atacante marcou aproveitando o rebote da trave."
        )

    if (
        ("pênalti" in texto or "penalti" in texto)
        and "goleiro" in texto
        and ("se adianta" in texto or "adianta da linha" in texto
             or "adiantou" in texto)
        and "trave" in texto
        and ("defensor afasta" in texto or "defensor afastou" in texto
             or "afasta a bola" in texto)
    ):
        return (
            "O árbitro deve avaliar se o adiantamento do goleiro afetou "
            "claramente o cobrador. Se afetou, a cobrança deve ser repetida; "
            "caso contrário, o jogo continua. Como o defensor afastou o "
            "rebote, não há gol a validar."
        )

    if (
        ("pênalti" in texto or "penalti" in texto)
        and "goleiro" in texto
        and ("se adianta" in texto or "adianta da linha" in texto
             or "adiantou" in texto)
        and "trave" in texto
        and ("rebote" in texto or "volta para o campo" in texto)
        and ("atacante" in texto or "jogador" in texto)
        and ("marca o gol" in texto or "faz o gol" in texto
             or "marcou o gol" in texto)
    ):
        return (
            "O árbitro deve avaliar se o adiantamento do goleiro afetou "
            "claramente o cobrador. Se afetou, a cobrança deve ser repetida. "
            "Se não afetou, o gol marcado no rebote pode ser validado, desde "
            "que o atacante não tenha cometido outra infração."
        )

    if (
        ("pênalti" in texto or "penalti" in texto)
        and "goleiro" in texto
        and ("se adianta" in texto or "adianta da linha" in texto
             or "adiantou" in texto)
        and "trave" in texto
        and ("volta para o campo" in texto
             or "volta ao campo" in texto)
        and ("sem entrar no gol" in texto
             or "não entrar no gol" in texto
             or "nao entrar no gol" in texto)
    ):
        return (
            "O árbitro deve avaliar se o adiantamento do goleiro afetou "
            "claramente o cobrador. Se afetou, a cobrança deve ser repetida; "
            "caso contrário, o jogo continua. O simples fato de a bola "
            "bater na trave não determina, por si só, a repetição."
        )

    if (
        ("pênalti" in texto or "penalti" in texto)
        and ("cobrador" in texto or "jogador" in texto)
        and ("escorrega" in texto or "escorregou" in texto)
        and ("dois pés" in texto or "dois pes" in texto
             or "ambos os pés" in texto or "ambos os pes" in texto)
        and ("para fora" in texto or "não entra no gol" in texto
             or "nao entra no gol" in texto)
    ):
        return (
            "O árbitro deve conceder um tiro livre indireto à equipe "
            "defensora. Quando o cobrador toca acidentalmente na bola "
            "com os dois pés ao mesmo tempo e ela não entra no gol, "
            "a cobrança não deve ser repetida, conforme a Regra 14 da IFAB."
        )

    if (
        ("pênalti" in texto or "penalti" in texto)
        and ("cobrador" in texto or "jogador" in texto)
        and ("escorrega" in texto or "escorregou" in texto)
        and ("dois pés" in texto or "dois pes" in texto
             or "ambos os pés" in texto or "ambos os pes" in texto)
        and ("gol" in texto or "entra" in texto)
    ):
        return (
            "O árbitro deve mandar repetir a cobrança. Quando o cobrador "
            "toca acidentalmente na bola com os dois pés ao mesmo tempo "
            "e ela entra diretamente no gol, a cobrança deve ser repetida, "
            "conforme a Regra 14 da IFAB."
        )

    if (
        ("pênalti" in texto or "penalti" in texto)
        and ("cobrador" in texto or "jogador" in texto)
        and ("trave" in texto)
        and ("segundo toque" in texto or "duas vezes" in texto
             or "novamente" in texto)
        and ("antes que qualquer outro jogador" in texto
             or "antes de outro jogador" in texto)
        and ("gol" in texto or "marcar" in texto)
    ):
        return (
            "O gol deve ser anulado e concedido tiro livre indireto "
            "à equipe defensora, pois o cobrador tocou na bola pela "
            "segunda vez antes que qualquer outro jogador a tocasse. "
            "O fato de a bola ter batido na trave não permite um "
            "segundo toque imediato do cobrador."
        )

    if (
        ("pênalti" in texto or "penalti" in texto)
        and ("defensor" in texto or "equipe defensora" in texto
             or "adversário" in texto or "adversario" in texto)
        and ("grita" in texto or "gritou" in texto
             or "distrair" in texto or "distrai" in texto)
        and ("perde" in texto or "perdeu" in texto
             or "para fora" in texto)
    ):
        return (
            "O árbitro deve mandar repetir a cobrança e advertir com "
            "cartão amarelo o jogador defensor por conduta antidesportiva, "
            "pois ele distraiu deliberadamente o cobrador durante a execução "
            "do pênalti."
        )

    if (
        ("pênalti" in texto or "penalti" in texto)
        and ("companheiro" in texto or "colega" in texto)
        and ("invade" in texto or "invadiu" in texto
             or "invasão" in texto or "invasao" in texto)
        and ("não interfere" in texto or "nao interfere" in texto)
        and ("não participa" in texto or "nao participa" in texto
             or "nem participa" in texto)
        and ("para fora" in texto or "chuta para fora" in texto
             or "erra o gol" in texto)
    ):
        return (
            "O árbitro deve conceder tiro de meta à equipe defensora, "
            "desde que a invasão do companheiro não tenha afetado o "
            "cobrador nem interferido na jogada. A cobrança não deve "
            "ser repetida apenas pela invasão sem influência no lance."
        )

    if (
        ("pênalti" in texto or "penalti" in texto)
        and ("companheiro" in texto or "colega" in texto)
        and ("invade" in texto or "invadiu" in texto
             or "invasão" in texto or "invasao" in texto)
        and ("não interfere" in texto or "nao interfere" in texto)
        and (
            "não participa" in texto
            or "nao participa" in texto
            or "nem participa" in texto
        )
        and ("gol" in texto or "entra diretamente" in texto)
    ):
        return (
            "O árbitro deve validar o gol, desde que a invasão não tenha "
            "afetado o goleiro nem interferido na jogada. Pela Regra 14 "
            "da IFAB, a invasão de um companheiro do cobrador não exige "
            "repetição automaticamente quando não afeta o goleiro."
        )

    if (
        ("pênalti" in texto or "penalti" in texto)
        and ("companheiro" in texto or "colega" in texto)
        and ("invade" in texto or "invadiu" in texto
             or "invasão" in texto or "invasao" in texto)
        and ("atrapalha" in texto or "atrapalhou" in texto
             or "interfere" in texto or "interferiu" in texto)
        and "goleiro" in texto
        and ("gol" in texto or "sofrendo o gol" in texto)
        and "não interfere" not in texto
        and "nao interfere" not in texto
        and "não participa" not in texto
        and "nao participa" not in texto
    ):
        return (
            "O árbitro deve mandar repetir a cobrança, pois o companheiro "
            "do cobrador invadiu a área e afetou claramente o goleiro. "
            "Como a bola entrou no gol, a repetição é a decisão correta "
            "conforme a Regra 14 da IFAB."
        )

    if (
        ("pênalti" in texto or "penalti" in texto)
        and ("companheiro" in texto or "colega" in texto)
        and ("invade" in texto or "invadiu" in texto
             or "invasão" in texto or "invasao" in texto)
        and ("não participa" in texto or "nao participa" in texto)
        and ("goleiro defende" in texto or "defende a cobrança" in texto
             or "defende a cobranca" in texto)
        and ("defensor afasta" in texto or "afasta a bola" in texto)
    ):
        return (
            "O árbitro deve deixar o jogo continuar, desde que a invasão "
            "não tenha afetado claramente o goleiro nem interferido no "
            "lance. Como o companheiro do cobrador não participou da "
            "jogada e um defensor afastou a bola, não há motivo para "
            "repetir a cobrança apenas pela invasão."
        )

    if (
        ("pênalti" in texto or "penalti" in texto)
        and ("cobrador" in texto or "jogador" in texto)
        and ("duas vezes" in texto or "segunda vez" in texto
             or "duas vezes seguidas" in texto)
        and ("outro jogador" in texto or "ninguém" in texto
             or "ninguem" in texto)
        and ("gol" in texto or "entra" in texto)
    ):
        return (
            "O árbitro deve anular o gol e conceder um tiro livre "
            "indireto à equipe defensora, pois o cobrador tocou na "
            "bola uma segunda vez antes que outro jogador a tocasse."
        )

    if (
        ("pênalti" in texto or "penalti" in texto)
        and "goleiro" in texto
        and ("se adianta" in texto or "adianta" in texto
             or "adiantou" in texto)
        and ("para fora" in texto or "fora do gol" in texto)
    ):
        return (
            "Se o goleiro se adiantar antes da cobrança e o cobrador "
            "chutar para fora, o árbitro deve mandar repetir o pênalti "
            "somente se o adiantamento tiver afetado claramente o "
            "cobrador. Caso contrário, mantém-se o tiro de meta."
        )

    if (
        ("pênalti" in texto or "penalti" in texto)
        and ("defensor" in texto or "equipe defensora" in texto
             or "jogador da equipe defensora" in texto)
        and ("invade" in texto or "invadiu" in texto
             or "invasão" in texto or "invasao" in texto)
        and ("para fora" in texto or "fora do gol" in texto)
    ):
        return (
            "O árbitro deve mandar repetir o pênalti se a invasão do "
            "jogador da equipe defensora tiver influenciado o cobrador "
            "ou afetado o lance. Se a invasão não tiver influenciado "
            "a cobrança, o jogo pode continuar."
        )

    if (
        ("pênalti" in texto or "penalti" in texto)
        and ("companheiro" in texto or "colega" in texto)
        and ("invade" in texto or "invadiu" in texto
             or "invasão" in texto or "invasao" in texto)
        and ("goleiro defende" in texto or "defende a cobrança" in texto
             or "defende a cobranca" in texto or "defesa do goleiro" in texto)
        and ("marca o gol" in texto or "marcou o gol" in texto
             or "marca" in texto)
    ):
        return (
            "O árbitro deve anular o gol e conceder um tiro livre "
            "indireto à equipe defensora, pois o companheiro do cobrador "
            "invadiu a área e obteve vantagem ao participar da jogada "
            "após a defesa do goleiro."
        )

    if (
        ("pênalti" in texto or "penalti" in texto)
        and ("companheiro" in texto or "colega" in texto)
        and ("invade" in texto or "invadiu" in texto
             or "invasão" in texto or "invasao" in texto)
        and ("área" in texto or "area" in texto)
        and ("bola entra" in texto or "gol" in texto)
        and "goleiro defende" not in texto
        and "defesa do goleiro" not in texto
        and "defensor afasta" not in texto
        and "afasta a bola" not in texto
        and "não participa" not in texto
        and "nao participa" not in texto
    ):
        return (
            "O árbitro deve mandar repetir a cobrança, pois um "
            "companheiro do cobrador invadiu a área antes do chute "
            "e a bola entrou no gol."
        )

    if (
        ("pênalti" in texto or "penalti" in texto)
        and ("para trás" in texto or "para tras" in texto)
        and ("chuta" in texto or "chutar" in texto or "chutou" in texto)
    ):
        return (
            "A bola deve ser chutada para a frente durante a cobrança "
            "de pênalti. Se o cobrador chutar a bola para trás, o árbitro "
            "deve interromper a cobrança e conceder um tiro livre "
            "indireto à equipe defensora."
        )

    if (
        ("pênalti" in texto or "penalti" in texto)
        and ("finta" in texto or "fingir" in texto or "simula" in texto)
        and ("cobrador" in texto or "jogador" in texto)
        and (
            "corrida" in texto
            or "chutar" in texto
            or "chute" in texto
        )
    ):
        return (
            "Se o cobrador fizer uma finta ilegal após concluir a corrida "
            "para a bola, o árbitro deve adverti-lo com cartão amarelo e "
            "marcar tiro livre indireto para a equipe defensora, "
            "independentemente de a bola entrar no gol."
        )

    if (
        ("pênalti" in texto or "penalti" in texto)
        and "goleiro" in texto
        and ("se adianta" in texto or "adianta" in texto
             or "adiantou" in texto)
        and ("trave" in texto or "bate na trave" in texto)
        and ("entra no gol" in texto or "bola entra" in texto
             or "gol" in texto)
    ):
        return (
            "O árbitro deve validar o gol. Se o goleiro se adiantar "
            "antes da cobrança, mas a bola entrar no gol, o pênalti "
            "não deve ser repetido apenas por causa do adiantamento."
        )

    if (
        ("pênalti" in texto or "penalti" in texto)
        and ("goleiro" in texto)
        and ("se adianta" in texto or "adianta" in texto)
        and ("defende" in texto or "defendeu" in texto)
    ):
        return (
            "O árbitro deve mandar repetir a cobrança se o goleiro se "
            "adiantou antes do chute e essa infração afetou o resultado "
            "da cobrança, impedindo o gol. O cartão amarelo pode ser "
            "aplicado se a infração for repetida ou houver outra razão "
            "disciplinar aplicável."
        )

    if (
        ("pênalti" in texto or "penalti" in texto)
        and ("cobrador" in texto or "jogador que bate" in texto)
        and ("invade" in texto or "invasão" in texto or "invasao" in texto)
        and ("marca o gol" in texto or "marcou o gol" in texto or "marca gol" in texto)
    ):
        return (
            "O árbitro deve anular o gol e marcar tiro livre indireto "
            "para a equipe defensora, pois o cobrador cometeu uma infração "
            "ao invadir a área antes da cobrança."
        )

    if (
        ("pênalti" in texto or "penalti" in texto)
        and ("invade" in texto or "invasão" in texto or "invasao" in texto)
        and ("goleiro defende" in texto or "defende a cobrança" in texto
             or "defende a cobranca" in texto)
        and ("defensor" in texto or "equipe defensora" in texto
             or "jogador da equipe defensora" in texto)
    ):
        return (
            "O árbitro deve mandar repetir a cobrança se a invasão do "
            "defensor tiver influenciado o lance, como ao disputar a bola "
            "que sobrou após a defesa do goleiro. Se a invasão não tiver "
            "influenciado o lance, o jogo pode continuar"
        )

    if (
        ("vantagem" in texto or "parar o jogo" in texto)
        and ("pênalti" in texto or "penalti" in texto)
        and ("atacante" in texto or "bola sobra" in texto)
    ):
        return (
            "O árbitro não precisa interromper o jogo imediatamente. "
            "Pode aplicar a vantagem se a continuidade da jogada beneficiar "
            "a equipe atacante. Se a vantagem esperada não se concretizar, "
            "o árbitro poderá voltar à infração e marcar o pênalti, conforme "
            "as circunstâncias e as regras aplicáveis."
        )

    if (
        ("zagueiro" in texto or "defensor" in texto)
        and ("empurra" in texto or "empurrar" in texto or "empurrão" in texto
             or "empurrao" in texto)
        and "atacante" in texto
        and ("área" in texto or "area" in texto)
        and (
            "não tinha uma clara oportunidade de gol" in texto
            or "nao tinha uma clara oportunidade de gol" in texto
        )
    ):
        return (
            "O árbitro deve marcar pênalti, pois o zagueiro cometeu uma "
            "infração punível com tiro livre direto dentro da própria área "
            "de pênalti. O cartão depende das circunstâncias e não é "
            "automaticamente vermelho."
        )

    if (
        ("zagueiro" in texto or "defensor" in texto)
        and (
            "segura" in texto
            or "segurando" in texto
            or "agarrando" in texto
            or "puxa pela camisa" in texto
        )
        and ("camisa" in texto or "atacante" in texto)
        and ("área" in texto or "area" in texto)
        and (
            "clara oportunidade" in texto
            or "impedindo" in texto
            or "impedir" in texto
        )
    ):
        return (
            "O árbitro deve marcar pênalti e expulsar o zagueiro com "
            "cartão vermelho por impedir uma clara oportunidade de gol, "
            "desde que os critérios para essa punição sejam atendidos."
        )

    if (
        ("zagueiro" in texto or "defensor" in texto)
        and ("derruba" in texto or "derrubar" in texto or "falta" in texto)
        and ("cara a cara" in texto or "clara oportunidade" in texto)
        and ("fora da área" in texto or "fora da propria area" in texto
             or "fora da própria área" in texto)
    ):
        return (
            "O árbitro deve marcar tiro livre direto e expulsar o zagueiro "
            "com cartão vermelho por impedir uma clara oportunidade de gol, "
            "desde que os critérios para essa punição sejam atendidos."
        )

    if (
        ("zagueiro" in texto or "defensor" in texto)
        and ("mão" in texto or "mao" in texto)
        and ("deliberadamente" in texto or "deliberada" in texto)
        and ("área" in texto or "area" in texto)
        and (
            "não estava indo em direção ao gol" in texto
            or "nao estava indo em direção ao gol" in texto
            or "não estava indo em direcao ao gol" in texto
            or "nao estava indo em direcao ao gol" in texto
        )
    ):
        return (
            "O árbitro deve marcar pênalti, pois o zagueiro tocou "
            "deliberadamente a bola com a mão dentro da própria área "
            "de pênalti. O cartão depende das circunstâncias da infração; "
            "não é automaticamente vermelho."
        )

    if (
        ("zagueiro" in texto or "defensor" in texto)
        and ("mão" in texto or "mao" in texto)
        and ("gol" in texto)
        and ("área" in texto or "area" in texto)
        and (
            "impede" in texto 
            or "impedir" in texto 
            or "impede que a bola entre" in texto
        )
    ):
        return (
            "O árbitro deve marcar pênalti e expulsar o zagueiro com "
            "cartão vermelho por impedir um gol com mão deliberada, "
            "desde que a infração tenha impedido um gol de forma clara."
        )

    if (
        "goleiro" in texto
        and ("chute" in texto or "chuta" in texto)
        and ("companheiro" in texto or "próprio gol" in texto or "proprio gol" in texto)
        and ("mãos" in texto or "maos" in texto or "defende" in texto)
    ):
        return (
            "Nenhuma infração deve ser marcada. O goleiro pode usar as mãos "
            "dentro da própria área de pênalti para defender um chute de "
            "um companheiro, desde que não se trate de uma situação proibida "
            "pelas regras."
        )

    if (
        ("simulação" in texto or "simulacao" in texto or "se joga" in texto)
        and ("árbitro" in texto or "arbitro" in texto)
        and (
            "pênalti" in texto or "penalti" in texto
            or "área" in texto or "area" in texto
        )
    ):
        return (
            "O árbitro deve advertir o atacante com cartão amarelo por "
            "simulação e marcar tiro livre indireto para a equipe "
            "adversária no local da infração."
        )

    if (
        "goleiro" in texto
        and ("cabeça" in texto or "cabeca" in texto)
        and ("defensor" in texto or "companheiro" in texto)
        and ("mãos" in texto or "maos" in texto or "pega" in texto)
    ):
        if (
            "truque" in texto
            or "contornar a regra" in texto
            or "levantar a bola com o pé" in texto
            or "levantar a bola com o pe" in texto
        ):
            return (
                "O árbitro deve marcar tiro livre indireto para a equipe "
                "adversária. O jogador que usar deliberadamente um truque "
                "para contornar a regra do recuo deve receber cartão amarelo."
            )

        return (
            "O árbitro deve permitir que o jogo continue. Um passe legítimo "
            "com a cabeça para o próprio goleiro não impede que ele pegue "
            "a bola com as mãos dentro da área de pênalti."
        )

    if (
        "goleiro" in texto
        and ("defensor" in texto or "companheiro" in texto)
        and ("deliberadamente" in texto or "deliberado" in texto)
        and ("pé" in texto or "pe" in texto)
        and ("mãos" in texto or "maos" in texto)
    ):
        return (
            "O árbitro deve marcar tiro livre indireto para a equipe "
            "adversária, pois o goleiro não pode tocar com as mãos "
            "dentro da própria área uma bola recebida diretamente "
            "de um passe deliberado com o pé de um companheiro."
        )

    if (
        ("falta" in texto or "tiro livre" in texto)
        and ("novamente" in texto or "segundo toque" in texto or "dois toques" in texto)
        and ("antes que qualquer outro jogador" in texto or "outro jogador" in texto)
    ):
        return (
            "O árbitro deve marcar tiro livre indireto para a equipe "
            "adversária no local do segundo toque, pois o cobrador "
            "não pode tocar na bola novamente antes que outro jogador "
            "a toque, desde que não tenha ocorrido uma infração mais grave."
        )

    if (
        ("pênalti" in texto or "penalti" in texto)
        and "goleiro" in texto
        and ("espalma" in texto or "defende" in texto)
        and ("novamente" in texto or "segunda vez" in texto)
    ):
        return (
            "Sim. Se o goleiro defende o pênalti e toca na bola, "
            "o cobrador pode tocá-la novamente e marcar o gol, "
            "desde que não cometa outra infração."
        )

    if (
        "pênalti" in texto or "penalti" in texto
    ):
        if (
            ("trave" in texto or "rebote" in texto)
            and ("cobrador" in texto or "cobrou" in texto)
            and ("novamente" in texto or "outra vez" in texto)
        ):
            return (
                "Não. Se a bola bate na trave e volta diretamente "
                "para o cobrador, ele não pode tocá-la novamente "
                "antes que outro jogador a toque. O árbitro deve "
                "marcar tiro livre indireto para a equipe adversária."
            )

    if (
        "impedimento" in texto
        and ("falta" in texto or "livre direto" in texto)
        and ("diretamente" in texto or "cobrança" in texto or "cobranca" in texto)
    ):
        return (
            "Sim, o impedimento pode ser marcado em uma cobrança de "
            "falta. Se o atacante estava em posição de impedimento no "
            "momento da cobrança e participa ativamente da jogada, "
            "o árbitro deve marcar tiro livre indireto para a equipe "
            "defensora."
        )

    if (
        "impedimento" in texto
        and ("defensor" in texto or "adversário" in texto or "adversario" in texto)
        and ("deliberadamente" in texto or "deliberada" in texto)
        and ("afastar" in texto or "erra o passe" in texto or "erra" in texto)
    ):
        return (
            "Em regra, não há impedimento se o defensor adversário "
            "joga deliberadamente a bola e ela chega ao atacante. "
            "A exceção ocorre quando se trata de uma defesa deliberada "
            "de uma bola que ia para o gol ou muito próxima dele."
        )

    if (
        "impedimento" in texto
        and ("rebater" in texto or "rebote" in texto)
        and "goleiro" in texto
    ):
        return (
            "O árbitro deve marcar impedimento se o atacante já estava "
            "em posição de impedimento quando um companheiro chutou a "
            "bola e ele passou a participar da jogada após o rebote. "
            "Uma defesa deliberada do goleiro não elimina o impedimento."
        )

    if (
        "impedimento" in texto
        and ("atrapalhando" in texto or "interferindo" in texto)
        and ("defensor" in texto or "adversário" in texto or "adversario" in texto)
    ):
        return (
            "O árbitro deve marcar tiro livre indireto para a equipe "
            "defensora, pois o atacante em posição de impedimento "
            "está interferindo na capacidade do adversário de jogar a bola."
        )

    if (
        ("mão" in texto or "mao" in texto)
        and ("área" in texto or "area" in texto)
        and (
            "defensor" in texto
            or "jogador" in texto
        )
    ):
        if (
            "fora da própria área" in texto
            or "fora da propria area" in texto
            or "fora da área" in texto
            or "fora da area" in texto
        ):
            return (
                "O árbitro deve marcar tiro livre direto para a equipe "
                "adversária, pois a infração de mão na bola ocorreu "
                "fora da área de pênalti."
            )

        if (
            "dentro da própria área" in texto
            or "dentro da propria area" in texto
            or "dentro da área" in texto
            or "dentro da area" in texto
        ):
            return (
                "O árbitro deve marcar pênalti para a equipe adversária, "
                "desde que a infração de mão na bola seja punível com "
                "tiro livre direto."
            )

    if (
        "impedimento" in texto
        and (
            "escanteio" in texto
            or "cobrança de canto" in texto
            or "cobranca de canto" in texto
        )
    ):
        return (
            "Não. Um jogador não comete infração de impedimento ao "
            "receber a bola diretamente de uma cobrança de escanteio, "
            "mesmo que esteja em posição de impedimento."
        )

    if (
        "impedimento" in texto
        and (
            "lateral" in texto
            or "arremesso lateral" in texto
        )
    ):
        return (
            "Não. Um jogador não comete infração de impedimento ao "
            "receber a bola diretamente de um arremesso lateral, "
            "mesmo que esteja em posição de impedimento."
        )

    if (
        "impedimento" in texto
        and (
            "tiro de meta" in texto
            or "tiro-de-meta" in texto
        )
    ):
        return (
            "Não. Um jogador não comete infração de impedimento ao "
            "receber a bola diretamente de um tiro de meta, mesmo "
            "que esteja em posição de impedimento."
        )

    if (
        "goleiro" in texto
        and (
            "oito segundos" in texto
            or "8 segundos" in texto
        )
    ):
        return (
            "Se o goleiro mantiver o controle da bola com as mãos por mais "
            "de oito segundos dentro da própria área, o árbitro concede "
            "um escanteio à equipe adversária."
        )

    if (
        "goleiro" in texto
        and (
            "lateral" in texto
            or "arremesso lateral" in texto
        )
        and (
            "pega a bola com as mãos" in texto
            or "pega a bola com as maos" in texto
            or "segura a bola com as mãos" in texto
            or "segura a bola com as maos" in texto
        )
    ):
        return (
            "O árbitro deve marcar tiro livre indireto para a equipe "
            "adversária. O goleiro não pode tocar com as mãos, dentro "
            "da própria área, uma bola recebida diretamente de um "
            "arremesso lateral cobrado por um companheiro de equipe."
        )

    if (
        "goleiro" in texto
        and (
            "defensor" in texto
            or "companheiro" in texto
        )
        and (
            "deliberadamente com o pé" in texto
            or "deliberadamente com o pe" in texto
            or "com o pé para seu goleiro" in texto
            or "com o pe para seu goleiro" in texto
            or "passa deliberadamente a bola com o pé" in texto
            or "passa deliberadamente a bola com o pe" in texto
        )
        and (
            "segura com as mãos" in texto
            or "segura com as maos" in texto
            or "segurou com as mãos" in texto
            or "segurou com as maos" in texto
            or "pega com as mãos" in texto
            or "pega com as maos" in texto
        )
    ):
        return (
            "O árbitro deve marcar tiro livre indireto para a equipe "
            "adversária. Isso ocorre porque o goleiro não pode tocar "
            "com as mãos, dentro da própria área, uma bola recebida "
            "diretamente de um passe intencional com o pé de um "
            "companheiro de equipe."
        )

    if (
        "goleiro" in texto
        and (
            "passe intencional" in texto
            or "passe deliberado" in texto
        )
        and (
            "pegou a bola com as mãos" in texto
            or "pegou a bola com as maos" in texto
            or "usou as mãos" in texto
            or "usou as maos" in texto
        )
    ):
        return (
            "O árbitro deve marcar tiro livre indireto para a equipe "
            "adversária. O goleiro não pode tocar com as mãos, dentro "
            "da própria área, uma bola recebida diretamente de um "
            "passe intencional com o pé de companheiro de equipe."
        )

    if (
        "gol" in texto
        and (
            "próxima cobrança" in texto
            or "proxima cobranca" in texto
            or "recomeça" in texto
            or "recomeca" in texto
            or "recomeça o jogo" in texto
            or "recomeca o jogo" in texto
        )
    ):
        return (
            "Após um gol válido, a partida recomeça com um tiro de "
            "saída no círculo central, cobrado pela equipe que sofreu "
            "o gol."
        )

    if (
        "linha lateral" in texto
        and (
            "quem cobra" in texto
            or "quem faz a cobrança" in texto
            or "quem faz a cobranca" in texto
            or "reposição" in texto
            or "reposicao" in texto
        )
    ):
        return (
            "O arremesso lateral é concedido à equipe adversária "
            "do jogador que tocou por último na bola antes de ela "
            "ultrapassar completamente a linha lateral. A cobrança "
            "é feita com as mãos, no ponto em que a bola saiu."
        )

    if (
        "goleiro" in texto
        and (
            "espalmar" in texto
            or "espalmou" in texto
            or "espalmada" in texto
        )
        and (
            "para fora" in texto
            or "fora" in texto
        )
    ):
        return CONHECIMENTO_FUTEBOL["escanteio"]

    if (
        "linha de fundo" in texto
        and "goleiro" in texto
        and (
            "defender" in texto
            or "defendeu" in texto
            or "defesa" in texto
        )
    ):
        return CONHECIMENTO_FUTEBOL["escanteio"]

    if (
        "linha de fundo" in texto
        and (
            "atacante" in texto
            or "equipe atacante" in texto
        )
        and (
            "tocou por último" in texto
            or "tocou por ultimo" in texto
            or "último no atacante" in texto
            or "ultimo no atacante" in texto
        )
    ):
        return CONHECIMENTO_FUTEBOL["tiro_de_meta"]

    if (
        "linha de fundo" in texto
        and (
            "zagueiro" in texto
            or "defensor" in texto
        )
        and (
            "tocou por último" in texto
            or "tocou por ultimo" in texto
            or "último no zagueiro" in texto
            or "ultimo no zagueiro" in texto
        )
    ):
        return CONHECIMENTO_FUTEBOL["escanteio"]

    if (
        "dois amarelos" in texto
        or "dois cartões amarelos" in texto
        or "dois cartoes amarelos" in texto
        or "segundo amarelo" in texto
        or "segundo cartão amarelo" in texto
        or "segundo cartao amarelo" in texto
    ):
        return (
            "Quando um jogador recebe o segundo cartão amarelo na mesma "
            "partida, ele recebe o cartão vermelho e é expulso. "
            "Ele deve deixar o campo e não pode continuar jogando."
        )

    if "impedimento" in texto:
        return CONHECIMENTO_FUTEBOL["impedimento"]

    if "impedido" in texto or "impedida" in texto:
        return CONHECIMENTO_FUTEBOL["impedimento"]

    if "champions" in texto and "2015" in texto:
        return CONHECIMENTO_FUTEBOL["champions_2015"]

    if ("pelé" in texto or "pele" in texto or "rei do futebol" in texto 
        or "tres copas do mundo" in texto or "três copas do mundo" in texto 
        or "edson arantes do nascimento" in texto):
        return CONHECIMENTO_FUTEBOL["pele"]

    if "goleiro" in texto:
        return CONHECIMENTO_FUTEBOL["goleiro"]

    if "gol" in texto:
        return CONHECIMENTO_FUTEBOL["gol"]

    if "escanteio" in texto:
        return CONHECIMENTO_FUTEBOL["escanteio"]

    if "falta" in texto:
        return CONHECIMENTO_FUTEBOL["falta"]

    if "jogadores" in texto:
        return CONHECIMENTO_FUTEBOL["jogadores"]

    if "cartão amarelo" in texto or "cartao amarelo" in texto:
        return CONHECIMENTO_FUTEBOL["cartao_amarelo"]

    if "cartão vermelho" in texto or "cartao vermelho" in texto:
        return CONHECIMENTO_FUTEBOL["cartao_vermelho"]

    if "pênalti" in texto or "penalti" in texto:
        return CONHECIMENTO_FUTEBOL["penalti"]

    if ( 
        "linha de fundo" in texto
        and (
            "último toque" in texto
            or "ultimo toque" in texto
            or "ninguém do ataque" in texto
            or "ninguem do ataque" in texto
        )
    ):
        return CONHECIMENTO_FUTEBOL["tiro_de_meta"]

    if "tiro de meta" in texto:
        return CONHECIMENTO_FUTEBOL["tiro_de_meta"]

    if "substituição" in texto or "substituicao" in texto:
        return CONHECIMENTO_FUTEBOL["substituicao"]

    if "árbitro" in texto or "arbitro" in texto:
        return CONHECIMENTO_FUTEBOL["arbitro"]

    if "hat-trick" in texto or "hat trick" in texto or "hattrick" in texto:
        return CONHECIMENTO_FUTEBOL["hat_trick"]

    if "assistência" in texto or "assistencia" in texto:
        return CONHECIMENTO_FUTEBOL["assistencia"]

    if "voleio" in texto:
        return CONHECIMENTO_FUTEBOL["voleio"]

    if "bicicleta" in texto:
        return CONHECIMENTO_FUTEBOL["bicicleta"]

    if "drible" in texto:
        return CONHECIMENTO_FUTEBOL["drible"]

    if "chute" in texto:
        return CONHECIMENTO_FUTEBOL["chute"]

    if "finalização" in texto or "finalizacao" in texto:
        return CONHECIMENTO_FUTEBOL["finalizacao"]

    if "cabeceio" in texto:
        return CONHECIMENTO_FUTEBOL["cabeceio"]

    if "passe" in texto:
        return CONHECIMENTO_FUTEBOL["passe"]

    if "domínio" in texto or "dominio" in texto:
        return CONHECIMENTO_FUTEBOL["dominio"]

    if "condução" in texto or "conducao" in texto:
        return CONHECIMENTO_FUTEBOL["conducao"]

    if "finta" in texto:
        return CONHECIMENTO_FUTEBOL["finta"]

    if (
            "atacante recua" in texto and "criação" in texto
        ) or ("atacante recua" in texto and "criacao" in texto):
    
        return "falso_9"

    if "volante" in texto:
        return CONHECIMENTO_FUTEBOL["volante"]

    if "zagueiro" in texto:
        return CONHECIMENTO_FUTEBOL["zagueiro"]

    if "lateral" in texto:
        return CONHECIMENTO_FUTEBOL["lateral"]

    if "meia" in texto:
        return CONHECIMENTO_FUTEBOL["meia"]

    if "segundo atacante" in texto:
        return CONHECIMENTO_FUTEBOL["segundo_atacante"]

    if "atacante" in texto:
        return CONHECIMENTO_FUTEBOL["atacante"]

    if "ponta" in texto:
        return CONHECIMENTO_FUTEBOL["ponta"]

    if "centroavante" in texto:
        return CONHECIMENTO_FUTEBOL["centroavante"]
    
    return None

def identificar_intencao_tatica(pergunta):
    texto = pergunta.lower()

    conceitos_comparados = [
        "linha alta", "linha_alta",
        "pressão alta", "pressao alta", "pressao_alta",
        "bloco baixo", "bloco_baixo",
        "contra-ataque", "contra ataque",
        "transição", "transicao"
    ]

    quantidade_conceitos = sum(
        1 for conceito in conceitos_comparados
        if conceito in texto
    )

    if any(expressao in texto for expressao in [
        "qual a diferença", "qual é a diferença",
        "quais as diferenças", "compare", "comparar",
        "diferença entre", "diferenca entre"
    ]) and quantidade_conceitos >= 2:
        return None

    if "falso 9" in texto and "falso 9" in texto:
        return "falso_9"

    if "pressão alta" in texto or "pressao alta" in texto:
        return "pressao_alta"

    if "bloco baixo" in texto or "bloco_baixo" in texto:
        return "bloco_baixo"

    if "contra ataque" in texto or "contra-ataque" in texto:
        return "contra_ataque"

    if "linha alta" in texto or "linha_alta" in texto:
        return "linha_alta"

    if "transição" in texto or "transicao" in texto:
        return "transicao"

    if "posse de bola" in texto:
        return "posse_de_bola"

    if "amplitude" in texto:
        return "amplitude"

    if "compactação" in texto or "compactacao" in texto:
        return "compactacao"

    if "marcação individual" in texto or "marcacao individual" in texto:
        return "marcacao_individual"

    if "marcação por zona" in texto or "marcacao por zona" in texto:
        return "marcacao_por_zona"

    # Pressão alta
    if (
        "pressiona a saída" in texto
        or "pressionar a saída" in texto
        or "pressionando a saída" in texto
        or "pressiona a saída de bola" in texto
        or "pressionar a saída de bola" in texto
    ):
        return "pressao_alta"

    # Bloco baixo
    if (
        "mais recuado" in texto
        or "mais recuada" in texto
        or "perto da própria área" in texto
        or "perto da propria área" in texto
        or "perto da propria area" in texto
        or "jogar recuado" in texto
        or "jogar recuada" in texto
    ):
        return "bloco_baixo"

    # Linha alta
    if (
        "defesa mais adiantada" in texto
        or "defesa adiantada" in texto
        or "linha defensiva adiantada" in texto
        or "zagueiros mais à frente" in texto
        or "zagueiros mais a frente" in texto
    ):
        return "linha_alta"

        # Contra-ataque
    if (
        "recupera a bola e sai rápido" in texto
        or "recuperar a bola e sair rápido" in texto
        or "recupera a bola e parte rápido" in texto
        or "recuperar a bola e partir rápido" in texto
        or "ataca rapidamente depois de recuperar" in texto
        or "sai rapidamente para o ataque" in texto
        or "parte rápido para o ataque" in texto
    ):
        return "contra_ataque"

    # Transição

    if "perde a bola e precisa rapidamente voltar para a defesa" in texto:
        return "transicao"
    
    if (
        "mudança rápida da defesa para o ataque" in texto
        or "mudança rápida do ataque para a defesa" in texto
        or "muda da defesa para o ataque" in texto
        or "muda do ataque para a defesa" in texto
        or "perde a bola e precisa se reorganizar" in texto
        or "perde a bola e volta para defender" in texto
        or "perde a bola e precisa voltar para a defesa" in texto
        or "perde a bola e volta rapidamente para a defesa" in texto
        or "perde a bola e precisa se reorganizar defensivamente" in texto
    ):
        return "transicao"

    # Posse de bola
    if (
        "mantém a posse de bola" in texto
        or "mantem a posse de bola" in texto
        or "ficar com a bola" in texto
        or "fica com a bola" in texto
        or "controla a posse de bola" in texto
        or "troca muitos passes" in texto
    ):
        return "posse_de_bola"

    # Falso 9
    if (
        "atacante recua para participar da criação" in texto
        or "atacante recua para criar jogadas" in texto
        or "centroavante recua para criar" in texto
        or "atacante sai da área para criar" in texto
        or "centroavante recua para participar da criação" in texto
        or "centroavante recua para criar jogadas" in texto
        or "centroavante sai da área para criar" in texto
    ):
        return "falso_9"

    # Amplitude
    if (
        "jogadores ficam mais abertos" in texto
        or "jogadores mais abertos pelas laterais" in texto
        or "jogar mais aberto pelas laterais" in texto
        or "abre o campo pelas laterais" in texto
    ):
        return "amplitude"

    # Compactação
    if (
        "jogadores próximos uns dos outros" in texto
        or "jogadores mais próximos" in texto
        or "mantém os jogadores próximos" in texto
        or "mantem os jogadores proximos" in texto
        or "dificultar os ataques adversários" in texto
        or "dificultar os ataques adversarios" in texto
    ):
        return "compactacao"

    # Marcação individual
    if (
        "cada jogador marca um adversário" in texto
        or "cada jogador marca um jogador adversário" in texto
        or "marcar individualmente" in texto
        or "marcar um adversário específico" in texto
        or "marcar um jogador específico" in texto
    ):
        return "marcacao_individual"

    # Marcação por zona
    if (
        "cada jogador pode ser responsável por proteger uma determinada região" in texto
        or "cada jogador e responsavel por proteger uma determinada regiao" in texto
        or "proteger uma determinada região do campo" in texto
        or "proteger uma determinada regiao do campo" in texto
        or "cada jogador protege uma região do campo" in texto
        or "cada jogador protege uma regiao do campo" in texto
    ):
        return "marcacao_por_zona"

    if "4-3-3" in texto or "4 3 3" in texto or "433" in texto:
        return "4-3-3"

    if "4-4-2" in texto or "4 4 2" in texto or "442" in texto:
        return "4-4-2"

    if "4-2-3-1" in texto or "4 2 3 1" in texto or "4231" in texto:
        return "4-2-3-1"

    if "3-5-2" in texto or "3 5 2" in texto or "352" in texto:
        return "3-5-2"

    if "3-4-3" in texto or "3 4 3" in texto or "343" in texto:
        return "3-4-3"

    if "4-3-1-2" in texto or "4 3 1 2" in texto or "4312" in texto:
        return "4-3-1-2"

    return None

def buscar_conhecimento_tatico(pergunta):
    intencao = identificar_intencao_tatica(pergunta)

    if intencao:
        return {
            "conceito": intencao,
            "dados": CONHECIMENTO_TATICO[intencao]
        }
    
    intencao = identificar_dado_classificacao(pergunta)

    if intencao and intencao in CONHECIMENTO_TATICO:
        return {
            "conceito": intencao,
            "dados": CONHECIMENTO_TATICO[intencao]
        }

    texto = pergunta.lower()

    if "4-3-3" in texto or "433" in texto:
        return CONHECIMENTO_TATICO["4-3-3"]

    if "4-4-2" in texto or "442" in texto:
        return CONHECIMENTO_TATICO["4-4-2"]

    if "4-2-3-1" in texto or "4231" in texto:
        return CONHECIMENTO_TATICO["4-2-3-1"]

    if "3-5-2" in texto or "352" in texto:
        return CONHECIMENTO_TATICO["3-5-2"]

    if "3-4-3" in texto or "343" in texto:
        return CONHECIMENTO_TATICO["3-4-3"]

    if "4-3-1-2" in texto or "4312" in texto:
        return CONHECIMENTO_TATICO["4-3-1-2"]

    if "pressão alta" in texto or "pressao alta" in texto:
        return CONHECIMENTO_TATICO["pressao_alta"]

    if "bloco baixo" in texto:
        return CONHECIMENTO_TATICO["bloco_baixo"]

    if "linha alta" in texto:
        return CONHECIMENTO_TATICO["linha_alta"]

    if "contra-ataque" in texto or "contra ataque" in texto:
        return CONHECIMENTO_TATICO["contra_ataque"]

    if "transição" in texto or "transicao" in texto:
        return CONHECIMENTO_TATICO["transicao"]

    if "posse de bola" in texto:
        return CONHECIMENTO_TATICO["posse_de_bola"]

    if "falso 9" in texto or "falso nove" in texto:
        return CONHECIMENTO_TATICO["falso_9"]

    if "amplitude" in texto:
        return CONHECIMENTO_TATICO["amplitude"]

    if "compactação" in texto or "compactacao" in texto:
        return CONHECIMENTO_TATICO["compactacao"]

    if "marcação individual" in texto or "marcacao individual" in texto:
        return CONHECIMENTO_TATICO["marcacao_individual"]

    if "marcação por zona" in texto or "marcacao por zona" in texto:
        return CONHECIMENTO_TATICO["marcacao_por_zona"]
    
    return None



def gerar_resposta_ollama(pergunta, dados):

    intencao_estatistica = identificar_intencao_estatistica(pergunta)
    pergunta_estatistica = intencao_estatistica is not None

    # Aceita tanto o contexto em texto quanto o dicionário.
    if isinstance(dados, dict):
        contexto = dados.get("dados", dados)
        conceito = dados.get("conceito") or "Não se aplica"
    else:
        contexto = dados
        conceito = "Não se aplica"

    contexto = str(contexto)

    if pergunta_estatistica:
        prompt_sistema = """
Você é o assistente virtual do Camisa10, especializado em futebol.

Responda em português brasileiro, de forma clara, objetiva e natural.

REGRAS:
- Responda à pergunta original, sem mudar seu objetivo.
- Utilize as evidências fornecidas para responder às perguntas estatísticas.
- Não invente números, fontes, datas ou critérios de contagem.
- Associe cada número à fonte e ao contexto que realmente o sustentam.
- Diferencie totais da carreira, estatísticas de clubes, seleção,
  temporadas e competições.
- Não confunda gols oficiais com totais que incluem partidas não oficiais.
- Não considere um número confirmado apenas porque aparece no contexto.
- Se as fontes forem insuficientes, antigas ou incompatíveis,
  explique a limitação de forma objetiva.
- Em comparações, analise cada jogador separadamente.
- Só conclua quem tem mais gols quando os números forem comparáveis.
- Não substitua os jogadores solicitados por outros.
- Não acrescente estatísticas irrelevantes.
- Não apresente títulos de notícias como se fossem respostas.
"""

    else:
        prompt_sistema = """
Você é o assistente virtual do Camisa10, especializado em futebol.

Responda em português do Brasil, de forma natural, clara e objetiva.

- Responda diretamente ao que o usuário perguntou.
- Para perguntas gerais e conceituais, use seu conhecimento sobre futebol.
- Quando houver dados fornecidos pelo sistema, utilize-os como referência.
- Não invente informações apresentadas como fatos.
- Respeite o conceito de futebol solicitado e não o substitua por outro.
- Em comparações, explique todos os elementos solicitados.
- Não apresente metadados internos ou títulos de notícias como resposta.
- Se não souber algo com segurança, seja transparente.
"""

    instrucoes_por_intencao = {
        "quantidade": """
A pergunta pede a quantidade de gols de um jogador.

- Identifique o jogador e a estatística solicitada.
- Se a pergunta pedir gols oficiais, considere somente gols
  em partidas classificadas como oficiais pelas fontes.
- Se pedir gols na carreira sem especificar "oficiais",
  considere o total geral informado pelas fontes, incluindo
  partidas não oficiais quando estiverem contabilizadas.
- Não some números que já fazem parte de um total apresentado.
- Informe o critério de contagem e a fonte de cada número.
- Se houver divergências, explique os critérios encontrados.
- Não invente números nem transforme a pergunta em comparação.
""",

        "comparacao": """
Compare os jogadores mencionados usando as evidências fornecidas.

REGRAS:
1. Identifique todos os jogadores da pergunta original.
2. Procure os números explicitamente presentes nas evidências de cada jogador.
3. Não diga que faltam dados se houver números relevantes no contexto.
4. Diferencie:
   - gols por clubes;
   - gols pela seleção principal;
   - total geral da carreira.
5. Em tabelas de clubes, a linha "Total" representa o total
   indicado por aquela tabela. Não a descarte por não conter
   a expressão "gols oficiais na carreira".
6. Em tabelas da seleção, identifique separadamente os jogos
   e gols pela seleção principal.
7. Não confunda o total de gols por clubes com o total da carreira.
8. Não some categorias se houver risco de sobreposição ou se
   os critérios e períodos não forem compatíveis.
9. Informe a fonte e o contexto de cada número.
10. Se houver números de datas diferentes, informe essa limitação
    quando a data estiver disponível.
11. Se os critérios não puderem ser confirmados, apresente os
    números separados e explique o que ainda precisa ser verificado.
12. Não invente números, datas ou critérios.

FORMATO:
- Nome do jogador.
- Gols por clubes, se disponíveis.
- Gols pela seleção principal, se disponíveis.
- Total geral, somente se estiver explicitamente informado ou
  puder ser calculado sem sobreposição e com critérios compatíveis.
- Fonte de cada informação.
- Conclusão comparativa, somente quando os números forem comparáveis.

Se houver dados parciais, apresente-os. Não transforme uma
limitação sobre o total geral em uma afirmação de que nenhuma
estatística está disponível.
""",

        "divergencia": """
A pergunta procura explicar diferenças entre números estatísticos.

- Apresente cada valor e sua respectiva fonte.
- Explique os critérios de contagem somente quando documentados.
- Diferencie gols oficiais e totais gerais quando as fontes permitirem.
- Não declare um único total universalmente correto sem evidências.
- Não invente explicações ou números ausentes.
"""
    }

    if intencao_estatistica:
        prompt_sistema += (
            "\n\nINSTRUÇÕES ESPECÍFICAS PARA A INTENÇÃO "
            f"{intencao_estatistica.upper()}:\n"
            + instrucoes_por_intencao[intencao_estatistica]
        )

    resposta = ollama.chat(
        model="llama3.2:3b",
        messages=[
            {
                "role": "system",
                "content": prompt_sistema
            },
            {
                "role": "user",
                "content": f"""
Pergunta do usuário:
{pergunta}

Conceito identificado pelo sistema:
{conceito}

Dados e contexto disponíveis:
{contexto}

Instruções finais:
- Responda à pergunta original, não apenas ao número mais destacado.
- Em comparações, avalie separadamente cada jogador.
- Use somente números sustentados pelas fontes fornecidas.
- Não invente informações ausentes.
- Se não for possível comparar os dois jogadores, explique por quê.
- Escreva a resposta completa em português brasileiro.
"""
            }
        ],
        options={
            "temperature": 0.2
        }
    )

    texto_resposta = resposta["message"]["content"].strip()

    return texto_resposta

def pergunta_e_de_futebol(pergunta):
    texto = pergunta.lower()

    if identificar_tipo_jogo(pergunta) is not None:
        return True

    if identificar_dado_classificacao(pergunta) is not None:
        return True

    if any(frase in texto for frase in [
        "campanha",
        "como está a campanha",
        "como esta a campanha",
        "campanha do time"
    ]):
        return True

    palavras_futebol = [
        "impedimento",
        "impedido",
        "impedida",
        "ficar impedido",
        "ficar impedida",
        "dois amarelos",
        "dois cartões amarelos",
        "dois cartoes amarelos",
        "segundo amarelo",
        "segundo cartão amarelo",
        "segundo cartao amarelo",
        "escanteio",
        "falta",
        "gol",
        "tiro de meta",
        "linha de fundo",
        "último toque",
        "ultimo toque",
        "substituição",
        "substituicao",
        "assistência",
        "assistencia",
        "passe",
        "voleio",
        "bicicleta",
        "chute",
        "cabeceio",
        "finalização",
        "finalizacao",
        "drible",
        "finta",
        "condução",
        "conducao",
        "domínio",
        "dominio",
        "amplitude",
        "compactação", 
        "compactacao",
        "marcação por zona", 
        "marcacao por zona",
        "marcação individual", 
        "marcacao individual",
        "pressão alta", 
        "pressao alta",
        "transição",
        "transicao",
        "linha alta",
        "contra-ataque", 
        "contra ataque",
        "falso 9", 
        "falso nove",
        "transição", 
        "transicao",
        "posse de bola",
        "bloco baixo",
        "pelé",
        "pele",
        "rei do futebol",
        "bola de ouro",
        "bolas de ouro",
        "ballon d'or",
        "ballon dor",
        "champions",
        "libertadores",
        "copa do mundo",
        "campeonato",
        "classificação",
        "classificacao",
        "posição",
        "posicao",
        "cartao",
        "cartão",
        "pênalti",
        "penalti",
        "hat-trick",
        "hat trick",
        "hattrick",
        "zagueiro",
        "goleiro",
        "atacante",
        "meia",
        "lateral",
        "volante",
        "árbitro",
        "arbitro"
    ]

    if any(palavra in texto for palavra in palavras_futebol):
        return True

    frases_futebol = [
        "quantos jogadores",
        "quantos jogadores tem um time",
        "quantos jogadores tem uma equipe",
        "quantos jogadores entram em campo",
        "quantos jogadores podem jogar",
        "quantos jogadores em campo"
    ]

    if any(frase in texto for frase in frases_futebol):
        return True
    
    resposta = ollama.chat(
        model="llama3.2:3b",
        messages=[
            {
                "role": "system",
                "content": """
                Sua única função é classificar perguntas.

                Responda SOMENTE:
                SIM
                ou
                NÃO

                Responda SIM se a pergunta estiver relacionada ao futebol,
                incluindo jogadores, times, campeonatos, partidas, regras,
                história do futebol, estatísticas ou assuntos diretamente 
                relacionados ao esporte.

                Também responda SIM para as perguntas sobre:
                - próximo jogo de um time
                - último jogo de um time
                - quando um time vai jogar
                - resultado de uma partida
                - placar de uma partida
                - adversário de um time
                - data ou horário de uma partida

                Responda NÃO se a pergunta não tiver relação com futebol.
                """
            },
            {
                "role": "user",
                "content": pergunta
            }
        ]
    )

    resultado = resposta["message"]["content"].strip().upper()
    return resultado.startswith("SIM")

def buscar_dados_classificacao_time(nome_time, codigo_competicao):
    classificacao = buscar_classificacao_competicao(codigo_competicao)

    if isinstance(classificacao, dict) and "erro" in classificacao:
        return classificacao

    nome_busca = normalizar_nome_time(nome_time)

    aliases = {
        "milan": ["ac milan", "milan"],
        "ac milan": ["ac milan", "milan"],
        "barcelona": ["barcelona", "fc barcelona"],
        "real madrid": ["real madrid", "real"]
    }

    nomes_aceitos = aliases.get(nome_busca, [nome_busca])

    for time in classificacao:
        nome_api = normalizar_nome_time(time["time"])

        if nome_api in nomes_aceitos:
            return time

    return {
        "erro": f"Não encontrei {nome_time} na classificação."
    }

def identificar_competicao(pergunta, nome_time):
    texto = normalizar_nome_time(pergunta)

    palavras_competicoes = {
        "PL": [
            "premier league",
            "campeonato ingles",
            "liga inglesa"
        ],
        "PD": [
            "la liga",
            "campeonato espanhol",
            "liga espanhola",
            "primera division"
        ],
        "SA": [
            "serie a italiana",
            "campeonato italiano",
            "liga italiana"
        ],
        "BL1": [
            "bundesliga",
            "campeonato alemao",
            "liga alema"
        ],
        "FL1": [
            "ligue 1",
            "campeonato frances",
            "liga francesa"
        ],
        "BSA": [
            "brasileirao",
            "campeonato brasileiro",
            "serie a brasileira"
        ],
        "CL": [
            "champions league",
            "champions",
            "liga dos campeões"
            "liga dos campeoes"
        ],
        "CLI": [
            "libertadores",
            "copa libertadores"
        ],
        "EC": [
            "eurocopa",
            "campeonato europeu de selecoes"
        ],
        "WC": [
            "copa do mundo",
            "fifa world cup"
        ]
    }

    for codigo, nomes in palavras_competicoes.items():
        if any(nome in texto for nome in nomes):
            return codigo

    if nome_time:
        time_api = buscar_time_football_data(nome_time)

        if isinstance(time_api, dict) and "erro" in time_api:
            return None

        competicoes = time_api.get("competicoes", [])

        ligas = [
            competicao
            for competicao in competicoes
            if competicao.get("type") == "LEAGUE"
            and competicao.get("code")
        ]

        if len(ligas) == 1:
            return ligas[0]["code"]

        if len(ligas) > 1:
            return None

    return None

def nome_exibicao_competicao(codigo):
    nomes = {
        "BSA": "Brasileirão",
        "PL": "Premier League",
        "PD": "La Liga",
        "BL1": "Bundesliga",
        "CL": "Champions League",
        "SA": "Serie A"
    }

    return nomes.get(codigo, "campeonato")

def artigo_competicao(codigo):
    artigos = {
        "BSA": "no",
        "PL": "na",
        "PD": "na",
        "BL1": "na",
        "SA": "na",
        "FL1": "na"
    }

    return artigos.get(codigo, "na")
    
def identificar_tipo_jogo(pergunta):
    texto = pergunta.lower()

    if (
                " x " in texto
                or " contra " in texto
                or " vs " in texto
                or " versus " in texto
    ):
        return "confronto"

    if (
        "próximos jogos" in texto
        or "proximos jogos" in texto
        or "próximas partidas" in texto
        or "proximas partidas" in texto
    ):
        return "proximos"

    if (
        "próximo jogo" in texto
        or "proximo jogo" in texto
        or "quando joga" in texto
        or "quando vai jogar" in texto
        or "vai jogar" in texto
        or "próxima partida" in texto
        or "proxima partida" in texto
        or "vai enfrentar" in texto
        or "enfrenta" in texto
        or "próximo adversário" in texto
        or "proximo adversario" in texto
        or "quando o " in texto and " joga" in texto
    ):
        return "proximo"

    if (
        "últimos jogos" in texto
        or "ultimos jogos" in texto
        or "últimos cinco jogos" in texto
        or "ultimos cinco jogos" in texto
        or "últimos 5 jogos" in texto
        or "ultimos 5 jogos" in texto
        or "últimas partidas" in texto
        or "ultimas partidas" in texto
        or "últimas cinco partidas" in texto
        or "ultimas cinco partidas" in texto
    ):
        return "ultimos"


    if (
        "último jogo" in texto
        or "ultimo jogo" in texto
        or "última partida" in texto
        or "ultima partida" in texto
        or "quanto foi o jogo" in texto
        or "quanto foi o último" in texto
        or "quanto foi o ultimo" in texto
        or "jogou pela última vez" in texto
        or "jogou pela ultima vez" in texto
    ):
        return "ultimo"

    return None

def identificar_confronto(pergunta):
    texto = pergunta.lower()

    frases = [
        "quanto foi o",
        "quanto foi",
        "qual foi o resultado de",
        "qual foi o resultado do",
        "resultado de",
        "resultado do",
        "placar de"
    ]

    for frase in frases:
        texto = texto.replace(frase, "").strip()

    if " entre " in texto:
        partes = texto.split(" entre ", 1)

        times = partes[1].split(" e ", 1)

        if len(times) == 2:
            return (
                identificar_time(times[0].strip(" ?!.,")),
                identificar_time(times[1].strip(" ?!.,"))
            )

    separadores = [" x ", " contra ", " vs ", " versus "]

    for separador in separadores:
        if separador in texto:
            partes = texto.split(separador, 1)

            partes[0] = partes[0].strip(" ?!.,")
            partes[1] = partes[1].strip(" ?!.,")

            return (
                identificar_time(partes[0]),
                identificar_time(partes[1])
            )

    return None, None

def formatar_data_jogo(data_utc):
    data = datetime.fromisoformat(
        data_utc.replace("Z", "+00:00")
    )

    data_brasil = data.astimezone(
        ZoneInfo("America/Sao_Paulo")
    )

    if data_brasil.minute == 0:
        return data_brasil.strftime("%d/%m às %Hh")

    return data_brasil.strftime("%d/%m às %Hh%M")

def gerar_resposta_tatica(dados):
    info = dados["dados"]

    resposta = f"{info['nome']}: {info['descricao']}"

    if "caracteristicas" in info:
        resposta += f"\n\nCaracterísticas: {info['caracteristicas']}"

    if "vantagens" in info:
        resposta += f"\n\nVantagens: {info['vantagens']}"

    if "desvantagens" in info:
        resposta += f"\n\nDesvantagens: {info['desvantagens']}"

    return resposta

def normalizar_texto(texto: str) -> str:
    texto = texto.lower().strip()
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(
        caractere
        for caractere in texto
        if unicodedata.category(caractere) != "Mn"
    )
    texto = re.sub(r"\s+", " ", texto)
    return texto


def identificar_intencao_estatistica(pergunta: str) -> str | None:
    texto = normalizar_texto(pergunta)

    termos_divergencia = [
        "numeros diferentes",
        "numero diferente",
        "por que existem numeros",
        "por que a contagem",
        "qual numero esta correto",
        "qual e o numero correto",
        "divergencia nas estatisticas",
        "estatisticas diferentes",
        "por que varia a contagem",
        "por que os dados divergem",
        "qual numero de gols esta correto",
        "qual numero de gols esta certo",
        "qual contagem esta correta",
        "qual total esta correto",
        "por que ha diferenca",
        "por que os totais sao diferentes",
    ]

    termos_comparacao = [
        "quem marcou mais",
        "quem fez mais gols",
        "quem tem mais gols",
        "quem marcou mais gols",
        "quem fez mais",
        "marcou mais gols",
        "fez mais gols",
        "maior artilheiro",
        "maiores artilheiros",
        "comparar os gols",
        "comparacao de gols",
        "comparacao entre",
        "compare os gols",
        "compare os jogadores",
        "comparar jogadores",
        "comparar a quantidade de gols",
        "quem e o maior goleador",
        "quem tem mais gols oficiais",
        "qual dos jogadores marcou mais",
        "qual jogador marcou mais",
        "qual jogador fez mais gols",
        "qual deles tem mais gols",
        "sao os maiores artilheiros",
    ]

    termos_quantidade = [
        "quantos gols",
        "quantos golos",
        "quantos gol marcou",
        "quantos gols marcou",
        "quantos gols fez",
        "quantos gols tem",
        "numero de gols",
        "total de gols",
        "gols na carreira",
        "gols pela selecao",
        "gols pelo clube",
        "marcou ao todo",
        "marcou na carreira",
        "quantidade de gols",
        "total marcado",
        "quantos gols oficiais",
        "quantos gols na carreira",
        "total de gols oficiais",
    ]

    if any(termo in texto for termo in termos_divergencia):
        return "divergencia"

    if any(termo in texto for termo in termos_comparacao):
        return "comparacao"

    if any(termo in texto for termo in termos_quantidade):
        return "quantidade"

    return None

def extrair_totais_gols_comparacao(resultados: list) -> dict:
    """
    Organiza fontes e extrai totais de gols por clubes
    quando a tabela identifica explicitamente Jogos e Gols.
    """
    dados = {}

    for resultado in resultados:
        jogador = (
            resultado.get("jogador_pesquisado") or ""
        ).strip()
        titulo = resultado.get("titulo", "")
        url = resultado.get("url", "")
        conteudo = resultado.get("conteudo", "")

        if not jogador or not conteudo:
            continue

        chave = jogador.casefold()

        if chave not in dados:
            dados[chave] = {
                "jogador": jogador,
                "fontes": [],
                "totais_clubes": [],
            }

        dados[chave]["fontes"].append({
            "titulo": titulo,
            "url": url,
            "conteudo": conteudo,
        })

        # Localiza especificamente a tabela de clubes profissionais.
        cabecalho = re.search(
            r"Período\s*\|\s*Clube\s*\|\s*Jogos\s*\|\s*Gol\(o\)s",
            conteudo,
            re.IGNORECASE,
        )

        if not cabecalho:
            continue

        # Recorta a tabela antes da seção seguinte.
        inicio = cabecalho.start()
        fim = conteudo.find("| Seleção", cabecalho.end())

        if fim == -1:
            fim = len(conteudo)

        tabela_clubes = conteudo[inicio:fim]

        # Extrai somente o total dentro da tabela de clubes.
        total = re.search(
            r"\|\s*Total\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|",
            tabela_clubes,
            re.IGNORECASE,
        )

        if total:
            jogos = int(total.group(1))
            gols = int(total.group(2))

            dados[chave]["totais_clubes"].append({
                "jogos": jogos,
                "gols": gols,
                "titulo": titulo,
                "url": url,
            })

    return dados

@app.post("/api/chat")
async def conversar(pergunta: Pergunta):
    texto_pergunta = pergunta.pergunta.lower()

    termos_comparacao = [
        "qual a diferença",
        "qual é a diferença",
        "diferença entre",
        "diferenca entre",
        "compare",
        "comparar"
    ]

    if any(termo in texto_pergunta for termo in termos_comparacao):
        conceitos = {
            "linha alta": "linha_alta",
            "linha_alta": "linha_alta",
            "pressão alta": "pressao_alta",
            "pressao alta": "pressao_alta",
            "pressao_alta": "pressao_alta",
            "bloco baixo": "bloco_baixo",
            "bloco_baixo": "bloco_baixo",
            "contra-ataque": "contra_ataque",
            "contra ataque": "contra_ataque",
            "transição": "transicao",
            "transicao": "transicao"
        }

        encontrados = []
        for termo, conceito in conceitos.items():
            if termo in texto_pergunta and conceito not in encontrados:
                encontrados.append(conceito)

        if len(encontrados) >= 2:
            partes = []

            for conceito in encontrados:
                info = CONHECIMENTO_TATICO[conceito]
                partes.append(
                    f"{info['nome']}: {info['descricao']}"
                )

            return {
                "response": "\n\n".join(partes)
            }

    intencao_tatica = identificar_intencao_tatica(pergunta.pergunta)

    if intencao_tatica:
        conhecimento_tatico = {
            "conceito": intencao_tatica,
            "dados": CONHECIMENTO_TATICO[intencao_tatica]
        }

        resposta = gerar_resposta_tatica(conhecimento_tatico)

        return {
            "response": resposta
        }

    if not pergunta_e_de_futebol(pergunta.pergunta):
        return {
            "response": "Posso ajudar apenas com assuntos relacionados ao futebol."
        }
    
    resposta_comparacao = comparar_conceitos_futebol(pergunta.pergunta)

    if resposta_comparacao:
        return {
            "response": resposta_comparacao
        }

    conhecimento = buscar_conhecimento(pergunta.pergunta)

    conhecimento_tatico = buscar_conhecimento_tatico(pergunta.pergunta)

    if conhecimento_tatico is not None:
        resposta = gerar_resposta_ollama(
            pergunta.pergunta,
            conhecimento_tatico
        )

        return {
            "response": resposta
        }

    tipo_jogo = identificar_tipo_jogo(pergunta.pergunta)
    
    texto = pergunta.pergunta.lower()

    if tipo_jogo == "proximo":

        time = identificar_time(pergunta.pergunta)
        id_time = obter_id_time(time)
        nome_time = nome_exibicao_time(time)

        jogo = buscar_proximo_jogo(id_time)

        if isinstance(jogo, dict) and "erro" in jogo:
            return {"response": f"Não consegui encontrar o próximo jogo: {jogo['erro']}"}

        if normalizar_nome_time(time) in normalizar_nome_time(jogo["mandante"]):
            adversario = nome_exibicao_api(jogo["visitante"]) 
        else:
            adversario = nome_exibicao_api(jogo["mandante"]) 

        data_jogo = formatar_data_jogo(jogo["data"])

        if "quando" in texto or "data" in texto:
            return {
                "response": f"O próximo jogo do {nome_time} será no dia {data_jogo}, contra o {adversario}."
            }

        if "competição" in texto or "competicao" in texto:
            return {
                "response": f"O próximo jogo do {nome_time} será pelo {jogo['competicao']}."
            }

        if "casa" in texto or "fora" in texto:
            if normalizar_nome_time(time) in normalizar_nome_time(jogo["mandante"]):
                local = "em casa"
            else:
                local = "fora de casa"

            return {
                "response": f"O {nome_time} jogará {local} no próximo jogo, contra o {adversario}."
            }

        resposta = (
            "O próximo jogo do "
            + nome_time
            + " será contra o "
            + adversario
            + ", no dia "
            + data_jogo
            + "."
        )

        return {
            "response": resposta
        }

    if tipo_jogo == "proximos":
        time = identificar_time(pergunta.pergunta)

        if time is None:
            return {
                "response": "Não consegui identificar o time na pergunta."
            }

        id_time = obter_id_time(time)
        nome_time = nome_exibicao_time(time)

        if id_time is None:
            return {
                "response": f"Não consegui encontrar informações sobre o time {nome_time}."
            }

        jogos = buscar_proximos_jogos(id_time, 5)

        if isinstance(jogos, dict) and "erro" in jogos:
            return {
                "response": f"Não consegui encontrar os próximos jogos: {jogos['erro']}"
            }

        linhas = []

        for jogo in jogos:
            mandante = nome_exibicao_api(jogo["mandante"])
            visitante = nome_exibicao_api(jogo["visitante"])
            data_jogo = formatar_data_jogo(jogo["data"])

            linhas.append(
                f"{data_jogo}: {mandante} x {visitante}"
            )

        resposta = (
            f"Estes são os próximos {len(jogos)} jogos do {nome_time}:\n\n"
            + "\n".join(linhas)
        )

        return {
            "response": resposta
        }

    if tipo_jogo == "ultimos":
        time = identificar_time(pergunta.pergunta)

        if time is None:
            return {
                "response": "Não consegui identificar o time na pergunta."
            }

        id_time = obter_id_time(time)
        nome_time = nome_exibicao_time(time)

        if id_time is None:
            return {
                "response": f"Não consegui encontrar informações sobre o time {nome_time}."
            }

        jogos = buscar_ultimos_jogos(id_time, 5)

        if isinstance(jogos, dict) and "erro" in jogos:
            return {
                "response": f"Não consegui encontrar os últimos jogos: {jogos['erro']}"
            }

        if not jogos:
            return {
                "response": f"Não encontrei jogos finalizados recentemente do {nome_time}."
            }

        linhas = []

        for jogo in jogos:
            time_casa = normalizar_nome_time(jogo["mandante"])
            time_consultado = normalizar_nome_time(time)

            if time_casa == time_consultado:
                adversario = nome_exibicao_api(jogo["visitante"]) 
                gols_time = jogo["gols_mandante"]
                gols_adversario = jogo["gols_visitante"]
            else:
                adversario = nome_exibicao_api(jogo["mandante"]) 
                gols_time = jogo["gols_visitante"]
                gols_adversario = jogo["gols_mandante"]

            data_jogo = formatar_data_jogo(jogo["data"])

            linhas.append(
                f"{data_jogo}: {nome_time} {gols_time} x {gols_adversario} {adversario}"
            )

        resposta = (
            f"Estes são os últimos {len(jogos)} jogos finalizados "
            f"do {nome_time}:\n\n"
            + "\n".join(linhas)
        )

        return {
            "response": resposta
        }

    if tipo_jogo == "ultimo":

        time = identificar_time(pergunta.pergunta)
        id_time = obter_id_time(time)
        nome_time = nome_exibicao_time(time)

        jogo = buscar_ultimo_jogo(id_time)

        if isinstance(jogo, dict) and "erro" in jogo:
            return {
                "response": f"Não consegui encontrar o último jogo: {jogo['erro']}"
            }

        if normalizar_nome_time(time) in normalizar_nome_time(jogo["mandante"]):

            adversario = nome_exibicao_api(jogo["visitante"]) 
            gols_time = jogo["gols_mandante"]
            gols_adversario = jogo["gols_visitante"]

        else:
            adversario = nome_exibicao_api(jogo["mandante"]) 
            gols_time = jogo["gols_visitante"]
            gols_adversario = jogo["gols_mandante"]

        if "casa" in texto or "fora" in texto:
            if normalizar_nome_time(time) in normalizar_nome_time(jogo["mandante"]):
                local = "em casa"
            else:
                local = "fora de casa"

            return {
                "response": f"O {nome_time} jogou {local} no último jogo, contra o {adversario}."
            }

        if "placar" in texto or "resultado" in texto:
            return {
                "response": f"O placar do último jogo do {nome_time} foi {gols_time} a {gols_adversario} contra o {adversario}."
            }

        if "competição" in texto or "competicao" in texto:
            return {
                "response": f"O último jogo do {nome_time} foi pelo {jogo['competicao']}."
            }

        if "quando" in texto or "data" in texto:
            data_jogo = formatar_data_jogo(jogo["data"])
            return {
                "response": f"O último jogo do {nome_time} foi no dia {data_jogo}, contra o {adversario}."
            }

        resposta = (
            "O último jogo do "
            + nome_time
            + " foi contra o "
            + adversario
            + " e terminou "
            + str(gols_time)
            + " a "
            + str(gols_adversario)
            + "."
        )

        if (
            jogo["penaltis_mandante"] is not None
            and jogo["penaltis_visitante"] is not None
        ):

            if jogo["penaltis_mandante"] > jogo["penaltis_visitante"]:
                vencedor_penaltis = nome_exibicao_api(jogo["mandante"]) 
                placar_penaltis = (
                    str(jogo["penaltis_mandante"])
                    + " a "
                    + str(jogo["penaltis_visitante"])
                )
            else:
                vencedor_penaltis = nome_exibicao_api(jogo["visitante"]) 
                placar_penaltis = (
                    str(jogo["penaltis_visitante"])
                    +
                    " a "
                    + str(jogo["penaltis_mandante"])
                )

            resposta += (
                " Nos pênaltis, "
                + vencedor_penaltis
                + " venceu por "
                + placar_penaltis
                + "."
            )

        return {
            "response": resposta
        }

    if tipo_jogo == "confronto":

        time1, time2 = identificar_confronto(pergunta.pergunta)

        confronto = buscar_jogo_contra_adversario(time1, time2)

        if confronto is None:
            return {
                "response": (
                    f"Não encontrei informações sobre o confronto entre "
                    f"{time1} e {time2} nas competições disponíveis."
                )
            }

        if isinstance(confronto, dict) and "erro" in confronto:
            print("Erro da API:", confronto["erro"])
            return {
                "response": (
                    "Não consegui consultar esse confronto com a fonte "
                    "de dados disponível no momento."
                )
            }

        ultimo_jogo = confronto["ultimo_jogo"]
        proximo_jogo = confronto["proximo_jogo"]

        pergunta_normalizada = normalizar_nome_time(pergunta.pergunta)

        palavras_proximo = [
            "quando sera",
            "quando vai ser",
            "quando será o proximo",
            "proximo confronto",
            "proximo jogo",
            "proximo duelo",
            "quando jogam",
            "quando vao jogar"
        ]

        palavras_temporada = [
            "nesta temporada",
            "nessa temporada",
            "na temporada atual",
            "esta temporada",
            "ja teve",
            "ja jogaram",
            "se enfrentaram nesta temporada",
            "se enfrentaram nessa temporada"
        ]

        palavras_ultimo = [
            "ultimo confronto",
            "ultimo jogo",
            "ultimo duelo",
            "quanto foi",
            "qual foi o resultado",
            "qual foi o placar",
            "quem ganhou",
            "quem venceu",
            "quem levou a melhor",
            "quem saiu vitorioso",
            "resultado do confronto",
            "resultado do jogo"
        ]

        quer_proximo = any(
            termo in pergunta_normalizada
            for termo in palavras_proximo
        )

        quer_temporada = any(
            termo in pergunta_normalizada
            for termo in palavras_temporada
        )

        quer_ultimo = any(
            termo in pergunta_normalizada
            for termo in palavras_ultimo
        )

        if quer_proximo:
            if proximo_jogo is None:
                return {
                    "response": (
                        f"Não encontrei um próximo confronto agendado "
                        f"entre {time1} e {time2} nas competições disponíveis."
                    )
                }

            fuso_brasilia = timezone(timedelta(hours=-3))

            data_jogo = datetime.fromisoformat(
                proximo_jogo["data"].replace("Z", "+00:00")
            )

            data_local = data_jogo.astimezone(fuso_brasilia)

            data_formatada = data_local.strftime("%d/%m às %Hh%M")

            mandante = nome_time_portugues(proximo_jogo["mandante"])
            visitante = nome_time_portugues(proximo_jogo["visitante"])

            return {
                "response": (
                    f"O próximo confronto entre {mandante} "
                    f"e {visitante} está previsto para {data_formatada}."
                )
            }

        if quer_temporada:
            if ultimo_jogo is None:
                return {
                    "response": (
                        f"Não encontrei um confronto finalizado entre "
                        f"{time1} e {time2} nesta temporada nas competições consultadas."
                    )
                }

            return {
                "response": (
                    f"Encontrei um confronto finalizado entre {time1} e {time2}, "
                    f"mas ainda preciso confirmar se ele pertence à temporada atual."
                )
            }

        if ultimo_jogo is None:
            return {
                "response": (
                    f"Não encontrei um confronto finalizado entre "
                    f"{time1} e {time2} nas competições disponíveis."
                )
            }

        mandante = nome_time_portugues(ultimo_jogo["mandante"])
        visitante = nome_time_portugues(ultimo_jogo["visitante"])

        gols_mandante = ultimo_jogo["gols_mandante"]
        gols_visitante = ultimo_jogo["gols_visitante"]

        if gols_mandante is None or gols_visitante is None:
            return {
                "response": (
                    "Encontrei a partida, mas não consegui obter o placar final do jogo. "
                )
            }

        if gols_mandante > gols_visitante:
            resposta = (
                f"{mandante} venceu {visitante} por "
                f"{gols_mandante} a {gols_visitante}."
            )

        elif gols_mandante < gols_visitante:
            resposta = (
                f"{visitante} venceu {mandante} por "
                f"{gols_visitante} a {gols_mandante}."
            )

        else:
            resposta = (
                f"{mandante} e {visitante} empataram por "
                f"{gols_mandante} a {gols_visitante}."
            )

        if (ultimo_jogo["penaltis_mandante"] is not None and ultimo_jogo["penaltis_visitante"] is not None):
            pen_mandante = ultimo_jogo["penaltis_mandante"]
            pen_visitante = ultimo_jogo["penaltis_visitante"]

            if pen_mandante > pen_visitante:
                resposta += (
                    f" Nos pênaltis, {mandante} venceu por "
                    f"{pen_mandante} a {pen_visitante}."
                )

            elif pen_mandante < pen_visitante:
                resposta += (
                    f" Nos pênaltis, {visitante} venceu por "
                    f"{pen_visitante} a {pen_mandante}."
                )
        
        return {
            "response": resposta
        }

    intencao_estatistica = identificar_intencao_estatistica(
        pergunta.pergunta
    )

    print("PERGUNTA:", pergunta.pergunta)
    print("INTENÇÃO:", intencao_estatistica)

    eh_pergunta_estatistica = intencao_estatistica in {
        "quantidade",
        "comparacao",
        "divergencia",
    }
        
    if conhecimento is not None and not eh_pergunta_estatistica:
        return {
            "response": conhecimento.strip()
        }

    conhecimento_historico = buscar_conhecimento_historico(
        pergunta.pergunta
    )

    if conhecimento_historico is not None and not eh_pergunta_estatistica:
        return {
            "response": conhecimento_historico["resposta"]
        }

    resultados_pesquisa = await pesquisar_na_web(pergunta.pergunta)

    dados_comparacao = extrair_totais_gols_comparacao(
        resultados_pesquisa
    )

    print("\n=== TOTAIS EXTRAÍDOS ===")
    print(dados_comparacao)
    print("=== FIM DOS TOTAIS ===\n")

    print("RESULTADOS DA WEB:", len(resultados_pesquisa))

    if resultados_pesquisa:
        contexto_web = formatar_resultados_pesquisa(
            resultados_pesquisa,
            pergunta.pergunta
        )

        print("\n=== EVIDÊNCIAS ORGANIZADAS ===")
        print(contexto_web)
        print("=== FIM DAS EVIDÊNCIAS ===\n")

        intencao_estatistica = identificar_intencao_estatistica(
            pergunta.pergunta
        )

        print("PERGUNTA:", pergunta.pergunta)
        print("INTENÇÃO:", intencao_estatistica)

        instrucoes_estatisticas = {
            "quantidade": """
        A pergunta pede a quantidade de gols de um jogador.

        - Identifique exatamente o jogador perguntado.
        - Responda diretamente sobre esse jogador.
        - Não apresente um número como definitivo se as fontes
          mostrarem critérios de contagem diferentes.
        - Informe o número e a fonte que o atribui ao jogador.
        - Esclareça se a contagem inclui amistosos ou jogos não oficiais,
          somente quando isso estiver documentado nas fontes.
        - Se houver números divergentes, cite os principais valores
          encontrados e explique brevemente por que variam,
          quando as fontes permitirem essa conclusão.
        - Não misture gols por clube, pela seleção e na carreira.
        - Não invente números ou critérios.
        - Se os dados não permitirem identificar um total confiável,
          explique essa limitação.
        """,
            
            "comparacao": """
        A pergunta solicita comparar a quantidade de gols oficiais na carreira
        dos jogadores mencionados.

        Siga obrigatoriamente estas etapas:

        1. Identifique todos os jogadores mencionados na pergunta original.
        2. Examine separadamente as fontes de cada jogador nos dados da pesquisa.
        3. Para cada jogador, procure um total explícito de gols oficiais
           na carreira e identifique o período a que esse total se refere.
        4. Verifique se os totais incluem clubes e seleção principal e se
           usam critérios de contagem equivalentes.
        5. Não confunda o total de gols de um jogador com uma marca isolada,
           como 700, 900 ou 1.000 gols, sem confirmar o que ela representa.
        6. Não use números de gols por um único clube como total da carreira.
        7. Não considere a data da consulta como prova de que um número
           foi atualizado nessa data.
        8. Não invente valores nem deduza totais que não estejam sustentados
           pelas fontes.
        9. Se houver dados comparáveis, apresente os dois números,
           as fontes e as respectivas datas disponíveis. Só então responda
           quem marcou mais.
        10. Se houver dados confiáveis para apenas um jogador, informe
            o número encontrado para ele e explique qual dado falta
            para concluir a comparação.

        Formato da resposta:
        - Primeiro jogador citado: total encontrado, critério, data e fonte,
          se disponíveis.
        - Segundo jogador citado: total encontrado, critério, data e fonte,
          se disponíveis.
        - Conclusão: comparação direta ou explicação objetiva da limitação.

        Não responda apenas com um número isolado.
        Não declare a comparação impossível somente porque existem
        critérios históricos diferentes.
        RESTRIÇÕES DE ESCOPO:

        - Compare exclusivamente os jogadores citados na pergunta original.
        - Não mencione outros jogadores, nem mesmo como exemplos ou contexto.
        - Não acrescente estatísticas de clubes, seleções, títulos ou competições
          que não sejam necessárias para responder à pergunta.
        - A resposta deve conter no máximo três partes:
          1. O total encontrado para cada jogador solicitado.
          2. A fonte que sustenta cada total e o critério de contagem.
          3. Uma conclusão direta, somente se os dados forem comparáveis.
        - Se não houver evidência suficiente para um dos totais, informe
          essa limitação em vez de preencher a lacuna com outro jogador
          ou com números não confirmados.
        """,

            "divergencia": """
    A pergunta solicita uma explicação sobre diferenças estatísticas.
    Apresente os números e atribua cada um à respectiva fonte.
    Explique os critérios de contagem apenas quando as fontes
    sustentarem essa explicação.
    Não declare um único total universalmente correto sem evidências.
    """
        }

        if intencao_estatistica == "comparacao":
            contexto_web = f"""
        Você é o assistente Camisa10, especializado em futebol.

        Responda à pergunta utilizando as evidências fornecidas.
        Analise cada jogador separadamente antes de comparar os números.

        REGRAS:
        1. Identifique os dois jogadores citados na pergunta original.
        2. Identifique exatamente a estatística solicitada.
        3. Se a pergunta mencionar gols oficiais, não use totais que
           incluam amistosos ou partidas não oficiais.
        4. Considere clubes e seleção principal somente quando as fontes
           permitirem identificar esses totais de maneira consistente.
        5. Não confunda estatísticas de uma temporada, de uma competição
           ou de um único clube com o total da carreira.
        6. Não misture números calculados com critérios diferentes.
        7. Não invente números nem complete informações ausentes por suposição.
        8. Se as fontes divergirem, explique brevemente a diferença e
           identifique as fontes.
        9. Só declare quem tem mais gols se houver dados comparáveis
           para os dois jogadores.
        10. Se houver evidência para apenas um jogador, apresente o dado
            encontrado e explique objetivamente o que falta para comparar.
        11. Não mencione outros jogadores além dos dois solicitados.
        12. Responda em português brasileiro, de forma objetiva.
        
        13. Utilize somente informações diretamente relacionadas à
            estatística solicitada na pergunta.
        14. Não transforme dados de tabelas diferentes em uma única
            tabela comparativa, a menos que os critérios sejam iguais.
        15. Não apresente jogos, gols, assistências, temporadas,
            estreias, prêmios ou duração de carreira se esses dados
            não forem necessários para responder à pergunta.
        16. Antes de apresentar um número, identifique a fonte,
            o período e o escopo estatístico a que ele se refere.
        17. Não atribua um número a um jogador se a evidência não
            deixar claro que aquele número pertence a ele.
        18. Se as fontes apresentarem somente estatísticas de temporadas
            ou competições específicas, não as apresente como totais
            da carreira.
        19. Se não houver dois totais comparáveis de gols oficiais,
            não declare qual jogador marcou mais. Explique brevemente
            qual informação está faltando.
        20. Nunca preencha lacunas com suposições, mesmo que isso
            produza uma resposta mais completa.
        21. Responda somente à pergunta feita. Para uma comparação de
            gols, limite a resposta aos gols, aos critérios de contagem,
            às fontes e à conclusão.
        22. Um número pode aparecer em uma fonte sem representar o total
            solicitado. Verifique o contexto imediato antes de utilizá-lo.
        23. Não apresente gols marcados sob o comando de um treinador,
            em uma temporada ou em uma competição como total da carreira.
        24. Não some gols por clubes e pela seleção se os períodos de
            atualização forem diferentes ou se houver risco de sobreposição.
        25. Não trate a quantidade de jogos como evidência da quantidade
            de gols oficiais.
        26. Se os trechos não confirmarem explicitamente dois totais
            comparáveis de gols oficiais, não apresente números parciais
            como se fossem esses totais.
        27. Nesse caso, informe que as fontes encontradas não permitem
            concluir a comparação e identifique quais dados faltam.



        PERGUNTA:
        {pergunta.pergunta}

        EVIDÊNCIAS ORGANIZADAS:
        {contexto_web}

        """

        elif intencao_estatistica in instrucoes_estatisticas:
            contexto_web = f"""
        PERGUNTA:
        {pergunta.pergunta}

        INSTRUÇÕES:
        {instrucoes_estatisticas[intencao_estatistica]}

        DADOS DA PESQUISA:
        {contexto_web}
        """
            
        resposta = gerar_resposta_ollama(
            pergunta.pergunta,
            contexto_web
        )

    if intencao_estatistica == "comparacao":
        pergunta_normalizada = pergunta.pergunta.lower()
        
        fontes = "\n\nFontes consultadas:\n" + "\n".join(
            f"- [{item.get('jogador_pesquisado') or 'Geral'}]"
            f"{item['titulo']}: {item['url']}"
            for item in resultados_pesquisa
            if item.get("url")
        )

        return {
            "response": resposta + fontes
        }
    
    time = identificar_time(pergunta.pergunta)

    if time is None:
        resposta = gerar_resposta_ollama(pergunta.pergunta, 
                                         "Nenhum dado específico foi encontrado para essa pergunta.")
        return {
            "response": resposta
        }

    #time_api = buscar_time(time)

    #if "erro" in time_api:
    #    return {
    #        "response": "Desculpe, não consegui encontrar esse time."
    #    }

    if time is not None:

        codigo_competicao = identificar_competicao(
            pergunta.pergunta,
            time
        )

        if codigo_competicao is not None:
            classificacao = buscar_classificacao_competicao(
                codigo_competicao
            )

            if isinstance(classificacao, dict) and "erro" in classificacao:
                return {
                    "response": "Não consegui buscar a classificação da competição no momento."
                }

            nome_busca = normalizar_nome_time(time)

            dados = None

            for item in classificacao:
                nome_classificacao = normalizar_nome_time(item["time"])

                if nome_busca == nome_classificacao or nome_busca in nome_classificacao or nome_classificacao in nome_busca:
                    dados = item
                    break

            if dados is None:
                return {
                    "response": f"Não encontrei o {nome_exibicao_time(time)} na classificação atual."
                }

        else: 
            return {
                "response": (
                    f"Não consegui identificar a competição do "
                    f"{nome_exibicao_time(time)}. "
                    "Informe também o campeonato, como Brasileirão, "
                    "Premier League ou La Liga."
                )
            }
            
    texto = pergunta.pergunta.lower()

    if (
    "campanha" in texto
    or "como foi" in texto
    or "como ficou" in texto
    or "qual foi a campanha" in texto
    or "me fale sobre a campanha" in texto):

        campeonato = nome_exibicao_competicao(codigo_competicao)
        
        return {
            "response": (
                f"O {dados['time']} está atualmente na "
                f"{dados['posicao']}ª posição {artigo_competicao(codigo_competicao)} {campeonato}, com {dados['pontos']} pontos "
                f"em {dados['jogos']} jogos. Até o momento, foram {dados['vitorias']} vitórias, "
                f"{dados['empates']} empates e {dados['derrotas']} derrotas."
            )
        }

    dado = identificar_dado_classificacao(pergunta.pergunta)

    if dado is not None:

        campeonato = nome_exibicao_competicao(codigo_competicao)

        respostas = {
            "pontos": f"O {dados['time']} fez {dados['pontos']} pontos {artigo_competicao(codigo_competicao)} {campeonato}.",
            "posicao": f"O {dados['time']} está atualmente na {dados['posicao']}ª posição {artigo_competicao(codigo_competicao)} {campeonato}.",
            "jogos": f"O {dados['time']} jogou {dados['jogos']} partidas {artigo_competicao(codigo_competicao)} {campeonato}.",
            "vitorias": f"O {dados['time']} venceu {dados['vitorias']} jogos {artigo_competicao(codigo_competicao)} {campeonato}.",
            "empates": f"O {dados['time']} empatou {dados['empates']} jogos {artigo_competicao(codigo_competicao)} {campeonato}.",
            "derrotas": f"O {dados['time']} perdeu {dados['derrotas']} jogos {artigo_competicao(codigo_competicao)} {campeonato}."
        }


        return {
            "response": respostas[dado]
        }
    
    resposta = gerar_resposta_ollama(pergunta.pergunta, dados)

    return {
        "response": resposta
    }