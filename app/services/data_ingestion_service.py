from app.core.database import async_engine
from app.core.spotipy_auth import sp_oauth_manager
import spotipy
import asyncio
from spotipy import Spotify
from app.services.spotipy_service import get_top_faixas, get_top_artistas
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.schema_usuario import UsuarioCreate
from app.models.usuario_top_faixa import UsuarioTopFaixa
from app.models.usuario_top_artista import UsuarioTopArtista
from app.models.faixa import Faixa 
from app.models.usuario import Usuario
from app.models.artista import Artista #
from sqlalchemy import select 
from sqlalchemy.orm import selectinload, attributes 
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
# Importações de CRUD
from app.repositories.user_repository import criar_usuario, ler_usuario, atualizar_status
from app.repositories.artista_repository import salvar_artistas_em_batch
from app.repositories.faixa_repository import salvar_faixas_em_batch
from app.services.spotipy_service import get_current_user_details
from app.services.extracao_de_letras import buscar_letras_em_batch
from app.services.emotion_extraction_service import extrair_emocoes_batch_bedrock


async def refresh_and_get_access_token(db: AsyncSession, user_id: str, refresh_token: str) -> str:
    new_token_info = await asyncio.to_thread(
    sp_oauth_manager.refresh_access_token, refresh_token
    )

    new_access_token = new_token_info['access_token']
    # access_token=new_token_info['access_token']
    new_refresh_token=new_token_info.get('refresh_token', refresh_token)
    expires_in=new_token_info['expires_in']

    token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)


    return {
        "new_access_token":new_access_token,
        "new_refresh_token":new_refresh_token,
        "new_expires_at":token_expires_at
    }
      
    

async def busca_informacoes_do_usuario(sp_client: spotipy.Spotify):
    return sp_client.current_user()


async def salvar_dados_iniciais_do_usuario(token_info):
    async with AsyncSession(async_engine) as db:

        user_dict = await get_current_user_details(token_info)
        print("TESTANDO0:::::::")
        print(user_dict["id_usuario"])


        user_create_data = UsuarioCreate(
            id_usuario = user_dict["id_usuario"],
            nome_exibicao = user_dict["nome_exibicao"],
            pais = user_dict["pais"],
            access_token = user_dict["access_token"],
            refresh_token = user_dict["refresh_token"],
            token_expires_at = user_dict["token_expires_at"],
            ultima_atualizacao = datetime.now().date(),
            status_processamento = "PROCESSANDO"
        )

        
        user_data_dict = user_create_data.model_dump()
        db_user = await criar_usuario(db, user_data_dict)

        

        pass



async def salvar_relacionamentos_top_faixas(
    db: AsyncSession, 
    user_id: str, 
    faixa_ids: List[str], 
    rank_map: Dict[str, Dict[str, Optional[int]]]
):
    
    print("Preparando para criar associações...")

    
    stmt_user = select(Usuario).where(Usuario.id_usuario == user_id).options(
        selectinload(Usuario.top_faixas_rel)
    )
    usuario_atual = await db.scalar(stmt_user)
    
    if not usuario_atual:
        print(f"Erro: Usuário {user_id} não encontrado.")
        return

  
    stmt_faixas = select(Faixa).where(Faixa.id_faixa.in_(faixa_ids))
    result = await db.execute(stmt_faixas)
    faixas_orm_salvas = result.scalars().all()
    faixas_map = {faixa.id_faixa: faixa for faixa in faixas_orm_salvas}

   
    usuario_atual.top_faixas_rel.clear() 

    
    for faixa_id in faixa_ids:
        faixa_orm = faixas_map.get(faixa_id)
        ranks = rank_map.get(faixa_id) 

        if faixa_orm and ranks:
          
            ass = UsuarioTopFaixa(
                faixa=faixa_orm, 
                short_time_rank=ranks["short"],
                medium_time_rank=ranks["medium"],
                long_time_rank=ranks["long"]
            )
            
            
            usuario_atual.top_faixas_rel.append(ass)
            
   
    num_relacionamentos_salvos = len(usuario_atual.top_faixas_rel)


  
    await db.commit() 
    
   
    print(f"Finalizado salvamento de {num_relacionamentos_salvos} relacionamentos com sucesso!")
  

