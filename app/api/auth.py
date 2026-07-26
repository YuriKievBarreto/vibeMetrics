from fastapi import APIRouter, Request, Depends, status, BackgroundTasks
from starlette.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_session
from app.services.auth_service import (
    gerar_url_autenticacao_spotify,
    processar_callback_autenticacao,
)

auth_router = APIRouter(
    prefix="/auth",
    tags=["Autenticação"]
)


@auth_router.get("/login", response_class=RedirectResponse)
async def login_spotify() -> RedirectResponse:
    auth_url = gerar_url_autenticacao_spotify()
    return RedirectResponse(auth_url)


@auth_router.get("/callback", response_class=RedirectResponse)
async def spotify_callback(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_session)
) -> RedirectResponse:
    code = request.query_params.get("code")
    session_token, redirect_url = await processar_callback_autenticacao(
        code, background_tasks, db
    )

    response = RedirectResponse(
        redirect_url,
        status_code=status.HTTP_302_FOUND
    )

    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=43200 * 60,
        path="/"
    )

    return response
