
import unicodedata


CONHECIMENTO_HISTORICO = {
    "sao_paulo_libertadores": {
        "termos": [
            "quantas libertadores tem o sao paulo",
            "quantas libertadores o sao paulo ganhou",
            "quantas libertadores o sao paulo possui",
            "titulos da libertadores do sao paulo",
            "o sao paulo ganhou quantas libertadores",
            "o sao paulo ganhou quantas libertadores em sua historia",
            "em quais anos o sao paulo venceu a libertadores",
            "em que anos o sao paulo ganhou a libertadores",
        ],
        "resposta": (
            "O São Paulo conquistou a Copa Libertadores três vezes: "
            "em 1992, 1993 e 2005."
        ),
        "fontes": [
            "CONMEBOL",
            "São Paulo Futebol Clube",
        ],
    },

    "real_madrid_champions": {
        "termos": [
            "quantas champions league o real madrid ganhou",
            "quantas champions o real madrid ganhou",
            "titulos da champions league do real madrid",
            "quantas vezes o real madrid venceu a champions",
        ],
        "resposta": (
            "O Real Madrid conquistou a Champions League "
            "15 vezes, até a temporada 2023/24."
        ),
        "fontes": [
            "UEFA",
            "Real Madrid CF",
        ],
    },
    
    "messi_bolas_de_ouro": {
        "termos": [
            "quantas bolas de ouro tem o messi",
            "quantas bolas de ouro o messi ganhou",
            "quantas vezes messi ganhou a bola de ouro",
            "titulos de bola de ouro do messi",
            "quantas ballon d'or tem messi",
        ],
        "resposta": (
            "Lionel Messi conquistou a Bola de Ouro oito vezes, "
            "em 2009, 2010, 2011, 2012, 2015, 2019, 2021 e 2023."
        ),
        "fontes": [
            "France Football",
        ],
    },

    "final_champions_2005": {
        "termos": [
            "qual foi a final da champions de 2005",
            "quem jogou a final da champions em 2005",
            "final da champions league de 2005",
            "quem ganhou a champions de 2005",
            "resultado da final da champions de 2005",
        ],
        "resposta": (
            "A final da Champions League de 2005 foi entre Milan e "
            "Liverpool. O Milan abriu 3 a 0, mas o Liverpool empatou "
            "em 3 a 3 e venceu a disputa de pênaltis por 3 a 2, "
            "conquistando o título."
        ),
        "fontes": [
            "UEFA",
        ],
    },

    "brasil_copas_mundo": {
        "termos": [
            "quantas copas do mundo o brasil ganhou",
            "quantas copas do mundo tem o brasil",
            "em quais anos o brasil ganhou a copa do mundo",
            "anos dos titulos mundiais do brasil",
            "titulos da selecao brasileira na copa do mundo",
        ],
        "resposta": (
            "A Seleção Brasileira masculina conquistou cinco Copas "
            "do Mundo: 1958, 1962, 1970, 1994 e 2002."
        ),
        "fontes": [
            "FIFA",
        ],
    },

    
    "cristiano_ronaldo_bolas_de_ouro": {
        "termos": [
            "quantas bolas de ouro tem cristiano ronaldo",
            "quantas bolas de ouro o cristiano ronaldo ganhou",
            "quantas vezes cristiano ronaldo ganhou a bola de ouro",
            "quantas ballon d'or tem cristiano ronaldo",
            "anos das bolas de ouro de cristiano ronaldo",
        ],
        "resposta": (
            "Cristiano Ronaldo conquistou a Bola de Ouro cinco vezes: "
            "em 2008, 2013, 2014, 2016 e 2017."
        ),
        "fontes": [
            "France Football",
        ],
    },

    "pele_copas_do_mundo": {
        "termos": [
            "quantas copas do mundo pele ganhou",
            "quantas copas do mundo o pele conquistou",
            "em quais anos pele ganhou a copa do mundo",
            "quantos titulos mundiais pele tem",
            "pele ganhou quantas copas do mundo",
        ],
        "resposta": (
            "Pelé conquistou três Copas do Mundo com a Seleção Brasileira: "
            "em 1958, 1962 e 1970."
        ),
        "fontes": [
            "FIFA",
        ],
    },

    "argentina_copas_do_mundo": {
        "termos": [
            "quantas copas do mundo a argentina ganhou",
            "quantas copas do mundo tem a argentina",
            "em quais anos a argentina ganhou a copa do mundo",
            "quantos titulos mundiais a argentina tem",
            "anos dos titulos mundiais da argentina",
        ],
        "resposta": (
            "A Seleção Argentina masculina conquistou três Copas do Mundo: "
            "em 1978, 1986 e 2022."
        ),
        "fontes": [
            "FIFA",
        ],
    },

}


def normalizar_texto(texto):
    texto = texto.lower().strip()

    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(
        caractere
        for caractere in texto
        if unicodedata.category(caractere) != "Mn"
    )

    return " ".join(texto.split())


def buscar_conhecimento_historico(pergunta):
    pergunta_normalizada = normalizar_texto(pergunta)

    for conhecimento in CONHECIMENTO_HISTORICO.values():
        for termo in conhecimento["termos"]:
            termo_normalizado = normalizar_texto(termo)

            if termo_normalizado in pergunta_normalizada:
                return conhecimento

    return None
