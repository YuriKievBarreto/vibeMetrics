import json
import numpy as np
import pandas as pd
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, List, Optional
from app.models.usuario_top_faixa import UsuarioTopFaixa, TopFaixaResponse
from app.models.faixa import UnifiedTrack
from app.repositories.user_repository import ler_usuario_com_relacionamentos
from app.repositories.faixa_repository import get_faixas_by_ids
from app.repositories.usuario_top_faixa_repository import ler_usuario_top_faixas


async def salvar_relacionamentos_top_faixas(
    db: AsyncSession, 
    user_id: str, 
    faixa_ids: List[str], 
    rank_map: Dict[str, Dict[str, Optional[int]]]
):
    
    print("Preparando para criar associações...")

    
    usuario_atual = await ler_usuario_com_relacionamentos(db, user_id)
    
    if not usuario_atual:
        print(f"Erro: Usuário {user_id} não encontrado.")
        return

  
    faixas_orm_salvas = await get_faixas_by_ids(db, faixa_ids)
    faixas_map = {faixa.id_faixa: faixa for faixa in faixas_orm_salvas}

    usuario_atual.top_faixas_rel.clear()

    
    for faixa_id in faixa_ids:
        faixa_orm = faixas_map.get(faixa_id)
        ranks = rank_map.get(faixa_id) 

        if faixa_orm and ranks:
          
            ass = UsuarioTopFaixa(
                id_usuario=user_id,
                id_faixa=faixa_id,
                faixa=faixa_orm, 
                short_time_rank=ranks["short"],
                medium_time_rank=ranks["medium"],
                long_time_rank=ranks["long"]
            )
            
            
            usuario_atual.top_faixas_rel.append(ass)
            
   
    num_relacionamentos_salvos = len(usuario_atual.top_faixas_rel)


  
    await db.commit() 
    
   
    print(f"Finalizado salvamento de {num_relacionamentos_salvos} relacionamentos com sucesso!")


def converter_faixa_e_relacionamento_para_obj(rel) -> UnifiedTrack:
    emo = rel.faixa.emocoes
    if isinstance(emo, str):
        try:
            emo: dict[str, float] = json.loads(emo)
        except Exception:
            pass
    return UnifiedTrack(
        id_faixa=rel.faixa.id_faixa,
        nome_faixa=rel.faixa.nome_faixa,
        album=rel.faixa.album,
        link_imagem=rel.faixa.link_imagem,
        emocoes=emo,
        duracao_ms=rel.faixa.duracao_ms,
        short_rank=rel.short_time_rank,
        medium_rank=rel.medium_time_rank,
        long_rank=rel.long_time_rank,
        popularidade=rel.faixa.popularidade,
        artista_principal=rel.faixa.artista_principal
    )


async def obter_top_musicas_usuario(user_id: str) -> TopFaixaResponse:
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

    return TopFaixaResponse(
        sentimento_predominante=sentimento_predominante,
        pontuacao_sentimento_predominante=pontuacao_predominante,
        duracao_media_ms=duracao_media,
        popularidade_media=popularidade_media,
        faixas=[converter_faixa_e_relacionamento_para_obj(rel) for rel in relacionamentos]
    )