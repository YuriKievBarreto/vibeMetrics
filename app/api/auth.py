from fastapi import APIRouter, Request, Depends, status, HTTPException
from app.core.spotipy_auth import sp_oauth_manager  
from starlette.responses import RedirectResponse
from spotipy import Spotify
from fastapi import BackgroundTasks
from app.services.data_ingestion_service import salvar_dados_iniciais_do_usuario, salvar_top_faixas, salvar_top_artistas
from app.core.security import create_access_token   
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.crud.user_crud import ler_usuario
from app.core.database import get_session
from app.core.database import async_engine
from app.api.user import valida_credenciais
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

DEFAULT_ADDRESS  = os.getenv("DEFAULT_ADDRESS")



auth_router = APIRouter(
    prefix="/auth",
    tags=["Autenticação"]
)


@auth_router.get("/login")
async def login_spotify():
    auth_url = sp_oauth_manager.get_authorize_url()
    return RedirectResponse(auth_url)

@auth_router.get("/callback")
async def spotify_callback(
    request: Request,
    background_tasks: BackgroundTasks
):
    code = request.query_params.get("code")
    if not code:
        raise HTTPException(status_code=400, detail="Código de autorização ausente")

    # Passo 1: Troca o código pelo token (Operação rápida)
    # Se sp_oauth_manager for síncrono, use asyncio.to_thread para não travar o loop
    token_info = await asyncio.to_thread(sp_oauth_manager.get_access_token, code)
    user_id = await get_user_id(token_info)
    access_token = token_info["access_token"]

    # Passo 2: Verifica existência do usuário (Rápido)
    usuario_bd = await ler_usuario(user_id=user_id)

    if usuario_bd is None:
        print("Usuário novo — Criando registro mínimo...")
        # Salva apenas o básico necessário para o login não falhar
        await salvar_dados_iniciais_do_usuario(token_info)
        
        # Passo 3: Workflow pesado em background (Não trava o return)
        background_tasks.add_task(workflow_ingestao_completa, user_id, access_token)
    else:
        print("Usuário já existe — Atualizando credenciais em background")
        # Também em background para o login ser instantâneo
        background_tasks.add_task(valida_credenciais, user_id) 

    # Passo 4: Gera o token de sessão da sua aplicação
    session_token = create_access_token(subject=user_id)

    # Passo 5: Resposta imediata ao navegador
    response = RedirectResponse(
        f"{DEFAULT_ADDRESS}/static/dashboard.html",
        status_code=status.HTTP_302_FOUND
    )

    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=False,
        samesite="Lax",
        max_age=43200 * 60,
        path="/"
    )

    return response




async def get_user_id(token_info):
    access_token = token_info['access_token']
    def _get_id_sync():
        sp = Spotify(auth=access_token)
        return sp.current_user()['id']

   
    user_id = await asyncio.to_thread(_get_id_sync)
    
    return user_id


async def workflow_ingestao_completa(user_id, access_token):
    async with AsyncSession(async_engine) as session:
        try:
            await salvar_top_faixas(user_id, access_token)
            await salvar_top_artistas(user_id, access_token)
        except Exception as e:
            await session.rollback()
            print(f"Erro no processamento: {e}")


