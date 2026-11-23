
from sqlalchemy.orm import Session

from database.connection import SessionLocal
from database.models import ImagemEsportiva, ProgressoImportacaoTimes, FilaImportacaoTimes, FilaImportacaoPaises

from services.cloudinary_service import enviar_imagem_externa_cloudinary
from services.api_football import buscar_competicoes_api_football, buscar_times_por_pais, buscar_paises_api_football, consultar_cota_api_football
from datetime import date
import time

def obter_sessao():
    return SessionLocal()

def obter_progresso_pais(
    db: Session,
    pais: str,
):
    progresso = (
        db.query(ProgressoImportacaoTimes)
        .filter(
            ProgressoImportacaoTimes.pais == pais
        )
        .first()
    )
    
    if progresso:
        return progresso
    
    progresso = ProgressoImportacaoTimes(
        pais=pais,
        total_encontrado=0,
        total_importado=0,
        concluido=False,
    )
    
    db.add(progresso)
    db.commit()
    db.refresh(progresso)
    
    return progresso

def armazenar_times_por_pais(
    db: Session,
    pais: str,
):
    times = buscar_times_por_pais(pais)
    
    if times is None:
        return None

    if not times:
        return {
            "pais": pais,
            "encontrados": 0,
            "novos": 0,
            "ja_existentes": 0,
        }

    ids_api = [time["id"] for time in times]

    ids_existentes = {
        resultado[0]
        for resultado in (
            db.query(FilaImportacaoTimes.api_id)
            .filter(FilaImportacaoTimes.api_id.in_(ids_api))
            .all()
        )
    }

    novos = 0

    for time in times:
        if time["id"] in ids_existentes:
            continue

        db.add(
            FilaImportacaoTimes(
                api_id=time["id"],
                nome=time["nome"],
                pais=time["pais"],
                nacional=time.get("nacional", False),
                url_original=time["logo"],
            )
        )

        novos += 1

    db.commit()

    return {
        "pais": pais,
        "encontrados": len(times),
        "novos": novos,
        "ja_existentes": len(ids_existentes),
    }

def imagem_ja_cadastrada(
    db: Session,
    tipo: str,
    api_id: int,
):
    return (
        db.query(ImagemEsportiva)
        .filter(
            ImagemEsportiva.tipo == tipo,
            ImagemEsportiva.api_id == api_id,
        )
        .first()
    )

def importar_imagem(
    db: Session,
    tipo: str,
    api_id: int,
    nome: str,
    url_original: str,
):
    existente = imagem_ja_cadastrada(db, tipo, api_id)
    
    if existente:
        return {
            "status": "ja_cadastrada",
            "nome": nome,
            "url": existente.cloudinary_url,
        }
        
    public_id = f"camisa10/{'times' if tipo == 'time' else 'competicoes'}/{api_id}"
    
    try:
        resultado = enviar_imagem_externa_cloudinary(
            url=url_original,
            public_id=public_id,
        )
        
        imagem = ImagemEsportiva(
            tipo=tipo,
            api_id=api_id,
            nome=nome,
            url_original=url_original,
            cloudinary_url=resultado["url"],
            public_id=resultado["public_id"],
        )
        
        db.add(imagem)
        db.commit()
        db.refresh(imagem)
        
        return {
            "status": "importada",
            "nome": nome,
            "url": imagem.cloudinary_url,
        }
        
    except Exception:
        db.rollback()
        raise


def importar_competicoes_atuais(db: Session, limite: int = None):
    competicoes = buscar_competicoes_api_football(atuais=True)
    
    if limite is not None:
        competicoes = competicoes[:limite]

    resultados = {
        "importadas": 0,
        "ja_cadastradas": 0,
        "ignoradas": 0,
        "erros": 0,
    }

    for competicao in competicoes:
        api_id = competicao.get("id")
        nome = competicao.get("nome")
        logo = competicao.get("logo")

        if not api_id or not nome or not logo:
            resultados["ignoradas"] += 1
            continue

        try:
            resultado = importar_imagem(
                db=db,
                tipo="competicao",
                api_id=api_id,
                nome=nome,
                url_original=logo,
            )

            chave = (
                "ja_cadastradas"
                if resultado["status"] == "ja_cadastrada"
                else "importadas"
            )
            resultados[chave] += 1

        except Exception as erro:
            db.rollback()
            resultados["erros"] += 1
            print(f"Erro ao importar {nome} (ID {api_id}): {erro}")

    return resultados

