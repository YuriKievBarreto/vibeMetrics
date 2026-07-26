import asyncio
import os
from dotenv import load_dotenv
from spotipy import Spotify
from fastapi import BackgroundTasks, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import async_engine
from app.core.spotipy_auth import sp_oauth_manager
from app.core.security import create_access_token
from app.repositories.user_repository import ler_usuario
from app.services.user_service import salvar_dados_iniciais_do_usuario, validar_e_renovar_credenciais
from app.services.faixa_service import salvar_top_faixas
from app.services.artista_service import salvar_top_artistas

load_dotenv()

FRONTEND_ADDRESS = os.getenv("FRONTEND_ADDRESS")


def gerar_url_autenticacao_spotify() -> str:
    return sp_oauth_manager.get_authorize_url()


async def obter_spotify_user_id(token_info: dict) -> str:
    access_token = token_info["access_token"]

    def _get_id_sync():
        sp = Spotify(auth=access_token)
        return sp.current_user()["id"]

    return await asyncio.to_thread(_get_id_sync)


async def workflow_ingestao_completa(user_id: str, access_token: str):
    async with AsyncSession(async_engine) as session:
        try:
            await salvar_top_faixas(user_id, access_token)
            await salvar_top_artistas(user_id, access_token)
        except Exception as e:
            await session.rollback()
            print(f"Erro no processamento de ingestao em background: {e}")


async def processar_callback_autenticacao(
    code: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession,
) -> tuple[str, str]:
    if not code:
        raise HTTPException(status_code=400, detail="Código de autorização ausente")

    token_info = await asyncio.to_thread(sp_oauth_manager.get_access_token, code)
    user_id = await obter_spotify_user_id(token_info)
    access_token = token_info["access_token"]

    usuario_bd = await ler_usuario(db, user_id=user_id)

    if usuario_bd is None:
        print("Usuário novo — Criando registro mínimo...")
        await salvar_dados_iniciais_do_usuario(token_info)
        background_tasks.add_task(workflow_ingestao_completa, user_id, access_token)
    else:
        print("Usuário já existe — Atualizando credenciais em background")
        background_tasks.add_task(validar_e_renovar_credenciais, user_id)

    session_token = create_access_token(subject=user_id)
    frontend_address = os.getenv("FRONTEND_ADDRESS", "http://127.0.0.1:5501/frontend")
    frontend_base = frontend_address.strip().rstrip("/")
    redirect_url = f"{frontend_base}/dashboard.html"

    return session_token, redirect_url
