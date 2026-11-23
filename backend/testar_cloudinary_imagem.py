from services.cloudinary_service import enviar_imagem_externa_cloudinary

url = "https://media.api-sports.io/football/teams/645.png"

try:
    resultado = enviar_imagem_externa_cloudinary(
        url=url,
        public_id="camisa10/testes/galatasaray_645",
    )

    print("\nImagem enviada com sucesso!")
    print("URL:", resultado["url"])
    print("Public ID:", resultado["public_id"])

except Exception as erro:
    print("\nErro ao enviar imagem:")
    print(erro)