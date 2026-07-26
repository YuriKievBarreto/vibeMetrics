from sqlmodel import SQLModel

class LogoutResponse(SQLModel):
    message: str


class SessionStatusResponse(SQLModel):
    message: str
    detail: str