
from knowledge.historic_knowledge import (buscar_conhecimento_historico, CONHECIMENTO_HISTORICO)


perguntas = [
    "Quantas Libertadores o São Paulo ganhou?",
    "quantas libertadores tem o sao paulo",
    "O São Paulo ganhou quantas Libertadores em sua história?",
    "Quantas Champions League o Real Madrid ganhou?",
    "Em que anos o São Paulo ganhou a Libertadores?",
]

for pergunta in perguntas:
    resultado = buscar_conhecimento_historico(pergunta)

    print(f"\nPergunta: {pergunta}")

    if resultado:
        print(f"Encontrado: {resultado['resposta']}")
    else:
        print("Nenhum conhecimento encontrado.")



novos_testes = [
    (
        "Quantas Bolas de Ouro tem Cristiano Ronaldo?",
        "cristiano_ronaldo_bolas_de_ouro",
    ),
    (
        "Quantas Copas do Mundo Pelé ganhou?",
        "pele_copas_do_mundo",
    ),
    (
        "Quantas Copas do Mundo a Argentina ganhou?",
        "argentina_copas_do_mundo",
    ),
]

for pergunta, chave_esperada in novos_testes:
    resultado = buscar_conhecimento_historico(pergunta)

    assert resultado is not None, (
        f"Não encontrou a pergunta: {pergunta}"
    )

    assert resultado == CONHECIMENTO_HISTORICO[chave_esperada], (
        f"Conhecimento incorreto para: {pergunta}"
    )

    print(f"PASSOU: {pergunta}")
