
from backend.database.connection import testar_conexao as verificar_conexao


def test_conexao_com_neon():
    resultado = verificar_conexao()

    assert resultado == 1, "A conexão com o Neon não foi estabelecida."

    print("Conexão com o Neon estabelecida com sucesso!")
