from backend.services.football_api import buscar_jogos_competicao

jogos = buscar_jogos_competicao("PD")

if isinstance(jogos, dict) and "erro" in jogos:
    print("Erro:", jogos["erro"])

else:
    encontrado = False

    for jogo in jogos:

        if (
            "Real Betis" in jogo["mandante"]
            and "Getafe" in jogo["visitante"]
        ) or (
            "Getafe" in jogo["mandante"]
            and "Real Betis" in jogo["visitante"]
        ):

            print("\nJOGO ENCONTRADO!")
            print("ID:", jogo["id"])
            print("Competição:", jogo["competicao"])
            print("Mandante:", jogo["mandante"])
            print("Visitante:", jogo["visitante"])
            print(
                "Placar:",
                jogo["gols_mandante"],
                "x",
                jogo["gols_visitante"]
            )

            print(
                "Pênaltis:",
                jogo["penaltis_mandante"],
                "x",
                jogo["penaltis_visitante"]
            )

            encontrado = True
            break

    if not encontrado:
        print("Real Betis x Getafe não encontrado.")


