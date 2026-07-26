from fastapi import Depends, HTTPException, Cookie, status
from app.core.security import decode_access_token

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
  