from datetime import datetime

from pydantic import BaseModel, Field


class UsuarioCreate(BaseModel):
    nome: str = Field(min_length=1, max_length=100)
    email: str = Field(max_length=100)
    senha: str = Field(min_length=6)


class UsuarioUpdate(BaseModel):
    nome: str | None = Field(default=None, max_length=100)
    email: str | None = Field(default=None, max_length=100)


class UsuarioOut(BaseModel):
    id_usuario: int
    nome: str
    email: str
    criado_em: datetime | None = None
