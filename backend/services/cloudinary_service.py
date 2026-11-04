import cloudinary
import os
import cloudinary.api
from cloudinary import uploader
from dotenv import load_dotenv

load_dotenv()  

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True,
)

def testar_conexao_cloudinary():
    try:
        resultado = cloudinary.api.ping()
        print("Conexão com Cloudinary realizada:", resultado)
        return True

    except Exception as erro:
        print("Erro ao conectar com Cloudinary:", erro)
        return False

def enviar_imagem_cloudinary(arquivo):
    """
    Envia uma imagem ao Cloudinary.
    
    Recebe um arquivo enviado pelo FastAPI (UploadFile)
    e retorna os dados da imagem hospedada.
    """
    resultado = uploader.upload(
        arquivo.file,
        folder="camisa10/perfis",
        resource_type="image",
    )

    return {
        "url": resultado["secure_url"],
        "public_id": resultado["public_id"],
    }