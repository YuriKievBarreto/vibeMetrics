from sqlalchemy.ext.asyncio import AsyncSession
from app.models.usuario_top_artista import UsuarioTopArtista
from app.models.artista import UnifiedArtist
from typing import Dict, List, Optional
from app.repositories.user_repository import ler_usuario_com_relacionamentos, ler_usuario
from app.repositories.artista_repository import get_artists_by_ids
from app.repositories.usuario_top_artista_repository import ler_usuario_top_artistas


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


def converter_artista_e_relacionamento_para_dict(rel) -> UnifiedArtist:
    return UnifiedArtist(
        nome_artista=rel.artista.nome_artista,
        link_imagem=rel.artista.link_imagem,
        short_rank=rel.short_time_rank,
        medium_rank=rel.medium_time_rank,
        long_rank=rel.long_time_rank,
        popularidade_artista=rel.artista.popularidade_artista,
        generos=rel.artista.generos
    )


async def obter_top_artistas_usuario(user_id: str) -> list[UnifiedArtist]:
    relacionamentos = await ler_usuario_top_artistas(user_id)
    print("rodando top artistas")

    return [converter_artista_e_relacionamento_para_dict(rel) for rel in relacionamentos]