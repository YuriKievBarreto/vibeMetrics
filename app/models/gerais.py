from sqlmodel import SQLModel

class LogoutResponse(SQLModel):
    message: str