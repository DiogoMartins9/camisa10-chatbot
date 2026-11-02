
from backend.database.connection import testar_conexao

try:
    resultado = testar_conexao()

    if resultado == 1:
        print("Conexão com o Neon estabelecida com sucesso!")

except Exception as erro:
    print("Não foi possível conectar ao Neon.")
    print(f"Erro: {erro}")
