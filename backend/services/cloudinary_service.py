import cloudinary
import os
import cloudinary.api
from cloudinary import uploader
from urllib.parse import urlparse
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

def excluir_imagem_cloudinary(public_id: str):
    """
    Remove uma imagem hospedada no Cloudinary
    utilizando seu public_id.
    """
    resultado = uploader.destroy(
        public_id,
        resource_type="image",
    )

    return resultado

def excluir_imagem_por_url(url: str):
    """
    Recupera o public_id de uma URL gerada pelo nosso
    serviço de upload e remove a imagem do Cloudinary.
    """
    if not url:
        return None

    caminho = urlparse(url).path

    if "/upload/" not in caminho:
        raise ValueError("URL do Cloudinary inválida.")

    public_id = caminho.split("/upload/", 1)[1]

    partes = public_id.split("/", 1)

    if partes[0].startswith("v") and partes[0][1:].isdigit():
        public_id = partes[1]

    public_id = public_id.rsplit(".", 1)[0]

    return excluir_imagem_cloudinary(public_id)