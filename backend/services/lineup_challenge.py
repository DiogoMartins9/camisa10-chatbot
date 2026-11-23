from backend.services.api_football import buscar_elenco_time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

def validar_escalacao(team_id: int, escalacao: dict) -> dict:
    """
    Verifica se os 11 jogadores escolhidos pertencem ao elenco
    da equipe informada.
    """
    
    resultado = buscar_elenco_time(team_id)
    
    if "erro" in resultado:
        return resultado
    
    jogadores_validos = {
        jogador["id"]
        for jogador in resultado["jogadores"]
        if jogador.get("id") is not None
    }
    
    jogadores_escolhidos = set(escalacao["jogadores"])
    
    invalidos = jogadores_escolhidos - jogadores_validos
    
    if invalidos:
        return {
            "erro": "Existem jogadores que não pertencem ao elenco informado.",
            "jogadores_invalidos": list(invalidos)
        }
        
    return {
        "valida": True
    }
    
def calcular_pontuacao(
    previsao: dict,
    escalacao_oficial: dict
) -> int:
    """
    Calcula os pontos da previsão de uma equipe.
    
    10 pontos por titular correto.
    20 pontos pela formação correta.
    """
    
    jogadores_previstos = set(previsao["jogadores"])
    
    jogadores_oficiais = {
        jogador["id"]
        for jogador in escalacao_oficial["titulares"]
        if jogador.get("id") is not None
    }
    
    acertos = len(jogadores_previstos & jogadores_oficiais)
    
    pontos = acertos * 10
    
    if (
        previsao["formacao"]
        == escalacao_oficial.get("formacao")
    ):
        pontos += 20
        
    return pontos


def escalacao_oficial_valida(escalacao: dict) -> bool:
    """
    Confirma que a escalação oficial possui
    11 titulares com IDs válidos e distintos.
    """
    titulares = escalacao.get("titulares", [])

    ids = [
        jogador.get("id")
        for jogador in titulares
    ]

    return (
        len(titulares) == 11
        and all(isinstance(id_jogador, int) and id_jogador > 0 for id_jogador in ids)
        and len(set(ids)) == 11
        and bool(escalacao.get("formacao"))
    )

def avaliar_previsao(
    previsao: dict,
    escalacoes_oficiais: dict,
) -> dict:
    """
    Calcula a pontuação das equipes previstas.
    Considera somente os titulares oficiais.
    """

    resultado = {
        "pontuacao_mandante": 0,
        "pontuacao_visitante": 0,
        "pontuacao_total": 0,
    }

    if previsao.get("mandante"):
        oficiais = escalacoes_oficiais.get("mandante", {})

        titulares = oficiais.get("titulares", [])

        if len(titulares) == 11 and oficiais.get("formacao"):
            resultado["pontuacao_mandante"] = calcular_pontuacao(
                previsao["mandante"],
                oficiais,
            )

    if previsao.get("visitante"):
        oficiais = escalacoes_oficiais.get("visitante", {})

        titulares = oficiais.get("titulares", [])

        if len(titulares) == 11 and oficiais.get("formacao"):
            resultado["pontuacao_visitante"] = calcular_pontuacao(
                previsao["visitante"],
                oficiais,
            )

    resultado["pontuacao_total"] = (
        resultado["pontuacao_mandante"]
        + resultado["pontuacao_visitante"]
    )

    return resultado


def verificar_prazo_previsao(data_partida: str) -> dict:
    """
    Verifica se ainda é permitido criar ou editar
    uma previsão para a partida.

    O prazo encerra uma hora antes do início.
    Utiliza o horário de São Paulo.
    """

    try:
        horario_partida = datetime.fromisoformat(
            data_partida.replace("Z", "+00:00")
        )

        fuso_sp = ZoneInfo("America/Sao_Paulo")

        if horario_partida.tzinfo is None:
            horario_partida = horario_partida.replace(
                tzinfo=fuso_sp
            )
        else:
            horario_partida = horario_partida.astimezone(
                fuso_sp
            )

        agora = datetime.now(fuso_sp)

        prazo_final = horario_partida - timedelta(hours=1)

        if agora >= prazo_final:
            return {
                "permitido": False,
                "mensagem": (
                    "As previsões para esta partida estão encerradas."
                ),
                "prazo_final": prazo_final.isoformat()
            }

        return {
            "permitido": True,
            "mensagem": "Ainda é possível enviar ou editar a previsão.",
            "prazo_final": prazo_final.isoformat()
        }

    except (ValueError, TypeError, AttributeError):
        return {
            "permitido": False,
            "mensagem": "Não foi possível verificar o horário da partida."
        }
