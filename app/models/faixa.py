from sqlalchemy import String, JSON, Integer, Text
from sqlalchemy.orm import  Mapped, mapped_column, relationship
from sqlmodel import SQLModel, Field, Relationship
from typing import List, Optional, Dict
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
    
    id_faixa: str = Field(..., alias='id') 
    nome_faixa: str = Field(..., alias='name')
    emocoes: Optional[Dict[str, float]] = None
    album: str = Field(..., alias='album') 
    popularidade: int 
    duracao_ms: int 
    link_imagem: str = Field(..., alias='link_imagem')
    letra_faixa:  str = Field(..., alias='letra_faixa')
    artista_principal: str = Field(..., alias='artista_principal')
    

    class Config:
        populate_by_name = True 
        extra = 'ignore'