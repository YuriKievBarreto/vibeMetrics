from app.core.spotipy_auth import sp_oauth_manager
from spotipy import Spotify
from datetime import datetime, timezone, timedelta
import asyncio
import spotipy
from app.utils.general import contar_elementos
from app.models.usuario import CurrentUserDetails
from app.models.faixa import UnifiedTracksResponse, UnifiedTrack
from app.models.artista import UnifiedArtist, UnifiedArtistsResponse

async def autenticar_sp(access_token: str) -> Spotify:
    return Spotify(auth=access_token)



async def busca_informacoes_do_usuario(sp_client: spotipy.Spotify):
    return sp_client.current_user()



async def get_current_user_details(token_info) -> CurrentUserDetails:

    access_token = token_info['access_token']
    sp_autenticado =  await autenticar_sp(access_token)
    user_info = sp_autenticado.current_user()

   
    refresh_token = token_info.get('refresh_token')
    
    expires_in_seconds = token_info['expires_in']
    token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in_seconds)

    
    
    return CurrentUserDetails(
    id_usuario=user_info["id"],
    nome_exibicao=user_info["display_name"],
    pais=user_info["country"],
    access_token=access_token,
    refresh_token=refresh_token,
    token_expires_at=token_expires_at,
)




async def get_top_faixas(access_token: str, quantitade: int = 20, time_ranges: list = ["short_term"]) -> UnifiedTracksResponse:
    sp = await autenticar_sp(access_token)

    final_unified_tracks: dict[str, UnifiedTrack] = {} 

    for term in time_ranges:
        
    
        resultados =  sp.current_user_top_tracks(time_range=term, limit=quantitade)
        
        rank_key = f"{term}_rank" 
        
    
        for rank_index, item in enumerate(resultados.get("items", [])):
            track_id = item["id"]
            rank_value = rank_index + 1
            
            
            if track_id not in final_unified_tracks:
                
            
                album_images = item.get("album", {}).get("images", [])
                link_imagem = album_images[1]["url"] if len(album_images) > 1 else (album_images[0]["url"] if album_images else None)
                artists = item.get("artists", [])
                artista_principal = artists[0]["name"] if artists else "Desconhecido"

                track_data = UnifiedTrack(
                    id_faixa=track_id,
                    nome_faixa=item["name"],
                    link_imagem=link_imagem,
                    artista_principal=artista_principal,
                    popularidade=item["popularity"],
                    duracao_ms=item["duration_ms"],
                    album=item.get("album", {}).get("name", ""),
                )
                    
                final_unified_tracks[track_id] = track_data
            
        
            setattr(final_unified_tracks[track_id], rank_key, rank_value)

    return  UnifiedTracksResponse(tracks=final_unified_tracks)

    
    


async def get_top_artistas(
    access_token: str,
    quantitade: int = 20,
    time_ranges: list[str] = ["short_term"],
) -> UnifiedArtistsResponse:
    sp = await autenticar_sp(access_token)

    final_unified_artists: dict[str, UnifiedArtist] = {}

    for term in time_ranges:
        resultados = sp.current_user_top_artists(
            time_range=term,
            limit=quantitade,
        )

        rank_key = f"{term}_rank"

        for rank_index, item in enumerate(resultados.get("items", [])):
            artist_id = item["id"]
            rank_value = rank_index + 1

            if artist_id not in final_unified_artists:
                artist_images = item.get("images", [])
                link_imagem = (
                    artist_images[1]["url"]
                    if len(artist_images) > 1
                    else (artist_images[0]["url"] if artist_images else None)
                )

                final_unified_artists[artist_id] = UnifiedArtist(
                    id_artista=artist_id,
                    nome_artista=item["name"],
                    link_imagem=link_imagem,
                    generos=item["genres"],
                    popularidade_artista=item["popularity"],
                )

            setattr(final_unified_artists[artist_id], rank_key, rank_value)

    return UnifiedArtistsResponse(
        artists=final_unified_artists
    )



async def get_user_top_genres(access_token: str, quantidade: int = 50) -> dict[str, int]:
  
    lista_generos = []

    sp_client = await autenticar_sp(access_token)

    artistas = sp_client.current_user_top_artists(
                limit=quantidade, 
                time_range="short_term"
                )
        
    
    
    lista_generos = [genero for artista in artistas.get("items", []) for genero in artista.get("genres", [])]

    dict_contagem = await contar_elementos(lista_generos)

    return dict_contagem

