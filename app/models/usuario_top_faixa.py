from typing import Optional
from sqlmodel import SQLModel, Field, Relationship


class UsuarioTopFaixa(SQLModel, table=True):
    __tablename__ = "usuario_top_faixa"

    id_usuario: str = Field(foreign_key="usuario.id_usuario", primary_key=True)
    id_faixa: str = Field(foreign_key="faixa.id_faixa", primary_key=True)

    short_time_rank: Optional[int] = Field(default=None)
    medium_time_rank: Optional[int] = Field(default=None)
    long_time_rank: Optional[int] = Field(default=None)

    usuario: "Usuario" = Relationship(back_populates="top_faixas_rel")
    faixa: "Faixa" = Relationship(back_populates="top_usuarios_rel")