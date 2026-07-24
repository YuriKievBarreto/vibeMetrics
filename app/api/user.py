from fastapi import APIRouter, Request, Depends, HTTPException, status
from starlette.responses import  JSONResponse
from app.core.dependencies import get_current_user_id
from app.services.data_ingestion_service import refresh_and_get_access_token
from app.repositories.user_repository import atualizar_credenciais_usuario, ler_usuario
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_session
from datetime import datetime, timezone
from app.repositories.user_repository import ler_usuario, get_basic_data, atualizar_perfil_emocional
from app.services.spotipy_service import get_top_faixas, get_top_artistas, get_user_top_genres
from app.repositories.usuario_top_faixa_repository import ler_usuario_top_faixas
from app.repositories.usuario_top_artista_repository import ler_usuario_top_artistas
from app.services.emotion_extraction_service import get_media_emocoes, get_perfil_emocional, get_analise_musica
import asyncio
import json


import numpy as np
import json
import pandas as pd

SESSION_TOKEN_COOKIE_NAME = "session_token"

user_router = APIRouter(
    prefix="/user",
    tags=["user"]
)

@user_router.get("/me")
async def me(
     spotify_user_id: str = Depends(get_current_user_id),
     db: AsyncSession = Depends(get_session)
):  
    await valida_credenciais(spotify_user_id, db)

    return {"message": "logado",
            "detail": "Sessão JWT validada e ativa."}


@user_router.post("/logout")
async def logout(): 
    response = JSONResponse(content={"message": "Logout bem sucedido"})

    response.set_cookie(
        key="session_token",
        httponly=True,
        secure=False,  # só porque é localhost
        samesite="Lax",
        max_age=43200 * 60,
        path="/"
    )

    return response

@user_router.get("/current_session_user_id")
async def get_user_id(
    spotify_user_id: str = Depends(get_current_user_id),
     db: AsyncSession = Depends(get_session)):
    
    return spotify_user_id


import asyncio
from fastapi import Depends, HTTPException

@user_router.get("/get_user_basic_data")
async def get_user_basic_data(
    spotify_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_session)
):
   
    user_db = await ler_usuario(spotify_user_id)
    
    if not user_db:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    
    if user_db.status_processamento == "PROCESSANDO":
        print("Puxando basic data direto da API do Spotify (Real-time Fallback)")
        
        try:
            
            tarefas = [
                get_top_faixas(user_db.access_token, quantitade=1),
                get_top_artistas(user_db.access_token, quantitade=1),
                get_user_top_genres(user_db.access_token, quantidade=50)
            ]
            
            res_faixas, res_artistas, top_generos = await asyncio.gather(*tarefas)

            
            top_faixa = list(res_faixas.values())[0] if res_faixas else None
            top_artista = list(res_artistas.values())[0] if res_artistas else None

            return {
                "nome_exibicao": user_db.nome_exibicao,
                "top_faixa": top_faixa,
                "top_artista": top_artista,
                "top_generos": top_generos
            }
        except Exception as e:
            print(f"Erro ao buscar dados no Spotify: {e}")
            raise HTTPException(status_code=502, detail="Erro ao buscar dados no Spotify")

  
    else:
        print("Puxando dados otimizados do Banco de Dados")
        return await get_basic_data(spotify_user_id, user_db)
    



async def valida_credenciais(spotify_user_id: str, db: AsyncSession):
    usuario = await ler_usuario(user_id=spotify_user_id)
    current_time = datetime.now(timezone.utc)

    if current_time >= usuario.token_expires_at:
        print("token do usuario expirado, atualizando credenciais")

        credenciais = await refresh_and_get_access_token(db=db, user_id=usuario.id_usuario, refresh_token=usuario.refresh_token)
        
        await atualizar_credenciais_usuario(db, usuario.id_usuario,
                                        credenciais["new_access_token"],
                                        credenciais["new_refresh_token"],
                                        credenciais["new_expires_at"])

    print("token não expirado")


