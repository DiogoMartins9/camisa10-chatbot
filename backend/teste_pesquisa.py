
import asyncio

from knowledge.external_research import pesquisar_na_web


async def main():
    pergunta = "Quantas Copas do Mundo Pelé ganhou?"

    resultados = await pesquisar_na_web(pergunta)

    if not resultados:
        print("Nenhum resultado retornado.")
        return

    for i, resultado in enumerate(resultados, start=1):
        print(f"\nResultado {i}: {resultado['titulo']}")
        print(f"URL: {resultado['url']}")
        print(f"Trecho: {resultado['conteudo'][:500]}")


if __name__ == "__main__":
    asyncio.run(main())
