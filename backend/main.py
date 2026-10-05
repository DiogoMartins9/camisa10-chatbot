from time import time
from backend.knowledge.tactical_knowledge import CONHECIMENTO_TATICO
from fastapi import FastAPI
from pydantic import BaseModel
import ollama
from backend.services.football_api import (buscar_time, buscar_proximo_jogo, buscar_ultimo_jogo, normalizar_nome_time, buscar_jogo_contra_adversario,buscar_jogos_time, FOOTBALL_DATA_TOKEN, API_KEY, nome_time_portugues, buscar_classificacao_competicao)
from backend.knowledge.football_knowledge import CONHECIMENTO_FUTEBOL
import unicodedata
from datetime import datetime
from zoneinfo import ZoneInfo
import requests

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

        if texto.strip() == nome_api:
            return time["name"]

        if texto.strip() == nome_curto_api:
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
    "sevilla": 559
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

    if "posicao" in texto or "posição" in texto or "lugar" in texto:
        return "posicao"

    if "ponto" in texto or "pontos" in texto:
        return "pontos"

    if "vitoria" in texto or "vitória" in texto or "venceu" in texto:
        return "vitorias"

    if "empate" in texto or "empatou" in texto:
        return "empates"
    
    if "derrota" in texto or "perdeu" in texto:
        return "derrotas"

    if "jogo" in texto or "partida" in texto:
        return "jogos"

    return None

def buscar_conhecimento(pergunta):

    texto = pergunta.lower()

    if "impedimento" in texto:
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

    resposta = ollama.chat(
        model="llama3.2:3b",
        messages=[
            {
                "role": "system",
                "content": """
                Você é o assistente virtual oficial do Camisa10, especializado em futebol.

                Sua função é responder perguntas dos usuários sobre futebol de forma
                natural, clara e objetiva.

                Você pode responder perguntas gerais e conceituais sobre futebol usando
                seu próprio conhecimento, como regras, posições, fundamentos, competições,
                história, termos e conceitos do esporte.

                Quando receber dados fornecidos pelo sistema, esses dados são a fonte
                de verdade e devem ser utilizados na resposta.

                IMPORTANTE:
                - Não omita informações importantes presentes nos dados fornecidos.
                - Não invente informações que não estejam presentes nos dados.
                - Não faça avaliações, julgamentos ou opiniões sobre o desempenho de times ou jogadores.
                - Não use termos como "bom", "ruim", "razoável", "decente", "fraco", "forte",
                "intermediário" ou semelhantes para avaliar uma campanha
                - Apenas apresente e organize os dados fornecidos de forma natural e objetiva.
                - Para perguntas sobre regras, história ou fatos específicos, responda 
                principalmente com base no conhecimento fornecido pelo sistema.
                - Você pode reformular o texto para deixar mais natural, mas não adicione informações
                que não estejam nos dados fornecidos e não altere o significado deles.
                - Quando os dados fornecidos apresentarem um conceito tático específico,
                mantenha exatamente esse conceito na resposta.
                - Não substitua um conceito tático por outro conceito semelhante.
                - Se os dados forem sobre "linha alta", explique linha alta e não pressão alta.
                - Se os dados forem sobre "pressão alta", explique pressão alta e não linha alta.
                - Se os dados forem sobre "bloco baixo", explique bloco baixo e não contra-ataque.
                - Preserve o significado do conceito tático mesmo quando a pergunta estiver escrita
                de forma diferente.
                - Nunca invente números, resultados, classificações ou estatísticas.
                - Nunca altere os dados fornecidos pelo sistema.
                - Para perguntas conceituais sobre futebol, responda normalmente usando
                  seu conhecimento.
                - Não diga que precisa consultar um "banco de dados do Camisa10".
                - Não diga que não encontrou a informação no Camisa10.
                - Se realmente não souber uma informação, seja transparente.
                - Responda sempre em português do Brasil.
                - Seja amigável e objetivo.
                """
            },
            {
                "role": "user",
                "content": f"""
                Pergunta do usuário: {pergunta}

                Conceito identificado pelo sistema: {
                    dados.get("conceito") if isinstance(dados, dict) else "nenhum conceito específico"
                    }

                Dados fornecidos: {
                    dados.get("dados") if isinstance(dados, dict) else dados
                    }

                Responda à pergunta utilizando os dados fornecidos.

                IMPORTANTE:
                Se houver um conceito identificado pelo sistema, ele é a classificação correta da pergunta.
                Explique especificamente esse conceito e não o substitua por outro conceito de futebol.
                """
            }
        ]
    )

    return resposta["message"]["content"]

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
        "escanteio",
        "falta",
        "gol",
        "tiro de meta",
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