@user_router.get("/top_musicas")
async def user_top_musicas(user_id: str = Depends(get_current_user_id)):
    
    relacionamentos = await ler_usuario_top_faixas(user_id)
    
    if not relacionamentos:
        raise HTTPException(status_code=404, detail="Nenhuma música encontrada para este usuário.")

  
    lista_emocoes_validas = []
    for rel in relacionamentos:
        emo = rel.faixa.emocoes
        if isinstance(emo, str):
            try:
                emo = json.loads(emo)
            except Exception:
                emo = None
        if isinstance(emo, dict):
            lista_emocoes_validas.append(emo)

    duracoes = np.array([rel.faixa.duracao_ms for rel in relacionamentos if rel.faixa.duracao_ms is not None])
    popularidades = np.array([rel.faixa.popularidade for rel in relacionamentos if rel.faixa.popularidade is not None])

    if lista_emocoes_validas:
        df_emocoes = pd.DataFrame(lista_emocoes_validas)
        medias_series = df_emocoes.mean(numeric_only=True).round(2)
        if not medias_series.empty and not medias_series.isna().all():
            sentimento_predominante = str(medias_series.idxmax())
            pontuacao_predominante = float(medias_series.max())
        else:
            sentimento_predominante = "Nenhum"
            pontuacao_predominante = 0.0
    else:
        sentimento_predominante = "Nenhum"
        pontuacao_predominante = 0.0

    duracao_media = int(np.round(duracoes.mean(), 0)) if len(duracoes) > 0 else 0
    popularidade_media = float(np.round(popularidades.mean(), 0)) if len(popularidades) > 0 else 0.0

    dict_resposta = {
        "sentimento_predominante": sentimento_predominante,
        "pontuacao_sentimento_predominante": pontuacao_predominante,
        "duracao_media_ms": duracao_media,
        "popularidade_media": popularidade_media,
        "faixas": [converter_faixa_e_relacionamento_para_dict(rel) for rel in relacionamentos]
    }

    return dict_resposta




def converter_faixa_e_relacionamento_para_dict(rel):
    emo = rel.faixa.emocoes
    if isinstance(emo, str):
        try:
            emo = json.loads(emo)
        except Exception:
            pass
    return {
        "nome_faixa": rel.faixa.nome_faixa,
        "album": rel.faixa.album,
        "link_imagem": rel.faixa.link_imagem,
        "emocoes": emo,
        "duracao_ms": rel.faixa.duracao_ms,
        "short_rank": rel.short_time_rank,
        "medium_rank": rel.medium_time_rank,
        "long_rank": rel.long_time_rank,
        "popularidade": rel.faixa.popularidade,
        "artista_principal": rel.faixa.artista_principal
    }

@user_router.get("/top_artistas")
async def user_top_artistas( user_id: str = Depends(get_current_user_id)):

    relacoinamentos = await ler_usuario_top_artistas(user_id)
    print("rodando top artistas")

    
    dict_resposta =  [converter_artista_e_relacionamento_para_dict(rel) for rel in relacoinamentos]
    
    return dict_resposta



def converter_artista_e_relacionamento_para_dict(rel):
    return {
        "nome_artista": rel.artista.nome_artista,
        "link_imagem": rel.artista.link_imagem,
        "short_rank": rel.short_time_rank,
        "medium_rank": rel.medium_time_rank,
        "long_rank": rel.long_time_rank,
        "popularidade_artista": rel.artista.popularidade_artista,
        "generos": rel.artista.generos
    }



@user_router.get("/perfil_musical")
async def get_perfil_musical(user_id: str = Depends(get_current_user_id)):
    usuario_banco = await ler_usuario(user_id)
    
    
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
        get_analise_musica(LETRA=faixa_top2.letra_faixa, EMOCAO=top2_nome)
    ]
    
    texto_perfil, analise_raw1, analise_raw2 = await asyncio.gather(*tarefas_ia)

   
    def parse_analise(raw):
        if isinstance(raw, dict):
            return raw
        if isinstance(raw, str):
            try:
                return json.loads(raw)
            except Exception:
                return {"citacao": "Não foi possível carregar o trecho.", "explicacao": raw}
        return {}

    dict_faixa1 = to_dict(faixa_top1)
    dict_faixa1.update({
        "emocao_mais_alta": (faixa_top1.emocoes or {}).get(top1_nome),
        "analise": parse_analise(analise_raw1)
    })
    dict_faixa1.pop("emocoes", None)

    dict_faixa2 = to_dict(faixa_top2)
    dict_faixa2.update({
        "emocao_mais_alta": (faixa_top2.emocoes or {}).get(top2_nome),
        "analise": parse_analise(analise_raw2)
    })
    dict_faixa2.pop("emocoes", None)

    dict_resposta = {
        "top1_sentimento": {"nome": top1_nome, "intensidade": top1_intensidade, "faixa": dict_faixa1},
        "top2_sentimento": {"nome": top2_nome, "intensidade": top2_intensidade, "faixa": dict_faixa2},
        "texto_perfil_emocional": texto_perfil
    }

  
    await atualizar_perfil_emocional(user_id, dict_resposta)
    return dict_resposta

    


def to_dict(obj):
    return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}