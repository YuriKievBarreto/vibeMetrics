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

async def ler_usuario_top_faixas(id_usuario: str, quantidade: int=None) -> list[UsuarioTopFaixa]:
   async with AsyncSession(async_engine) as db:
      print("iniciando busca de relacionamentos")
      stmt = select(UsuarioTopFaixa).where(
         UsuarioTopFaixa.id_usuario == id_usuario
      ).options(
         joinedload(UsuarioTopFaixa.faixa) 
      ).order_by(
        UsuarioTopFaixa.short_time_rank.asc()
    ).limit(quantidade)
      
   result =  await db.execute(stmt)
   return list(result.scalars().all())