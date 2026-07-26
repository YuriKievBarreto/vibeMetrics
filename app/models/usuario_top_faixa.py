from typing import Optional
from sqlmodel import SQLModel, Field, Relationship
from app.models.faixa import UnifiedTrack


class UsuarioTopFaixa(SQLModel, table=True):
    __tablename__ = "usuario_top_faixa"

    id_usuario: str = Field(foreign_key="usuario.id_usuario", primary_key=True)
    id_faixa: str = Field(foreign_key="faixa.id_faixa", primary_key=True)

    short_time_rank: Optional[int] = Field(default=None)
    medium_time_rank: Optional[int] = Field(default=None)
    long_time_rank: Optional[int] = Field(default=None)

    usuario: "Usuario" = Relationship(back_populates="top_faixas_rel")
    faixa: "Faixa" = Relationship(back_populates="top_usuarios_rel")


class UsuarioTopFaixaCreate(SQLModel):
   
    id_usuario: str  
    id_faixa: str   
    short_time_rank: int
    medium_time_rank: int
    long_time_rank: int
    

class TopFaixaResponse(SQLModel):
    sentimento_predominante: str
    pontuacao_sentimento_predominante: float
    duracao_media_ms: float
    popularidade_media: float
    faixas: list[UnifiedTrack]