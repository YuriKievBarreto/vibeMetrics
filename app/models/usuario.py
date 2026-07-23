from typing import List, Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import DateTime, JSON


class Usuario(SQLModel, table=True):
    __tablename__ = "usuario"

    id_usuario: str = Field(max_length=50, primary_key=True)
    nome_exibicao: str = Field(max_length=50)
    pais: str = Field(max_length=50)

    access_token: str = Field(max_length=512)
    refresh_token: str = Field(max_length=1024)
    token_expires_at: Optional[datetime] = Field(default=None, sa_type=DateTime(timezone=True))
    ultima_atualizacao: Optional[datetime] = Field(default=None, sa_type=DateTime(timezone=True))
    status_processamento: Optional[str] = Field(default=None, max_length=512)
    perfil_emocional: Optional[str] = Field(default=None, sa_type=JSON)

    top_artistas_rel: List["UsuarioTopArtista"] = Relationship(back_populates="usuario")
    top_faixas_rel: List["UsuarioTopFaixa"] = Relationship(back_populates="usuario")