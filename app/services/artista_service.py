from app.core.database import async_engine
from app.services.spotipy_service import get_top_artistas
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.artista import ArtistaCreate
from app.repositories.user_repository import atualizar_status
from app.repositories.artista_repository import salvar_artistas_em_batch
from app.services.usuario_top_artista_service import salvar_relacionamentos_top_artistas



async def salvar_top_artistas(user_id: str, access_token: str) -> None:
    async with AsyncSession(async_engine) as db:
        top_artistas = await get_top_artistas(access_token=access_token, quantitade=10, time_ranges=["short_term", "medium_term", "long_term"])
        
        rank_map = {}
        lista_artistas_para_adicionar = []

        for _, artista in top_artistas.artists.items():
            id_artista = artista.id_artista

            artista_create = ArtistaCreate(
                id_artista=id_artista,
                nome_artista=artista.nome_artista,
                popularidade_artista=artista.popularidade_artista,
                link_imagem=artista.link_imagem,
                generos=artista.generos,
            )

            lista_artistas_para_adicionar.append(artista_create)

            rank_map[id_artista] = {
                "short": artista.short_term_rank,
                "medium": artista.medium_term_rank,
                "long": artista.long_term_rank,
            }
            

        
        await salvar_artistas_em_batch(db, lista_artistas_para_adicionar)
        artistas_ids = list(top_artistas.artists.keys())
        await salvar_relacionamentos_top_artistas(db, user_id, artistas_ids, rank_map)

        await atualizar_status(user_id, "PRONTO")