async def salvar_top_faixas(user_id:str, access_token:str):
    print("iniciando salvamento de top faixas do usuario no bancon de dados")

    async with AsyncSession(async_engine) as db:
     
        print("puxando top 10 faixas de todos os periodos de tempo")
        top_faixas = await get_top_faixas(access_token, quantitade=10, time_ranges=["short_term", "medium_term", "long_term"])
        
        top_faixas_unicas = {}
        tuplas_vistas = set()

        for id_faixa, faixa_dados in top_faixas.items():
            chave_de_unicidade = (faixa_dados["artista_principal"], faixa_dados["nome_faixa"])
 
            if chave_de_unicidade not in tuplas_vistas:
                tuplas_vistas.add(chave_de_unicidade)
                top_faixas_unicas[id_faixa] = faixa_dados

        
        print("--------------------------")
        lista_musicas = [(faixa["artista_principal"], faixa["nome_faixa"]) 
        for faixa in top_faixas_unicas.values()]

      
        
        
        
        print("extraindo letras de musicas")
        letras_musicas = await buscar_letras_em_batch(lista_musicas)

        print("TAMANHO", len(letras_musicas))

        for i, (chave, dados_faixa) in enumerate(top_faixas_unicas.items()):
            if letras_musicas[i]["letra"] is None:
               dados_faixa["letra"] = letras_musicas[i]["letra"]
               
            else:
                dados_faixa["letra"] = letras_musicas[i]["letra"]

        
        
        print("extraindo emocoes")
        faixas_com_letra = [faixa for faixa in top_faixas_unicas.values() if faixa["letra"] is not None]
        lista_letras = [faixa["letra"] for faixa in faixas_com_letra]

        if lista_letras:
            lista_emocoes = await extrair_emocoes_batch_bedrock(lista_letras, chunk_size=5)
            for faixa, emocoes in zip(faixas_com_letra, lista_emocoes):
                faixa["emocoes"] = emocoes

        for faixa in top_faixas_unicas.values():
            if "emocoes" not in faixa:
                faixa["emocoes"] = None

        
        
        
        rank_map = {} 
        
       
        lista_faixas_para_adicionar = []

        for i, (chave, valor_faixa) in enumerate(top_faixas_unicas.items()):
            faixa_id = valor_faixa["id_faixa"]
            
           
            faixa_dict = {
                "id_faixa": faixa_id,
                "nome_faixa": valor_faixa["nome_faixa"],
                "emocoes": valor_faixa["emocoes"],
                "duracao_ms": valor_faixa["duracao_ms"],
                "popularidade": valor_faixa["popularidade"],
                "album": valor_faixa["album"],
                "link_imagem": valor_faixa["link_imagem"],
                "letra_faixa": valor_faixa["letra"],
                "artista_principal": valor_faixa["artista_principal"]
            }

            lista_faixas_para_adicionar.append(faixa_dict)
            
           
            rank_map[faixa_id] = {
                "short": valor_faixa.get("short_term_rank"), 
                "medium": valor_faixa.get("medium_term_rank"), 
                "long": valor_faixa.get("long_term_rank")
            }
            
        print("salvando/atualizando faixas no banco de dados (Passo 1/2)")
      
        await salvar_faixas_em_batch(db, lista_faixas_para_adicionar)

        
       
        faixa_ids = list(top_faixas_unicas.keys())
        await salvar_relacionamentos_top_faixas(db, user_id, faixa_ids, rank_map)



async def salvar_top_artistas(user_id: str, access_token: str):
    async with AsyncSession(async_engine) as db:
        top_artistas = await get_top_artistas(access_token=access_token, quantitade=10, time_ranges=["short_term", "medium_term", "long_term"])
        
        rank_map = {} 
        lista_artistas_para_adicionar = []
        for chave, valor in top_artistas.items():
            id_artista = valor["id_artista"]
            dict_artista = {
                "id_artista": id_artista,
                "nome_artista": valor["nome_artista"],
                "popularidade_artista": valor["popularidade_artista"],
                "link_imagem": valor["link_imagem"],
                "generos": valor["generos"]
            }

            lista_artistas_para_adicionar.append(dict_artista)

            rank_map[id_artista] = {
            "short": valor.get("short_term_rank"), 
            "medium": valor.get("medium_term_rank"), 
            "long": valor.get("long_term_rank")
        }
            

        
        await salvar_artistas_em_batch(db, lista_artistas_para_adicionar)
        artistas_ids = list(top_artistas.keys())
        await salvar_relacionamentos_top_artistas(db, user_id, artistas_ids, rank_map)

        await atualizar_status(user_id, "PRONTO")


    


async def salvar_relacionamentos_top_artistas(
    db: AsyncSession, 
    user_id: str, 
    artista_ids: List[str], 
    rank_map: Dict[str, Dict[str, Optional[int]]]
):
    
    print("Preparando para criar associações...")

    
    stmt_user = select(Usuario).where(Usuario.id_usuario == user_id).options(
        selectinload(Usuario.top_artistas_rel)
    )
    usuario_atual = await db.scalar(stmt_user)
    
    if not usuario_atual:
        print(f"Erro: Usuário {user_id} não encontrado.")
        return

  
    stmt_artistas = select(Artista).where(Artista.id_artista.in_(artista_ids))
    result = await db.execute(stmt_artistas)
    artistas_orm_salvas = result.scalars().all()
    artistas_map = {artista.id_artista: artista for artista in artistas_orm_salvas}

   
    usuario_atual.top_artistas_rel.clear() 

    
    for artista_id in artista_ids:
        artista_orm = artistas_map.get(artista_id)
        ranks = rank_map.get(artista_id) 

        if artista_orm and ranks:
          
            ass = UsuarioTopArtista(
                artista=artista_orm, 
                short_time_rank=ranks["short"],
                medium_time_rank=ranks["medium"],
                long_time_rank=ranks["long"]
            )
            
            
            usuario_atual.top_artistas_rel.append(ass)
            
   
    num_relacionamentos_salvos = len(usuario_atual.top_artistas_rel)


  
    await db.commit() 
    
   
    print(f"Finalizado salvamento de {num_relacionamentos_salvos} relacionamentos com sucesso!")
  
    
