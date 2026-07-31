from fastapi import Depends, HTTPException, Cookie, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import decode_access_token
from app.core.database import get_session
from app.repositories.user_repository import ler_usuario
from app.services.user_service import validar_e_renovar_credenciais
from app.models.usuario import Usuario

async def get_current_user_id(
    session_token: str | None = Cookie(default=None)
) -> str:

    if not session_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Não autenticado. Cookie de sessão ausente."
        )

    token_decodificado = decode_access_token(session_token)
    if not token_decodificado:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sessão inválida ou expirada. Faça login novamente."
        )

    return token_decodificado


async def get_current_active_user(
    spotify_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_session)
) -> Usuario:
    usuario = await ler_usuario(db, spotify_user_id)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado no banco de dados. Faça login novamente."
        )

    await validar_e_renovar_credenciais(spotify_user_id, db)
    await db.refresh(usuario)
    return usuario

  