# def testar_busca_times():
    #times = buscar_times_por_pais("Brazil")

    #print(f"Total de times encontrados: {len(times)}")

    #for time in times[:10]:
        #print(
            #f"ID: {time['id']} | "
            #f"Nome: {time['nome']} | "
            #f"País: {time['pais']}"
        #)

def importar_times_por_pais(
    db: Session,
    pais: str,
    limite: int = 5,
):
    progresso = obter_progresso_pais(db, pais)

    times = buscar_times_por_pais(pais)

    if not times:
        return {
            "pais": pais,
            "encontrados": 0,
            "importados": 0,
            "ja_cadastrados": 0,
            "erros": 0,
        }

    progresso.total_encontrado = len(times)
    db.commit()

    resultados = {
        "pais": pais,
        "encontrados": len(times),
        "importados": 0,
        "ja_cadastrados": 0,
        "erros": 0,
    }

    processados_neste_lote = 0
    total_cadastrado = 0

    for time in times:
        api_id = time.get("id")
        nome = time.get("nome")
        logo = time.get("logo")

        if not api_id or not nome or not logo:
            continue

        existente = imagem_ja_cadastrada(
            db,
            "time",
            api_id,
        )

        if existente:
            resultados["ja_cadastrados"] += 1
            total_cadastrado += 1
            continue

        if (
            limite is not None
            and processados_neste_lote >= limite
        ):
            continue

        try:
            importar_imagem(
                db=db,
                tipo="time",
                api_id=api_id,
                nome=nome,
                url_original=logo,
            )

            resultados["importados"] += 1
            total_cadastrado += 1
            processados_neste_lote += 1

        except Exception as erro:
            db.rollback()
            resultados["erros"] += 1
            print(
                f"Erro ao importar {nome} "
                f"(ID {api_id}): {erro}"
            )

    progresso.total_importado = total_cadastrado
    progresso.concluido = (
        total_cadastrado == len(times)
        and resultados["erros"] == 0
    )

    db.commit()

    return resultados

def processar_lote_cloudinary(
    db: Session,
    limite: int = 50,
    pais: str = None,
):
    consulta = (
        db.query(FilaImportacaoTimes)
        .filter(
            FilaImportacaoTimes.importado == False,
            FilaImportacaoTimes.tentativas < 3,
            )
    )

    if pais:
        consulta = consulta.filter(
            FilaImportacaoTimes.pais == pais
        )

    fila = (
        consulta
        .order_by(FilaImportacaoTimes.id)
        .limit(limite)
        .all()
    )

    resultados = {
        "processados": 0,
        "importados": 0,
        "ja_cadastrados": 0,
        "erros": 0,
    }

    for item in fila:
        try:
            existente = imagem_ja_cadastrada(
                db,
                "time",
                item.api_id,
            )

            if existente:
                resultados["ja_cadastrados"] += 1
            else:
                importar_imagem(
                    db=db,
                    tipo="time",
                    api_id=item.api_id,
                    nome=item.nome,
                    url_original=item.url_original,
                )

                resultados["importados"] += 1

            item.importado = True
            db.commit()

            resultados["processados"] += 1

        except Exception as erro:
            db.rollback()

            item_atualizado = (
                db.query(FilaImportacaoTimes)
                .filter(
                    FilaImportacaoTimes.id == item.id
                )
                .first()
            )

            if item_atualizado:
                item_atualizado.tentativas += 1
                db.commit()

            resultados["erros"] += 1
            print(
                f"Erro ao processar {item.nome} "
                f"(ID {item.api_id}): {erro}"
            )

    return resultados

def testar_armazenamento_times():
    db = obter_sessao()
    
    try:
        resultado = armazenar_times_por_pais(
            db=db,
            pais="Brazil",
        )
        
        print("Resultado armazenamento:")
        print(resultado)
        
    finally:
        db.close()
        
def testar_lote_cloudinary():
    db = obter_sessao()
    
    try:
        resultado = processar_lote_cloudinary(
            db=db,
            limite=5,
            pais="Brazil",
        )
        
        print("Resultado do lote:")
        print(resultado)
        
    finally:
        db.close()

def importar_fila_automaticamente(
    pais: str = None,
    tamanho_lote: int = 50,
    maximo_por_execucao: int = 200,
):
    db = obter_sessao()

    resultados_totais = {
        "processados": 0,
        "importados": 0,
        "ja_cadastrados": 0,
        "erros": 0,
    }

    try:
        while (
            resultados_totais["processados"]
            < maximo_por_execucao
        ):
            restante = (
                maximo_por_execucao
                - resultados_totais["processados"]
            )

            limite = min(tamanho_lote, restante)

            resultado = processar_lote_cloudinary(
                db=db,
                limite=limite,
                pais=pais,
            )

            for chave in resultados_totais:
                resultados_totais[chave] += resultado[chave]

            if resultado["processados"] == 0:
                break

        print("Resultado da importação automática:")
        print(resultados_totais)

        return resultados_totais

    finally:
        db.close()

