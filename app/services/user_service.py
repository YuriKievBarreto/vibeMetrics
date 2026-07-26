import asyncio
import json
from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import async_engine
from app.services.spotipy_service import (
    get_current_user_details,
    get_top_faixas,
    get_top_artistas,
    get_user_top_genres,
)
from app.services.data_ingestion_service import refresh_and_get_access_token
from app.services.emotion_extraction_service import (
    get_media_emocoes,
    get_perfil_emocional,
    get_analise_musica,
)
from app.repositories.user_repository import (
    criar_usuario,
    ler_usuario,
    get_basic_data,
    atualizar_credenciais_usuario,
    atualizar_perfil_emocional,
)
from app.repositories.usuario_top_faixa_repository import ler_usuario_top_faixas
from app.models.usuario import (
    CurrentUserDetails,
    UsuarioCreate,
    UserBasicData,
    PerfilMusical,
    Sentimento,
)
from app.models.faixa import FaixaEmocional


async def salvar_dados_iniciais_do_usuario(token_info: str):
    async with AsyncSession(async_engine) as db:

        user_details: CurrentUserDetails = await get_current_user_details(token_info)
        print(user_details.id_usuario)

        user_create_data = UsuarioCreate(
            id_usuario=user_details.id_usuario,
            nome_exibicao=user_details.nome_exibicao,
            pais=user_details.pais,
            access_token=user_details.access_token,
            refresh_token=user_details.refresh_token,
            token_expires_at=user_details.token_expires_at,
            ultima_atualizacao=datetime.now().date(),
            status_processamento="PROCESSANDO",
        )
        
        db_user = await criar_usuario(db, user_create_data)
        pass


async def validar_e_renovar_credenciais(spotify_user_id: str, db: AsyncSession | None = None) -> None:
    if db is None:
        async with AsyncSession(async_engine) as session:
            await _validar_e_renovar_credenciais_impl(spotify_user_id, session)
    else:
        await _validar_e_renovar_credenciais_impl(spotify_user_id, db)


async def _validar_e_renovar_credenciais_impl(spotify_user_id: str, db: AsyncSession) -> None:
    usuario = await ler_usuario(db, spotify_user_id)
    if not usuario:
        return

    current_time = datetime.now(timezone.utc)

    if current_time >= usuario.token_expires_at:
        print("token do usuario expirado, atualizando credenciais")

        credenciais = await refresh_and_get_access_token(
            db=db, user_id=usuario.id_usuario, refresh_token=usuario.refresh_token
        )
        
        await atualizar_credenciais_usuario(
            db,
            usuario.id_usuario,
            credenciais["new_access_token"],
            credenciais["new_refresh_token"],
            credenciais["new_expires_at"],
        )

    print("token não expirado")


async def obter_dados_basicos_usuario(
    spotify_user_id: str, db: AsyncSession
) -> UserBasicData:
    user_db = await ler_usuario(db, spotify_user_id)
    
    if not user_db:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    if user_db.status_processamento == "PROCESSANDO":
        print("Puxando basic data direto da API do Spotify (Real-time Fallback)")
        
        try:
            tarefas = [
                get_top_faixas(user_db.access_token, quantitade=1),
                get_top_artistas(user_db.access_token, quantitade=1),
                get_user_top_genres(user_db.access_token, quantidade=50),
            ]
            
            res_faixas, res_artistas, top_generos = await asyncio.gather(*tarefas)

            top_faixa = next(iter(res_faixas.tracks.values()), None)
            top_artista = next(iter(res_artistas.artists.values()), None)
            return UserBasicData(
                nome_exibicao=user_db.nome_exibicao,
                top_faixa=top_faixa,
                top_artista=top_artista,
                top_generos=top_generos,
            )
        except Exception as e:
            print(f"Erro ao buscar dados no Spotify: {e}")
            raise HTTPException(status_code=502, detail="Erro ao buscar dados no Spotify")
    else:
        print("Puxando dados otimizados do Banco de Dados")
        return await get_basic_data(spotify_user_id, user_db)


def _to_dict(obj):
    return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}


def _parse_analise(raw):
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except Exception:
            return {"citacao": "Não foi possível carregar o trecho.", "explicacao": raw}
    return {}


async def obter_perfil_musical_usuario(
    user_id: str, db: AsyncSession
) -> PerfilMusical | str:
    usuario_banco = await ler_usuario(db, user_id)
    
    if usuario_banco and usuario_banco.perfil_emocional:
        return usuario_banco.perfil_emocional

    usuario_top_faixas = await ler_usuario_top_faixas(user_id)
    if not usuario_top_faixas:
        raise HTTPException(status_code=404, detail="Dados musicais ainda não processados.")

    lista_emocoes = [rel.faixa.emocoes for rel in usuario_top_faixas]
    lista_faixas = [rel.faixa for rel in usuario_top_faixas]

    dict_media_emocoes = await get_media_emocoes(lista_emocoes)
    
    copia_media = dict_media_emocoes.copy()
    top1_nome = max(copia_media, key=copia_media.get)
    top1_intensidade = copia_media.pop(top1_nome)
    
    top2_nome = max(copia_media, key=copia_media.get)
    top2_intensidade = copia_media[top2_nome]

    faixa_top1 = max(lista_faixas, key=lambda f: (f.emocoes or {}).get(top1_nome, 0))
    faixa_top2 = max(lista_faixas, key=lambda f: (f.emocoes or {}).get(top2_nome, 0))

    tarefas_ia = [
        get_perfil_emocional(dict_media_emocoes),
        get_analise_musica(LETRA=faixa_top1.letra_faixa, EMOCAO=top1_nome),
        get_analise_musica(LETRA=faixa_top2.letra_faixa, EMOCAO=top2_nome),
    ]
    
    texto_perfil, analise_raw1, analise_raw2 = await asyncio.gather(*tarefas_ia)

    dict_faixa1 = _to_dict(faixa_top1)
    dict_faixa1.update({
        "emocao_mais_alta": (faixa_top1.emocoes or {}).get(top1_nome),
        "analise": _parse_analise(analise_raw1),
    })
    dict_faixa1.pop("emocoes", None)

    dict_faixa2 = _to_dict(faixa_top2)
    dict_faixa2.update({
        "emocao_mais_alta": (faixa_top2.emocoes or {}).get(top2_nome),
        "analise": _parse_analise(analise_raw2),
    })
    dict_faixa2.pop("emocoes", None)

    dict_resposta = PerfilMusical(
        top1_sentimento=Sentimento(
            nome=top1_nome,
            intensidade=top1_intensidade,
            faixa=FaixaEmocional(**dict_faixa1),
        ),
        top2_sentimento=Sentimento(
            nome=top2_nome,
            intensidade=top2_intensidade,
            faixa=FaixaEmocional(**dict_faixa2),
        ),
        texto_perfil_emocional=texto_perfil,
    )

    await atualizar_perfil_emocional(user_id, dict_resposta)
    return dict_resposta
