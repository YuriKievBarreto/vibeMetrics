from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship



class UsuarioTopArtista(SQLModel, table=True):
    __tablename__ = "usuario_top_artista"

    id_usuario: str = Field(foreign_key="usuario.id_usuario", primary_key=True)
    id_artista: str = Field(foreign_key="artista.id_artista", primary_key=True)

    short_time_rank: Optional[int] = Field(default=None)
    medium_time_rank: Optional[int] = Field(default=None)
    long_time_rank: Optional[int] = Field(default=None)

    usuario: "Usuario" = Relationship(back_populates="top_artistas_rel")
    artista: "Artista" = Relationship(back_populates="top_usuarios_rel")


class UsuarioTopArtistaCreate(SQLModel):
   
    id_usuario: str 
    id_artista: str  
    
    time_range: str
    rank: int



