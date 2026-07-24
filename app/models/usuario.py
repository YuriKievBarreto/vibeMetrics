from typing import List, Optional, Any
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


"""class UserBasicData(SQLModel):
    "nome_exibicao": user_db.nome_exibicao,
    "top_faixa": top_faixa,
    "top_artista": top_artista,
    "top_generos": top_generos"""