from app.schemas.schema_faixa import FaixaCreate
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.faixa import Faixa  
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import async_engine
from sqlalchemy import select


async def ler_faixa(id_faixa:str):
     async with AsyncSession(async_engine) as db:
        try:
            db_faixa = await db.get(Faixa, id_faixa)

            if db_faixa is None:
                print("Faixa de id {user_id} não encontrada")
                return None
    
            print("faixa_encontrada encontrado")
            return db_faixa

        except Exception as e:
            raise e

    


async def criar_faixa(db: AsyncSession, faixa_data_dict):

    print("iniciandi criacao de faiax==x")

    try:
        db_faixa = Faixa(**faixa_data_dict)
        db.add(db_faixa)
        await db.commit()

        return db_faixa

    except Exception as e:

        print("erro ao tenta adicionar faixa:" , e)




async def salvar_faixas_em_batch(db: AsyncSession, lista_de_faixas_data: list[dict]):

    print(f"Processando {len(lista_de_faixas_data)} faixas para inserção...")

    if not lista_de_faixas_data:
        print("Lista de faixas vazia. Nenhuma ação realizada.")
        return []

    try:
        ids_a_verificar = [faixa.get('id_faixa') for faixa in lista_de_faixas_data if faixa.get('id_faixa')]
        
        if not ids_a_verificar:
            print("Nenhum ID de faixa encontrado para verificação.")
            return []

      
        stmt = select(Faixa.id_faixa).where(Faixa.id_faixa.in_(ids_a_verificar))
        result = await db.execute(stmt)
        
        ids_existentes = set(result.scalars().all())
        
        num_existentes = len(ids_existentes)
        print(f"{num_existentes} faixas já existem e serão ignoradas.")

        faixas_a_inserir = [
            faixa_data 
            for faixa_data in lista_de_faixas_data
            if faixa_data.get('id_faixa') not in ids_existentes
        ]

        if not faixas_a_inserir:
            print("Todas as faixas já existem. Nenhuma inserção necessária.")
            return []


        objetos_faixa = [Faixa(**faixa_data) for faixa_data in faixas_a_inserir]
        db.add_all(objetos_faixa)
        await db.commit()
        
        print(f"Sucesso: {len(objetos_faixa)} novas faixas salvas.")
        return objetos_faixa

    except Exception as e:
       
        await db.rollback() 
        print("Erro ao tentar adicionar faixas em lote com validação:", e)
       
        raise