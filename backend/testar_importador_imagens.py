
from database.connection import SessionLocal
from services.importador_imagens import importar_competicoes_atuais

db = SessionLocal()

try:
    print("Testando reutilização de imagem existente...")

    resultado = importar_competicoes_atuais(
        db=db,
        limite=1,
    )

    print("\nResultado:")
    print(resultado)

finally:
    db.close()
