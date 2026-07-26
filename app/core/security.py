from datetime import datetime, timedelta, timezone
from typing import Any
from jose import jwt, JWTError
from app.core.config import settings

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM


def create_access_token(subject: str | Any, 
    expires_delta: timedelta | None = None) -> str:
    

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=43200) 

   
    to_encode = {"exp": expire, "sub": str(subject)} 

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")

        if user_id is None:
            return None
    
        return user_id
    
    except JWTError:
       
        return None