from app.schemas.schema_usuario import UsuarioCreate
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.usuario import Usuario  
from datetime import datetime
from app.core.database import async_engine
from app.services.crud.relacionamentos_crud import ler_usuario_top_faixas, ler_usuario_top_artistas
from app.utils.general import contar_elementos
from sqlalchemy import update
from sqlalchemy.exc import SQLAlchemyError
import asyncio


async def criar_usuario(db: AsyncSession, user_data_dict):

    print("iniciandi criacao de usuaroi")


    try:
        db_user = Usuario(**user_data_dict)
        db.add(db_user)
        await db.commit()

        return db_user

    except Exception as e:

        print("erro ao tenta adicionar usuario:" , e)



async def atualizar_credenciais_usuario(db: AsyncSession, 
                                        user_id: str,
                                        new_access_token: str,
                                        new_refresh_token: str,
                                        new_expires_at: datetime):
    

    print("iniciando atualização de credenciais do usuario")
    try:
        db_user = await db.get(Usuario, user_id)

        if db_user is None:
            print("Usuario de id {user_id} não encontrado para atualização de credenciais")
            return None
        
        db_user.access_token = new_access_token
        db_user.refresh_token = new_refresh_token
        db_user.token_expires_at = new_expires_at

        db.add(db_user)

        await db.commit()

        print("credenciais do usuario atualizadas com sucesso")

        return db_user

    except Exception as e:
        print("erro ao atualizar credenciais do usuario: ", e)
        raise e
    

async def ler_usuario(user_id:str):
   async with AsyncSession(async_engine) as db:
        try:
            db_user = await db.get(Usuario, user_id)

            if db_user is None:
                print("Usuario de id {user_id} não encontrado")
                return None
            
            print("usuario encontrado")
            return db_user
    
        except Exception as e:
            raise e 
        


async def get_basic_data(spotify_user_id: str, user_db):
    print(f"Buscando insights para o usuário: {spotify_user_id}")
    try:
        tarefas = [
            ler_usuario_top_faixas(spotify_user_id, quantidade=1),
            ler_usuario_top_artistas(spotify_user_id, quantidade=1),
            ler_usuario_top_artistas(spotify_user_id, quantidade=20)
        ]
        
        
        res_faixa_1, res_artista_1, res_artistas_20 = await asyncio.gather(*tarefas)

        top_faixa = res_faixa_1[0].faixa if res_faixa_1 else None
        top_artista = res_artista_1[0].artista if res_artista_1 else None

        
        top_generos = []
        if res_artistas_20:
            generos_brutos = [gen for art in res_artistas_20 for gen in art.artista.generos]
            top_generos = await contar_elementos(generos_brutos)

        return {
            "nome_exibicao": user_db.nome_exibicao,
            "top_faixa": top_faixa,
            "top_artista": top_artista,
            "top_generos": top_generos
        }
    
    except Exception as e:
        print(f"Erro ao compilar dados básicos: {e}")
        raise e
      

async def atualizar_status(spotify_user_id: str, status: str):
    async with AsyncSession(async_engine) as db:
        print(f"tentanto atualizar  status do usuario para : {status}")

        try:
            consulta = select(Usuario).where(Usuario.id_usuario == spotify_user_id)
            resultado = await db.execute(consulta)
        
        
            usuario_db = resultado.scalar_one_or_none() 

            if usuario_db:
                usuario_db.status_processamento = status
                db.add(usuario_db)
                await db.commit()
                
                return usuario_db
            else:
                print(f"Usuário {spotify_user_id} não encontrado.")
                return None
            
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Erro ao atualizar status: {e}")
            raise e
        



async def atualizar_perfil_emocional(id_usuario: str, json_perfil: dict):
     async with AsyncSession(async_engine) as db:
        try:
            print("atualizando perfil emocional do usuário")
            stmt = (
            update(Usuario)
            .where(Usuario.id_usuario == id_usuario)
            .values(perfil_emocional=json_perfil)
        )
        
            await db.execute(stmt)
            await db.commit()

        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Erro de banco de dados ao atualizar perfil: {e}")
          
            raise ValueError("Falha técnica ao salvar análise emocional no banco.")
            
        except Exception as e:
            await db.rollback()
            print(f"Erro inesperado: {e}")
            raise e
    
