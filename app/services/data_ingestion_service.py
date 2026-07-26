from app.core.spotipy_auth import sp_oauth_manager
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta, timezone

async def refresh_and_get_access_token(db: AsyncSession, user_id: str, refresh_token: str) -> dict:
    new_token_info = await asyncio.to_thread(
    sp_oauth_manager.refresh_access_token, refresh_token
    )

    new_access_token = new_token_info['access_token']
    new_refresh_token=new_token_info.get('refresh_token', refresh_token)
    expires_in=new_token_info['expires_in']

    token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)


    return {
        "new_access_token":new_access_token,
        "new_refresh_token":new_refresh_token,
        "new_expires_at":token_expires_at
    }


  





    



  
    
