from sqlalchemy.ext.asyncio import AsyncSession
from app.models.usuario_top_faixa import UsuarioTopFaixa
from typing import Dict, List, Optional
from app.repositories.user_repository import ler_usuario_com_relacionamentos
from app.repositories.faixa_repository import get_faixas_by_ids


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