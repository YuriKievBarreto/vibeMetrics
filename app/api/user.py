from fastapi import APIRouter, Depends
from starlette.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_current_active_user
from app.core.database import get_session
from app.models.gerais import LogoutResponse
from app.models.usuario import UserBasicData, PerfilMusical, Usuario
from app.models.usuario_top_faixa import TopFaixaResponse
from app.core.config import settings
from app.models.artista import UnifiedArtist
from app.services.user_service import (
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


@user_router.post("/logout", response_model=LogoutResponse)
async def logout():
    response = JSONResponse(content=LogoutResponse(message="Logout bem sucedido").model_dump())
    is_prod = settings.ENVIRONMENT in ("production", "prod")
    response.delete_cookie(
        key=SESSION_TOKEN_COOKIE_NAME,
        path="/",
        httponly=True,
        secure=is_prod,
        samesite="none" if is_prod else "lax"
    )
    return response


@user_router.get("/current_session_user_id")
async def get_user_id(
    current_user: Usuario = Depends(get_current_active_user)
) -> str:
    return current_user.id_usuario


@user_router.get("/get_user_basic_data", response_model=UserBasicData)
async def get_user_basic_data(
    current_user: Usuario = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session)
) -> UserBasicData:
    return await obter_dados_basicos_usuario(current_user.id_usuario, db)


@user_router.get("/top_musicas", response_model=TopFaixaResponse)
async def user_top_musicas(
    current_user: Usuario = Depends(get_current_active_user)
) -> TopFaixaResponse:
    return await obter_top_musicas_usuario(current_user.id_usuario)


@user_router.get("/top_artistas", response_model=list[UnifiedArtist])
async def user_top_artistas(
    current_user: Usuario = Depends(get_current_active_user)
) -> list[UnifiedArtist]:
    return await obter_top_artistas_usuario(current_user.id_usuario)


@user_router.get("/perfil_musical", response_model=PerfilMusical | str)
async def get_perfil_musical(
    current_user: Usuario = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session)
) -> PerfilMusical | str:
    return await obter_perfil_musical_usuario(current_user.id_usuario, db)