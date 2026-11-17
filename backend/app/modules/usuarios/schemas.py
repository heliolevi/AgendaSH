from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.core.email_policy import validar_email_undb


class UsuarioCreate(BaseModel):
    nome: str = Field(min_length=1, max_length=100)
    email: str = Field(max_length=100)
    senha: str = Field(min_length=6)
    codigo: str = Field(pattern=r"^\d{6}$", description="Codigo de 6 digitos enviado por e-mail (POST /auth/cadastro/enviar-codigo)")

    @field_validator("email")
    @classmethod
    def email_da_undb(cls, v: str) -> str:
        return validar_email_undb(v)[0]  # so e-mail institucional da UNDB; ja volta em minusculas


class UsuarioUpdate(BaseModel):
    nome: str | None = Field(default=None, max_length=100)
    email: str | None = Field(default=None, max_length=100)

    @field_validator("email")
    @classmethod
    def email_da_undb(cls, v: str | None) -> str | None:
        return None if v is None else validar_email_undb(v)[0]


class UsuarioOut(BaseModel):
    id_usuario: int
    nome: str
    email: str
    criado_em: datetime | None = None
    papel: str | None = None
