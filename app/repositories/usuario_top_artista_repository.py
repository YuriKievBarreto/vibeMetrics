from app.models.faixa import FaixaCreate
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import async_engine
from app.models.usuario_top_faixa import UsuarioTopFaixa
from app.models.usuario_top_artista import UsuarioTopArtista
from app.models.faixa import Faixa  
from sqlalchemy.orm import joinedload
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from typing import Type, List, Dict



async def ler_usuario_top_artistas(id_usuario: str, quantidade:str=None):
   async with AsyncSession(async_engine) as db:
      print("iniciando busca de relacionamentos")
      stmt = select(UsuarioTopArtista).where(
         UsuarioTopArtista.id_usuario == id_usuario
      ).options(
         joinedload(UsuarioTopArtista.artista) 
      ).order_by(
        UsuarioTopArtista.short_time_rank.asc()
    ).limit(quantidade)
      
   result =  await db.execute(stmt)
   return result.scalars().all()







