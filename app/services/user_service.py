from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import async_engine
from app.services.spotipy_service import get_current_user_details
from app.models.usuario import CurrentUserDetails
from app.models.usuario import UsuarioCreate
from datetime import datetime
from app.repositories.user_repository import criar_usuario


async def salvar_dados_iniciais_do_usuario(token_info: str):
    async with AsyncSession(async_engine) as db:

        user_details: CurrentUserDetails  = await get_current_user_details(token_info)
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
