from fastapi import APIRouter, Depends
from starlette.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_current_user_id
from app.core.database import get_session
from app.models.gerais import LogoutResponse, SessionStatusResponse
from app.models.usuario import UserBasicData, PerfilMusical
from app.models.usuario_top_faixa import TopFaixaResponse
from app.models.artista import UnifiedArtist
from app.services.user_service import (
    validar_e_renovar_credenciais,
    obter_dados_basicos_usuario,
    obter_perfil_musical_usuario,
)
from app.services.usuario_top_faixa_service import obter_top_musicas_usuario
from app.services.usuario_top_artista_service import obter_top_artistas_usuario

SESSION_TOKEN_COOKIE_NAME = "session_token"

user_router = APIRouter(
    prefix="/user",
    tags=["user"]
)


@user_router.get("/me", response_model=SessionStatusResponse)
async def me(
    spotify_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_session)
) -> dict[str, str]:
    await validar_e_renovar_credenciais(spotify_user_id, db)
    return {
        "message": "logado",
        "detail": "Sessão JWT validada e ativa."
    }


@user_router.post("/logout", response_model=LogoutResponse)
async def logout():
    response = JSONResponse(content=LogoutResponse(message="Logout bem sucedido").model_dump())
    response.delete_cookie(key=SESSION_TOKEN_COOKIE_NAME, path="/")
    return response


@user_router.get("/current_session_user_id")
async def get_user_id(
    spotify_user_id: str = Depends(get_current_user_id)
) -> str:
    return spotify_user_id


@user_router.get("/get_user_basic_data", response_model=UserBasicData)
async def get_user_basic_data(
    spotify_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_session)
) -> UserBasicData:
    return await obter_dados_basicos_usuario(spotify_user_id, db)


@user_router.get("/top_musicas", response_model=TopFaixaResponse)
async def user_top_musicas(
    user_id: str = Depends(get_current_user_id)
) -> TopFaixaResponse:
    return await obter_top_musicas_usuario(user_id)


@user_router.get("/top_artistas", response_model=list[UnifiedArtist])
async def user_top_artistas(
    user_id: str = Depends(get_current_user_id)
) -> list[UnifiedArtist]:
    return await obter_top_artistas_usuario(user_id)


@user_router.get("/perfil_musical", response_model=PerfilMusical | str)
async def get_perfil_musical(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_session)
) -> PerfilMusical | str:
    return await obter_perfil_musical_usuario(user_id, db)