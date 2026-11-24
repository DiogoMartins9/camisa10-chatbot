
REGRAS_ZONAS = {
    # Ligas nacionais
    "BSA": {
        "nome": "Brasileirão Série A",
        "temporadas": {
            2026: [
                {
                    "inicio": 1,
                    "fim": 4,
                    "nome": "Libertadores - Fase de grupos",
                    "tipo": "classificacao",
                    "cor": "verde"
                },
                {
                    "inicio": 5,
                    "fim": 5,
                    "nome": "Libertadores - Fase preliminar",
                    "tipo": "classificacao",
                    "cor": "azul"
                },
                {
                    "inicio": 6,
                    "fim": 11,
                    "nome": "Sul-Americana - Zona nominal",
                    "tipo": "classificacao",
                    "cor": "laranja",
                    "dinamica": True
                },
                {
                    "inicio": 17,
                    "fim": 20,
                    "nome": "Rebaixamento",
                    "tipo": "rebaixamento",
                    "cor": "vermelho"
                }
            ]
        }
    },
    "PL": {
        "nome": "Premier League",
        "temporadas": {
            2026: [
                {
                    "inicio": 1,
                    "fim": 5,
                    "nome": "Champions League",
                    "tipo": "classificacao",
                    "cor": "verde"
                },
                {
                    "inicio": 6,
                    "fim": 8,
                    "nome": "Vagas europeias - classificação dinâmica",
                    "tipo": "classificacao",
                    "cor": "azul",
                    "dinamica": True
                },
                {
                    "inicio": 18,
                    "fim": 20,
                    "nome": "Rebaixamento",
                    "tipo": "rebaixamento",
                    "cor": "vermelho"
                }
            ]
        }
    },
    "ELC": {
        "nome": "Championship",
        "temporadas": {
            2026: [
                {    
                    "inicio": 1,
                    "fim": 2,
                    "nome": "Acesso direto",
                    "tipo": "classificacao",
                    "cor": "verde"
                },
                {
                    "inicio": 3,
                    "fim": 8,
                    "nome": "Playoffs de acesso",
                    "tipo": "classificacao",
                    "cor": "azul"
                },
                {
                    "inicio": 22,
                    "fim": 24,
                    "nome": "Rebaixamento",
                    "tipo": "rebaixamento",
                    "cor": "vermelho"
                }
            ]
        }
    },
    "FL1": {
        "nome": "Ligue 1",
        "temporadas": {
            2026: [
                {
                    "inicio": 1,
                    "fim": 3,
                    "nome": "Champions League - Fase de liga",
                    "tipo": "classificacao",
                    "cor": "verde"
                },
                {
                    "inicio": 4,
                    "fim": 4,
                    "nome": "Champions League - Qualificação",
                    "tipo": "classificacao",
                    "cor": "verde_claro"
                },
                {
                    "inicio": 5,
                    "fim": 6,
                    "nome": "Europa League",
                    "tipo": "classificacao",
                    "cor": "azul",
                },
                {
                    "inicio": 7,
                    "fim": 7,
                    "nome": "Conference League - playoffs",
                    "tipo": "classificacao",
                    "cor": "laranja"
                },
                {
                    "inicio": 16,
                    "fim": 16,
                    "nome": "Playoff contra o rebaixamento",
                    "tipo": "rebaixamento",
                    "cor": "vermelho_claro"
                },
                {
                    "inicio": 17,
                    "fim": 18,
                    "nome": "Rebaixamento",
                    "tipo": "rebaixamento",
                    "cor": "vermelho"
                }
            ]
        }
    },
    "BL1": {
        "nome": "Bundesliga",
        "temporadas": {
            2026: [
                {
                    "inicio": 1,
                    "fim": 4,
                    "nome": "Champions League",
                    "tipo": "classificacao",
                    "cor": "verde"
                },
                {
                    "inicio": 5,
                    "fim": 5,
                    "nome": "Europa League",
                    "tipo": "classificacao",
                    "cor": "azul"
                },
                {
                    "inicio": 6,
                    "fim": 7,
                    "nome": "Vagas europeias - classificação dinâmica",
                    "tipo": "classificacao",
                    "cor": "amarelo",
                    "dinamica": True
                },
                {
                    "inicio": 16,
                    "fim": 16,
                    "nome": "Playoff contra o rebaixamento",
                    "tipo": "rebaixamento",
                    "cor": "laranja"
                },
                {
                    "inicio": 17,
                    "fim": 18,
                    "nome": "Rebaixamento",
                    "tipo": "rebaixamento",
                    "cor": "vermelho"
                }
            ]
        }
    },
    "SA": {
        "nome": "Serie A",
        "temporadas": {
            2026: [
                {
                    "inicio": 1,
                    "fim": 4,
                    "nome": "Champions League",
                    "tipo": "classificacao",
                    "cor": "verde"
                },
                {
                    "inicio": 5,
                    "fim": 6,
                    "nome": "Europa League",
                    "tipo": "classificacao",
                    "cor": "azul",
                },
                {
                    "inicio": 7,
                    "fim": 7,
                    "nome": "Conference League",
                    "tipo": "classificacao",
                    "cor": "laranja"
                },
                {
                    "inicio": 18,
                    "fim": 20,
                    "nome": "Rebaixamento",
                    "tipo": "rebaixamento",
                    "cor": "vermelho"
                }
            ]
        }
    },
    "DED": {
        "nome": "Eredivisie",
        "temporadas": {
            2026: [
                {
                    "inicio": 1,
                    "fim": 1,
                    "nome": "Champions League",
                    "tipo": "classificacao",
                    "cor": "verde"
                },
                {
                    "inicio": 2,
                    "fim": 2,
                    "nome": "Champions League - fase qualificatória",
                    "tipo": "classificacao",
                    "cor": "verde_claro"
                },
                {
                    "inicio": 3,
                    "fim": 3,
                    "nome": "Europa League - fase qualificatória",
                    "tipo": "classificacao",
                    "cor": "azul_claro"
                },
                {
                    "inicio": 4,
                    "fim": 7,
                    "nome": "Playoffs europeus - Conference League",
                    "tipo": "classificacao",
                    "cor": "laranja",
                    "dinamica": True
                },
                {
                    "inicio": 16,
                    "fim": 16,
                    "nome": "Playoff de permanência",
                    "tipo": "rebaixamento",
                    "cor": "vermelho_claro"
                },
                {
                    "inicio": 17,
                    "fim": 18,
                    "nome": "Rebaixamento",
                    "tipo": "rebaixamento",
                    "cor": "vermelho"
                }
            ]
        }
    },
    "PPL": {
        "nome": "Primeira Liga",
        "temporadas": {
            2026: [
                {
                    "inicio": 1,
                    "fim": 2,
                    "nome": "Champions League",
                    "tipo": "classificacao",
                    "cor": "verde"
                },
                {
                    "inicio": 3,
                    "fim": 3,
                    "nome": "Champions League - Qualificação",
                    "tipo": "classificacao",
                    "cor": "verde_claro"
                },
                {
                    "inicio": 4,
                    "fim": 4,
                    "nome": "Europa League - fase qualificatória",
                    "tipo": "classificacao",
                    "cor": "azul_claro"
                },
                {
                    "inicio": 5,
                    "fim": 5,
                    "nome": "Conference League - fase qualificatória",
                    "tipo": "classificacao",
                    "cor": "laranja",
                },
                {
                    "inicio": 16,
                    "fim": 16,
                    "nome": "Playoff de permanência",
                    "tipo": "rebaixamento",
                    "cor": "vermelho_claro"
                },
                {
                    "inicio": 17,
                    "fim": 18,
                    "nome": "Rebaixamento",
                    "tipo": "rebaixamento",
                    "cor": "vermelho"
                }
            ]
        }
    },
    "PD": {
        "nome": "La Liga",
        "temporadas": {
            2026: [
                {
                    "inicio": 1,
                    "fim": 5,
                    "nome": "Champions League",
                    "tipo": "classificacao",
                    "cor": "verde"
                },
                {
                    "inicio": 6,
                    "fim": 7,
                    "nome": "Vagas europeias - classificação dinâmica",
                    "tipo": "classificacao",
                    "cor": "azul",
                    "dinamica": True
                },
                {
                    "inicio": 18,
                    "fim": 20,
                    "nome": "Rebaixamento",
                    "tipo": "rebaixamento",
                    "cor": "vermelho"
                }
            ]
        }
    },

    # Competições internacionais
    "CL": {
        "nome": "UEFA Champions League",
        "temporadas": {
            2026: [
                {
                    "inicio": 1,
                    "fim": 8,
                    "nome": "Classificação direta - Oitavas de final",
                    "tipo": "classificacao",
                    "cor": "verde"
                },
                {
                    "inicio": 9,
                    "fim": 24,
                    "nome": "Playoffs classificatórios",
                    "tipo": "classificacao",
                    "cor": "azul"
                },
                {
                    "inicio": 25,
                    "fim": 36,
                    "nome": "Eliminado",
                    "tipo": "eliminacao",
                    "cor": "vermelho"
                }
            ]
        }
    },
    "EC": {
        "nome": "European Championship",
        "temporadas": {
            2028: [
                {
                    "inicio": 1,
                    "fim": 2,
                    "nome": "Classificado - Oitavas de final",
                    "tipo": "classificacao",
                    "cor": "verde"
                },
                {
                    "inicio": 3,
                    "fim": 3,
                    "nome": "Classificação dinâmica - Melhores terceiros",
                    "tipo": "classificacao",
                    "cor": "azul",
                    "dinamica": True
                }
            ]
        }
    },
    "CLI": {
        "nome": "Copa Libertadores",
        "temporadas": {
            2026: [
                {
                    "inicio": 1,
                    "fim": 2,
                    "nome": "Classificado - Oitavas de final",
                    "tipo": "classificacao",
                    "cor": "verde"
                },
                {
                    "inicio": 3,
                    "fim": 3,
                    "nome": "Playoffs da Sul-Americana",
                    "tipo": "classificacao",
                    "cor": "azul"
                }
            ]
        }
    },
    "WC": {
        "nome": "FIFA World Cup",
        "temporadas": {
            2026: [
                {
                    "inicio": 1,
                    "fim": 2,
                    "nome": "Classificado - Fase eliminatória",
                    "tipo": "classificacao",
                    "cor": "verde"
                },
                {
                    "inicio": 3,
                    "fim": 3,
                    "nome": "Classificação dinâmica - Melhores terceiros",
                    "tipo": "classificacao",
                    "cor": "azul",
                    "dinamica": True
                }
            ]
        }
    }
}


def obter_zona_classificacao(codigo_competicao, temporada, posicao):
    regras_competicao = REGRAS_ZONAS.get(codigo_competicao, {})
    regras_temporada = regras_competicao.get("temporadas", {}).get(
        temporada, []
    )

    for regra in regras_temporada:
        if regra["inicio"] <= posicao <= regra["fim"]:
            return {
                "nome": regra["nome"],
                "tipo": regra["tipo"],
                "cor": regra["cor"],
                "dinamica": regra.get("dinamica", False)
            }

    return None


def obter_legenda_classificacao(codigo_competicao, temporada):
    regras_competicao = REGRAS_ZONAS.get(codigo_competicao, {})
    regras_temporada = regras_competicao.get("temporadas", {}).get(
        temporada, []
    )

    return [
        {
            "nome": regra["nome"],
            "tipo": regra["tipo"],
            "cor": regra["cor"],
            "dinamica": regra.get("dinamica", False)
        }
        for regra in regras_temporada
    ]