def cadastrar_paises_importacao(db: Session):
    paises = buscar_paises_api_football()

    if not paises:
        return {
            "encontrados": 0,
            "novos": 0,
            "existentes": 0,
        }

    # Prioridade 1: países europeus
    paises_uefa = {
        "England", "Spain", "Germany", "Italy", "France",
        "Portugal", "Netherlands", "Belgium", "Scotland",
        "Turkey", "Austria", "Switzerland", "Ukraine",
        "Greece", "Denmark", "Norway", "Sweden",
        "Poland", "Czech Republic", "Croatia", "Serbia",
    }

    # Prioridade 2: países sul-americanos
    paises_conmebol = {
        "Brazil", "Argentina", "Uruguay", "Colombia",
        "Chile", "Ecuador", "Paraguay", "Peru",
        "Bolivia", "Venezuela",
    }

    existentes = {
        resultado[0]
        for resultado in db.query(FilaImportacaoPaises.pais).all()
    }

    novos = 0

    for pais in paises:
        if pais in existentes:
            continue

        if pais in paises_uefa:
            prioridade = 1
        elif pais in paises_conmebol:
            prioridade = 2
        else:
            prioridade = 3

        db.add(
            FilaImportacaoPaises(
                pais=pais,
                prioridade=prioridade,
            )
        )
        novos += 1

    db.commit()

    return {
        "encontrados": len(paises),
        "novos": novos,
        "existentes": len(existentes),
    }

def executar_cadastro_paises():
    cota = consultar_cota_api_football()

    if not cota["disponivel"]:
        print("Não foi possível consultar a cota da API.")
        print(cota.get("erro"))
        return None

    print(
        f"Cota disponível: {cota['restantes']}/"
        f"{cota['limite']}"
    )

    if cota["restantes"] < 1:
        print("Cota diária esgotada. Cadastro cancelado.")
        return None

    db = obter_sessao()

    try:
        resultado = cadastrar_paises_importacao(db)

        print("Resultado do cadastro de países:")
        print(resultado)

        return resultado

    finally:
        db.close()

def importar_proximo_pais():
    db = obter_sessao()
    
    hoje = date.today()
    
    try:
        pais = (
            db.query(FilaImportacaoPaises)
            .filter(
                FilaImportacaoPaises.consultado == False,
                (
                    FilaImportacaoPaises.ultima_consulta.is_(None)
                    | (FilaImportacaoPaises.ultima_consulta < hoje)
                ),
            )
            .order_by(
                FilaImportacaoPaises.prioridade,
                FilaImportacaoPaises.id,
            )
            .first()
        )

        if not pais:
            print("Todos os países já foram consultados.")
            return None

        cota = consultar_cota_api_football()

        if not cota["disponivel"]:
            print("Não foi possível verificar a cota.")
            return None

        if cota["restantes"] < 2:
            print("Cota insuficiente para consultar outro país.")
            return None

        time.sleep(7)
        
        resultado = armazenar_times_por_pais(
            db=db,
            pais=pais.pais,
        )
        
        if resultado is None:
            pais.ultima_consulta = hoje
            db.commit()
            
            print(
                f"Falha ao consultar {pais.pais}. "
                "Nova tentativa ficará para outro dia."
            )
            return {
                "pais": pais.pais,
                "erro": True,
            }

        pais.consultado = True
        pais.total_encontrado = resultado["encontrados"]
        pais.total_novos = resultado["novos"]
        pais.ultima_consulta = hoje

        db.commit()

        print(f"País consultado: {pais.pais}")
        print(resultado)

        return resultado

    finally:
        db.close()

def importar_paises_do_dia(limite_paises: int = 20):
    processados = 0
    resultados = []

    while processados < limite_paises:
        resultado = importar_proximo_pais()

        if resultado is None:
            print("Não há mais países disponíveis para consulta hoje.")
            break

        resultados.append(resultado)
        processados += 1

        if resultado.get("erro"):
            print(
                f"Consulta de {resultado['pais']} falhou. "
                "Continuando para o próximo país."
            )

        if processados < limite_paises:
            print("Aguardando 7 segundos para respeitar o limite da API...")
            time.sleep(7)

    print(f"Países processados: {processados}")
    return resultados
