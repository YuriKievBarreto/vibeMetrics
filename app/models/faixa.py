from sqlalchemy import String, JSON, Integer, Text
from sqlalchemy.orm import  Mapped, mapped_column, relationship
from sqlmodel import SQLModel, Field, Relationship
from typing import List, Optional, Dict, Any
import uuid





class Faixa(SQLModel, table=True):
    __tablename__ = "faixa"
    id_faixa: str = Field(primary_key=True, max_length=50)
    nome_faixa: str = Field(max_length=255)
    emocoes: Optional[str] = Field(default=None, sa_type=JSON)
    duracao_ms: int
    popularidade: int
    album: str = Field(max_length=255)
    link_imagem: str = Field(max_length=255)
    letra_faixa: Optional[str] = Field(default=None, sa_type=Text)
    artista_principal: str = Field(max_length=255)

    top_usuarios_rel: List["UsuarioTopFaixa"] = Relationship(back_populates="faixa")



class FaixaCreate(SQLModel):
    
    id_faixa: str 
    nome_faixa: str 
    emocoes: Optional[Dict[str, float]] = None
    album: str  
    popularidade: int 
    duracao_ms: int 
    link_imagem: str 
    letra_faixa:  str | None
    artista_principal: str 

    class Config:
        populate_by_name = True 
        extra = 'ignore'


class UnifiedTrack(SQLModel):
    id_faixa: str
    nome_faixa: str
    link_imagem: Optional[str] = None
    artista_principal: str
    popularidade: int
    duracao_ms: int
    album: str

    letra: Optional[str] = None
    emocoes: Optional[dict[str, float]] = None

    short_rank: Optional[int] = None
    medium_rank: Optional[int] = None
    long_rank: Optional[int] = None


class UnifiedTracksResponse(SQLModel):
    tracks: dict[str, UnifiedTrack]



class FaixaEmocional(SQLModel):
    id_faixa: str = Field(primary_key=True, max_length=50)
    nome_faixa: str = Field(max_length=255)
    emocoes: Optional[Any] = Field(default=None, sa_type=JSON)
    duracao_ms: int
    popularidade: int
    album: str = Field(max_length=255)
    link_imagem: str = Field(max_length=255)
    letra_faixa: Optional[str] = Field(default=None, sa_type=Text)
    artista_principal: str = Field(max_length=255)
    emocao_mais_alta: float | None = None
    analise: dict[str, Any] | None = None


    
