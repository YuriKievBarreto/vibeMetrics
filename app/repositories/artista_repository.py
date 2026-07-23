from app.schemas.schema_artista import ArtistaCreate
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.artista import Artista  
from sqlalchemy import select


async def ler_artista(id_artista:str, db: AsyncSession):
    try:
        db_artista = await db.get(Artista, id_artista)

        if db_artista is None:
            print(f"Artista de id {id_artista} não encontrada")
            return None
        
        print("artista_encontrada encontrado")
        return db_artista
    
    except Exception as e:
        raise e
    


async def criar_artista(db: AsyncSession, artista_data_dict):

    print("iniciandi criacao de faiax==x")


    try:
        db_artista = Artista(**artista_data_dict)
        db.add(db_artista)
        await db.commit()

        return db_artista

    except Exception as e:

        print("erro ao tenta adicionar artista:" , e)


async def salvar_artistas_em_batch(db: AsyncSession, lista_artistas_data: list[dict]):

    print(f"Processando {len(lista_artistas_data)} artistas para inserção...")

    if not lista_artistas_data:
        print("Lista de artistas vazia. Nenhuma ação realizada.")
        return []

    try:
        ids_a_verificar = [artista.get('id_artista') for artista in lista_artistas_data if artista.get('id_artista')]
        
        if not ids_a_verificar:
            print("Nenhum ID de artista encontrado para verificação.")
            return []

      
        stmt = select(Artista.id_artista).where(Artista.id_artista.in_(ids_a_verificar))
        result = await db.execute(stmt)
        
        ids_existentes = set(result.scalars().all())
        
        num_existentes = len(ids_existentes)
        print(f"{num_existentes} artistas já existem e serão ignoradas.")

        artistas_a_inserir = [
            artista_data 
            for artista_data in lista_artistas_data
            if artista_data.get('id_artista') not in ids_existentes
        ]

        if not artistas_a_inserir:
            print("Todas as artistas já existem. Nenhuma inserção necessária.")
            return []


        objetos_artista = [Artista(**artista_data) for artista_data in artistas_a_inserir]
        db.add_all(objetos_artista)
        await db.commit()
        
        print(f"Sucesso: {len(objetos_artista)} novas artistas salvas.")
        return objetos_artista

    except Exception as e:
       
        await db.rollback() 
        print("Erro ao tentar adicionar artistas em lote com validação:", e)
       
        raise