def identificar_tipo_jogo(pergunta):
    texto = pergunta.lower()

    if (
        "próximo jogo" in texto
        or "proximo jogo" in texto
        or "quando joga" in texto
        or "quando vai jogar" in texto
        or "vai jogar" in texto
        or "próxima partida" in texto
        or "proxima partida" in texto
        or "próximo adversário" in texto
        or "proximo adversario" in texto
        or "quando o " in texto and " joga" in texto
    ):
        return "proximo"

    if (
            " x " in texto
            or " contra " in texto
            or " entre " in texto
            or " vs " in texto
            or " versus " in texto
    ):
        return "confronto"

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

    return resposta

@app.post("/api/chat")
def conversar(pergunta: Pergunta):
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

        jogo = buscar_jogo_contra_adversario(
            time1,
            time2
        )

        if isinstance(jogo, dict) and "erro" in jogo:
            print("Erro da API:", jogo["erro"])

            return {
                "response": "Não consegui consultar esse confronto com a fonte de dados disponível no momento."
            }

        mandante = nome_time_portugues(jogo["mandante"])
        visitante = nome_time_portugues(jogo["visitante"])

        nome_time1 = mandante
        nome_time2 = visitante

        if (
            jogo["penaltis_mandante"] is not None
            and jogo["penaltis_visitante"] is not None
        ):
            gols_mandante = 0
            gols_visitante = 0
        else:
            gols_mandante = jogo["gols_mandante"]
            gols_visitante = jogo["gols_visitante"]

        if jogo["gols_mandante"] > jogo["gols_visitante"]:

            resposta = (
                nome_time1
                + " venceu o "
                + nome_time2
                + " por "
                + str(jogo["gols_mandante"])
                + " a "
                + str(jogo["gols_visitante"])
                + "."
            )

        elif jogo["gols_visitante"] > jogo["gols_mandante"]:

            resposta = (
                nome_time2
                + " venceu o "
                + nome_time1
                + " por "
                + str(jogo["gols_visitante"])
                + " a "
                + str(jogo["gols_mandante"])
                + "."
            )

        else:

            resposta = (
                nome_time1
                + " e "
                + nome_time2
                + " empataram em "
                + str(jogo["gols_mandante"])
                + " a "
                + str(jogo["gols_visitante"])
                + "."
            )

        if (
            jogo["penaltis_mandante"] is not None
            and jogo["penaltis_visitante"] is not None
        ):

            if jogo["penaltis_mandante"] > jogo["penaltis_visitante"]:
                vencedor_penaltis = mandante
                placar_penaltis = (
                    str(jogo["penaltis_mandante"])
                    + " a "
                    + str(jogo["penaltis_visitante"])
                )
            else: 
                vencedor_penaltis = visitante
                placar_penaltis = (
                    str(jogo["penaltis_visitante"])
                    + " a "
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
        
    if conhecimento is not None:

        return {
            "response": conhecimento.strip()
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

        classificacao = buscar_classificacao_competicao("BSA")

        if isinstance(classificacao, dict) and "erro" in classificacao:
            return {
                "response": "Não consegui consultar a classificação do campeonato no momento."
            }

        nome_busca = normalizar_nome_time(time)

        dados = None

        for item in classificacao:
            nome_classificacao = normalizar_nome_time(item["time"])

            if nome_busca in nome_classificacao or nome_classificacao in nome_busca:
                dados = item
                break

        if dados is None:
            return {
                "response": f"Não encontrei o {nome_exibicao_time(time)} na classificação atual."
            }

    texto = pergunta.pergunta.lower()

    if (
    "campanha" in texto
    or "como foi" in texto
    or "como ficou" in texto
    or "qual foi a campanha" in texto
    or "me fale sobre a campanha" in texto):
        return {
            "response": (
                f"O {dados['time']} está atualmente na "
                f"{dados['posicao']}ª posição do Brasileirão, com {dados['pontos']} pontos "
                f"em {dados['jogos']} jogos. Até o momento, foram {dados['vitorias']} vitórias, "
                f"{dados['empates']} empates e {dados['derrotas']} derrotas."
            )
        }

    dado = identificar_dado_classificacao(pergunta.pergunta)

    if dado is not None:

        respostas = {
            "pontos": f"O {dados['time']} fez {dados['pontos']} pontos no Brasileirão.",
            "posicao": f"O {dados['time']} está atualmente na {dados['posicao']}ª posição do Brasileirão.",
            "jogos": f"O {dados['time']} jogou {dados['jogos']} partidas no Brasileirão.",
            "vitorias": f"O {dados['time']} venceu {dados['vitorias']} jogos no Brasileirão.",
            "empates": f"O {dados['time']} empatou {dados['empates']} jogos no Brasileirão.",
            "derrotas": f"O {dados['time']} perdeu {dados['derrotas']} jogos no Brasileirão."
        }

        return {
            "response": respostas[dado]
        }
    
    resposta = gerar_resposta_ollama(pergunta.pergunta, dados)

    return {
        "response": resposta
    }
