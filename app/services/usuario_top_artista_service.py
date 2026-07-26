from sqlalchemy.ext.asyncio import AsyncSession
from app.models.usuario_top_artista import UsuarioTopArtista
from typing import Dict, List, Optional
from app.repositories.user_repository import ler_usuario_com_relacionamentos, ler_usuario
from app.repositories.artista_repository import get_artists_by_ids


async def salvar_relacionamentos_top_artistas(
    db: AsyncSession, 
    user_id: str, 
    artista_ids: List[str], 
    rank_map: Dict[str, Dict[str, Optional[int]]]
):
    
    print("Preparando para criar associações...")

    usuario_atual = await ler_usuario_com_relacionamentos(db, user_id)
    
    if not usuario_atual:
        print(f"Erro: Usuário {user_id} não encontrado.")
        return

    artistas_orm_salvas = await get_artists_by_ids(db, artista_ids)
    artistas_map = {
        artista.id_artista: artista
        for artista in artistas_orm_salvas
    }

    usuario_atual.top_artistas_rel.clear()

    
    for artista_id in artista_ids:
        artista_orm = artistas_map.get(artista_id)
        ranks = rank_map.get(artista_id) 

        if artista_orm and ranks:
          
            ass = UsuarioTopArtista(
                id_artista=artista_id,
                id_usuario=user_id,
                artista=artista_orm, 
                short_time_rank=ranks["short"],
                medium_time_rank=ranks["medium"],
                long_time_rank=ranks["long"]
            )
            
            
            usuario_atual.top_artistas_rel.append(ass)
            
   
    num_relacionamentos_salvos = len(usuario_atual.top_artistas_rel)


  
    await db.commit() 
    
   
    print(f"Finalizado salvamento de {num_relacionamentos_salvos} relacionamentos com sucesso!")