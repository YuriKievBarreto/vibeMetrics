from typing import List, Optional, Any
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import DateTime, JSON
from app.models.usuario_top_artista import UsuarioTopArtista
from app.models.artista import Artista
from app.models.usuario_top_faixa import UsuarioTopFaixa
from app.models.faixa import Faixa
from datetime import datetime


class Usuario(SQLModel, table=True):
    __tablename__ = "usuario"

    id_usuario: str = Field(max_length=50, primary_key=True)
    nome_exibicao: str = Field(max_length=50)
    pais: str = Field(max_length=50)

    access_token: str = Field(max_length=512)
    refresh_token: str = Field(max_length=1024)
    token_expires_at: Optional[datetime] = Field(default=None, sa_type=DateTime(timezone=True))
    ultima_atualizacao: Optional[datetime] = Field(default_factory=datetime.now().date(), sa_type=DateTime(timezone=True))
    status_processamento: Optional[str] = Field(default=None, max_length=512)
    perfil_emocional: Optional[str] = Field(default=None, sa_type=JSON)

    top_artistas_rel: List["UsuarioTopArtista"] = Relationship(back_populates="usuario")
    top_faixas_rel: List["UsuarioTopFaixa"] = Relationship(back_populates="usuario")



class UsuarioCreate(SQLModel):
    id_usuario: str
    nome_exibicao: str
    pais: str
    
  
    access_token: str
    refresh_token: str
    token_expires_at: datetime 

    ultima_atualizacao: datetime
    status_processamento: str

    perfil_emocional: Optional[Any] = None


class UserBasicData(SQLModel):
    nome_exibicao: str
    top_faixa: Faixa
    top_artista: Artista
    top_generos: dict[str, int]


class CurrentUserDetails(SQLModel):
    id_usuario: str
    nome_exibicao: str
    pais: str
    access_token: str
    refresh_token: str
    token_expires_at: datetime  