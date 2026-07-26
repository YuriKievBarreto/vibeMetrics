from sqlalchemy import  Integer, String
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, Optional
from sqlmodel import SQLModel, Field, Relationship

class Artista(SQLModel, table=True):
    __tablename__ = "artista"

    id_artista: str = Field(max_length=50, primary_key=True)
    nome_artista: str = Field(max_length=50)
    popularidade_artista: int
    link_imagem: str = Field(max_length=250)
    generos: List[str] = Field(sa_type=postgresql.ARRAY(String))

    top_usuarios_rel: List["UsuarioTopArtista"] = Relationship(back_populates="artista")


class ArtistaCreate(SQLModel):
    id_artista: str = Field(...) 
    nome_artista: str = Field(...) 
    popularidade_artista: int
    link_imagem: str
    generos: List[str]
    class Config:
        populate_by_name = True 
        extra = 'ignore'


class UnifiedArtist(SQLModel):
    id_artista: Optional[str] = None
    nome_artista: str
    link_imagem: str | None = None
    generos: list[str]
    popularidade_artista: int

    short_rank: int | None = None
    medium_rank: int | None = None
    long_rank: int | None = None

class UnifiedArtistsResponse(SQLModel):
    artists: dict[str, UnifiedArtist]


